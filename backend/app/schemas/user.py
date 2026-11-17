"""
User Pydantic Schemas (Pydantic V2).
"""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    display_name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    google_id: Optional[str] = None


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: str
    role: str
    xp: int
    streak_days: int
    last_study_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoogleAuthRequest(BaseModel):
    id_token: str


class DevLoginRequest(BaseModel):
    email: str
    display_name: Optional[str] = "Dev Scholar"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str
