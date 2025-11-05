"""
Consolidated Authentication Middleware for Career Copilot System.
Handles Firebase ID token validation, JWT token processing, API key authentication,
session management, and security headers.
"""

# def None  # get_authentication_service(): return None
# def None  # get_authorization_service(): return None
# from ..services.authentication_service import get_authentication_service

# def None  # get_authentication_service(): return None
# def None  # get_authorization_service(): return None

# from ..services.authorization_service import get_authorization_service

import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional

import firebase_admin
import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from starlette.middleware.base import BaseHTTPMiddleware

# Security utilities are imported as needed
from ..config.firebase_config import get_firebase_config
from ..core.audit import AuditEventType, AuditSeverity, audit_logger
from ..core.config import get_settings
from ..core.logging import get_logger
from ..services.api_key_service import get_api_key_manager

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
	"""Custom authentication error."""

	pass


class AuthorizationError(Exception):
	"""Custom authorization error."""

	pass


class FirebaseAuthManager:
	"""Manages Firebase authentication and token validation."""

	def __init__(self):
		self.settings = get_settings()
		self.firebase_config = get_firebase_config()
		self.app = None
		self.initialized = False

	def initialize(self) -> bool:
		"""Initialize Firebase Admin SDK."""
		try:
			if self.initialized:
				return True

			# Get service account configuration
			service_account_config = self.firebase_config.get_service_account_config()
			if not service_account_config:
				logger.warning("Firebase service account not configured - authentication disabled")
				return False

			# Initialize Firebase Admin SDK
			cred = credentials.Certificate(service_account_config)
			self.app = firebase_admin.initialize_app(cred)

			self.initialized = True
			logger.info("Firebase Admin SDK initialized successfully")
			return True

		except Exception as e:
			logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
			return False

	async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
		"""Verify Firebase ID token and return user claims."""
		try:
			if not self.initialized:
				if not self.initialize():
					raise AuthenticationError("Firebase not initialized")

			# Verify the ID token
			decoded_token = firebase_auth.verify_id_token(id_token)

			# Extract user information
			user_info = {
				"uid": decoded_token["uid"],
				"email": decoded_token.get("email"),
				"email_verified": decoded_token.get("email_verified", False),
				"name": decoded_token.get("name"),
				"picture": decoded_token.get("picture"),
				"firebase_claims": decoded_token,
			}

			# Get custom claims
			user_record = firebase_auth.get_user(decoded_token["uid"])
			if user_record.custom_claims:
				user_info["custom_claims"] = user_record.custom_claims

			logger.info(f"Successfully verified Firebase token for user: {user_info['uid']}")
			return user_info

		except firebase_auth.InvalidIdTokenError as e:
			logger.warning(f"Invalid Firebase ID token: {e}")
			raise AuthenticationError("Invalid authentication token")
		except firebase_auth.ExpiredIdTokenError as e:
			logger.warning(f"Expired Firebase ID token: {e}")
			raise AuthenticationError("Authentication token expired")
		except Exception as e:
			logger.error(f"Error verifying Firebase ID token: {e}")
			raise AuthenticationError("Authentication verification failed")

	async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
		"""Set custom claims for a user."""
		try:
			if not self.initialized:
				if not self.initialize():
					return False

			firebase_auth.set_custom_user_claims(uid, claims)
			logger.info(f"Set custom claims for user {uid}: {claims}")

			# Log audit event
			audit_logger.log_security_event(event_type="custom_claims_updated", user_id=uid, details={"claims": claims})

			return True

		except Exception as e:
			logger.error(f"Error setting custom claims for user {uid}: {e}")
			return False

	async def revoke_refresh_tokens(self, uid: str) -> bool:
		"""Revoke all refresh tokens for a user."""
		try:
			if not self.initialized:
				if not self.initialize():
					return False

			firebase_auth.revoke_refresh_tokens(uid)
			logger.info(f"Revoked refresh tokens for user: {uid}")

			# Log audit event
			audit_logger.log_security_event(event_type="refresh_tokens_revoked", user_id=uid, severity="warning")

			return True

		except Exception as e:
			logger.error(f"Error revoking refresh tokens for user {uid}: {e}")
			return False


