from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginResponse(BaseModel):
    session_id: str
    role: str


class LogoutResponse(BaseModel):
    status: str
