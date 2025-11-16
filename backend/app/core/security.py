"""Security utilities for hashing, token generation, and token validation."""

from datetime import timedelta
from typing import Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.datetime import utc_now

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt", "sha256_crypt"], default="bcrypt", deprecated="auto")
logger = get_logger(__name__)


class TokenPayload(BaseModel):
	"""Typed payload stored inside JWT access tokens."""

	sub: str
	email: str | None = None
	exp: int
	iat: int | None = None


class InvalidTokenError(Exception):
	"""Raised when a JWT cannot be decoded or validated."""


def _get_jwt_settings() -> tuple[str, str, int]:
	"""Fetch secret, algorithm, and expiration (minutes) from unified settings."""
	settings = get_settings()
	secret_proxy = settings.jwt_secret_key
	secret_value = secret_proxy.get_secret_value().strip() if secret_proxy else ""
	if not secret_value:
		raise RuntimeError("JWT secret key is not configured. Set JWT_SECRET_KEY or secrets/jwt_secret.txt.")

	algorithm = getattr(settings, "jwt_algorithm", "HS256")
	expiration_hours = getattr(settings, "jwt_expiration_hours", 24)
	default_expiration_minutes = max(1, int(expiration_hours) * 60)
	return secret_value, algorithm, default_expiration_minutes


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
	"""
	Create a JWT access token.

	Args:
		data: Data to encode into the token (e.g., user ID, username)
		expires_delta: Optional timedelta for token expiration. If None, defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

	Returns:
		str: Encoded JWT access token
	"""
	secret, algorithm, default_minutes = _get_jwt_settings()
	to_encode = data.copy()
	expire_delta = expires_delta or timedelta(minutes=default_minutes)
	expire = utc_now() + expire_delta
	to_encode.update({"exp": expire, "iat": utc_now()})
	return jwt.encode(to_encode, secret, algorithm=algorithm)


def decode_access_token(token: str) -> TokenPayload:
	"""Decode and validate a JWT access token, returning the typed payload."""
	secret, algorithm, _ = _get_jwt_settings()
	try:
		payload: dict[str, Any] = jwt.decode(token, secret, algorithms=[algorithm])
		return TokenPayload(**payload)
	except (JWTError, ValidationError) as exc:
		raise InvalidTokenError("Could not validate credentials") from exc


def get_password_hash(password: str) -> str:
	"""
	Hash a password using bcrypt.

	Args:
		password: Plain text password to hash

	Returns:
		str: Hashed password
	"""
	try:
		return pwd_context.hash(password)
	except ValueError as exc:
		logger.warning("bcrypt hashing failed (%s); falling back to sha256_crypt", exc)
		return pwd_context.hash(password, scheme="sha256_crypt")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""
	Verify a password against a hash.

	Args:
		plain_password: Plain text password to verify
		hashed_password: Hashed password to verify against

	Returns:
		bool: True if password matches, False otherwise
	"""
	return pwd_context.verify(plain_password, hashed_password)
