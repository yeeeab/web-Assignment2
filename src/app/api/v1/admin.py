from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.api.deps import require_admin
from app.core.errors import AppError
from app.models.user import User, UserStatus
from app.models.item import Item, ItemStatus
from app.schemas.common import PageRes
from app.schemas.admin import AdminUserRes

router = APIRouter(prefix="/admin")

@router.get("/users", response_model=PageRes[AdminUserRes])
def admin_list_users(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    page: int = 0,
    size: int = 20,
    sort: str = "createdAt,DESC",
    keyword: str | None = None,
):
    if size > 100:
        raise AppError(400, "INVALID_QUERY_PARAM", "size는 최대 100입니다.", {"size": size})

    q = select(User)
    if keyword:
        q = q.where((User.email.like(f"%{keyword}%")) | (User.nickname.like(f"%{keyword}%")))

    total = db.scalar(select(func.count()).select_from(q.subquery()))

    if sort == "createdAt,DESC":
        q = q.order_by(User.created_at.desc())
    elif sort == "createdAt,ASC":
        q = q.order_by(User.created_at.asc())
    else:
        raise AppError(400, "INVALID_QUERY_PARAM", "sort 값이 올바르지 않습니다.", {"sort": sort})

    rows = db.scalars(q.offset(page * size).limit(size)).all()
    content = [
        AdminUserRes(
            id=u.id, email=u.email, nickname=u.nickname,
            role=u.role.value, status=u.status.value, createdAt=u.created_at
        )
        for u in rows
    ]
    total_pages = (total + size - 1) // size if total else 0
    return PageRes[AdminUserRes](content=content, page=page, size=size, totalElements=total, totalPages=total_pages, sort=sort)

@router.patch("/users/{user_id}/deactivate")
def admin_deactivate_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise AppError(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")
    u.status = UserStatus.DEACTIVATED
    db.commit()
    return {"ok": True}

@router.patch("/items/{item_id}/force-close")
def admin_force_close_item(item_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.get(Item, item_id)
    if not item:
        raise AppError(404, "RESOURCE_NOT_FOUND", "아이템을 찾을 수 없습니다.")
    if item.status != ItemStatus.OPEN:
        raise AppError(409, "STATE_CONFLICT", "OPEN 상태만 강제 마감할 수 있습니다.", {"status": item.status.value})
    item.status = ItemStatus.CLOSED
    db.commit()
    return {"ok": True, "status": item.status.value}
