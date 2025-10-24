from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, conint, confloat, Field


class UserProfileBase(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=128)
    age: Optional[conint(ge=0, le=150)] = None
    gender: Optional[str] = Field(default=None, pattern=r"^(male|female|other)$")
    current_weight: Optional[confloat(gt=0, le=1000)] = None  # kg
    height: Optional[confloat(gt=0, le=300)] = None           # cm
    goal: Optional[conint(ge=1, le=5)] = None
    activity: Optional[conint(ge=1, le=4)] = None
    special_needs: Optional[conint(ge=1, le=4)] = None
    desired_weight: Optional[confloat(gt=0, le=1000)] = None
    tastes: Optional[conint(ge=1, le=4)] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    profile: Optional[UserProfileCreate] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None

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