class JWTManager:
	"""Manages JWT token creation and validation for internal API access."""

	def __init__(self):
		self.settings = get_settings()
		self.secret_key = self.settings.jwt_secret_key.get_secret_value()
		self.algorithm = self.settings.jwt_algorithm
		self.expiration_hours = self.settings.jwt_expiration_hours

	def create_access_token(self, user_data: Dict[str, Any]) -> str:
		"""Create JWT access token for authenticated user."""
		try:
			# Prepare token payload
			payload = {
				"sub": user_data["uid"],
				"email": user_data.get("email"),
				"name": user_data.get("name"),
				"email_verified": user_data.get("email_verified", False),
				"iat": datetime.now(timezone.utc),
				"exp": datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours),
				"iss": "career-copilot-system",
				"aud": "career-copilot-api",
			}

			# Add custom claims if present
			if "custom_claims" in user_data:
				payload["custom_claims"] = user_data["custom_claims"]

			# Create JWT token
			token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

			logger.info(f"Created JWT access token for user: {user_data['uid']}")
			return token

		except Exception as e:
			logger.error(f"Error creating JWT access token: {e}")
			raise AuthenticationError("Failed to create access token")

	def verify_access_token(self, token: str) -> Dict[str, Any]:
		"""Verify JWT access token and return user data."""
		try:
			# Decode and verify token
			payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], audience="career-copilot-api", issuer="career-copilot-system")

			# Extract user information
			user_data = {
				"uid": payload["sub"],
				"email": payload.get("email"),
				"name": payload.get("name"),
				"email_verified": payload.get("email_verified", False),
				"custom_claims": payload.get("custom_claims", {}),
			}

			return user_data

		except jwt.ExpiredSignatureError:
			logger.warning("JWT token expired")
			raise AuthenticationError("Access token expired")
		except jwt.InvalidTokenError as e:
			logger.warning(f"Invalid JWT token: {e}")
			raise AuthenticationError("Invalid access token")
		except Exception as e:
			logger.error(f"Error verifying JWT token: {e}")
			raise AuthenticationError("Token verification failed")


