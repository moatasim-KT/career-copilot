"""
Consolidated OAuth Service for Career Copilot System.
Handles OAuth authentication with multiple providers and Firebase integration.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import firebase_admin
import httpx
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

try:
	from authlib.integrations.base_client import OAuthError
	from authlib.integrations.starlette_client import OAuth
except ModuleNotFoundError:  # Optional dependency; allow import without authlib for tests

	class OAuthError(Exception):
		"""Fallback OAuth error when authlib is unavailable."""

	class OAuth:  # type: ignore[override]
		"""Minimal stub to satisfy imports when authlib is missing."""

		def __init__(self):
			self._providers: Dict[str, Any] = {}

		def register(self, name: str, **kwargs: Any) -> None:
			self._providers[name] = kwargs

		def __getattr__(self, item: str) -> Any:
			return self._providers.get(item)


from app.core.config import get_settings
from app.core.logging import get_audit_logger, get_logger
from app.core.security import create_access_token
from app.models.user import User
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = get_logger(__name__)
audit_logger = get_audit_logger()
settings = get_settings()


class FirebaseUser(BaseModel):
	"""Firebase user model."""

	uid: str
	email: Optional[str] = None
	email_verified: bool = False
	display_name: Optional[str] = None
	photo_url: Optional[str] = None
	phone_number: Optional[str] = None
	disabled: bool = False
	custom_claims: Dict[str, Any] = {}
	provider_data: List[Dict[str, Any]] = []
	created_at: Optional[datetime] = None
	last_sign_in: Optional[datetime] = None


class OAuthService:
	"""Consolidated OAuth service with Firebase integration."""

	def __init__(self):
		"""Initialize OAuth service."""
		self.oauth = OAuth()
		self.firebase_app: Optional[firebase_admin.App] = None
		self.firebase_initialized = False

		# Initialize OAuth providers
		self._setup_oauth_providers()

		# Initialize Firebase if enabled
		if settings.firebase_enabled:
			self._initialize_firebase()

		logger.info("OAuth Service initialized")

	def _setup_oauth_providers(self):
		"""Setup OAuth providers based on configuration."""
		if not settings.oauth_enabled:
			logger.info("OAuth is disabled")
			return

		# Google OAuth setup
		if settings.google_client_id and settings.google_client_secret:
			self.oauth.register(
				name="google",
				client_id=settings.google_client_id,
				client_secret=settings.google_client_secret,
				server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
				client_kwargs={"scope": "openid email profile"},
			)
			logger.info("Google OAuth provider configured")

		# LinkedIn OAuth setup
		if settings.linkedin_client_id and settings.linkedin_client_secret:
			self.oauth.register(
				name="linkedin",
				client_id=settings.linkedin_client_id,
				client_secret=settings.linkedin_client_secret,
				access_token_url="https://www.linkedin.com/oauth/v2/accessToken",
				authorize_url="https://www.linkedin.com/oauth/v2/authorization",
				api_base_url="https://api.linkedin.com/v2/",
				client_kwargs={"scope": "r_liteprofile r_emailaddress"},
			)
			logger.info("LinkedIn OAuth provider configured")

		# GitHub OAuth setup
		if settings.github_client_id and settings.github_client_secret:
			self.oauth.register(
				name="github",
				client_id=settings.github_client_id,
				client_secret=settings.github_client_secret,
				access_token_url="https://github.com/login/oauth/access_token",
				authorize_url="https://github.com/login/oauth/authorize",
				api_base_url="https://api.github.com/",
				client_kwargs={"scope": "user:email"},
			)
			logger.info("GitHub OAuth provider configured")

	def _initialize_firebase(self) -> bool:
		"""Initialize Firebase Admin SDK."""
		try:
			if self.firebase_initialized:
				return True

			# Check if Firebase is enabled
			if not settings.firebase_enabled:
				logger.info("Firebase authentication is disabled")
				return False

			# Get service account configuration
			service_account_config = self._get_firebase_service_account_config()
			if not service_account_config:
				logger.warning("Firebase service account not configured")
				return False

			# Initialize Firebase Admin SDK
			cred = credentials.Certificate(service_account_config)

			# Check if app already exists
			try:
				self.firebase_app = firebase_admin.get_app()
				logger.info("Using existing Firebase app")
			except ValueError:
				# App doesn't exist, create new one
				self.firebase_app = firebase_admin.initialize_app(cred)
				logger.info("Firebase Admin SDK initialized successfully")

			self.firebase_initialized = True
			return True

		except Exception as e:
			logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
			return False

	def _get_firebase_service_account_config(self) -> Optional[Dict[str, Any]]:
		"""Get Firebase service account configuration."""
		try:
			# Try to get from environment variable first
			if hasattr(settings, "firebase_service_account_key") and settings.firebase_service_account_key:
				return json.loads(settings.firebase_service_account_key)

			# Try to get from file
			service_account_path = getattr(settings, "firebase_service_account_path", None)
			if service_account_path and Path(service_account_path).exists():
				with open(service_account_path, "r") as f:
					return json.load(f)

			# Try default locations
			default_paths = ["secrets/firebase-service-account.json", "config/firebase-service-account.json", "firebase-service-account.json"]

			for path in default_paths:
				if Path(path).exists():
					with open(path, "r") as f:
						return json.load(f)

			return None

		except Exception as e:
			logger.error(f"Error loading Firebase service account config: {e}")
			return None

	# OAuth Provider Methods
	def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
		"""Get authorization URL for OAuth provider."""
		if not settings.oauth_enabled:
			raise ValueError("OAuth is not enabled")

		client = getattr(self.oauth, provider, None)
		if not client:
			raise ValueError(f"OAuth provider '{provider}' not configured")

		return client.authorize_redirect_uri(redirect_uri)

	async def oauth_login(self, provider: str, code: str, state: str | None = None) -> Dict:
		"""
		Handle OAuth login and exchange code for token.

		Args:
		    provider: OAuth provider name
		    code: Authorization code
		    state: State parameter for security

		Returns:
		    Dictionary with user data and tokens
		"""
		if not settings.oauth_enabled:
			raise ValueError("OAuth is not enabled")

		try:
			if provider == "google":
				return await self._handle_google_callback(code)
			elif provider == "linkedin":
				return await self._handle_linkedin_callback(code)
			elif provider == "github":
				return await self._handle_github_callback(code)
			else:
				raise ValueError(f"Unsupported OAuth provider: {provider}")
		except Exception as e:
			logger.error(f"OAuth login failed for provider {provider}: {e}")
			raise OAuthError(f"OAuth callback failed: {e!s}")

	async def _handle_google_callback(self, code: str) -> Dict:
		"""Handle Google OAuth callback."""
		async with httpx.AsyncClient() as client:
			# Exchange code for token
			token_response = await client.post(
				"https://oauth2.googleapis.com/token",
				data={
					"client_id": settings.google_client_id,
					"client_secret": settings.google_client_secret,
					"code": code,
					"grant_type": "authorization_code",
					"redirect_uri": settings.google_redirect_uri,
				},
			)
			token_data = token_response.json()

			if "access_token" not in token_data:
				raise OAuthError("Failed to get access token from Google")

			# Get user info
			user_response = await client.get(
				"https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {token_data['access_token']}"}
			)
			user_data = user_response.json()

			return {
				"provider": "google",
				"oauth_id": user_data["id"],
				"email": user_data["email"],
				"name": user_data.get("name", ""),
				"picture": user_data.get("picture", ""),
				"access_token": token_data["access_token"],
			}

	async def _handle_linkedin_callback(self, code: str) -> Dict:
		"""Handle LinkedIn OAuth callback."""
		async with httpx.AsyncClient() as client:
			# Exchange code for token
			token_response = await client.post(
				"https://www.linkedin.com/oauth/v2/accessToken",
				data={
					"grant_type": "authorization_code",
					"code": code,
					"redirect_uri": settings.linkedin_redirect_uri,
					"client_id": settings.linkedin_client_id,
					"client_secret": settings.linkedin_client_secret,
				},
				headers={"Content-Type": "application/x-www-form-urlencoded"},
			)
			token_data = token_response.json()

			if "access_token" not in token_data:
				raise OAuthError("Failed to get access token from LinkedIn")

			# Get user profile
			profile_response = await client.get("https://api.linkedin.com/v2/me", headers={"Authorization": f"Bearer {token_data['access_token']}"})
			profile_data = profile_response.json()

			# Get user email
			email_response = await client.get(
				"https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
				headers={"Authorization": f"Bearer {token_data['access_token']}"},
			)
			email_data = email_response.json()

			email = None
			if email_data.get("elements"):
				email = email_data["elements"][0]["handle~"]["emailAddress"]

			return {
				"provider": "linkedin",
				"oauth_id": profile_data["id"],
				"email": email,
				"name": f"{profile_data.get('firstName', {}).get('localized', {}).get('en_US', '')} {profile_data.get('lastName', {}).get('localized', {}).get('en_US', '')}".strip(),
				"picture": profile_data.get("profilePicture", {})
				.get("displayImage~", {})
				.get("elements", [{}])[0]
				.get("identifiers", [{}])[0]
				.get("identifier", ""),
				"access_token": token_data["access_token"],
			}

	async def _handle_github_callback(self, code: str) -> Dict:
		"""Handle GitHub OAuth callback."""
		async with httpx.AsyncClient() as client:
			# Exchange code for token
			token_response = await client.post(
				"https://github.com/login/oauth/access_token",
				data={"client_id": settings.github_client_id, "client_secret": settings.github_client_secret, "code": code},
				headers={"Accept": "application/json"},
			)
			token_data = token_response.json()

			if "access_token" not in token_data:
				raise OAuthError("Failed to get access token from GitHub")

			# Get user info
			user_response = await client.get("https://api.github.com/user", headers={"Authorization": f"token {token_data['access_token']}"})
			user_data = user_response.json()

			# Get user email (GitHub may not provide email in user endpoint)
			email = user_data.get("email")
			if not email:
				email_response = await client.get(
					"https://api.github.com/user/emails", headers={"Authorization": f"token {token_data['access_token']}"}
				)
				emails = email_response.json()
				primary_email = next((e["email"] for e in emails if e["primary"]), None)
				email = primary_email or (emails[0]["email"] if emails else None)

			return {
				"provider": "github",
				"oauth_id": str(user_data["id"]),
				"email": email,
				"name": user_data.get("name", user_data.get("login", "")),
				"picture": user_data.get("avatar_url", ""),
				"access_token": token_data["access_token"],
			}

	def create_or_link_user(self, oauth_data: Dict, db: Session) -> Tuple[User, str]:
		"""Create new user or link existing user with OAuth data."""
		provider = oauth_data["provider"]
		oauth_id = oauth_data["oauth_id"]
		email = oauth_data["email"]

		if not email:
			raise ValueError("Email is required for user creation")

		# Check if user already exists with this OAuth provider
		existing_oauth_user = db.query(User).filter(User.oauth_provider == provider, User.oauth_id == oauth_id).first()

		if existing_oauth_user:
			# Update existing OAuth user with latest info
			existing_oauth_user.profile_picture_url = oauth_data.get("picture", "")
			existing_oauth_user.updated_at = existing_oauth_user.updated_at
			# Re-populate profile in case of new data
			self._pre_populate_profile(existing_oauth_user, oauth_data, provider)
			db.commit()
			token = create_access_token({"sub": existing_oauth_user.username, "user_id": existing_oauth_user.id})
			return existing_oauth_user, token

		# Check if user exists with same email
		existing_email_user = db.query(User).filter(User.email == email).first()

		if existing_email_user:
			# Link OAuth to existing email user
			if existing_email_user.oauth_provider is None:
				existing_email_user.oauth_provider = provider
				existing_email_user.oauth_id = oauth_id
				existing_email_user.profile_picture_url = oauth_data.get("picture", "")
				existing_email_user.updated_at = existing_email_user.updated_at
				# Pre-populate profile for newly linked account
				self._pre_populate_profile(existing_email_user, oauth_data, provider)
				db.commit()
				token = create_access_token({"sub": existing_email_user.username, "user_id": existing_email_user.id})
				return existing_email_user, token
			else:
				raise ValueError("Email already associated with another OAuth account")

		# Create new user
		username = self._generate_username_from_oauth(oauth_data, db)
		# For SQLite compatibility, OAuth users get a placeholder password
		placeholder_password = f"oauth_{provider}_{oauth_id}"
		new_user = User(
			username=username,
			email=email,
			hashed_password=placeholder_password,  # Placeholder for OAuth users
			oauth_provider=provider,
			oauth_id=oauth_id,
			profile_picture_url=oauth_data.get("picture", ""),
		)

		# Pre-populate profile if possible
		self._pre_populate_profile(new_user, oauth_data, provider)

		db.add(new_user)
		db.commit()
		db.refresh(new_user)

		token = create_access_token({"sub": new_user.username, "user_id": new_user.id})
		return new_user, token

	def _generate_username_from_oauth(self, oauth_data: Dict, db: Session) -> str:
		"""Generate unique username from OAuth data."""
		name = oauth_data.get("name", "")
		email = oauth_data.get("email", "")
		provider = oauth_data["provider"]

		# Try to create username from name
		if name:
			base_username = name.lower().replace(" ", "_").replace("-", "_")
			# Remove non-alphanumeric characters except underscore
			base_username = "".join(c for c in base_username if c.isalnum() or c == "_")
		else:
			# Fallback to email prefix
			base_username = email.split("@")[0].lower()

		# Ensure username is unique
		username = base_username
		counter = 1
		while db.query(User).filter(User.username == username).first():
			username = f"{base_username}_{counter}"
			counter += 1

		return username

	def _pre_populate_profile(self, user: User, oauth_data: Dict, provider: str) -> None:
		"""Pre-populate user profile based on OAuth provider data."""
		name = oauth_data.get("name", "")

		# Basic skill extraction based on provider
		if provider == "github":
			# GitHub users might have technical skills
			basic_skills = ["Git", "GitHub"]
			if user.skills is None:
				user.skills = basic_skills
			else:
				# Add GitHub skills if not already present
				existing_skills = [skill.lower() for skill in user.skills]
				for skill in basic_skills:
					if skill.lower() not in existing_skills:
						user.skills.append(skill)

		elif provider == "linkedin":
			# LinkedIn users might have professional skills
			if name:
				# Extract potential skills from name/title if it contains technical terms
				technical_terms = [
					"developer",
					"engineer",
					"programmer",
					"architect",
					"analyst",
					"manager",
					"lead",
					"senior",
					"junior",
					"full stack",
					"frontend",
					"backend",
					"devops",
					"data scientist",
					"ml engineer",
				]
				name_lower = name.lower()
				detected_skills = []

				if any(term in name_lower for term in ["developer", "engineer", "programmer"]):
					detected_skills.extend(["Software Development", "Programming"])
				if "full stack" in name_lower:
					detected_skills.extend(["Full Stack Development", "Frontend", "Backend"])
				if "frontend" in name_lower:
					detected_skills.append("Frontend Development")
				if "backend" in name_lower:
					detected_skills.append("Backend Development")
				if "devops" in name_lower:
					detected_skills.extend(["DevOps", "CI/CD"])
				if any(term in name_lower for term in ["data scientist", "ml engineer"]):
					detected_skills.extend(["Data Science", "Machine Learning"])

				if detected_skills:
					if user.skills is None:
						user.skills = detected_skills
					else:
						existing_skills = [skill.lower() for skill in user.skills]
						for skill in detected_skills:
							if skill.lower() not in existing_skills:
								user.skills.append(skill)

		elif provider == "google":
			# Google OAuth provides limited profile information
			# Basic setup for Google users
			if user.skills is None:
				user.skills = []

	def disconnect_oauth_account(self, user_id: int, provider: str, db: Session) -> bool:
		"""Disconnect OAuth account from user."""
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			return False

		if user.oauth_provider == provider:
			# Check if user has a real password (not placeholder) - if not, they can't disconnect OAuth
			if user.hashed_password.startswith("oauth_"):
				raise ValueError("Cannot disconnect OAuth account without setting a password first")

			user.oauth_provider = None
			user.oauth_id = None
			user.profile_picture_url = None
			user.updated_at = user.updated_at
			db.commit()
			return True

		return False

	# Firebase Authentication Methods
	async def verify_firebase_token(self, id_token: str) -> Optional[FirebaseUser]:
		"""Verify Firebase ID token and return user information."""
		try:
			if not self.firebase_initialized:
				if not self._initialize_firebase():
					return None

			# Verify the ID token
			decoded_token = firebase_auth.verify_id_token(id_token)

			# Get user record for additional information
			user_record = firebase_auth.get_user(decoded_token["uid"])

			# Convert to FirebaseUser model
			firebase_user = FirebaseUser(
				uid=user_record.uid,
				email=user_record.email,
				email_verified=user_record.email_verified,
				display_name=user_record.display_name,
				photo_url=user_record.photo_url,
				phone_number=user_record.phone_number,
				disabled=user_record.disabled,
				custom_claims=user_record.custom_claims or {},
				provider_data=[
					{
						"uid": provider.uid,
						"email": provider.email,
						"display_name": provider.display_name,
						"photo_url": provider.photo_url,
						"provider_id": provider.provider_id,
					}
					for provider in user_record.provider_data
				],
				created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000)
				if user_record.user_metadata.creation_timestamp
				else None,
				last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000)
				if user_record.user_metadata.last_sign_in_timestamp
				else None,
			)

			logger.info(f"Successfully verified Firebase token for user: {firebase_user.uid}")
			return firebase_user

		except firebase_auth.InvalidIdTokenError as e:
			logger.warning(f"Invalid Firebase ID token: {e}")
			return None
		except firebase_auth.ExpiredIdTokenError as e:
			logger.warning(f"Expired Firebase ID token: {e}")
			return None
		except Exception as e:
			logger.error(f"Error verifying Firebase ID token: {e}")
			return None

	async def get_firebase_user(self, uid: str) -> Optional[FirebaseUser]:
		"""Get Firebase user by UID."""
		try:
			if not self.firebase_initialized:
				if not self._initialize_firebase():
					return None

			user_record = firebase_auth.get_user(uid)

			firebase_user = FirebaseUser(
				uid=user_record.uid,
				email=user_record.email,
				email_verified=user_record.email_verified,
				display_name=user_record.display_name,
				photo_url=user_record.photo_url,
				phone_number=user_record.phone_number,
				disabled=user_record.disabled,
				custom_claims=user_record.custom_claims or {},
				provider_data=[
					{
						"uid": provider.uid,
						"email": provider.email,
						"display_name": provider.display_name,
						"photo_url": provider.photo_url,
						"provider_id": provider.provider_id,
					}
					for provider in user_record.provider_data
				],
				created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000)
				if user_record.user_metadata.creation_timestamp
				else None,
				last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000)
				if user_record.user_metadata.last_sign_in_timestamp
				else None,
			)

			return firebase_user

		except firebase_auth.UserNotFoundError:
			logger.warning(f"Firebase user not found: {uid}")
			return None
		except Exception as e:
			logger.error(f"Error getting Firebase user {uid}: {e}")
			return None

	async def create_firebase_user(
		self,
		uid: Optional[str] = None,
		email: Optional[str] = None,
		password: Optional[str] = None,
		display_name: Optional[str] = None,
		photo_url: Optional[str] = None,
		email_verified: bool = False,
		phone_number: Optional[str] = None,
		disabled: bool = False,
	) -> Optional[FirebaseUser]:
		"""Create a new Firebase user."""
		try:
			if not self.firebase_initialized:
				if not self._initialize_firebase():
					return None

			# Prepare user creation arguments
			user_args = {}
			if uid:
				user_args["uid"] = uid
			if email:
				user_args["email"] = email
			if password:
				user_args["password"] = password
			if display_name:
				user_args["display_name"] = display_name
			if photo_url:
				user_args["photo_url"] = photo_url
			if phone_number:
				user_args["phone_number"] = phone_number

			user_args["email_verified"] = email_verified
			user_args["disabled"] = disabled

			# Create user
			user_record = firebase_auth.create_user(**user_args)

			# Set default custom claims
			default_claims = {
				"roles": ["user"],
				"created_at": datetime.now(timezone.utc).isoformat(),
				"profile": {"skills": [], "locations": [], "experience_level": "entry", "job_preferences": {}},
			}

			firebase_auth.set_custom_user_claims(user_record.uid, default_claims)

			# Log user creation
			audit_logger.log_event(
				event_type="firebase_user_created",
				action=f"Firebase user created",
				user_id=user_record.uid,
				details={"email": email, "display_name": display_name, "email_verified": email_verified},
			)

			# Return created user
			return await self.get_firebase_user(user_record.uid)

		except firebase_auth.EmailAlreadyExistsError:
			logger.warning(f"Firebase user with email {email} already exists")
			return None
		except firebase_auth.UidAlreadyExistsError:
			logger.warning(f"Firebase user with UID {uid} already exists")
			return None
		except Exception as e:
			logger.error(f"Error creating Firebase user: {e}")
			return None

	async def set_firebase_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
		"""Set custom claims for a Firebase user."""
		try:
			if not self.firebase_initialized:
				if not self._initialize_firebase():
					return False

			firebase_auth.set_custom_user_claims(uid, claims)

			# Log custom claims update
			audit_logger.log_event(
				event_type="firebase_custom_claims_updated", action=f"Firebase custom claims updated", user_id=uid, details={"claims": claims}
			)

			logger.info(f"Firebase custom claims set for user {uid}")
			return True

		except firebase_auth.UserNotFoundError:
			logger.warning(f"Firebase user not found for custom claims: {uid}")
			return False
		except Exception as e:
			logger.error(f"Error setting Firebase custom claims for user {uid}: {e}")
			return False

	async def revoke_firebase_tokens(self, uid: str) -> bool:
		"""Revoke all refresh tokens for a Firebase user."""
		try:
			if not self.firebase_initialized:
				if not self._initialize_firebase():
					return False

			firebase_auth.revoke_refresh_tokens(uid)

			# Log token revocation
			audit_logger.log_event(event_type="firebase_tokens_revoked", action=f"Firebase refresh tokens revoked", user_id=uid, severity="warning")

			logger.info(f"Firebase refresh tokens revoked for user: {uid}")
			return True

		except firebase_auth.UserNotFoundError:
			logger.warning(f"Firebase user not found for token revocation: {uid}")
			return False
		except Exception as e:
			logger.error(f"Error revoking Firebase tokens for user {uid}: {e}")
			return False

	def get_oauth_status(self) -> Dict[str, Any]:
		"""Get OAuth service status."""
		return {
			"oauth_enabled": settings.oauth_enabled,
			"firebase_enabled": settings.firebase_enabled,
			"firebase_initialized": self.firebase_initialized,
			"configured_providers": [provider for provider in ["google", "linkedin", "github"] if getattr(self.oauth, provider, None) is not None],
		}


# Global service instance
_oauth_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
	"""Get OAuth service instance."""
	global _oauth_service
	if _oauth_service is None:
		_oauth_service = OAuthService()
	return _oauth_service
