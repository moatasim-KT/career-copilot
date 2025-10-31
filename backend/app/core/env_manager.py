"""
Secure environment configuration and API key management.
"""

import base64
import json
import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class SecureEnvironmentManager:
	"""Secure management of environment variables and API keys."""

	def __init__(self):
		self.settings = get_settings()
		self._encryption_key = None
		self._secure_vars: Dict[str, str] = {}
		self._load_secure_environment()

	def _get_encryption_key(self) -> bytes:
		"""Get or generate encryption key for secure storage."""
		if self._encryption_key is None:
			# Use configured encryption key or generate from master key
			if self.settings.encryption_key:
				password = self.settings.encryption_key.get_secret_value().encode()
			else:
				# Security: Generate a secure random key instead of using predictable system info
				# In production, ENCRYPTION_KEY environment variable must be set
				logger.warning("No encryption key configured. Using generated key (not persistent across restarts)")
				password = secrets.token_bytes(32)

			# Derive key using PBKDF2 with strong parameters
			# Use a unique salt per installation (stored in secure location)
			salt_file = Path(".encryption_salt")
			if salt_file.exists():
				salt = salt_file.read_bytes()
			else:
				salt = secrets.token_bytes(32)
				salt_file.write_bytes(salt)
				salt_file.chmod(0o600)
			
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA256(),
				length=32,
				salt=salt,
				iterations=600000,  # Increased from 100k to 600k for better security (OWASP 2023)
			)
			key = base64.urlsafe_b64encode(kdf.derive(password))
			self._encryption_key = key

		return self._encryption_key

	def _load_secure_environment(self):
		"""Load secure environment variables."""
		secure_env_file = Path(".env.secure")
		if secure_env_file.exists():
			try:
				fernet = Fernet(self._get_encryption_key())
				with open(secure_env_file, "rb") as f:
					encrypted_data = f.read()

				decrypted_data = fernet.decrypt(encrypted_data)
				self._secure_vars = json.loads(decrypted_data.decode())
				logger.info("Loaded secure environment variables")
			except Exception as e:
				logger.error(f"Failed to load secure environment: {e}")

	def store_secure_variable(self, key: str, value: str) -> None:
		"""Store a variable securely encrypted."""
		self._secure_vars[key] = value
		self._save_secure_environment()
		logger.info(f"Stored secure variable: {key}")

	def get_secure_variable(self, key: str) -> Optional[str]:
		"""Get a securely stored variable."""
		return self._secure_vars.get(key)

	def _save_secure_environment(self):
		"""Save secure environment variables to encrypted file."""
		try:
			fernet = Fernet(self._get_encryption_key())
			data = json.dumps(self._secure_vars).encode()
			encrypted_data = fernet.encrypt(data)

			secure_env_file = Path(".env.secure")
			with open(secure_env_file, "wb") as f:
				f.write(encrypted_data)

			# Set secure file permissions
			secure_env_file.chmod(0o600)
		except Exception as e:
			logger.error(f"Failed to save secure environment: {e}")

	def validate_environment(self) -> List[str]:
		"""Validate environment configuration and return issues."""
		issues = []

		# Check required variables
		required_vars = [
			"OPENAI_API_KEY",
		]

		for var in required_vars:
			if not os.getenv(var) and not self.get_secure_variable(var):
				issues.append(f"Missing required environment variable: {var}")

		# Check API key format
		openai_key = os.getenv("OPENAI_API_KEY") or self.get_secure_variable("OPENAI_API_KEY")
		if openai_key and not openai_key.startswith("sk-"):
			issues.append("OPENAI_API_KEY appears to have invalid format")

		# Check file permissions on sensitive files
		sensitive_files = [".env", ".env.local", ".env.secure"]
		for file_path in sensitive_files:
			if Path(file_path).exists():
				stat = Path(file_path).stat()
				permissions = oct(stat.st_mode)[-3:]
				if permissions != "600":
					issues.append(f"Insecure permissions on {file_path}: {permissions}")

		return issues


