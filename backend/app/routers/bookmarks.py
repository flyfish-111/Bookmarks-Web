import asyncio
import hashlib
import html as html_lib
import json

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Bookmark, BookmarkOrder, Category, Tag, User, bookmark_tags, utcnow
from ..schemas import (
    BookmarkCreate,
    BookmarkListOut,
    BookmarkOut,
    BookmarkUpdate,
    ImportRequest,
    ImportResult,
    ReorderPayload,
)
from ..security import get_current_user
from ..services.extractor import _md_to_text, extract_content, extract_metadata
from ..services.fetcher import FetchError, fetch_html

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


async def _get_or_create_tags(db: AsyncSession, names: list[str], user: User) -> list[Tag]:
    tags: list[Tag] = []
    seen: set[str] = set()
    for raw in names:
        name = (raw or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result = await db.execute(select(Tag).where(Tag.user_id == user.id, Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name, user_id=user.id)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


async def _get_or_create_category(db: AsyncSession, name: str, user: User) -> Category:
    name = name.strip()
    result = await db.execute(select(Category).where(Category.user_id == user.id, Category.name == name))
    category = result.scalar_one_or_none()
    if not category:
        category = Category(name=name, user_id=user.id)
        db.add(category)
        await db.flush()
    return category


async def _get_bookmark(db: AsyncSession, bookmark_id: int, user: User) -> Bookmark | None:
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id))
    return result.scalar_one_or_none()


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def _get_bookmark_by_url(db: AsyncSession, url: str, user: User) -> Bookmark | None:
    result = await db.execute(
        select(Bookmark).where(Bookmark.url_hash == _url_hash(url), Bookmark.user_id == user.id)
    )
    return result.scalar_one_or_none()


def _bookmark_to_export_item(b: Bookmark) -> dict:
    return {
        "url": b.url,
        "title": b.title,
        "description": b.description or "",
        "content_markdown": b.content_markdown or "",
        "favicon_url": b.favicon_url or "",
        "is_favorite": b.is_favorite,
        "category_name": b.category.name if b.category else None,
        "tags": [t.name for t in b.tags],
    }


def _bookmarks_to_html(bookmarks: list[Bookmark]) -> str:
    """生成可导入浏览器（Chrome/Edge）的 Netscape 书签 HTML。"""
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>",
    ]
    by_cat: dict[str, list[Bookmark]] = {}
    uncategorized: list[Bookmark] = []
    for b in bookmarks:
        if b.category:
            by_cat.setdefault(b.category.name, []).append(b)
        else:
            uncategorized.append(b)

    def emit(items: list[Bookmark]) -> None:
        for b in items:
            lines.append(f'<DT><A HREF="{html_lib.escape(b.url)}">{html_lib.escape(b.title)}</A>')

    for cat, items in by_cat.items():
        lines.append(f"<DT><H3>{html_lib.escape(cat)}</H3>")
        lines.append("<DL><p>")
        emit(items)
        lines.append("</DL><p>")
    if uncategorized:
        emit(uncategorized)
    lines.append("</DL><p>")
    return "\n".join(lines)


def _detect_import_format(text: str) -> str:
    t = text.lstrip()
    if t.startswith("[") or t.startswith("{"):
        return "json"
    if "NETSCAPE" in t.upper() or "<DT><A" in t.upper() or "<A " in t.upper():
        return "html"
    return "txt"


def _parse_html_bookmarks(text: str) -> list[dict]:
    soup = BeautifulSoup(text, "html.parser")
    items: list[dict] = []
    category: str | None = None
    for node in soup.find_all(["h3", "a"]):
        if node.name == "h3":
            category = node.get_text(strip=True) or None
        elif node.name == "a":
            href = node.get("href")
            if href:
                title = node.get_text(strip=True) or href
                items.append({"url": href, "title": title, "category_name": category})
    return items


def _parse_txt_bookmarks(text: str) -> list[dict]:
    """解析纯文本网址列表：每行一个网址，可附带标题（用空格/制表符分隔），# 开头为注释。"""
    items: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        url = parts[0]
        title = parts[1].strip() if len(parts) > 1 else ""
        # 跳过明显不是网址的行（既无协议也无点号）
        if "://" not in url and "." not in url:
            continue
        items.append({"url": url, "title": title})
    return items


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


async def _fetch_one_for_import(url: str) -> dict | None:
    """抓取单个网址的标题/描述/正文/favicon，任何失败都返回 None（不阻断导入）。"""
    try:
        final_url, html = await fetch_html(url, timeout=8.0)
    except Exception:
        return None
    try:
        title, description, favicon = extract_metadata(html, final_url)
        content_markdown, content_text = extract_content(html, final_url)
    except Exception:
        title, description, favicon = "", "", ""
        content_markdown, content_text = "", ""
    return {
        "title": title,
        "description": description,
        "content_markdown": content_markdown,
        "content_text": content_text,
        "favicon_url": favicon,
    }


