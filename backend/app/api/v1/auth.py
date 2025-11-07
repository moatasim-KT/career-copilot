"""
Authentication and User Management Endpoints
Handles OAuth flows, user authentication, and user profile management
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.user import User
from ...schemas.user import OAuthUserCreate, UserCreate, UserResponse, UserUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["authentication", "users"])

# ==================== OAuth Endpoints ====================


@router.get("/auth/oauth/google/login")
async def google_oauth_login():
	"""
	Initiate Google OAuth 2.0 authentication flow.
	Redirects user to Google's authorization page.

	Returns:
		RedirectResponse: Redirect to Google OAuth consent screen
	"""
	settings = get_settings()

	if not settings.google_client_id or not settings.google_client_secret:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
		)

	# Build Google OAuth URL
	google_auth_url = (
		"https://accounts.google.com/o/oauth2/v2/auth"
		f"?client_id={settings.google_client_id}"
		f"&redirect_uri={settings.backend_url}/api/v1/auth/oauth/google/callback"
		"&response_type=code"
		"&scope=openid email profile"
		"&access_type=offline"
		"&prompt=consent"
	)

	logger.info("Redirecting user to Google OAuth")
	return RedirectResponse(url=google_auth_url)


@router.get("/auth/oauth/google/callback")
async def google_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
	"""
	Handle Google OAuth callback and create/update user.

	Args:
		code: Authorization code from Google
		db: Database session

	Returns:
		dict: User information and access token
	"""
	settings = get_settings()

	try:
		# Exchange code for access token
		import httpx

		async with httpx.AsyncClient() as client:
			token_response = await client.post(
				"https://oauth2.googleapis.com/token",
				data={
					"code": code,
					"client_id": settings.google_client_id,
					"client_secret": settings.google_client_secret,
					"redirect_uri": f"{settings.backend_url}/api/v1/auth/oauth/google/callback",
					"grant_type": "authorization_code",
				},
			)

			if token_response.status_code != 200:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange authorization code for token")

			token_data = token_response.json()
			access_token = token_data.get("access_token")

			# Get user info from Google
			user_info_response = await client.get(
				"https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"}
			)

			if user_info_response.status_code != 200:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user information from Google")

			user_info = user_info_response.json()

		# Check if user exists
		result = await db.execute(
			select(User).where((User.email == user_info["email"]) | ((User.oauth_provider == "google") & (User.oauth_id == user_info["id"])))
		)
		existing_user = result.scalar_one_or_none()

		if existing_user:
			# Update existing user
			existing_user.oauth_provider = "google"
			existing_user.oauth_id = user_info["id"]
			existing_user.profile_picture_url = user_info.get("picture")
			existing_user.updated_at = datetime.utcnow()
			await db.commit()
			await db.refresh(existing_user)
			user = existing_user
			logger.info(f"Existing user logged in via Google: {user.email}")
		else:
			# Create new user
			new_user = User(
				email=user_info["email"],
				username=user_info.get("name", user_info["email"].split("@")[0]),
				oauth_provider="google",
				oauth_id=user_info["id"],
				profile_picture_url=user_info.get("picture"),
				is_active=True,
			)
			db.add(new_user)
			await db.commit()
			await db.refresh(new_user)
			user = new_user
			logger.info(f"New user created via Google OAuth: {user.email}")

		# In production, generate and return JWT token here
		return {
			"message": "Authentication successful",
			"user": UserResponse.model_validate(user),
			"access_token": "mock_token_for_development",  # Replace with actual JWT
			"token_type": "bearer",
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Google OAuth error: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authentication failed: {e!s}")


@router.get("/auth/oauth/linkedin/login")
async def linkedin_oauth_login():
	"""
	Initiate LinkedIn OAuth 2.0 authentication flow.
	Redirects user to LinkedIn's authorization page.

	Returns:
		RedirectResponse: Redirect to LinkedIn OAuth consent screen
	"""
	settings = get_settings()

	if not settings.linkedin_client_id or not settings.linkedin_client_secret:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="LinkedIn OAuth is not configured. Please set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET.",
		)

	# Build LinkedIn OAuth URL
	linkedin_auth_url = (
		"https://www.linkedin.com/oauth/v2/authorization"
		f"?client_id={settings.linkedin_client_id}"
		f"&redirect_uri={settings.backend_url}/api/v1/auth/oauth/linkedin/callback"
		"&response_type=code"
		"&scope=r_liteprofile r_emailaddress"
	)

	logger.info("Redirecting user to LinkedIn OAuth")
	return RedirectResponse(url=linkedin_auth_url)


@router.get("/auth/oauth/linkedin/callback")
async def linkedin_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
	"""
	Handle LinkedIn OAuth callback and create/update user.

	Args:
		code: Authorization code from LinkedIn
		db: Database session

	Returns:
		dict: User information and access token
	"""
	settings = get_settings()

	try:
		# Exchange code for access token
		import httpx

		async with httpx.AsyncClient() as client:
			token_response = await client.post(
				"https://www.linkedin.com/oauth/v2/accessToken",
				data={
					"code": code,
					"client_id": settings.linkedin_client_id,
					"client_secret": settings.linkedin_client_secret,
					"redirect_uri": f"{settings.backend_url}/api/v1/auth/oauth/linkedin/callback",
					"grant_type": "authorization_code",
				},
				headers={"Content-Type": "application/x-www-form-urlencoded"},
			)

			if token_response.status_code != 200:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange authorization code for token")

			token_data = token_response.json()
			access_token = token_data.get("access_token")

			# Get user email
			email_response = await client.get(
				"https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
				headers={"Authorization": f"Bearer {access_token}"},
			)

			# Get user profile
			profile_response = await client.get("https://api.linkedin.com/v2/me", headers={"Authorization": f"Bearer {access_token}"})

			if email_response.status_code != 200 or profile_response.status_code != 200:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user information from LinkedIn")

			email_data = email_response.json()
			profile_data = profile_response.json()

			user_email = email_data["elements"][0]["handle~"]["emailAddress"]
			user_id = profile_data["id"]
			user_name = f"{profile_data.get('firstName', {}).get('localized', {}).get('en_US', '')} {profile_data.get('lastName', {}).get('localized', {}).get('en_US', '')}"

		# Check if user exists
		result = await db.execute(select(User).where((User.email == user_email) | ((User.oauth_provider == "linkedin") & (User.oauth_id == user_id))))
		existing_user = result.scalar_one_or_none()

		if existing_user:
			# Update existing user
			existing_user.oauth_provider = "linkedin"
			existing_user.oauth_id = user_id
			existing_user.updated_at = datetime.utcnow()
			await db.commit()
			await db.refresh(existing_user)
			user = existing_user
			logger.info(f"Existing user logged in via LinkedIn: {user.email}")
		else:
			# Create new user
			new_user = User(
				email=user_email,
				username=user_name.strip() or user_email.split("@")[0],
				oauth_provider="linkedin",
				oauth_id=user_id,
				is_active=True,
			)
			db.add(new_user)
			await db.commit()
			await db.refresh(new_user)
			user = new_user
			logger.info(f"New user created via LinkedIn OAuth: {user.email}")

		# In production, generate and return JWT token here
		return {
			"message": "Authentication successful",
			"user": UserResponse.model_validate(user),
			"access_token": "mock_token_for_development",  # Replace with actual JWT
			"token_type": "bearer",
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"LinkedIn OAuth error: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authentication failed: {e!s}")


# ==================== User Management Endpoints ====================


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
	"""
	Get the currently authenticated user's profile information.

	Returns:
		UserResponse: Current user's profile data
	"""
	return UserResponse.model_validate(current_user)


@router.put("/users/me", response_model=UserResponse)
async def update_current_user(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Update the currently authenticated user's profile.

	Args:
		user_update: Fields to update
		current_user: Current authenticated user
		db: Database session

	Returns:
		UserResponse: Updated user profile
	"""
	# Update only provided fields
	update_data = user_update.model_dump(exclude_unset=True)

	for field, value in update_data.items():
		if hasattr(current_user, field):
			setattr(current_user, field, value)

	current_user.updated_at = datetime.utcnow()

	await db.commit()
	await db.refresh(current_user)

	logger.info(f"User profile updated: {current_user.email}")

	return UserResponse.model_validate(current_user)


