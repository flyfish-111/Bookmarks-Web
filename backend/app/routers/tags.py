from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Tag, User, bookmark_tags
from ..schemas import TagOut, TagWithCount
from ..security import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get("", response_model=list[TagWithCount])
async def list_tags(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Tag, func.count(bookmark_tags.c.bookmark_id))
        .outerjoin(bookmark_tags, bookmark_tags.c.tag_id == Tag.id)
        .where(Tag.user_id == user.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    rows = (await db.execute(stmt)).all()
    return [TagWithCount(id=t.id, name=t.name, count=c) for t, c in rows]


@router.post("", response_model=TagOut, status_code=201)
async def create_tag(payload: TagCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="标签名不能为空")
    existing = (
        await db.execute(select(Tag).where(Tag.user_id == user.id, Tag.name == name))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag = Tag(name=name, user_id=user.id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagOut)
async def rename_tag(
    tag_id: int, payload: TagCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="标签名不能为空")
    tag = (
        await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id))
    ).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    existing = (
        await db.execute(select(Tag).where(Tag.user_id == user.id, Tag.name == name, Tag.id != tag_id))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag.name = name
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tag = (
        await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id))
    ).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await db.commit()
