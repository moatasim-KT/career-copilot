"""
User schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
	"""Base user schema with common fields."""

	username: str = Field(..., min_length=3, max_length=50)
	email: EmailStr


class UserCreate(UserBase):
	"""Schema for creating a new user."""

	password: str = Field(..., min_length=8)
	skills: Optional[List[str]] = Field(default_factory=list)
	preferred_locations: Optional[List[str]] = Field(default_factory=list)
	experience_level: Optional[str] = None
	daily_application_goal: Optional[int] = Field(default=10, ge=1, le=100)
	prefer_remote_jobs: Optional[bool] = False


class UserLogin(BaseModel):
	"""Schema for user login."""

	username: str
	password: str


class UserResponse(UserBase):
	"""Schema for user response."""

	id: int
	skills: List[str]
	preferred_locations: List[str]
	experience_level: Optional[str]
	daily_application_goal: int
	is_admin: bool
	prefer_remote_jobs: bool
	oauth_provider: Optional[str]
	oauth_id: Optional[str]
	profile_picture_url: Optional[str]
	created_at: datetime
	updated_at: datetime

	model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
	"""Schema for updating user information."""

	email: Optional[EmailStr] = None
	skills: Optional[List[str]] = None
	preferred_locations: Optional[List[str]] = None
	experience_level: Optional[str] = None
	daily_application_goal: Optional[int] = Field(default=None, ge=1, le=100)
	prefer_remote_jobs: Optional[bool] = None


class TokenResponse(BaseModel):
	"""Schema for token response."""

	access_token: str
	token_type: str = "bearer"
	user: UserResponse


class OAuthUserCreate(BaseModel):
	"""Schema for creating a user via OAuth."""

	email: EmailStr
	username: str
	oauth_provider: str
	oauth_id: str
	profile_picture_url: Optional[str] = None
