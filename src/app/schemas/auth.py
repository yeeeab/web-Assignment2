from pydantic import BaseModel, EmailStr, Field

class RegisterReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=2, max_length=30)

class LoginReq(BaseModel):
    email: EmailStr
    password: str

class TokenRes(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"

class RefreshReq(BaseModel):
    refreshToken: str
