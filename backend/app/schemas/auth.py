"""
Authentication schemas for request/response validation
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
	"""Base user schema"""

	email: EmailStr
	is_active: bool = True


class UserCreate(UserBase):
	"""Schema for user creation"""

	password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
	profile: Optional[Dict[str, Any]] = Field(default_factory=dict)
	settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserUpdate(BaseModel):
	"""Schema for user updates"""

	email: Optional[EmailStr] = None
	password: Optional[str] = Field(None, min_length=8)
	profile: Optional[Dict[str, Any]] = None
	settings: Optional[Dict[str, Any]] = None
	is_active: Optional[bool] = None


class UserResponse(UserBase):
	"""Schema for user response"""

	model_config = ConfigDict(from_attributes=True)

	id: int
	profile: Dict[str, Any]
	settings: Dict[str, Any]
	created_at: str
	updated_at: str
	last_active: str


class UserLogin(BaseModel):
	"""Schema for user login"""

	email: EmailStr
	password: str


class Token(BaseModel):
	"""Schema for token response"""

	access_token: str
	refresh_token: str
	token_type: str = "bearer"


class TokenData(BaseModel):
	"""Schema for token data"""

	user_id: Optional[int] = None
	email: Optional[str] = None


class RefreshToken(BaseModel):
	"""Schema for refresh token request"""

	refresh_token: str


class PasswordChange(BaseModel):
	"""Schema for password change"""

	current_password: str
	new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class PasswordReset(BaseModel):
	"""Schema for password reset"""

	email: EmailStr


class PasswordResetConfirm(BaseModel):
	"""Schema for password reset confirmation"""

	token: str
	new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