class APIKeyManager:
	"""Enhanced API key management with secure storage."""

	def __init__(self):
		self.env_manager = SecureEnvironmentManager()
		self.api_keys: Dict[str, Dict] = {}
		self._load_api_keys()

	def _load_api_keys(self):
		"""Load API keys from secure storage."""
		# Load from environment variables
		master_key = os.getenv("MASTER_API_KEY") or self.env_manager.get_secure_variable("MASTER_API_KEY")
		if master_key:
			self.api_keys[self._hash_key(master_key)] = {
				"name": "master",
				"scopes": ["read", "write", "admin"],
				"rate_limit": 10000,
				"created_at": "system",
				"is_active": True,
			}

		# Load client keys
		client_keys = os.getenv("CLIENT_API_KEYS", "") or self.env_manager.get_secure_variable("CLIENT_API_KEYS") or ""
		for i, key in enumerate(client_keys.split(","), 1):
			if key.strip():
				self.api_keys[self._hash_key(key.strip())] = {
					"name": f"client_{i}",
					"scopes": ["read", "write"],
					"rate_limit": 1000,
					"created_at": "system",
					"is_active": True,
				}

		logger.info(f"Loaded {len(self.api_keys)} API keys")

	def _hash_key(self, api_key: str) -> str:
		"""Hash API key for secure storage."""
		import hashlib

		return hashlib.sha256(api_key.encode()).hexdigest()

	def generate_api_key(self, name: str, scopes: List[str], rate_limit: int = 1000) -> str:
		"""Generate a new API key."""
		# Generate secure random key
		key = f"ca_{secrets.token_urlsafe(32)}"
		key_hash = self._hash_key(key)

		self.api_keys[key_hash] = {"name": name, "scopes": scopes, "rate_limit": rate_limit, "created_at": "generated", "is_active": True}

		logger.info(f"Generated new API key: {name}")
		return key

	def validate_api_key(self, api_key: str) -> Optional[Dict]:
		"""Validate API key and return key info."""
		if not api_key:
			return None

		key_hash = self._hash_key(api_key)
		key_info = self.api_keys.get(key_hash)

		if key_info and key_info.get("is_active", True):
			return key_info

		return None

	def revoke_api_key(self, api_key: str) -> bool:
		"""Revoke an API key."""
		key_hash = self._hash_key(api_key)
		if key_hash in self.api_keys:
			self.api_keys[key_hash]["is_active"] = False
			logger.info(f"Revoked API key: {self.api_keys[key_hash]['name']}")
			return True
		return False


class EnvironmentValidator:
	"""Validate environment security configuration."""

	def __init__(self):
		self.settings = get_settings()

	def validate_security_config(self) -> Dict[str, List[str]]:
		"""Validate security configuration."""
		issues = {"critical": [], "warning": [], "info": []}

		# Check debug mode (only warn in production)
		if self.settings.api_debug and os.getenv("DEVELOPMENT_MODE", "false").lower() != "true":
			issues["critical"].append("Debug mode is enabled in production")

		# Check default secrets
		if self.settings.jwt_secret_key.get_secret_value() == "your-secret-key-change-in-production":
			issues["critical"].append("Default JWT secret key is being used")

		# Check CORS configuration
		if self.settings.cors_origins == "*":
			issues["critical"].append("CORS allows all origins")

		# Check rate limiting
		if self.settings.rate_limit_requests_per_minute > 1000:
			issues["warning"].append("Rate limit is very high")

		# Check file size limits
		if self.settings.max_file_size_mb > 100:
			issues["warning"].append("File size limit is very high")

		# Check encryption
		if not self.settings.encryption_key:
			issues["warning"].append("No encryption key configured")

		# Check audit logging
		if not self.settings.enable_audit_logging:
			issues["warning"].append("Audit logging is disabled")

		return issues

	def check_file_permissions(self) -> List[str]:
		"""Check file permissions for security."""
		issues = []

		sensitive_files = [".env", ".env.local", ".env.secure", "logs/", "data/"]

		for file_path in sensitive_files:
			path = Path(file_path)
			if path.exists():
				if path.is_file():
					stat = path.stat()
					permissions = oct(stat.st_mode)[-3:]
					if permissions not in ["600", "644"]:
						issues.append(f"Insecure file permissions: {file_path} ({permissions})")
				elif path.is_dir():
					stat = path.stat()
					permissions = oct(stat.st_mode)[-3:]
					if permissions not in ["700", "755"]:
						issues.append(f"Insecure directory permissions: {file_path} ({permissions})")

		return issues


# Global instances
env_manager = SecureEnvironmentManager()
api_key_manager = APIKeyManager()
env_validator = EnvironmentValidator()
