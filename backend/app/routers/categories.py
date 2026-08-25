from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Bookmark, Category
from ..schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Category, func.count(Bookmark.id))
        .outerjoin(Bookmark, Bookmark.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.sort_order, Category.id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        CategoryOut(id=c.id, name=c.name, parent_id=c.parent_id, sort_order=c.sort_order, count=cnt)
        for c, cnt in rows
    ]


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="分类名不能为空")
    if payload.parent_id is not None:
        parent = await db.get(Category, payload.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分类不存在")
    category = Category(name=name, parent_id=payload.parent_id, sort_order=payload.sort_order)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: int, payload: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    await db.delete(category)
    await db.commit()