async def _fetch_many(urls: list[str], concurrency: int = 8) -> dict[str, dict]:
    """并发抓取多个网址，返回 {url: 抓取结果}（失败的不在其中）。"""
    sem = asyncio.Semaphore(concurrency)

    async def one(url: str) -> tuple[str, dict | None]:
        async with sem:
            return url, await _fetch_one_for_import(url)

    results = await asyncio.gather(*[one(u) for u in urls])
    return {u: info for u, info in results if info}


@router.post("", response_model=BookmarkOut)
async def create_bookmark(
    payload: BookmarkCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    existing = await _get_bookmark_by_url(db, url, user)
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    try:
        final_url, html = await fetch_html(url)
    except FetchError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(status_code=422, detail="网络请求失败，请检查网址是否可达")

    # 正文提取失败不阻断收藏，退化为空正文
    try:
        title, description, favicon = extract_metadata(html, final_url)
        content_markdown, content_text = extract_content(html, final_url)
    except Exception:
        title, description, favicon = "", "", ""
        content_markdown, content_text = "", ""

    min_order = (await db.execute(select(func.min(Bookmark.sort_order)).where(Bookmark.user_id == user.id))).scalar()
    bookmark = Bookmark(
        url=url,
        url_hash=_url_hash(url),
        title=(title or "").strip() or url,
        description=description or "",
        content_markdown=content_markdown or "",
        content_text=content_text or "",
        favicon_url=favicon or "",
        sort_order=(min_order - 1) if min_order is not None else 0,
        user_id=user.id,
    )
    if payload.category_name and payload.category_name.strip():
        bookmark.category = await _get_or_create_category(db, payload.category_name, user)
    if payload.tags:
        bookmark.tags = await _get_or_create_tags(db, payload.tags, user)

    db.add(bookmark)
    await db.commit()
    response.status_code = status.HTTP_201_CREATED
    return await _get_bookmark(db, bookmark.id, user)


@router.get("", response_model=BookmarkListOut)
async def list_bookmarks(
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    uncategorized: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Bookmark.user_id == user.id]
    if category_id is not None:
        conditions.append(Bookmark.category_id == category_id)
    if is_favorite is not None:
        conditions.append(Bookmark.is_favorite == is_favorite)
    if uncategorized:
        conditions.append(Bookmark.category_id.is_(None))
    if tag_id is not None:
        conditions.append(
            Bookmark.id.in_(select(bookmark_tags.c.bookmark_id).where(bookmark_tags.c.tag_id == tag_id))
        )
    if q:
        kw = q.strip()
        if kw:
            like = f"%{kw}%"
            conditions.append(
                or_(Bookmark.title.like(like), Bookmark.description.like(like), Bookmark.content_text.like(like))
            )

    total = (await db.execute(select(func.count(Bookmark.id)).where(*conditions))).scalar() or 0

    # 分类/标签视图下按该作用域的手动顺序排，未手动排序的按全局顺序兜底
    scope = None
    if tag_id is not None:
        scope = f"tag:{tag_id}"
    elif category_id is not None:
        scope = f"cat:{category_id}"

    stmt = select(Bookmark).where(*conditions)
    if scope:
        stmt = (
            stmt.outerjoin(
                BookmarkOrder,
                and_(BookmarkOrder.scope == scope, BookmarkOrder.bookmark_id == Bookmark.id),
            )
            .order_by(
                BookmarkOrder.position.is_(None),
                BookmarkOrder.position.asc(),
                Bookmark.sort_order.asc(),
                Bookmark.created_at.desc(),
            )
        )
    else:
        stmt = stmt.order_by(Bookmark.sort_order.asc(), Bookmark.created_at.desc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()
    return BookmarkListOut(items=items, total=total, page=page, page_size=page_size)


@router.put("/reorder", status_code=204)
async def reorder_bookmarks(
    payload: ReorderPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not payload.ids:
        return
    owned = (
        await db.execute(select(Bookmark.id).where(Bookmark.id.in_(payload.ids), Bookmark.user_id == user.id))
    ).scalars().all()
    if len(owned) != len(payload.ids):
        raise HTTPException(status_code=404, detail="存在不属于你的收藏")

    if payload.scope == "all":
        for index, bookmark_id in enumerate(payload.ids):
            await db.execute(
                update(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id).values(sort_order=index)
            )
    else:
        await db.execute(delete(BookmarkOrder).where(BookmarkOrder.scope == payload.scope))
        for index, bookmark_id in enumerate(payload.ids):
            db.add(BookmarkOrder(scope=payload.scope, bookmark_id=bookmark_id, position=index))
    await db.commit()


@router.get("/export")
async def export_bookmarks(
    format: str = Query(default="json"),
    category_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出收藏：json（完整备份）或 html（可导入浏览器）；可按分类/标签过滤。"""
    conditions = [Bookmark.user_id == user.id]
    if category_id is not None:
        conditions.append(Bookmark.category_id == category_id)
    if tag_id is not None:
        conditions.append(
            Bookmark.id.in_(select(bookmark_tags.c.bookmark_id).where(bookmark_tags.c.tag_id == tag_id))
        )

    bookmarks = (
        await db.execute(
            select(Bookmark).where(*conditions).order_by(Bookmark.sort_order, Bookmark.created_at.desc())
        )
    ).scalars().all()

    if format == "html":
        content = _bookmarks_to_html(bookmarks)
        return Response(
            content=content,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="bookmarks.html"'},
        )
    if format == "txt":
        content = "\n".join(b.url for b in bookmarks)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="bookmarks.txt"'},
        )
    return [_bookmark_to_export_item(b) for b in bookmarks]


@router.post("/import", response_model=ImportResult)
async def import_bookmarks(
    payload: ImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导入收藏（JSON 备份 / 浏览器书签 HTML / 纯文本网址列表），按 url 去重，txt/html 自动抓取页面信息。"""
    text = payload.data or ""
    fmt = _detect_import_format(text)

    if fmt == "json":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="JSON 解析失败")
        if isinstance(raw, dict):
            raw = raw.get("bookmarks", raw)
        if not isinstance(raw, list):
            raise HTTPException(status_code=422, detail="JSON 结构不正确")
        items = [i for i in raw if isinstance(i, dict)]
    elif fmt == "html":
        items = _parse_html_bookmarks(text)
    else:
        items = _parse_txt_bookmarks(text)

    # 规范化 + 去重
    to_import: list[tuple[dict, str]] = []
    skipped = 0
    seen: set[str] = set()
    for item in items:
        url = _normalize_url(item.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        if await _get_bookmark_by_url(db, url, user):
            skipped += 1
            continue
        to_import.append((item, url))

    # txt/html 自动抓取页面信息；json 已含正文，无需抓取
    fetched: dict[str, dict] = {}
    if to_import and fmt != "json":
        fetched = await _fetch_many([u for _, u in to_import])

    min_order = (await db.execute(select(func.min(Bookmark.sort_order)).where(Bookmark.user_id == user.id))).scalar()
    next_order = (min_order - 1) if min_order is not None else 0

    imported = 0
    for item, url in to_import:
        info = fetched.get(url)
        if info:
            title = (info["title"] or "").strip() or url
            description = info["description"] or ""
            content_markdown = info["content_markdown"] or ""
            content_text = info["content_text"] or ""
            favicon_url = info["favicon_url"] or ""
        else:
            title = (item.get("title") or "").strip() or url
            description = item.get("description") or ""
            content_markdown = item.get("content_markdown") or ""
            content_text = _md_to_text(content_markdown)
            favicon_url = item.get("favicon_url") or ""

        category_name = item.get("category_name")
        tags = item.get("tags") or []

        bookmark = Bookmark(
            url=url,
            url_hash=_url_hash(url),
            title=title,
            description=description,
            content_markdown=content_markdown,
            content_text=content_text,
            favicon_url=favicon_url,
            is_favorite=bool(item.get("is_favorite", False)),
            sort_order=next_order,
            user_id=user.id,
        )
        if category_name and str(category_name).strip():
            bookmark.category = await _get_or_create_category(db, str(category_name), user)
        if tags:
            bookmark.tags = await _get_or_create_tags(db, [str(t) for t in tags], user)

        db.add(bookmark)
        next_order -= 1
        imported += 1

    await db.commit()
    return ImportResult(imported=imported, skipped=skipped)


@router.get("/{bookmark_id}", response_model=BookmarkOut)
async def get_bookmark(bookmark_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id, user)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return bookmark


@router.put("/{bookmark_id}", response_model=BookmarkOut)
async def update_bookmark(
    bookmark_id: int,
    payload: BookmarkUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookmark = await _get_bookmark(db, bookmark_id, user)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")

    data = payload.model_dump(exclude_unset=True)
    tags = data.pop("tags", None)
    has_category = "category_name" in data
    category_name = data.pop("category_name", None)
    for key, value in data.items():
        setattr(bookmark, key, value)
    bookmark.updated_at = utcnow()
    if has_category:
        if category_name and category_name.strip():
            category = await _get_or_create_category(db, category_name, user)
            bookmark.category = category
        else:
            bookmark.category = None
    if tags is not None:
        bookmark.tags = await _get_or_create_tags(db, tags, user)

    await db.commit()
    return await _get_bookmark(db, bookmark_id, user)


@router.post("/{bookmark_id}/refetch", response_model=BookmarkOut)
async def refetch_bookmark(
    bookmark_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    bookmark = await _get_bookmark(db, bookmark_id, user)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")

    try:
        final_url, html = await fetch_html(bookmark.url)
    except FetchError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except httpx.HTTPError:
        raise HTTPException(status_code=422, detail="网络请求失败，请检查网址是否可达")

    try:
        title, description, favicon = extract_metadata(html, final_url)
        content_markdown, content_text = extract_content(html, final_url)
    except Exception:
        title, description, favicon = "", "", ""
        content_markdown, content_text = "", ""

    if title:
        bookmark.title = title
    bookmark.description = description or bookmark.description
    bookmark.content_markdown = content_markdown
    bookmark.content_text = content_text
    if favicon:
        bookmark.favicon_url = favicon
    bookmark.updated_at = utcnow()
    await db.commit()
    return await _get_bookmark(db, bookmark.id, user)


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(bookmark_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id, user)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    await db.delete(bookmark)
    await db.commit()