class ConsolidatedAuthMiddleware(BaseHTTPMiddleware):
	"""Consolidated authentication middleware supporting JWT, Firebase, and API key authentication."""

	def __init__(self, app):
		super().__init__(app)
		self.settings = get_settings()
		self.firebase_manager = FirebaseAuthManager()
		self.jwt_manager = JWTManager()
		self.auth_service = None  # get_authentication_service()
		self.authz_service = None  # get_authorization_service()
		self.api_key_manager = get_api_key_manager()

		# Session management
		self.session_timeout_minutes = 30
		self.active_sessions = {}  # In production, use Redis

		# Paths that don't require authentication
		self.public_paths = {
			"/",
			"/favicon.ico",
			"/docs",
			"/redoc",
			"/openapi.json",
			"/api/v1/health",
			"/api/v1/health/detailed",
			"/api/v1/health/readiness",
			"/api/v1/health/liveness",
			"/api/v1/health/metrics",
			"/api/v1/health/logging",
			"/api/v1/health/services",
			"/api/v1/auth/login",
			"/api/v1/auth/register",
			"/api/v1/auth/refresh",
			"/monitoring/health",
			"/monitoring/health/detailed",
			"/monitoring/health/live",
			"/monitoring/health/ready",
			"/monitoring/status",
			"/monitoring/metrics",
			"/monitoring/metrics/prometheus",
			"/monitoring/metrics/performance",
			"/monitoring/alerts",
			"/monitoring/langsmith/status",
			"/monitoring/config",
		}

		# Paths that require specific permissions
		self.protected_paths = {"/api/v1/admin": ["admin"], "/api/v1/users": ["user_management"], "/api/v1/security": ["security_management"]}

	async def dispatch(self, request: Request, call_next):
		"""Process request with consolidated authentication."""
		start_time = time.time()

		try:
			# Skip authentication entirely in development mode if disabled
			if self.settings.disable_auth or self.settings.development_mode:
				# Add mock authentication context for development
				request.state.current_user = None
				request.state.session_id = "dev-session"
				request.state.auth_method = "development"
				request.state.is_authenticated = False
				return await call_next(request)

			# Skip authentication for public paths
			if self._should_skip_auth(request.url.path):
				return await call_next(request)

			# Try different authentication methods in order of preference
			auth_result = await self._authenticate_request(request)

			if not auth_result:
				# No valid authentication found
				await self._log_auth_attempt(request, "no_valid_auth", False)
				raise HTTPException(
					status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer, ApiKey"}
				)

			# Check path-specific permissions
			if not await self._check_path_permissions(request.url.path, auth_result):
				await self._log_auth_attempt(request, "insufficient_permissions", False, auth_result.get("uid"))
				raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this resource")

			# Add authentication context to request
			request.state.current_user = auth_result
			request.state.session_id = auth_result.get("session_id", "unknown")
			request.state.auth_method = auth_result.get("auth_method", "unknown")
			request.state.is_authenticated = True

			# Handle session management for JWT tokens
			if auth_result.get("auth_method") == "jwt":
				await self._handle_session_management(request, auth_result)

			# Process request
			response = await call_next(request)

			# Add security headers
			self._add_security_headers(response, auth_result)

			# Log successful authentication
			duration = time.time() - start_time
			await self._log_auth_attempt(request, "success", True, auth_result.get("uid"), duration)

			return response

		except HTTPException:
			raise
		except Exception as e:
			logger.error(f"Authentication error: {e}")
			await self._log_auth_attempt(request, "error", False)
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service error")

	async def _authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
		"""Try different authentication methods and return user data."""

		# 1. Try API key authentication first
		api_key = self._extract_api_key(request)
		if api_key:
			try:
				validation_result = await self.api_key_manager.validate_api_key(
					api_key=api_key, ip_address=request.client.host if request.client else "unknown"
				)

				if validation_result.is_valid:
					return {
						"uid": str(validation_result.user_data["id"]),
						"email": validation_result.user_data["email"],
						"name": validation_result.user_data["username"],
						"roles": validation_result.user_data.get("roles", []),
						"permissions": validation_result.key_data.permissions,
						"auth_method": "api_key",
						"session_id": validation_result.key_data.key_id,
						"rate_limit_remaining": validation_result.rate_limit_remaining,
						"rate_limit_reset": validation_result.rate_limit_reset,
					}
			except Exception as e:
				logger.warning(f"API key authentication failed: {e}")

		# 2. Try JWT token authentication
		token = self._extract_jwt_token(request)
		if token:
			try:
				# Try internal JWT first
				user_data = self.jwt_manager.verify_access_token(token)
				if user_data:
					user_data["auth_method"] = "jwt"
					user_data["session_id"] = f"jwt-{user_data['uid']}"
					return user_data
			except AuthenticationError:
				pass  # Try Firebase token

			# Try Firebase ID token
			try:
				user_data = await self.firebase_manager.verify_id_token(token)
				if user_data:
					# Create JWT token for future API calls
					access_token = self.jwt_manager.create_access_token(user_data)
					user_data["access_token"] = access_token
					user_data["auth_method"] = "firebase"
					user_data["session_id"] = f"firebase-{user_data['uid']}"
					return user_data
			except AuthenticationError as e:
				logger.warning(f"Firebase authentication failed: {e}")

		return None

	def _should_skip_auth(self, path: str) -> bool:
		"""Check if authentication should be skipped for this path."""
		return any(path.startswith(public_path) for public_path in self.public_paths)

	def _extract_jwt_token(self, request: Request) -> Optional[str]:
		"""Extract JWT token from request headers."""
		# Check Authorization header
		auth_header = request.headers.get("Authorization")
		if auth_header and auth_header.startswith("Bearer "):
			return auth_header[7:]  # Remove "Bearer " prefix

		# Check for token in cookies (for web sessions)
		token_cookie = request.cookies.get("access_token")
		if token_cookie:
			return token_cookie

		return None

	def _extract_api_key(self, request: Request) -> Optional[str]:
		"""Extract API key from request headers."""
		# Check X-API-Key header
		api_key = request.headers.get("X-API-Key")
		if api_key:
			return api_key

		# Check Authorization header with ApiKey scheme
		auth_header = request.headers.get("Authorization")
		if auth_header and auth_header.startswith("ApiKey "):
			return auth_header[7:]  # Remove "ApiKey " prefix

		return None

	async def _check_path_permissions(self, path: str, auth_result: Dict[str, Any]) -> bool:
		"""Check if user has required permissions for the path."""
		# Check protected paths
		for protected_path, required_roles in self.protected_paths.items():
			if path.startswith(protected_path):
				# Check if user has any of the required roles
				user_roles = set(auth_result.get("roles", []))
				if "custom_claims" in auth_result:
					user_roles.update(auth_result["custom_claims"].get("roles", []))

				required_roles_set = set(required_roles)

				if not user_roles.intersection(required_roles_set):
					return False

		# For job application tracking endpoints, check specific permissions
		if path.startswith("/api/v1/contracts"):
			user_permissions = auth_result.get("permissions", [])
			if "analyze_contract" not in user_permissions:
				return False

		return True

	async def _handle_session_management(self, request: Request, auth_result: Dict[str, Any]):
		"""Handle session management for JWT tokens."""
		session_id = auth_result.get("session_id")
		user_id = auth_result.get("uid")

		if session_id and user_id:
			# Update session activity
			self._update_session_activity(session_id, user_id)

			# Check session timeout
			if self._is_session_expired(session_id):
				# Log session timeout
				audit_logger.log_event(
					event_type=AuditEventType.SESSION_TIMEOUT,
					action="Session expired due to inactivity",
					user_id=user_id,
					details={"session_id": session_id},
				)

				raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired due to inactivity")

	def _update_session_activity(self, session_id: str, user_id: str):
		"""Update session last activity time."""
		self.active_sessions[session_id] = {"user_id": user_id, "last_activity": datetime.now(timezone.utc)}

	def _is_session_expired(self, session_id: str) -> bool:
		"""Check if session has expired."""
		if session_id not in self.active_sessions:
			return True

		session_data = self.active_sessions[session_id]
		last_activity = session_data["last_activity"]

		# Check if session has been inactive for too long
		inactive_duration = datetime.now(timezone.utc) - last_activity
		return inactive_duration.total_seconds() > (self.session_timeout_minutes * 60)

	def _add_security_headers(self, response, auth_result: Dict[str, Any]):
		"""Add security headers to response."""
		# Add session information
		response.headers["X-Session-ID"] = auth_result.get("session_id", "unknown")
		response.headers["X-User-ID"] = str(auth_result.get("uid", "unknown"))
		response.headers["X-Auth-Method"] = auth_result.get("auth_method", "unknown")

		# Add security headers
		response.headers["X-Content-Type-Options"] = "nosniff"
		response.headers["X-Frame-Options"] = "DENY"
		response.headers["X-XSS-Protection"] = "1; mode=block"
		response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

		# Add cache control for authenticated responses
		response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
		response.headers["Pragma"] = "no-cache"

		# Add rate limit headers for API key authentication
		if auth_result.get("auth_method") == "api_key":
			if "rate_limit_remaining" in auth_result:
				response.headers["X-RateLimit-Remaining"] = str(auth_result["rate_limit_remaining"])
			if auth_result.get("rate_limit_reset"):
				response.headers["X-RateLimit-Reset"] = auth_result["rate_limit_reset"].isoformat()

		# Add session timeout info for JWT sessions
		if auth_result.get("auth_method") == "jwt":
			response.headers["X-Session-Timeout"] = str(self.session_timeout_minutes * 60)

	async def _log_auth_attempt(self, request: Request, result: str, success: bool, user_id: Optional[str] = None, duration: Optional[float] = None):
		"""Log authentication attempt."""
		client_ip = self._get_client_ip(request)
		user_agent = request.headers.get("user-agent", "")

		# Determine severity
		if success:
			severity = AuditSeverity.LOW
		elif result in ["invalid_token", "token_expired", "insufficient_permissions"]:
			severity = AuditSeverity.MEDIUM
		else:
			severity = AuditSeverity.HIGH

		# Log to audit system
		audit_logger.log_event(
			event_type=AuditEventType.AUTHENTICATION_ATTEMPT,
			action=f"Authentication: {result}",
			result="success" if success else "failure",
			severity=severity,
			user_id=user_id,
			ip_address=client_ip,
			user_agent=user_agent,
			details={"path": request.url.path, "method": request.method, "result": result, "duration_ms": duration * 1000 if duration else None},
		)

	def _get_client_ip(self, request: Request) -> str:
		"""Extract client IP address."""
		# Check for forwarded headers
		forwarded_for = request.headers.get("x-forwarded-for")
		if forwarded_for:
			return forwarded_for.split(",")[0].strip()

		real_ip = request.headers.get("x-real-ip")
		if real_ip:
			return real_ip

		return request.client.host if request.client else "unknown"


