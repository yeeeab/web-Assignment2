from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.models.item import Item, ItemStatus
from app.models.bid import Bid
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreateReq, OrderRes
from app.schemas.common import PageRes

router = APIRouter(prefix="")

def _winner_bid(db: Session, item_id: int):
    return db.scalar(select(Bid).where(Bid.item_id == item_id).order_by(Bid.amount.desc()).limit(1))

@router.post("/items/{item_id}/orders", response_model=OrderRes)
def create_order(item_id: int, payload: OrderCreateReq, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.status != ItemStatus.CLOSED:
        raise AppError(409, "STATE_CONFLICT", "마감된 아이템만 주문을 생성할 수 있습니다.")

    top = _winner_bid(db, item_id)
    if not top:
        raise AppError(422, "UNPROCESSABLE_ENTITY", "입찰이 없어 낙찰자가 없습니다.")
    if top.bidder_id != me.id:
        raise AppError(403, "FORBIDDEN", "낙찰자만 주문을 생성할 수 있습니다.")

    # 중복 주문 방지 (uq_orders_item_id)
    exists = db.scalar(select(Order).where(Order.item_id == item_id))
    if exists:
        raise AppError(409, "STATE_CONFLICT", "이미 주문이 생성된 아이템입니다.")

    order = Order(
        item_id=item_id,
        buyer_id=me.id,
        total_price=top.amount,
        address=payload.address,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return OrderRes(
        id=order.id, itemId=order.item_id, buyerId=order.buyer_id,
        status=order.status.value, totalPrice=order.total_price,
        address=order.address, createdAt=order.created_at
    )

@router.get("/orders", response_model=PageRes[OrderRes])
def list_my_orders(
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
    page: int = 0,
    size: int = 20,
    sort: str = "createdAt,DESC",
    status: str | None = None,
):
    if size > 100:
        raise AppError(400, "INVALID_QUERY_PARAM", "size는 최대 100입니다.", {"size": size})

    q = select(Order).where(Order.buyer_id == me.id)
    if status:
        try:
            q = q.where(Order.status == OrderStatus(status))
        except Exception:
            raise AppError(400, "INVALID_QUERY_PARAM", "status 값이 올바르지 않습니다.", {"status": status})

    total = db.scalar(select(func.count()).select_from(q.subquery()))

    if sort == "createdAt,DESC":
        q = q.order_by(Order.created_at.desc())
    elif sort == "createdAt,ASC":
        q = q.order_by(Order.created_at.asc())
    else:
        raise AppError(400, "INVALID_QUERY_PARAM", "sort 값이 올바르지 않습니다.", {"sort": sort})

    rows = db.scalars(q.offset(page * size).limit(size)).all()
    content = [
        OrderRes(
            id=o.id, itemId=o.item_id, buyerId=o.buyer_id,
            status=o.status.value, totalPrice=o.total_price,
            address=o.address, createdAt=o.created_at
        )
        for o in rows
    ]
    total_pages = (total + size - 1) // size if total else 0
    return PageRes[OrderRes](content=content, page=page, size=size, totalElements=total, totalPages=total_pages, sort=sort)

@router.get("/orders/{order_id}", response_model=OrderRes)
def get_order(order_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    o = db.get(Order, order_id)
    if not o or o.buyer_id != me.id:
        raise AppError(404, "RESOURCE_NOT_FOUND", "주문을 찾을 수 없습니다.")
    return OrderRes(
        id=o.id, itemId=o.item_id, buyerId=o.buyer_id,
        status=o.status.value, totalPrice=o.total_price,
        address=o.address, createdAt=o.created_at
    )

@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), me=Depends(get_current_user)):
    o = db.get(Order, order_id)
    if not o or o.buyer_id != me.id:
        raise AppError(404, "RESOURCE_NOT_FOUND", "주문을 찾을 수 없습니다.")
    if o.status not in (OrderStatus.PENDING, OrderStatus.PAID):
        raise AppError(409, "STATE_CONFLICT", "취소할 수 없는 상태입니다.", {"status": o.status.value})
    o.status = OrderStatus.CANCELLED
    db.commit()
    return {"ok": True, "status": o.status.value}
