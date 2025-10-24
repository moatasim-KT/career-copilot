"""
API security management and secure configuration.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class APISecurityManager:
	"""Secure API key management and configuration."""

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.encryption_key = self._get_or_create_encryption_key()
		self.cipher_suite = Fernet(self.encryption_key)

		# Rate limiting
		self.rate_limits = {}
		self.max_requests_per_minute = 60
		self.max_requests_per_hour = 1000

		# API key validation
		self.api_keys = self._load_api_keys()

	def _get_or_create_encryption_key(self) -> bytes:
		"""Get or create encryption key for secure storage."""
		key_file = Path("security/api_key.key")
		key_file.parent.mkdir(parents=True, exist_ok=True)

		if key_file.exists():
			with open(key_file, "rb") as f:
				return f.read()
		else:
			# Generate new key
			key = Fernet.generate_key()
			with open(key_file, "wb") as f:
				f.write(key)
			# Set restrictive permissions
			os.chmod(key_file, 0o600)
			return key

	def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
		"""Load API keys from secure storage."""
		keys_file = Path("security/api_keys.json")
		if not keys_file.exists():
			return {}

		try:
			with open(keys_file, "r") as f:
				encrypted_data = f.read()

			# Decrypt the data
			decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
			return json.loads(decrypted_data.decode())
		except Exception as e:
			self.logger.error(f"Failed to load API keys: {e!s}")
			return {}

	def _save_api_keys(self, keys: Dict[str, Dict[str, Any]]):
		"""Save API keys to secure storage."""
		keys_file = Path("security/api_keys.json")
		keys_file.parent.mkdir(parents=True, exist_ok=True)

		try:
			# Encrypt the data
			json_data = json.dumps(keys, default=str)
			encrypted_data = self.cipher_suite.encrypt(json_data.encode())

			with open(keys_file, "wb") as f:
				f.write(encrypted_data)

			# Set restrictive permissions
			os.chmod(keys_file, 0o600)

		except Exception as e:
			self.logger.error(f"Failed to save API keys: {e!s}")

	def generate_api_key(self, name: str, permissions: List[str] = None, expires_in_days: int = 365) -> str:
		"""
		Generate a new API key.

		Args:
		    name: Name/description for the API key
		    permissions: List of permissions for the key
		    expires_in_days: Days until key expires

		Returns:
		    Generated API key
		"""
		if permissions is None:
			permissions = ["read"]

		# Generate secure random key
		api_key = secrets.token_urlsafe(32)

		# Create key metadata
		key_metadata = {
			"name": name,
			"created_at": datetime.utcnow().isoformat(),
			"expires_at": (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
			"permissions": permissions,
			"is_active": True,
			"last_used": None,
			"usage_count": 0,
		}

		# Store the key
		self.api_keys[api_key] = key_metadata
		self._save_api_keys(self.api_keys)

		self.logger.info(f"Generated new API key: {name}")
		return api_key

	def validate_api_key(self, api_key: str) -> Dict[str, Any]:
		"""
		Validate an API key.

		Args:
		    api_key: API key to validate

		Returns:
		    Validation result with key metadata
		"""
		if api_key not in self.api_keys:
			return {"is_valid": False, "reason": "Invalid API key"}

		key_metadata = self.api_keys[api_key]

		# Check if key is active
		if not key_metadata.get("is_active", False):
			return {"is_valid": False, "reason": "API key is inactive"}

		# Check if key is expired
		expires_at = datetime.fromisoformat(key_metadata["expires_at"])
		if datetime.utcnow() > expires_at:
			return {"is_valid": False, "reason": "API key has expired"}

		# Update usage statistics
		key_metadata["last_used"] = datetime.utcnow().isoformat()
		key_metadata["usage_count"] = key_metadata.get("usage_count", 0) + 1
		self._save_api_keys(self.api_keys)

		return {"is_valid": True, "metadata": key_metadata}

	def revoke_api_key(self, api_key: str) -> bool:
		"""
		Revoke an API key.

		Args:
		    api_key: API key to revoke

		Returns:
		    True if key was revoked successfully
		"""
		if api_key in self.api_keys:
			self.api_keys[api_key]["is_active"] = False
			self.api_keys[api_key]["revoked_at"] = datetime.utcnow().isoformat()
			self._save_api_keys(self.api_keys)
			self.logger.info(f"Revoked API key: {api_key[:8]}...")
			return True
		return False

	def list_api_keys(self) -> List[Dict[str, Any]]:
		"""List all API keys (without the actual key values)."""
		keys_list = []
		for key, metadata in self.api_keys.items():
			keys_list.append(
				{
					"key_id": key[:8] + "...",
					"name": metadata.get("name", "Unknown"),
					"created_at": metadata.get("created_at"),
					"expires_at": metadata.get("expires_at"),
					"is_active": metadata.get("is_active", False),
					"last_used": metadata.get("last_used"),
					"usage_count": metadata.get("usage_count", 0),
				}
			)
		return keys_list

	def check_rate_limit(self, identifier: str) -> Dict[str, Any]:
		"""
		Check if request is within rate limits.

		Args:
		    identifier: Client identifier (IP, user ID, etc.)

		Returns:
		    Rate limit check result
		"""
		now = datetime.utcnow()

		if identifier not in self.rate_limits:
			self.rate_limits[identifier] = {"requests": [], "last_cleanup": now}

		client_data = self.rate_limits[identifier]

		# Clean up old requests
		if (now - client_data["last_cleanup"]).seconds > 3600:  # Cleanup every hour
			self._cleanup_old_requests(identifier, now)
			client_data["last_cleanup"] = now

		# Check minute limit
		minute_ago = now - timedelta(minutes=1)
		recent_requests = [req_time for req_time in client_data["requests"] if req_time > minute_ago]

		if len(recent_requests) >= self.max_requests_per_minute:
			return {"allowed": False, "reason": "Rate limit exceeded (per minute)", "retry_after": 60}

		# Check hour limit
		hour_ago = now - timedelta(hours=1)
		hourly_requests = [req_time for req_time in client_data["requests"] if req_time > hour_ago]

		if len(hourly_requests) >= self.max_requests_per_hour:
			return {"allowed": False, "reason": "Rate limit exceeded (per hour)", "retry_after": 3600}

		# Add current request
		client_data["requests"].append(now)

		return {
			"allowed": True,
			"remaining_minute": self.max_requests_per_minute - len(recent_requests) - 1,
			"remaining_hour": self.max_requests_per_hour - len(hourly_requests) - 1,
		}

	def _cleanup_old_requests(self, identifier: str, now: datetime):
		"""Clean up old request timestamps."""
		if identifier in self.rate_limits:
			hour_ago = now - timedelta(hours=1)
			self.rate_limits[identifier]["requests"] = [req_time for req_time in self.rate_limits[identifier]["requests"] if req_time > hour_ago]

	def create_secure_headers(self, api_key: str, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
		"""
		Create secure headers for API requests.

		Args:
		    api_key: API key for authentication
		    additional_headers: Additional headers to include

		Returns:
		    Dictionary of secure headers
		"""
		headers = {
			"Authorization": f"Bearer {api_key}",
			"User-Agent": "Contract-Analyzer-Frontend/1.0",
			"Accept": "application/json",
			"Content-Type": "application/json",
			"X-Request-ID": secrets.token_urlsafe(16),
			"X-Timestamp": str(int(datetime.utcnow().timestamp())),
		}

		if additional_headers:
			headers.update(additional_headers)

		return headers

	def sign_request(self, method: str, url: str, body: str, api_secret: str) -> str:
		"""
		Create a request signature for additional security.

		Args:
		    method: HTTP method
		    url: Request URL
		    body: Request body
		    api_secret: API secret for signing

		Returns:
		    Request signature
		"""
		# Create signature string
		timestamp = str(int(datetime.utcnow().timestamp()))
		signature_string = f"{method.upper()}{url}{body}{timestamp}"

		# Create HMAC signature
		signature = hmac.new(api_secret.encode(), signature_string.encode(), hashlib.sha256).hexdigest()

		return signature

	def validate_request_signature(self, method: str, url: str, body: str, signature: str, api_secret: str, timestamp: str) -> bool:
		"""
		Validate a request signature.

		Args:
		    method: HTTP method
		    url: Request URL
		    body: Request body
		    signature: Provided signature
		    api_secret: API secret for validation
		    timestamp: Request timestamp

		Returns:
		    True if signature is valid
		"""
		try:
			# Check timestamp (prevent replay attacks)
			request_time = datetime.fromtimestamp(int(timestamp))
			if abs((datetime.utcnow() - request_time).seconds) > 300:  # 5 minutes
				return False

			# Create expected signature
			signature_string = f"{method.upper()}{url}{body}{timestamp}"
			expected_signature = hmac.new(api_secret.encode(), signature_string.encode(), hashlib.sha256).hexdigest()

			# Compare signatures
			return hmac.compare_digest(signature, expected_signature)

		except Exception as e:
			self.logger.error(f"Signature validation failed: {e!s}")
			return False

	def encrypt_sensitive_data(self, data: str) -> str:
		"""Encrypt sensitive data."""
		try:
			encrypted_data = self.cipher_suite.encrypt(data.encode())
			return base64.b64encode(encrypted_data).decode()
		except Exception as e:
			self.logger.error(f"Encryption failed: {e!s}")
			return data

	def decrypt_sensitive_data(self, encrypted_data: str) -> str:
		"""Decrypt sensitive data."""
		try:
			decoded_data = base64.b64decode(encrypted_data.encode())
			decrypted_data = self.cipher_suite.decrypt(decoded_data)
			return decrypted_data.decode()
		except Exception as e:
			self.logger.error(f"Decryption failed: {e!s}")
			return encrypted_data

	def get_environment_config(self) -> Dict[str, Any]:
		"""Get secure environment configuration."""
		return {
			"backend_url": os.getenv("BACKEND_URL", "http://localhost:8002"),
			"api_timeout": int(os.getenv("API_TIMEOUT", "300")),
			"max_file_size": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
			"allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
			"enable_cors": os.getenv("ENABLE_CORS", "true").lower() == "true",
			"log_level": os.getenv("LOG_LEVEL", "INFO"),
			"encryption_enabled": os.getenv("ENCRYPTION_ENABLED", "true").lower() == "true",
		}

	def validate_environment(self) -> List[str]:
		"""Validate environment configuration for security issues."""
		issues = []

		# Check for default values
		if os.getenv("BACKEND_URL") == "http://localhost:8002":
			issues.append("Using default backend URL in production")

		if os.getenv("MAX_FILE_SIZE_MB", "50") == "50":
			issues.append("Using default file size limit")

		# Check for missing security headers
		if not os.getenv("SECRET_KEY"):
			issues.append("SECRET_KEY not set")

		if not os.getenv("API_SECRET"):
			issues.append("API_SECRET not set")

		# Check for insecure configurations
		if os.getenv("DEBUG", "false").lower() == "true":
			issues.append("Debug mode enabled in production")

		if os.getenv("ALLOWED_ORIGINS") == "*":
			issues.append("CORS allows all origins")

		return issues
