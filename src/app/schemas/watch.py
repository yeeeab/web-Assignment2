from pydantic import BaseModel
from datetime import datetime

class WatchItemRes(BaseModel):
    itemId: int
    watchedAt: datetime
