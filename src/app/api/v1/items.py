from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.models.item import Item, ItemStatus
from app.models.bid import Bid
from app.schemas.item import ItemCreateReq, ItemUpdateReq, ItemRes
from app.schemas.common import PageRes

router = APIRouter(prefix="/items")

def _apply_sort(query, sort: str):
    # sort="createdAt,DESC" 형태
    field, direction = (sort.split(",") + ["DESC"])[:2]
    direction = direction.upper()

    mapping = {
        "createdAt": Item.created_at,
        "endsAt": Item.ends_at,
        "startPrice": Item.start_price,
        "title": Item.title,
    }
    col = mapping.get(field)
    if not col:
        raise AppError(400, "INVALID_QUERY_PARAM", "sort 값이 올바르지 않습니다.", {"sort": sort})

    return query.order_by(desc(col) if direction == "DESC" else asc(col))

@router.post("", response_model=ItemRes)
def create_item(payload: ItemCreateReq, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = Item(
        seller_id=me.id,
        category_id=payload.categoryId,
        title=payload.title,
        description=payload.description,
        start_price=payload.startPrice,
        bid_unit=payload.bidUnit,
        status=ItemStatus.DRAFT,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ItemRes(
        id=item.id, sellerId=item.seller_id, categoryId=item.category_id, title=item.title,
        startPrice=item.start_price, bidUnit=item.bid_unit, status=item.status.value,
        endsAt=item.ends_at, createdAt=item.created_at
    )

@router.get("", response_model=PageRes[ItemRes])
def list_items(
    db: Session = Depends(get_db),
    page: int = 0,
    size: int = 20,
    sort: str = "createdAt,DESC",
    keyword: str | None = None,
    categoryId: int | None = None,
    status: str | None = None,
    minPrice: int | None = None,
    maxPrice: int | None = None,
):
    if size > 100:
        raise AppError(400, "INVALID_QUERY_PARAM", "size는 최대 100입니다.", {"size": size})

    q = select(Item)

    if keyword:
        q = q.where(Item.title.like(f"%{keyword}%"))
    if categoryId:
        q = q.where(Item.category_id == categoryId)
    if status:
        try:
            q = q.where(Item.status == ItemStatus(status))
        except Exception:
            raise AppError(400, "INVALID_QUERY_PARAM", "status 값이 올바르지 않습니다.", {"status": status})
    if minPrice is not None:
        q = q.where(Item.start_price >= minPrice)
    if maxPrice is not None:
        q = q.where(Item.start_price <= maxPrice)

    count_q = select(func.count()).select_from(q.subquery())
    total = db.scalar(count_q)

    q = _apply_sort(q, sort).offset(page * size).limit(size)
    items = db.scalars(q).all()

    content = [
        ItemRes(
            id=i.id, sellerId=i.seller_id, categoryId=i.category_id, title=i.title,
            startPrice=i.start_price, bidUnit=i.bid_unit, status=i.status.value,
            endsAt=i.ends_at, createdAt=i.created_at
        )
        for i in items
    ]
    total_pages = (total + size - 1) // size if total else 0

    return PageRes[ItemRes](
        content=content, page=page, size=size,
        totalElements=total, totalPages=total_pages, sort=sort
    )

@router.get("/{item_id}", response_model=ItemRes)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    return ItemRes(
        id=item.id, sellerId=item.seller_id, categoryId=item.category_id, title=item.title,
        startPrice=item.start_price, bidUnit=item.bid_unit, status=item.status.value,
        endsAt=item.ends_at, createdAt=item.created_at
    )

@router.patch("/{item_id}", response_model=ItemRes)
def update_item(item_id: int, payload: ItemUpdateReq, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.seller_id != me.id:
        raise AppError(403, "FORBIDDEN", "본인 아이템만 수정할 수 있습니다.")
    if item.status != ItemStatus.DRAFT:
        raise AppError(409, "STATE_CONFLICT", "경매가 시작된 아이템은 수정할 수 없습니다.")

    if payload.categoryId is not None:
        item.category_id = payload.categoryId
    if payload.title is not None:
        item.title = payload.title
    if payload.description is not None:
        item.description = payload.description
    if payload.bidUnit is not None:
        item.bid_unit = payload.bidUnit

    db.commit()
    db.refresh(item)
    return ItemRes(
        id=item.id, sellerId=item.seller_id, categoryId=item.category_id, title=item.title,
        startPrice=item.start_price, bidUnit=item.bid_unit, status=item.status.value,
        endsAt=item.ends_at, createdAt=item.created_at
    )

@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.seller_id != me.id:
        raise AppError(403, "FORBIDDEN", "본인 아이템만 삭제할 수 있습니다.")
    if item.status != ItemStatus.DRAFT:
        raise AppError(409, "STATE_CONFLICT", "경매가 시작된 아이템은 삭제할 수 없습니다.")
    db.delete(item)
    db.commit()
    return {"ok": True}

@router.post("/{item_id}/publish")
def publish_item(item_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.seller_id != me.id:
        raise AppError(403, "FORBIDDEN", "본인 아이템만 오픈할 수 있습니다.")
    if item.status != ItemStatus.DRAFT:
        raise AppError(409, "STATE_CONFLICT", "DRAFT 상태만 오픈할 수 있습니다.")

    now = datetime.now(timezone.utc)
    item.status = ItemStatus.OPEN
    item.starts_at = now
    item.ends_at = now + timedelta(days=3)  # 예: 3일 경매
    db.commit()
    return {"ok": True, "status": item.status.value, "endsAt": item.ends_at}

@router.post("/{item_id}/close")
def close_item(item_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.seller_id != me.id:
        raise AppError(403, "FORBIDDEN", "본인 아이템만 마감할 수 있습니다.")
    if item.status != ItemStatus.OPEN:
        raise AppError(409, "STATE_CONFLICT", "OPEN 상태만 마감할 수 있습니다.")

    item.status = ItemStatus.CLOSED
    db.commit()
    return {"ok": True, "status": item.status.value}

@router.get("/{item_id}/winner")
def winner(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.status != ItemStatus.CLOSED:
        raise AppError(409, "STATE_CONFLICT", "CLOSED 상태에서만 낙찰자를 조회할 수 있습니다.")

    top = db.scalar(
        select(Bid).where(Bid.item_id == item_id).order_by(Bid.amount.desc()).limit(1)
    )
    if not top:
        return {"itemId": item_id, "winnerUserId": None, "price": item.start_price}
    return {"itemId": item_id, "winnerUserId": top.bidder_id, "price": top.amount}
