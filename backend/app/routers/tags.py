from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Tag, bookmark_tags
from ..schemas import TagOut, TagWithCount

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get("", response_model=list[TagWithCount])
async def list_tags(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Tag, func.count(bookmark_tags.c.bookmark_id))
        .outerjoin(bookmark_tags, bookmark_tags.c.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    rows = (await db.execute(stmt)).all()
    return [TagWithCount(id=t.id, name=t.name, count=c) for t, c in rows]


@router.post("", response_model=TagOut, status_code=201)
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="标签名不能为空")
    existing = (await db.execute(select(Tag).where(Tag.name == name))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag = Tag(name=name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagOut)
async def rename_tag(tag_id: int, payload: TagCreate, db: AsyncSession = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="标签名不能为空")
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    existing = (await db.execute(select(Tag).where(Tag.name == name, Tag.id != tag_id))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag.name = name
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await db.commit()
