from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, cast, Date
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.api.deps import require_admin
from app.models.bid import Bid
from app.models.order import Order, OrderStatus

router = APIRouter(prefix="/stats")

@router.get("/items/top-bid-count")
def top_bid_count(db: Session = Depends(get_db), limit: int = 10):
    limit = min(max(limit, 1), 50)
    rows = db.execute(
        select(Bid.item_id, func.count(Bid.id).label("bidCount"))
        .group_by(Bid.item_id)
        .order_by(desc("bidCount"))
        .limit(limit)
    ).all()
    return {"content": [{"itemId": r[0], "bidCount": r[1]} for r in rows]}

@router.get("/sales/daily")
def daily_sales(db: Session = Depends(get_db), _=Depends(require_admin), days: int = 7):
    days = min(max(days, 1), 30)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # CANCELLED 제외, PENDING도 매출로 볼지 애매하니 PAID/SHIPPED/COMPLETED만 집계 추천
    valid = (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED)

    rows = db.execute(
        select(
            cast(Order.created_at, Date).label("day"),
            func.sum(Order.total_price).label("sales"),
            func.count(Order.id).label("orders"),
        )
        .where(Order.created_at >= since)
        .where(Order.status.in_(valid))
        .group_by("day")
        .order_by(desc("day"))
    ).all()

    return {
        "since": since.isoformat().replace("+00:00", "Z"),
        "content": [{"day": str(r[0]), "sales": int(r[1] or 0), "orders": int(r[2])} for r in rows]
    }
