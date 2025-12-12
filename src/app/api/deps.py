from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserStatus, UserRole
from app.core.security import decode_token
from app.core.errors import AppError

bearer = HTTPBearer(auto_error=False)

def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not cred:
        raise AppError(401, "UNAUTHORIZED", "인증 토큰이 필요합니다.")

    token = cred.credentials
    try:
        payload = decode_token(token)
    except Exception:
        # 만료 구분을 엄밀히 하고 싶으면 PyJWT ExpiredSignatureError를 따로 처리
        raise AppError(401, "UNAUTHORIZED", "토큰이 올바르지 않습니다.")

    if payload.get("type") != "access":
        raise AppError(401, "UNAUTHORIZED", "Access token이 아닙니다.")

    user_id = payload.get("sub")
    user = db.scalar(select(User).where(User.id == int(user_id)))
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")

    if user.status != UserStatus.ACTIVE:
        raise AppError(403, "FORBIDDEN", "비활성화된 계정입니다.")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise AppError(403, "FORBIDDEN", "관리자 권한이 필요합니다.")
    return user
