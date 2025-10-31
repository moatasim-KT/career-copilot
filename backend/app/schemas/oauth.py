"""OAuth-related Pydantic schemas"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class OAuthUserData(BaseModel):
	"""Schema for OAuth user data from providers"""

	provider: str
	oauth_id: str
	email: EmailStr
	name: str | None = None
	picture: str | None = None
	access_token: str


class OAuthLoginResponse(BaseModel):
	"""Schema for OAuth login response"""

	access_token: str
	token_type: str = "bearer"
	user_id: int
	username: str
	email: EmailStr
	oauth_provider: str | None = None
	profile_picture_url: str | None = None


class OAuthStatusResponse(BaseModel):
	"""Schema for OAuth connection status"""

	oauth_enabled: bool
	connected_provider: str | None = None
	oauth_id: str | None = None
	profile_picture_url: str | None = None
	available_providers: list[str] = []


class OAuthDisconnectRequest(BaseModel):
	"""Schema for OAuth disconnect request"""

	provider: str


class OAuthDisconnectResponse(BaseModel):
	"""Schema for OAuth disconnect response"""

	message: str
