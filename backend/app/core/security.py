"""Security utilities for authentication"""

import hashlib
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify password using SHA-256 hashing.
	
	Note: This is a simplified implementation for development.
	For production, use proper password hashing like bcrypt, argon2, or scrypt.
	"""
	return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
	"""Hash password using SHA-256.
	
	Note: This is a simplified implementation for development.
	For production, use proper password hashing like bcrypt, argon2, or scrypt
	with salt and multiple iterations.
	"""
	return hashlib.sha256(password.encode()).hexdigest()


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
