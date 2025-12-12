from pydantic import BaseModel
from datetime import datetime

class MyBidRes(BaseModel):
    bidId: int
    itemId: int
    amount: int
    createdAt: datetime
    itemTitle: str
    itemStatus: str
