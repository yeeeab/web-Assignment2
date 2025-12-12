from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "buildTime": settings.build_time,
        "name": settings.app_name
    }
