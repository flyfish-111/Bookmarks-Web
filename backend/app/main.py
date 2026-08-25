import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text, update

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Bookmark, Category, Tag, User
from .routers import auth, bookmarks, categories, tags
from .security import hash_password

logger = logging.getLogger("uvicorn.error")


async def _column_exists(conn, table: str, column: str) -> bool:
    result = await conn.execute(text(f"SHOW COLUMNS FROM {table} LIKE '{column}'"))
    return result.fetchone() is not None


async def _index_exists(conn, table: str, index_name: str) -> bool:
    rows = (await conn.execute(text(f"SHOW INDEX FROM {table}"))).fetchall()
    return any(r[2] == index_name for r in rows)


async def _migrate(conn) -> None:
    """轻量迁移：补充 sort_order / user_id 列，并将 tags.name 的唯一约束改为 (user_id, name)。"""
    # bookmarks.sort_order（历史列）
    if not await _column_exists(conn, "bookmarks", "sort_order"):
        await conn.execute(text("ALTER TABLE bookmarks ADD COLUMN sort_order INT NOT NULL DEFAULT 0"))

    # 三个业务表补 user_id 列（可空，存量数据随后归入管理员）
    for table in ("bookmarks", "categories", "tags"):
        if not await _column_exists(conn, table, "user_id"):
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INT NULL"))

    # bookmarks.user_id 加普通索引（列表查询最频繁）
    if not await _index_exists(conn, "bookmarks", "ix_bookmarks_user_id"):
        await conn.execute(text("ALTER TABLE bookmarks ADD INDEX ix_bookmarks_user_id (user_id)"))

    # tags：把「name 全局唯一」改成「(user_id, name) 每用户唯一」
    # SHOW INDEX 每列一行，按 Key_name 分组，找出「只含 name 一列」的唯一索引（旧的全局唯一）
    rows = (await conn.execute(text("SHOW INDEX FROM tags"))).fetchall()
    index_cols: dict[str, list[str]] = {}
    index_nonunique: dict[str, int] = {}
    for r in rows:
        index_cols.setdefault(r[2], []).append(r[4])  # r[2]=Key_name, r[4]=Column_name
        index_nonunique[r[2]] = r[1]  # r[1]=Non_unique
    old_name_index = next(
        (k for k, cols in index_cols.items() if index_nonunique.get(k) == 0 and cols == ["name"]),
        None,
    )
    if old_name_index:
        await conn.execute(text(f"ALTER TABLE tags DROP INDEX {old_name_index}"))
    if "uq_tags_user_name" not in index_cols:
        await conn.execute(text("ALTER TABLE tags ADD UNIQUE INDEX uq_tags_user_name (user_id, name)"))


async def init_db(retries: int = 10, delay: float = 3.0) -> None:
    """等待 MySQL 就绪后建表（幂等，重复启动不会重建已有表）。"""
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await _migrate(conn)
            return
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)


async def _bootstrap_admin() -> None:
    """引导管理员账号：配置了 ADMIN_USERNAME/ADMIN_PASSWORD 时创建（幂等），并把存量无归属数据归入它。"""
    if not (settings.admin_username and settings.admin_password):
        logger.warning("未配置 ADMIN_USERNAME / ADMIN_PASSWORD，跳过管理员引导；存量数据将保持无归属。")
        return

    async with SessionLocal() as session:
        username = settings.admin_username.strip()
        result = await session.execute(select(User).where(User.username == username))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(username=username, password_hash=hash_password(settings.admin_password))
            session.add(admin)
            await session.flush()

        admin_id = admin.id
        await session.execute(update(Bookmark).where(Bookmark.user_id.is_(None)).values(user_id=admin_id))
        await session.execute(update(Category).where(Category.user_id.is_(None)).values(user_id=admin_id))
        await session.execute(update(Tag).where(Tag.user_id.is_(None)).values(user_id=admin_id))
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _bootstrap_admin()
    yield
    await engine.dispose()


app = FastAPI(title="网址收藏夹", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(categories.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
