"""
Token and Session Blacklist Management
Supports Redis-backed storage with in-memory fallback
"""

import time
from typing import Optional, Set

from ..core.logging import get_logger

logger = get_logger(__name__)

# Check Redis availability
try:
	from ..utils.redis_client import redis_client

	REDIS_AVAILABLE = redis_client is not None
except Exception as e:
	logger.warning(f"Redis not available for token blacklist: {e}")
	REDIS_AVAILABLE = False
	redis_client = None


class TokenBlacklist:
	"""
	Token blacklist with Redis backend and in-memory fallback.
	Manages JWT token revocation for logout and security purposes.
	"""

	def __init__(self, key_prefix: str = "token_blacklist"):
		"""
		Initialize token blacklist.

		Args:
			key_prefix: Prefix for Redis keys
		"""
		self.key_prefix = key_prefix
		self.use_redis = REDIS_AVAILABLE and redis_client is not None
		self._memory_blacklist: Set[str] = set()

		if not self.use_redis:
			logger.warning("Using in-memory token blacklist (not recommended for production)")

	def add_token(self, token: str, expiry: int) -> bool:
		"""
		Add a token to the blacklist.

		Args:
			token: Token to blacklist
			expiry: Expiry time in seconds

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{token}"
				redis_client.setex(key, expiry, "1")
				return True
			except Exception as e:
				logger.error(f"Redis add_token failed: {e}, falling back to in-memory")
				self._memory_blacklist.add(token)
				return True
		else:
			self._memory_blacklist.add(token)
			return True

	def is_blacklisted(self, token: str) -> bool:
		"""
		Check if a token is blacklisted.

		Args:
			token: Token to check

		Returns:
			True if blacklisted
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{token}"
				return redis_client.exists(key) > 0
			except Exception as e:
				logger.error(f"Redis is_blacklisted failed: {e}, falling back to in-memory")
				return token in self._memory_blacklist
		else:
			return token in self._memory_blacklist

	def remove_token(self, token: str) -> bool:
		"""
		Remove a token from the blacklist.

		Args:
			token: Token to remove

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{token}"
				redis_client.delete(key)
				return True
			except Exception as e:
				logger.error(f"Redis remove_token failed: {e}, falling back to in-memory")
				self._memory_blacklist.discard(token)
				return True
		else:
			self._memory_blacklist.discard(token)
			return True

	def clear(self) -> bool:
		"""
		Clear all tokens from the blacklist.

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				cursor = 0
				pattern = f"{self.key_prefix}:*"
				while True:
					cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
					if keys:
						redis_client.delete(*keys)
					if cursor == 0:
						break
				return True
			except Exception as e:
				logger.error(f"Redis clear failed: {e}, clearing in-memory")
				self._memory_blacklist.clear()
				return True
		else:
			self._memory_blacklist.clear()
			return True

	def cleanup(self) -> int:
		"""
		Clean up expired tokens (for in-memory storage).
		Redis handles expiry automatically.

		Returns:
			Number of tokens cleaned up
		"""
		# In-memory cleanup is not implemented as we don't track expiry times
		# Redis handles this automatically with TTL
		return 0


class SessionBlacklist:
	"""
	Session blacklist with Redis backend and in-memory fallback.
	Manages session revocation for multi-device logout.
	"""

	def __init__(self, key_prefix: str = "session_blacklist"):
		"""
		Initialize session blacklist.

		Args:
			key_prefix: Prefix for Redis keys
		"""
		self.key_prefix = key_prefix
		self.use_redis = REDIS_AVAILABLE and redis_client is not None
		self._memory_blacklist: Set[str] = set()

		if not self.use_redis:
			logger.warning("Using in-memory session blacklist (not recommended for production)")

	def add_session(self, session_id: str, expiry: int) -> bool:
		"""
		Add a session to the blacklist.

		Args:
			session_id: Session ID to blacklist
			expiry: Expiry time in seconds

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{session_id}"
				redis_client.setex(key, expiry, "1")
				return True
			except Exception as e:
				logger.error(f"Redis add_session failed: {e}, falling back to in-memory")
				self._memory_blacklist.add(session_id)
				return True
		else:
			self._memory_blacklist.add(session_id)
			return True

	def is_blacklisted(self, session_id: str) -> bool:
		"""
		Check if a session is blacklisted.

		Args:
			session_id: Session ID to check

		Returns:
			True if blacklisted
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{session_id}"
				return redis_client.exists(key) > 0
			except Exception as e:
				logger.error(f"Redis is_blacklisted failed: {e}, falling back to in-memory")
				return session_id in self._memory_blacklist
		else:
			return session_id in self._memory_blacklist

	def is_session_blacklisted(self, session_id: str) -> bool:
		"""
		Alias for is_blacklisted for backward compatibility.

		Args:
			session_id: Session ID to check

		Returns:
			True if blacklisted
		"""
		return self.is_blacklisted(session_id)

	def remove_session(self, session_id: str) -> bool:
		"""
		Remove a session from the blacklist.

		Args:
			session_id: Session ID to remove

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				key = f"{self.key_prefix}:{session_id}"
				redis_client.delete(key)
				return True
			except Exception as e:
				logger.error(f"Redis remove_session failed: {e}, falling back to in-memory")
				self._memory_blacklist.discard(session_id)
				return True
		else:
			self._memory_blacklist.discard(session_id)
			return True

	def clear(self) -> bool:
		"""
		Clear all sessions from the blacklist.

		Returns:
			True if successful
		"""
		if self.use_redis:
			try:
				cursor = 0
				pattern = f"{self.key_prefix}:*"
				while True:
					cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
					if keys:
						redis_client.delete(*keys)
					if cursor == 0:
						break
				return True
			except Exception as e:
				logger.error(f"Redis clear failed: {e}, clearing in-memory")
				self._memory_blacklist.clear()
				return True
		else:
			self._memory_blacklist.clear()
			return True

	def cleanup(self) -> int:
		"""
		Clean up expired sessions (for in-memory storage).
		Redis handles expiry automatically.

		Returns:
			Number of sessions cleaned up
		"""
		# In-memory cleanup is not implemented as we don't track expiry times
		# Redis handles this automatically with TTL
		return 0

	def revoke_user_sessions(self, user_id: int, expiry: int) -> int:
		"""
		Revoke all sessions for a user.

		Note: This is a simplified implementation that returns 0.
		In a real implementation, you would need to track user_id -> session_id mapping.

		Args:
			user_id: User ID whose sessions to revoke
			expiry: Expiry time for the revocation record

		Returns:
			Number of sessions revoked
		"""
		# This would require additional data structure to map users to sessions
		# For now, return 0 as a stub implementation
		logger.info(f"Revoke user sessions called for user {user_id} (stub implementation)")
		return 0


# Global instances
token_blacklist = TokenBlacklist()
session_blacklist = SessionBlacklist()
