"""OAuth-related Pydantic schemas"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class OAuthUserData(BaseModel):
    """Schema for OAuth user data from providers"""
    provider: str
    oauth_id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    access_token: str


class OAuthLoginResponse(BaseModel):
    """Schema for OAuth login response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: EmailStr
    oauth_provider: Optional[str] = None
    profile_picture_url: Optional[str] = None


class OAuthStatusResponse(BaseModel):
    """Schema for OAuth connection status"""
    oauth_enabled: bool
    connected_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    available_providers: list[str] = []


class OAuthDisconnectRequest(BaseModel):
    """Schema for OAuth disconnect request"""
    provider: str


class OAuthDisconnectResponse(BaseModel):
    """Schema for OAuth disconnect response"""
    message: str