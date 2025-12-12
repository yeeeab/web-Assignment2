from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserStatus
from app.schemas.auth import RegisterReq, LoginReq, TokenRes, RefreshReq
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.errors import AppError

router = APIRouter(prefix="/auth")

@router.post("/register", response_model=TokenRes)
def register(req: RegisterReq, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == req.email))
    if exists:
        raise AppError(409, "DUPLICATE_RESOURCE", "이미 사용 중인 이메일입니다.", {"email": "duplicate"})

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)
    return TokenRes(accessToken=access, refreshToken=refresh)

@router.post("/login", response_model=TokenRes)
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == req.email))
    if not user or not verify_password(req.password, user.password_hash):
        raise AppError(401, "UNAUTHORIZED", "이메일 또는 비밀번호가 올바르지 않습니다.")

    if user.status != UserStatus.ACTIVE:
        raise AppError(403, "FORBIDDEN", "비활성화된 계정입니다.")

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)
    return TokenRes(accessToken=access, refreshToken=refresh)

@router.post("/refresh", response_model=TokenRes)
def refresh(req: RefreshReq):
    try:
        payload = decode_token(req.refreshToken)
    except Exception:
        raise AppError(401, "UNAUTHORIZED", "토큰이 올바르지 않습니다.")

    if payload.get("type") != "refresh":
        raise AppError(401, "UNAUTHORIZED", "Refresh token이 아닙니다.")

    sub = payload.get("sub")
    role = payload.get("role")
    if not sub or not role:
        raise AppError(401, "UNAUTHORIZED", "토큰 payload가 올바르지 않습니다.")

    access = create_access_token(sub, role)
    refresh_token = create_refresh_token(sub, role)
    return TokenRes(accessToken=access, refreshToken=refresh_token)

@router.post("/logout")
def logout():
    # 과제 범위에선 서버측 블랙리스트를 안 해도 됨(선택).
    # Postman/Swagger에서 “클라 토큰 삭제”로 처리한다고 문서화하면 충분.
    return {"ok": True}
