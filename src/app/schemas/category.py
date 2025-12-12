from pydantic import BaseModel, Field

class CategoryCreateReq(BaseModel):
    name: str = Field(min_length=1, max_length=50)

class CategoryUpdateReq(BaseModel):
    name: str = Field(min_length=1, max_length=50)

class CategoryRes(BaseModel):
    id: int
    name: str
