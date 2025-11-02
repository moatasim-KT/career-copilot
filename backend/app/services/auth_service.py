"""
Consolidated Authentication Service for Career Copilot System.
Handles user authentication, JWT token management, and authorization.
"""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import jwt
from app.core.config import get_settings
from app.core.logging import get_audit_logger, get_logger
from app.core.password_validator import default_validator as password_validator
from app.core.security import (create_access_token, decode_access_token,
                               get_password_hash, verify_password)
from app.core.token_blacklist import session_blacklist, token_blacklist
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserUpdate
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = get_logger(__name__)
audit_logger = get_audit_logger()
settings = get_settings()


class TokenType(str):
	"""Token types."""

	ACCESS = "access"
	REFRESH = "refresh"
	API_KEY = "api_key"
	RESET = "reset"
	VERIFICATION = "verification"


class Role(str):
	"""User roles in the system."""

	USER = "user"
	ADMIN = "admin"
	MODERATOR = "moderator"


class Permission(str):
	"""System permissions."""

	READ_JOBS = "read_jobs"
	WRITE_JOBS = "write_jobs"
	DELETE_JOBS = "delete_jobs"
	READ_PROFILE = "read_profile"
	WRITE_PROFILE = "write_profile"
	READ_ANALYTICS = "read_analytics"
	WRITE_ANALYTICS = "write_analytics"
	ADMIN_ACCESS = "admin_access"
	MANAGE_USERS = "manage_users"
	SYSTEM_CONFIG = "system_config"


class TokenClaims(BaseModel):
	"""JWT token claims."""

	sub: str  # Subject (user ID)
	username: str
	email: str
	roles: List[str]
	permissions: List[str]
	security_level: str
	session_id: str
	token_type: str
	mfa_verified: bool = False
	iat: int  # Issued at
	exp: int  # Expires at
	iss: str = "career-copilot"  # Issuer
	aud: str = "career-copilot-api"  # Audience
	jti: str  # JWT ID (unique token identifier)


class TokenValidationResult(BaseModel):
	"""Token validation result."""

	is_valid: bool
	claims: Optional[TokenClaims] = None
	error: Optional[str] = None
	user_id: Optional[str] = None
	session_id: Optional[str] = None