# Global instances
_firebase_auth_manager: Optional[FirebaseAuthManager] = None
_jwt_manager: Optional[JWTManager] = None


def get_firebase_auth_manager() -> FirebaseAuthManager:
	"""Get Firebase authentication manager instance."""
	global _firebase_auth_manager
	if _firebase_auth_manager is None:
		_firebase_auth_manager = FirebaseAuthManager()
	return _firebase_auth_manager


def get_jwt_manager() -> JWTManager:
	"""Get JWT manager instance."""
	global _jwt_manager
	if _jwt_manager is None:
		_jwt_manager = JWTManager()
	return _jwt_manager


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
	"""Extract and validate user from request authentication."""
	settings = get_settings()

	# Skip authentication if disabled
	if settings.disable_auth:
		return {"uid": "test-user", "email": "test@example.com", "name": "Test User", "email_verified": True, "custom_claims": {"roles": ["user"]}}

	# Get user from request state (set by middleware)
	if hasattr(request.state, "current_user") and request.state.is_authenticated:
		return request.state.current_user

	return None


# FastAPI dependencies
async def get_current_active_user(request: Request):
	"""Get current active user."""
	current_user = await get_current_user(request)

	if not current_user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

	return current_user


def require_auth(func: Callable) -> Callable:
	"""Decorator to require authentication for endpoint."""

	@wraps(func)
	async def wrapper(*args, **kwargs):
		# Find request object in arguments
		request = None
		for arg in args:
			if isinstance(arg, Request):
				request = arg
				break

		if not request:
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request object not found")

		# Get current user
		user = await get_current_user(request)
		if not user:
			audit_logger.log_security_event(
				event_type="unauthorized_access_attempt",
				ip_address=request.client.host if request.client else None,
				user_agent=request.headers.get("User-Agent"),
				details={"endpoint": request.url.path},
				severity="warning",
			)

			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})

		# Add user to kwargs
		kwargs["current_user"] = user

		# Log successful authentication
		audit_logger.log_security_event(
			event_type="authenticated_access",
			user_id=user["uid"],
			ip_address=request.client.host if request.client else None,
			details={"endpoint": request.url.path},
		)

		return await func(*args, **kwargs)

	return wrapper


