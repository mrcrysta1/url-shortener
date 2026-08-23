from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List
from datetime import datetime

class URLBase(BaseModel):
    original_url: HttpUrl

class URLCreate(URLBase):
    custom_code: Optional[str] = None
    expires_in_days: Optional[int] = None

class URLResponse(URLBase):
    id: int
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    click_count: int
    short_url: str
    
    class Config:
        orm_mode = True

class URLStats(BaseModel):
    total_clicks: int
    unique_visitors: int
    clicks_by_date: dict
    top_referrers: List[dict]
    recent_clicks: List[dict]

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