class AuthenticationSystem:
	"""Consolidated authentication system with JWT and authorization."""

	def __init__(self, db: Session):
		"""Initialize authentication system."""
		self.db = db
		self.secret_key = settings.jwt_secret_key.get_secret_value()
		self.algorithm = settings.jwt_algorithm
		self.access_token_expire_minutes = settings.jwt_expiration_hours * 60
		self.refresh_token_expire_days = 30

		# Use Redis-based blacklists (with in-memory fallback)
		self.token_blacklist = token_blacklist
		self.session_blacklist = session_blacklist
		self.blacklisted_tokens = set()  # In-memory fallback for compatibility

		# Define role permissions
		self.role_permissions = {
			Role.USER: [Permission.READ_JOBS, Permission.WRITE_JOBS, Permission.READ_PROFILE, Permission.WRITE_PROFILE, Permission.READ_ANALYTICS],
			Role.MODERATOR: [
				Permission.READ_JOBS,
				Permission.WRITE_JOBS,
				Permission.DELETE_JOBS,
				Permission.READ_PROFILE,
				Permission.WRITE_PROFILE,
				Permission.READ_ANALYTICS,
				Permission.WRITE_ANALYTICS,
			],
			Role.ADMIN: [
				Permission.READ_JOBS,
				Permission.WRITE_JOBS,
				Permission.DELETE_JOBS,
				Permission.READ_PROFILE,
				Permission.WRITE_PROFILE,
				Permission.READ_ANALYTICS,
				Permission.WRITE_ANALYTICS,
				Permission.ADMIN_ACCESS,
				Permission.MANAGE_USERS,
				Permission.SYSTEM_CONFIG,
			],
		}

		logger.info("Authentication System initialized")

	# User Management Methods
	def validate_password_strength(self, password: str, username: Optional[str] = None) -> bool:
		"""
		Validate password strength using configurable validator pattern.

		Args:
		    password: Password to validate
		    username: Optional username to check against password

		Returns:
		    True if password meets requirements

		Raises:
		    HTTPException: If password doesn't meet requirements
		"""
		result = password_validator.validate(password, username)

		if not result.is_valid:
			# Join all error messages
			error_detail = ". ".join(result.errors)
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

		return True

	def validate_email_format(self, email: str) -> bool:
		"""
		Validate email format.

		Args:
		    email: Email to validate

		Returns:
		    True if email is valid

		Raises:
		    HTTPException: If email format is invalid
		"""
		email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
		if not re.match(email_pattern, email):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
		return True

	def get_user_by_email(self, email: str) -> Optional[User]:
		"""
		Get user by email address.

		Args:
		    email: User email address

		Returns:
		    User object or None if not found
		"""
		return self.db.query(User).filter(User.email == email).first()

	def get_user_by_id(self, user_id: int) -> Optional[User]:
		"""
		Get user by ID.

		Args:
		    user_id: User ID

		Returns:
		    User object or None if not found
		"""
		return self.db.query(User).filter(User.id == user_id).first()

	def create_user(self, user_data: UserCreate) -> User:
		"""
		Create new user account.

		Args:
		    user_data: User creation data

		Returns:
		    Created user object

		Raises:
		    HTTPException: If email already exists or validation fails
		"""
		# Validate email format
		self.validate_email_format(user_data.email)

		# Validate password strength
		self.validate_password_strength(user_data.password)

		# Check if user already exists
		existing_user = self.get_user_by_email(user_data.email)
		if existing_user:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

		# Create new user
		hashed_password = get_password_hash(user_data.password)

		# Set default profile and settings if not provided
		default_profile = {
			"skills": [],
			"experience_level": "entry",
			"locations": [],
			"preferences": {"salary_min": None, "company_size": [], "industries": [], "remote_preference": "no_preference"},
			"career_goals": [],
		}

		default_settings = {
			"notifications": {"morning_briefing": True, "evening_summary": True, "email_time": "08:00"},
			"ui_preferences": {"theme": "light", "dashboard_layout": "standard"},
		}

		user = User(
			email=user_data.email,
			password_hash=hashed_password,
			profile=user_data.profile or default_profile,
			settings=user_data.settings or default_settings,
			is_active=user_data.is_active,
		)

		self.db.add(user)
		self.db.commit()
		self.db.refresh(user)

		return user

	def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
		"""
		Authenticate user with email and password.

		Args:
		    login_data: Login credentials

		Returns:
		    User object if authentication successful, None otherwise
		"""
		user = self.get_user_by_email(login_data.email)

		if not user:
			return None

		if not user.is_active:
			return None

		if not verify_password(login_data.password, user.password_hash):
			return None

		# Update last active timestamp
		user.last_active = datetime.now(timezone.utc)
		self.db.commit()

		return user

	def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
		"""
		Update user information.

		Args:
		    user_id: User ID to update
		    user_data: Updated user data

		Returns:
		    Updated user object or None if not found
		"""
		user = self.get_user_by_id(user_id)
		if not user:
			return None

		# Update fields if provided
		if user_data.email is not None:
			# Check if new email is already taken
			existing_user = self.get_user_by_email(user_data.email)
			if existing_user and existing_user.id != user_id:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
			user.email = user_data.email

		if user_data.password is not None:
			self.validate_password_strength(user_data.password)
			user.password_hash = get_password_hash(user_data.password)

		if user_data.profile is not None:
			user.profile = user_data.profile

		if user_data.settings is not None:
			user.settings = user_data.settings

		if user_data.is_active is not None:
			user.is_active = user_data.is_active

		user.updated_at = datetime.now(timezone.utc)
		self.db.commit()
		self.db.refresh(user)

		return user

	def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
		"""
		Change user password.

		Args:
		    user_id: User ID
		    current_password: Current password for verification
		    new_password: New password

		Returns:
		    True if password changed successfully, False otherwise
		"""
		user = self.get_user_by_id(user_id)
		if not user:
			return False

		# Verify current password
		if not verify_password(current_password, user.password_hash):
			return False

		# Validate new password strength
		self.validate_password_strength(new_password)

		# Update password
		user.password_hash = get_password_hash(new_password)
		user.updated_at = datetime.now(timezone.utc)
		self.db.commit()

		return True

	# JWT Token Management Methods
	async def generate_jwt(self, user: User, session_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
		"""
		Generate JWT access token with comprehensive claims.

		Args:
		    user: User object
		    session_id: Session identifier
		    additional_claims: Additional claims to include

		Returns:
		    JWT access token string
		"""
		try:
			now = datetime.now(timezone.utc)
			expires_at = now + timedelta(minutes=self.access_token_expire_minutes)

			# Create unique token ID
			jti = str(uuid4())

			# Get user roles and permissions
			user_roles = self.get_user_roles(user)
			user_permissions = self.get_user_permissions_from_roles(user_roles)

			# Build claims
			claims = TokenClaims(
				sub=str(user.id),
				username=getattr(user, "username", user.email),
				email=user.email,
				roles=[role for role in user_roles],
				permissions=[perm for perm in user_permissions],
				security_level=getattr(user, "security_level", "standard"),
				session_id=session_id,
				token_type=TokenType.ACCESS,
				mfa_verified=getattr(user, "mfa_enabled", False),
				iat=int(now.timestamp()),
				exp=int(expires_at.timestamp()),
				jti=jti,
			)

			# Add additional claims if provided
			claims_dict = claims.dict()
			if additional_claims:
				claims_dict.update(additional_claims)

			# Create JWT token
			token = jwt.encode(claims_dict, self.secret_key, algorithm=self.algorithm)

			# Log token creation
			audit_logger.log_event(
				event_type="token_created",
				action=f"Access token created for user {user.email}",
				user_id=str(user.id),
				session_id=session_id,
				details={"token_type": TokenType.ACCESS, "expires_at": expires_at.isoformat(), "jti": jti},
			)

			logger.debug(f"Access token created for user {user.email}")
			return token

		except Exception as e:
			logger.error(f"Error creating access token: {e}")
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create access token")

	async def create_refresh_token(self, user: User, session_id: str, token_family: Optional[str] = None) -> str:
		"""
		Create JWT refresh token with rotation support.

		Args:
		    user: User object
		    session_id: Session identifier
		    token_family: Token family for rotation

		Returns:
		    JWT refresh token string
		"""
		try:
			now = datetime.now(timezone.utc)
			expires_at = now + timedelta(days=self.refresh_token_expire_days)

			# Create unique token ID and family
			jti = str(uuid4())
			if not token_family:
				token_family = str(uuid4())

			# Build claims
			claims = {
				"sub": str(user.id),
				"session_id": session_id,
				"token_family": token_family,
				"token_type": TokenType.REFRESH,
				"iat": int(now.timestamp()),
				"exp": int(expires_at.timestamp()),
				"iss": "career-copilot",
				"aud": "career-copilot-api",
				"jti": jti,
			}

			# Create JWT token
			token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

			# Log token creation
			audit_logger.log_event(
				event_type="token_created",
				action=f"Refresh token created for user {user.email}",
				user_id=str(user.id),
				session_id=session_id,
				details={"token_type": TokenType.REFRESH, "token_family": token_family, "expires_at": expires_at.isoformat(), "jti": jti},
			)

			logger.debug(f"Refresh token created for user {user.email}")
			return token

		except Exception as e:
			logger.error(f"Error creating refresh token: {e}")
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create refresh token")

	async def validate_token(self, token: str) -> TokenValidationResult:
		"""
		Validate JWT token with comprehensive security checks.

		Args:
		    token: JWT token string

		Returns:
		    TokenValidationResult with validation details
		"""
		try:
			# Check if token is blacklisted
			token_hash = hashlib.sha256(token.encode()).hexdigest()
			if token_hash in self.blacklisted_tokens:
				return TokenValidationResult(is_valid=False, error="Token is blacklisted")

			# Decode and validate token
			try:
				payload = jwt.decode(
					token,
					self.secret_key,
					algorithms=[self.algorithm],
					options={"verify_signature": True, "verify_exp": True, "verify_iat": True, "verify_aud": True, "verify_iss": True},
				)
			except jwt.ExpiredSignatureError:
				return TokenValidationResult(is_valid=False, error="Token has expired")
			except jwt.InvalidTokenError as e:
				return TokenValidationResult(is_valid=False, error=f"Invalid token: {e!s}")

			# Extract claims
			try:
				if payload.get("token_type") == TokenType.ACCESS:
					claims = TokenClaims(**payload)
				else:
					# For refresh tokens, create minimal claims
					claims = TokenClaims(
						sub=payload["sub"],
						username="",
						email="",
						roles=[],
						permissions=[],
						security_level="standard",
						session_id=payload["session_id"],
						token_type=payload["token_type"],
						iat=payload["iat"],
						exp=payload["exp"],
						jti=payload["jti"],
					)
			except Exception as e:
				return TokenValidationResult(is_valid=False, error=f"Invalid token claims: {e!s}")

			# Check if session is blacklisted
			if claims.session_id in self.blacklisted_sessions:
				return TokenValidationResult(is_valid=False, error="Session is blacklisted")

			# Validate user still exists and is active
			if claims.token_type == TokenType.ACCESS:
				user = self.get_user_by_id(int(claims.sub))
				if not user or not user.is_active:
					return TokenValidationResult(is_valid=False, error="User not found or inactive")

			return TokenValidationResult(is_valid=True, claims=claims, user_id=claims.sub, session_id=claims.session_id)

		except Exception as e:
			logger.error(f"Error validating token: {e}")
			return TokenValidationResult(is_valid=False, error=f"Token validation error: {e!s}")

	def create_tokens(self, user: User) -> dict:
		"""
		Create access and refresh tokens for user.

		Args:
		    user: User object

		Returns:
		    Dictionary containing access and refresh tokens
		"""
		session_id = str(uuid4())

		access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
		# For now, use the same token structure for refresh token
		# In production, this should have different expiration and claims
		refresh_token = create_access_token(data={"sub": str(user.id), "email": user.email, "type": "refresh"})

		return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

	def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
		"""
		Create new access token from refresh token.

		Args:
		    refresh_token: Valid refresh token

		Returns:
		    New token pair or None if refresh token invalid
		"""
		payload = decode_access_token(refresh_token)
		if not payload:
			return None

		# Check if it's a refresh token
		if payload.get("type") != "refresh":
			return None

		user_id = payload.get("sub")
		if not user_id:
			return None

		user = self.get_user_by_id(int(user_id))
		if not user or not user.is_active:
			return None

		return self.create_tokens(user)

	def get_current_user_from_token(self, token: str) -> Optional[User]:
		"""
		Get current user from access token.

		Args:
		    token: JWT access token

		Returns:
		    User object or None if token invalid
		"""
		payload = decode_access_token(token)
		if not payload:
			return None

		user_id = payload.get("sub")
		if not user_id:
			return None

		user = self.get_user_by_id(int(user_id))
		if not user or not user.is_active:
			return None

		return user

	# Authorization Methods
	def get_user_roles(self, user: User) -> List[str]:
		"""Get user roles from user data."""
		try:
			# Check if user has roles attribute or custom claims
			if hasattr(user, "roles") and user.roles:
				return user.roles

			# Default to USER role
			return [Role.USER]

		except Exception as e:
			logger.error(f"Error getting user roles: {e}")
			return [Role.USER]

	def get_user_permissions_from_roles(self, roles: List[str]) -> List[str]:
		"""Get user permissions based on roles."""
		try:
			permissions = set()

			for role in roles:
				role_perms = self.role_permissions.get(role, [])
				permissions.update(role_perms)

			return list(permissions)

		except Exception as e:
			logger.error(f"Error getting user permissions: {e}")
			return self.role_permissions[Role.USER]

	def get_user_permissions(self, user: User) -> List[str]:
		"""Get user permissions based on roles."""
		roles = self.get_user_roles(user)
		return self.get_user_permissions_from_roles(roles)

	def has_permission(self, user: User, permission: str) -> bool:
		"""Check if user has specific permission."""
		try:
			user_permissions = self.get_user_permissions(user)
			return permission in user_permissions

		except Exception as e:
			logger.error(f"Error checking permission: {e}")
			return False

	def has_role(self, user: User, role: str) -> bool:
		"""Check if user has specific role."""
		try:
			user_roles = self.get_user_roles(user)
			return role in user_roles

		except Exception as e:
			logger.error(f"Error checking role: {e}")
			return False

	def has_any_role(self, user: User, roles: List[str]) -> bool:
		"""Check if user has any of the specified roles."""
		try:
			user_roles = self.get_user_roles(user)
			return any(role in user_roles for role in roles)

		except Exception as e:
			logger.error(f"Error checking roles: {e}")
			return False

	def check_resource_access(self, user: User, resource_owner_id: str) -> bool:
		"""Check if user can access a resource owned by another user."""
		try:
			# Users can always access their own resources
			if str(user.id) == resource_owner_id:
				return True

			# Admins and moderators can access any resource
			if self.has_any_role(user, [Role.ADMIN, Role.MODERATOR]):
				return True

			return False

		except Exception as e:
			logger.error(f"Error checking resource access: {e}")
			return False

	# Token Management Methods
	async def blacklist_token(self, token: str) -> None:
		"""
		Blacklist a JWT token.

		Args:
		    token: JWT token to blacklist
		"""
		try:
			token_hash = hashlib.sha256(token.encode()).hexdigest()
			self.blacklisted_tokens.add(token_hash)

			logger.debug(f"Token blacklisted: {token_hash[:16]}...")

		except Exception as e:
			logger.error(f"Error blacklisting token: {e}")

	async def blacklist_session(self, session_id: str) -> None:
		"""
		Blacklist all tokens for a session.

		Args:
		    session_id: Session identifier
		"""
		try:
			self.blacklisted_sessions.add(session_id)

			logger.info(f"Session blacklisted: {session_id}")

		except Exception as e:
			logger.error(f"Error blacklisting session: {e}")

	async def logout_user(self, user_id: str, session_id: Optional[str] = None) -> None:
		"""
		Logout user by blacklisting their sessions.

		Args:
		    user_id: User identifier
		    session_id: Specific session to logout (optional)
		"""
		try:
			if session_id:
				# Logout specific session
				await self.blacklist_session(session_id)

			# Log logout event
			audit_logger.log_event(
				event_type="user_logout",
				action=f"User logged out",
				user_id=user_id,
				session_id=session_id,
				details={"logout_type": "specific_session" if session_id else "all_sessions"},
			)

			logger.info(f"User {user_id} logged out")

		except Exception as e:
			logger.error(f"Error logging out user: {e}")

	def get_auth_status(self) -> Dict[str, Any]:
		"""Get authentication service status."""
		return {
			"jwt_enabled": True,
			"token_expiration_hours": self.access_token_expire_minutes / 60,
			"algorithm": self.algorithm,
			"roles_configured": len(self.role_permissions),
			"available_roles": [Role.USER, Role.MODERATOR, Role.ADMIN],
			"available_permissions": [
				Permission.READ_JOBS,
				Permission.WRITE_JOBS,
				Permission.DELETE_JOBS,
				Permission.READ_PROFILE,
				Permission.WRITE_PROFILE,
				Permission.READ_ANALYTICS,
				Permission.WRITE_ANALYTICS,
				Permission.ADMIN_ACCESS,
				Permission.MANAGE_USERS,
				Permission.SYSTEM_CONFIG,
			],
		}


# Global service instance
_authentication_system: Optional[AuthenticationSystem] = None


def get_authentication_system(db: Session) -> AuthenticationSystem:
	"""Get authentication system instance."""
	global _authentication_system
	if _authentication_system is None:
		_authentication_system = AuthenticationSystem(db)
	return _authentication_system


# Backward compatibility aliases
AuthService = AuthenticationSystem
get_auth_service = get_authentication_system
