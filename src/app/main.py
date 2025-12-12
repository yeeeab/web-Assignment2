from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import PlainTextResponse

from app.core.config import settings
from app.core.errors import AppError, error_response
from app.api.v1.router import router as v1

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppError)
def app_error_handler(req: Request, exc: AppError):
    return error_response(req, exc.status, exc.code, exc.message, exc.details)

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(req: Request, exc: RateLimitExceeded):
    return error_response(req, 429, "TOO_MANY_REQUESTS", "요청 한도를 초과했습니다.", {})

app.include_router(v1)
