import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)

def _now():
    return datetime.now(timezone.utc)

def create_access_token(sub: str, role: str):
    exp = _now() + timedelta(minutes=settings.jwt_access_expires_min)
    payload = {"sub": sub, "role": role, "type": "access", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_refresh_token(sub: str, role: str):
    exp = _now() + timedelta(days=settings.jwt_refresh_expires_days)
    payload = {"sub": sub, "role": role, "type": "refresh", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str):
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
