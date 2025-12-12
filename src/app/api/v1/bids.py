from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.models.item import Item, ItemStatus
from app.models.bid import Bid
from app.schemas.bid import BidCreateReq, BidRes
from app.schemas.common import PageRes

router = APIRouter(prefix="")

@router.post("/items/{item_id}/bids", response_model=BidRes)
def place_bid(item_id: int, payload: BidCreateReq, db: Session = Depends(get_db), me=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")

    if item.status != ItemStatus.OPEN:
        raise AppError(409, "STATE_CONFLICT", "경매 진행 중인 아이템만 입찰할 수 있습니다.")

    if item.seller_id == me.id:
        raise AppError(403, "FORBIDDEN", "판매자는 자기 아이템에 입찰할 수 없습니다.")

    # 현재 최고가 조회
    highest = db.scalar(select(func.max(Bid.amount)).where(Bid.item_id == item_id))
    current = highest if highest is not None else item.start_price

    # 최소 입찰가 = 현재가 + bid_unit
    min_bid = current + item.bid_unit
    if payload.amount < min_bid:
        raise AppError(422, "UNPROCESSABLE_ENTITY", "입찰 금액이 너무 낮습니다.", {"minBid": min_bid})

    # bid_unit 배수 검증(선택이지만 과제용으로 좋음)
    if (payload.amount - item.start_price) % item.bid_unit != 0:
        raise AppError(422, "UNPROCESSABLE_ENTITY", "입찰 단위가 올바르지 않습니다.", {"bidUnit": item.bid_unit})

    bid = Bid(item_id=item_id, bidder_id=me.id, amount=payload.amount)
    db.add(bid)
    db.commit()
    db.refresh(bid)

    return BidRes(id=bid.id, itemId=bid.item_id, bidderId=bid.bidder_id, amount=bid.amount, createdAt=bid.created_at)

@router.get("/items/{item_id}/bids", response_model=PageRes[BidRes])
def list_bids(item_id: int, db: Session = Depends(get_db), page: int = 0, size: int = 20, sort: str = "amount,DESC"):
    if size > 100:
        raise AppError(400, "INVALID_QUERY_PARAM", "size는 최대 100입니다.", {"size": size})

    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")

    q = select(Bid).where(Bid.item_id == item_id)
    total = db.scalar(select(func.count()).select_from(q.subquery()))

    if sort == "amount,DESC":
        q = q.order_by(Bid.amount.desc())
    elif sort == "createdAt,DESC":
        q = q.order_by(Bid.created_at.desc())
    else:
        raise AppError(400, "INVALID_QUERY_PARAM", "sort 값이 올바르지 않습니다.", {"sort": sort})

    bids = db.scalars(q.offset(page * size).limit(size)).all()
    content = [BidRes(id=b.id, itemId=b.item_id, bidderId=b.bidder_id, amount=b.amount, createdAt=b.created_at) for b in bids]
    total_pages = (total + size - 1) // size if total else 0

    return PageRes[BidRes](content=content, page=page, size=size, totalElements=total, totalPages=total_pages, sort=sort)

@router.get("/items/{item_id}/bids/highest")
def highest_bid(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    highest = db.scalar(select(func.max(Bid.amount)).where(Bid.item_id == item_id))
    return {"itemId": item_id, "highestBid": highest if highest is not None else item.start_price}