@router.get("/users", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	List all users (admin only in production).
	For now, returns all users with pagination.

	Args:
		skip: Number of records to skip
		limit: Maximum number of records to return
		current_user: Current authenticated user
		db: Database session

	Returns:
		List[UserResponse]: List of users
	"""
	if skip < 0:
		raise HTTPException(status_code=400, detail="Skip parameter must be non-negative")

	if limit < 1 or limit > 1000:
		raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

	result = await db.execute(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit))
	users = result.scalars().all()

	return [UserResponse.model_validate(user) for user in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
	"""
	Create a new user account.

	Args:
		user_data: User creation data
		db: Database session

	Returns:
		UserResponse: Created user profile
	"""
	# Check if user already exists
	result = await db.execute(select(User).where((User.email == user_data.email) | (User.username == user_data.username)))
	existing_user = result.scalar_one_or_none()

	if existing_user:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email or username already exists")

	# Create new user
	new_user = User(
		email=user_data.email,
		username=user_data.username,
		hashed_password=user_data.password,  # In production, hash the password!
		skills=user_data.skills or [],
		locations=user_data.locations or [],
		experience=user_data.experience,
		is_active=True,
	)

	db.add(new_user)
	await db.commit()
	await db.refresh(new_user)

	logger.info(f"New user created: {new_user.email}")

	return UserResponse.model_validate(new_user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get a specific user by ID.

	Args:
		user_id: User ID to retrieve
		current_user: Current authenticated user
		db: Database session

	Returns:
		UserResponse: User profile
	"""
	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()

	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")

	return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Delete a user account (admin only in production).

	Args:
		user_id: User ID to delete
		current_user: Current authenticated user
		db: Database session
	"""
	# Prevent users from deleting themselves
	if current_user.id == user_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account via this endpoint")

	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()

	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")

	await db.delete(user)
	await db.commit()

	logger.info(f"User deleted: {user.email} (ID: {user_id})")

	return None
