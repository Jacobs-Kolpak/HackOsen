from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    token_type: Optional[str] = None  # "access" or "refresh"


class UserStatus(BaseModel):
    user: UserResponse
    is_authenticated: bool = True