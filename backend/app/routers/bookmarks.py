import hashlib

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Bookmark, BookmarkOrder, Category, Tag, bookmark_tags, utcnow
from ..schemas import BookmarkCreate, BookmarkListOut, BookmarkOut, BookmarkUpdate, ReorderPayload
from ..services.extractor import extract_content, extract_metadata
from ..services.fetcher import FetchError, fetch_html

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


async def _get_or_create_tags(db: AsyncSession, names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    seen: set[str] = set()
    for raw in names:
        name = (raw or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


async def _get_or_create_category(db: AsyncSession, name: str) -> Category:
    name = name.strip()
    result = await db.execute(select(Category).where(Category.name == name))
    category = result.scalar_one_or_none()
    if not category:
        category = Category(name=name)
        db.add(category)
        await db.flush()
    return category


async def _get_bookmark(db: AsyncSession, bookmark_id: int) -> Bookmark | None:
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    return result.scalar_one_or_none()


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def _get_bookmark_by_url(db: AsyncSession, url: str) -> Bookmark | None:
    result = await db.execute(select(Bookmark).where(Bookmark.url_hash == _url_hash(url)))
    return result.scalar_one_or_none()


@router.post("", response_model=BookmarkOut)
async def create_bookmark(payload: BookmarkCreate, response: Response, db: AsyncSession = Depends(get_db)):
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    existing = await _get_bookmark_by_url(db, url)
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

    min_order = (await db.execute(select(func.min(Bookmark.sort_order)))).scalar()
    bookmark = Bookmark(
        url=url,
        url_hash=_url_hash(url),
        title=(title or "").strip() or url,
        description=description or "",
        content_markdown=content_markdown or "",
        content_text=content_text or "",
        favicon_url=favicon or "",
        sort_order=(min_order - 1) if min_order is not None else 0,
    )
    if payload.category_name and payload.category_name.strip():
        bookmark.category = await _get_or_create_category(db, payload.category_name)
    if payload.tags:
        bookmark.tags = await _get_or_create_tags(db, payload.tags)

    db.add(bookmark)
    await db.commit()
    response.status_code = status.HTTP_201_CREATED
    return await _get_bookmark(db, bookmark.id)


@router.get("", response_model=BookmarkListOut)
async def list_bookmarks(
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    uncategorized: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
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
async def reorder_bookmarks(payload: ReorderPayload, db: AsyncSession = Depends(get_db)):
    if payload.scope == "all":
        for index, bookmark_id in enumerate(payload.ids):
            await db.execute(update(Bookmark).where(Bookmark.id == bookmark_id).values(sort_order=index))
    else:
        await db.execute(delete(BookmarkOrder).where(BookmarkOrder.scope == payload.scope))
        for index, bookmark_id in enumerate(payload.ids):
            db.add(BookmarkOrder(scope=payload.scope, bookmark_id=bookmark_id, position=index))
    await db.commit()


@router.get("/{bookmark_id}", response_model=BookmarkOut)
async def get_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return bookmark


@router.put("/{bookmark_id}", response_model=BookmarkOut)
async def update_bookmark(bookmark_id: int, payload: BookmarkUpdate, db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id)
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
            category = await _get_or_create_category(db, category_name)
            bookmark.category = category
        else:
            bookmark.category = None
    if tags is not None:
        bookmark.tags = await _get_or_create_tags(db, tags)

    await db.commit()
    return await _get_bookmark(db, bookmark_id)


@router.post("/{bookmark_id}/refetch", response_model=BookmarkOut)
async def refetch_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id)
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
    return await _get_bookmark(db, bookmark.id)


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    bookmark = await _get_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="收藏不存在")
    await db.delete(bookmark)
    await db.commit()
