from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    """返回无时区的 UTC 时间，便于直接存入 MySQL DATETIME。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column("bookmark_id", BigInteger, ForeignKey("bookmarks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    children = relationship("Category", passive_deletes=True)
    bookmarks = relationship("Bookmark", back_populates="category", passive_deletes=True)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    url_hash = Column(String(64), nullable=False, unique=True)
    title = Column(String(512), nullable=False)
    description = Column(Text)
    content_markdown = Column(LONGTEXT)
    content_text = Column(LONGTEXT)
    favicon_url = Column(String(2048), default="")
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    is_favorite = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    category = relationship("Category", back_populates="bookmarks", lazy="selectin")
    tags = relationship("Tag", secondary=bookmark_tags, lazy="selectin")


class BookmarkOrder(Base):
    __tablename__ = "bookmark_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(64), nullable=False, index=True)
    bookmark_id = Column(BigInteger, ForeignKey("bookmarks.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("scope", "bookmark_id", name="uq_bookmark_order_scope_bookmark"),)
