"""
Security utilities for password hashing and verification, and JWT token handling.
"""

from datetime import datetime, timedelta
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings (should be loaded from config in a real app)
SECRET_KEY = "super-secret-key"  # Replace with a strong, randomly generated key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
	"""
	Create a JWT access token.

	Args:
		data: Data to encode into the token (e.g., user ID, username)
		expires_delta: Optional timedelta for token expiration. If None, defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

	Returns:
		str: Encoded JWT access token
	"""
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt


def get_password_hash(password: str) -> str:
	"""
	Hash a password using bcrypt.

	Args:
		password: Plain text password to hash

	Returns:
		str: Hashed password
	"""
	return pwd_context.hash(password)


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
