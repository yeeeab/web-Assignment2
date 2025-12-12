from pydantic import BaseModel
from datetime import datetime

class AdminUserRes(BaseModel):
    id: int
    email: str
    nickname: str
    role: str
    status: str
    createdAt: datetime
