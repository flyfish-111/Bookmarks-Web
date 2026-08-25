import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import Base, engine
from .routers import bookmarks, categories, tags


async def _migrate(conn) -> None:
    """轻量迁移：为已有 bookmarks 表补充 sort_order 列。"""
    result = await conn.execute(text("SHOW COLUMNS FROM bookmarks LIKE 'sort_order'"))
    if not result.fetchone():
        await conn.execute(text("ALTER TABLE bookmarks ADD COLUMN sort_order INT NOT NULL DEFAULT 0"))


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title="网址收藏夹", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookmarks.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(categories.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