def require_roles(*required_roles: str) -> Callable:
	"""Decorator to require specific roles for endpoint access."""

	def decorator(func: Callable) -> Callable:
		@wraps(func)
		async def wrapper(*args, **kwargs):
			# Get current user (should be set by require_auth)
			current_user = kwargs.get("current_user")
			if not current_user:
				raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

			# Check roles
			user_roles = current_user.get("custom_claims", {}).get("roles", [])
			user_roles.extend(current_user.get("roles", []))

			if not any(role in user_roles for role in required_roles):
				audit_logger.log_security_event(
					event_type="insufficient_permissions",
					user_id=current_user["uid"],
					details={"required_roles": list(required_roles), "user_roles": user_roles},
					severity="warning",
				)

				raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

			return await func(*args, **kwargs)

		return wrapper

	return decorator


def require_permissions(*required_permissions: str):
	"""Dependency factory for requiring specific permissions."""

	async def permission_checker(request: Request):
		"""Check if current user has required permissions."""
		current_user = await get_current_user(request)

		if not current_user:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

		user_permissions = set(current_user.get("permissions", []))
		required_permissions_set = set(required_permissions)

		if not required_permissions_set.issubset(user_permissions):
			missing_permissions = required_permissions_set - user_permissions
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permissions: {', '.join(missing_permissions)}")

		return current_user

	return permission_checker


def require_verified_email(func: Callable) -> Callable:
	"""Decorator to require verified email for endpoint access."""

	@wraps(func)
	async def wrapper(*args, **kwargs):
		# Get current user (should be set by require_auth)
		current_user = kwargs.get("current_user")
		if not current_user:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

		# Check email verification
		if not current_user.get("email_verified", False):
			audit_logger.log_security_event(
				event_type="unverified_email_access_attempt",
				user_id=current_user["uid"],
				details={"email": current_user.get("email")},
				severity="warning",
			)

			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required")

		return await func(*args, **kwargs)

	return wrapper


async def authenticate_request(request: Request) -> Dict[str, Any]:
	"""Authenticate request and return user data or raise HTTPException."""
	user = await get_current_user(request)
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
	return user


# Alias for backward compatibility
AuthMiddleware = ConsolidatedAuthMiddleware
