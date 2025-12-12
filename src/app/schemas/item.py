from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ItemCreateReq(BaseModel):
    categoryId: int
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    startPrice: int = Field(ge=0)
    bidUnit: int = Field(ge=1, le=1_000_000)

class ItemUpdateReq(BaseModel):
    categoryId: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1)
    bidUnit: Optional[int] = Field(default=None, ge=1, le=1_000_000)

class ItemRes(BaseModel):
    id: int
    sellerId: int
    categoryId: int
    title: str
    startPrice: int
    bidUnit: int
    status: str
    endsAt: Optional[datetime] = None
    createdAt: datetime
