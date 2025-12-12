from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import require_admin
from app.core.errors import AppError
from app.models.category import Category
from app.schemas.category import CategoryCreateReq, CategoryUpdateReq, CategoryRes

router = APIRouter(prefix="/categories")

@router.post("", response_model=CategoryRes)
def create_category(payload: CategoryCreateReq, db: Session = Depends(get_db), _=Depends(require_admin)):
    exists = db.scalar(select(Category).where(Category.name == payload.name))
    if exists:
        raise AppError(409, "DUPLICATE_RESOURCE", "이미 존재하는 카테고리입니다.", {"name": "duplicate"})
    c = Category(name=payload.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return CategoryRes(id=c.id, name=c.name)

@router.get("", response_model=list[CategoryRes])
def list_categories(db: Session = Depends(get_db)):
    cats = db.scalars(select(Category).order_by(Category.name.asc())).all()
    return [CategoryRes(id=c.id, name=c.name) for c in cats]

@router.patch("/{category_id}", response_model=CategoryRes)
def update_category(category_id: int, payload: CategoryUpdateReq, db: Session = Depends(get_db), _=Depends(require_admin)):
    c = db.get(Category, category_id)
    if not c:
        raise AppError(404, "RESOURCE_NOT_FOUND", "카테고리를 찾을 수 없습니다.")
    exists = db.scalar(select(Category).where(Category.name == payload.name, Category.id != category_id))
    if exists:
        raise AppError(409, "DUPLICATE_RESOURCE", "이미 존재하는 카테고리입니다.", {"name": "duplicate"})
    c.name = payload.name
    db.commit()
    db.refresh(c)
    return CategoryRes(id=c.id, name=c.name)

@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    c = db.get(Category, category_id)
    if not c:
        raise AppError(404, "RESOURCE_NOT_FOUND", "카테고리를 찾을 수 없습니다.")
    db.delete(c)
    db.commit()
    return {"ok": True}
