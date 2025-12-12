from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrderCreateReq(BaseModel):
    address: Optional[str] = Field(default=None, max_length=255)

class OrderRes(BaseModel):
    id: int
    itemId: int
    buyerId: int
    status: str
    totalPrice: int
    address: Optional[str]
    createdAt: datetime
