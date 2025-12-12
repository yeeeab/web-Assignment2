from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PageRes(BaseModel, Generic[T]):
    content: List[T]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str
