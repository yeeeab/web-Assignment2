from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}

def error_response(req: Request, status: int, code: str, message: str, details: dict | None = None):
    return JSONResponse(
        status_code=status,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "path": req.url.path,
            "status": status,
            "code": code,
            "message": message,
            "details": details or {},
        },
    )
