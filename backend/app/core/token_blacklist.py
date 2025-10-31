"""
Redis-Based Token Blacklist Service
Provides distributed token blacklisting with TTL support
"""

from typing import Set

try:
	from app.utils.redis_client import redis_client

	REDIS_AVAILABLE = True
except ImportError:
	REDIS_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)


class TokenBlacklist:
	"""
	Distributed token blacklist using Redis.
	Falls back to in-memory storage if Redis is unavailable.
	"""

	def __init__(self, key_prefix: str = "token_blacklist"):
		"""
		Initialize token blacklist.

		Args:
		    key_prefix: Prefix for Redis keys
		"""
		self.key_prefix = key_prefix
		self.use_redis = REDIS_AVAILABLE and redis_client is not None

		# Fallback in-memory storage
		self._memory_blacklist: Set[str] = set()

		if not self.use_redis:
			logger.warning("Redis not available, using in-memory token blacklist (not suitable for production)")

	def _get_key(self, token: str) -> str:
		"""Get Redis key for token."""
		return f"{self.key_prefix}:{token}"

	def add_token(self, token: str, expiry_seconds: int) -> bool:
		"""
		Add token to blacklist with expiry.

		Args:
		    token: JWT token to blacklist
		    expiry_seconds: Time until token expires (used for TTL)

		Returns:
		    True if successfully added
		"""
		if self.use_redis:
			try:
				key = self._get_key(token)
				# Set with expiry - token will auto-remove when it expires anyway
				redis_client.setex(key, expiry_seconds, "1")
				logger.info(f"Token blacklisted in Redis (expires in {expiry_seconds}s)")
				return True
			except Exception as e:
				logger.error(f"Failed to blacklist token in Redis: {e}")
				# Fall back to memory
				self._memory_blacklist.add(token)
				return True
		else:
			# In-memory fallback
			self._memory_blacklist.add(token)
			logger.debug(f"Token blacklisted in memory")
			return True

	def is_blacklisted(self, token: str) -> bool:
		"""
		Check if token is blacklisted.

		Args:
		    token: JWT token to check

		Returns:
		    True if token is blacklisted
		"""
		if self.use_redis:
			try:
				key = self._get_key(token)
				exists = redis_client.exists(key)
				return bool(exists)
			except Exception as e:
				logger.error(f"Failed to check token blacklist in Redis: {e}")
				# Fall back to memory
				return token in self._memory_blacklist
		else:
			# In-memory fallback
			return token in self._memory_blacklist

	def remove_token(self, token: str) -> bool:
		"""
		Remove token from blacklist (rarely needed - tokens auto-expire).

		Args:
		    token: JWT token to remove

		Returns:
		    True if successfully removed
		"""
		if self.use_redis:
			try:
				key = self._get_key(token)
				deleted = redis_client.delete(key)
				return bool(deleted)
			except Exception as e:
				logger.error(f"Failed to remove token from Redis blacklist: {e}")
				# Fall back to memory
				self._memory_blacklist.discard(token)
				return True
		else:
			# In-memory fallback
			self._memory_blacklist.discard(token)
			return True

	def clear_all(self) -> bool:
		"""
		Clear all blacklisted tokens.
		WARNING: Use with caution in production!

		Returns:
		    True if successfully cleared
		"""
		if self.use_redis:
			try:
				# Find all blacklist keys
				pattern = f"{self.key_prefix}:*"
				cursor = 0
				deleted_count = 0

				while True:
					cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
					if keys:
						deleted = redis_client.delete(*keys)
						deleted_count += deleted

					if cursor == 0:
						break

				logger.info(f"Cleared {deleted_count} tokens from Redis blacklist")
				return True
			except Exception as e:
				logger.error(f"Failed to clear Redis blacklist: {e}")
				self._memory_blacklist.clear()
				return False
		else:
			# In-memory fallback
			self._memory_blacklist.clear()
			return True

	def get_count(self) -> int:
		"""
		Get count of blacklisted tokens.

		Returns:
		    Number of blacklisted tokens
		"""
		if self.use_redis:
			try:
				pattern = f"{self.key_prefix}:*"
				cursor = 0
				count = 0

				while True:
					cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
					count += len(keys)

					if cursor == 0:
						break

				return count
			except Exception as e:
				logger.error(f"Failed to count blacklisted tokens in Redis: {e}")
				return len(self._memory_blacklist)
		else:
			# In-memory fallback
			return len(self._memory_blacklist)

	def clear(self) -> bool:
		"""
		Alias for clear_all() for backward compatibility.

		Returns:
		    True if successfully cleared
		"""
		return self.clear_all()


