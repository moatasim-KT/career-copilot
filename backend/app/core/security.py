"""Security utilities for authentication"""

import warnings
from datetime import datetime, timedelta, timezone

warnings.filterwarnings(
	"ignore",
	message="'crypt' is deprecated and slated for removal in Python 3.13",
	category=DeprecationWarning,
)

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

settings = get_settings()
# Use bcrypt with cost factor 12 for strong password hashing (OWASP recommendation)
pwd_context = CryptContext(
	schemes=["bcrypt"],
	deprecated="auto",
	bcrypt__rounds=12,  # Computational cost factor (default is 12, minimum recommended)
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	"""Hash password using bcrypt with sufficient computational effort.
	
	Uses bcrypt with cost factor 12 (2^12 = 4096 iterations) which provides
	sufficient protection against brute-force attacks while maintaining
	reasonable performance.
	"""
	return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
	try:
		return jwt.decode(token, settings.jwt_secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
	except JWTError:
		return None
