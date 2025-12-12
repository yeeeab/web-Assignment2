from pydantic import BaseModel, Field, EmailStr

class UserMeRes(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    role: str
    status: str

class UserUpdateReq(BaseModel):
    nickname: str = Field(min_length=2, max_length=30)

class PasswordChangeReq(BaseModel):
    currentPassword: str = Field(min_length=8, max_length=72)
    newPassword: str = Field(min_length=8, max_length=72)
