from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.models.item import Item
from app.models.watch import Watch
from app.schemas.watch import WatchItemRes

router = APIRouter(prefix="")

@router.post("/items/{item_id}/watch")
def watch_item(item_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    exists = db.get(Watch, {"user_id": me.id, "item_id": item_id})
    if exists:
        raise AppError(409, "DUPLICATE_RESOURCE", "이미 찜한 아이템입니다.")
    w = Watch(user_id=me.id, item_id=item_id)
    db.add(w)
    db.commit()
    return {"ok": True}

@router.delete("/items/{item_id}/watch")
def unwatch_item(item_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    w = db.get(Watch, {"user_id": me.id, "item_id": item_id})
    if not w:
        raise AppError(404, "RESOURCE_NOT_FOUND", "찜 정보가 없습니다.")
    db.delete(w)
    db.commit()
    return {"ok": True}

@router.get("/users/me/watches", response_model=list[WatchItemRes])
def my_watches(db: Session = Depends(get_db), me=Depends(get_current_user)):
    rows = db.scalars(select(Watch).where(Watch.user_id == me.id).order_by(Watch.created_at.desc())).all()
    return [WatchItemRes(itemId=r.item_id, watchedAt=r.created_at) for r in rows]
