from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.errors import AppError
from app.core.security import verify_password, hash_password

from app.models.user import User
from app.models.bid import Bid
from app.models.item import Item

from app.schemas.user import UserMeRes, UserUpdateReq, PasswordChangeReq
from app.schemas.user_bid import MyBidRes
from app.schemas.common import PageRes

router = APIRouter(prefix="/users")

@router.get("/me", response_model=UserMeRes)
def me(user: User = Depends(get_current_user)):
    return UserMeRes(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        role=user.role.value,
        status=user.status.value,
    )

@router.patch("/me", response_model=UserMeRes)
def update_me(payload: UserUpdateReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.nickname = payload.nickname
    db.commit()
    db.refresh(user)
    return UserMeRes(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        role=user.role.value,
        status=user.status.value,
    )

@router.patch("/me/password")
def change_password(payload: PasswordChangeReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(payload.currentPassword, user.password_hash):
        raise AppError(401, "UNAUTHORIZED", "현재 비밀번호가 올바르지 않습니다.")
    if payload.currentPassword == payload.newPassword:
        raise AppError(422, "UNPROCESSABLE_ENTITY", "새 비밀번호는 기존과 달라야 합니다.")
    user.password_hash = hash_password(payload.newPassword)
    db.commit()
    return {"ok": True}

@router.get("/me/bids", response_model=PageRes[MyBidRes])
def my_bids(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = 0,
    size: int = 20,
    sort: str = "createdAt,DESC",
):
    if size > 100:
        raise AppError(400, "INVALID_QUERY_PARAM", "size는 최대 100입니다.", {"size": size})

    q = (
        select(
            Bid.id.label("bid_id"),
            Bid.item_id.label("item_id"),
            Bid.amount.label("amount"),
            Bid.created_at.label("created_at"),
            Item.title.label("item_title"),
            Item.status.label("item_status"),
        )
        .join(Item, Item.id == Bid.item_id)
        .where(Bid.bidder_id == user.id)
    )

    # 총 개수
    total = db.execute(select(q.subquery().count())).scalar()

    # 정렬
    if sort == "createdAt,DESC":
        q = q.order_by(Bid.created_at.desc())
    elif sort == "createdAt,ASC":
        q = q.order_by(Bid.created_at.asc())
    elif sort == "amount,DESC":
        q = q.order_by(Bid.amount.desc())
    else:
        raise AppError(400, "INVALID_QUERY_PARAM", "sort 값이 올바르지 않습니다.", {"sort": sort})

    rows = db.execute(q.offset(page * size).limit(size)).all()

    content = [
        MyBidRes(
            bidId=r.bid_id,
            itemId=r.item_id,
            amount=r.amount,
            createdAt=r.created_at,
            itemTitle=r.item_title,
            itemStatus=r.item_status.value if hasattr(r.item_status, "value") else str(r.item_status),
        )
        for r in rows
    ]

    total_pages = (total + size - 1) // size if total else 0
    return PageRes[MyBidRes](
        content=content,
        page=page,
        size=size,
        totalElements=total or 0,
        totalPages=total_pages,
        sort=sort,
    )

@router.get("/{user_id}", response_model=UserMeRes)
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    u = db.get(User, user_id)
    if not u:
        raise AppError(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")
    return UserMeRes(
        id=u.id,
        email=u.email,
        nickname=u.nickname,
        role=u.role.value,
        status=u.status.value,
    )
