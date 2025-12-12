from pydantic import BaseModel, Field
from datetime import datetime

class BidCreateReq(BaseModel):
    amount: int = Field(ge=0)

class BidRes(BaseModel):
    id: int
    itemId: int
    bidderId: int
    amount: int
    createdAt: datetime