class SessionBlacklist:
	"""
	Distributed session blacklist using Redis.
	Separate from token blacklist to handle session revocation.
	"""

	def __init__(self, key_prefix: str = "session_blacklist"):
		"""
		Initialize session blacklist.

		Args:
		    key_prefix: Prefix for Redis keys
		"""
		self.key_prefix = key_prefix
		self.use_redis = REDIS_AVAILABLE and redis_client is not None

		# Fallback in-memory storage
		self._memory_blacklist: Set[str] = set()

		if not self.use_redis:
			logger.warning("Redis not available, using in-memory session blacklist")

	def _get_key(self, session_id: str) -> str:
		"""Get Redis key for session."""
		return f"{self.key_prefix}:{session_id}"

	def add_session(self, session_id: str, expiry_seconds: int = 86400) -> bool:
		"""
		Add session to blacklist.

		Args:
		    session_id: Session ID to blacklist
		    expiry_seconds: Time until entry expires (default 24 hours)

		Returns:
		    True if successfully added
		"""
		if self.use_redis:
			try:
				key = self._get_key(session_id)
				redis_client.setex(key, expiry_seconds, "1")
				logger.info(f"Session {session_id} blacklisted")
				return True
			except Exception as e:
				logger.error(f"Failed to blacklist session in Redis: {e}")
				self._memory_blacklist.add(session_id)
				return True
		else:
			self._memory_blacklist.add(session_id)
			return True

	def is_blacklisted(self, session_id: str) -> bool:
		"""
		Check if session is blacklisted.

		Args:
		    session_id: Session ID to check

		Returns:
		    True if session is blacklisted
		"""
		if self.use_redis:
			try:
				key = self._get_key(session_id)
				exists = redis_client.exists(key)
				return bool(exists)
			except Exception as e:
				logger.error(f"Failed to check session blacklist in Redis: {e}")
				return session_id in self._memory_blacklist
		else:
			return session_id in self._memory_blacklist

	def remove_session(self, session_id: str) -> bool:
		"""
		Remove session from blacklist.

		Args:
		    session_id: Session ID to remove

		Returns:
		    True if successfully removed
		"""
		if self.use_redis:
			try:
				key = self._get_key(session_id)
				deleted = redis_client.delete(key)
				return bool(deleted)
			except Exception as e:
				logger.error(f"Failed to remove session from Redis blacklist: {e}")
				self._memory_blacklist.discard(session_id)
				return True
		else:
			self._memory_blacklist.discard(session_id)
			return True

	def is_session_blacklisted(self, session_id: str) -> bool:
		"""
		Alias for is_blacklisted() for backward compatibility.

		Args:
		    session_id: Session ID to check

		Returns:
		    True if session is blacklisted
		"""
		return self.is_blacklisted(session_id)

	def revoke_user_sessions(self, user_id: int, expiry_seconds: int = 86400) -> int:
		"""
		Revoke all sessions for a user.
		Note: This is a placeholder implementation. In production, you would
		need to track user-to-session mappings.

		Args:
		    user_id: User ID whose sessions to revoke
		    expiry_seconds: Expiry time for the revocation entry

		Returns:
		    Number of sessions revoked
		"""
		# This is a simplified implementation
		# In production, you would maintain a mapping of user_id -> session_ids
		# For now, we'll just log a warning
		logger.warning(f"revoke_user_sessions called for user {user_id} - implement user-session tracking")
		return 0


# Singleton instances
token_blacklist = TokenBlacklist()
session_blacklist = SessionBlacklist()
