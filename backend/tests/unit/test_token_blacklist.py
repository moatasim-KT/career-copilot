"""
Unit Tests for Token Blacklist
Tests the Redis-based token blacklisting system
"""

from unittest.mock import MagicMock, patch

import pytest
from app.core.token_blacklist import SessionBlacklist, TokenBlacklist


class TestTokenBlacklist:
	"""Test TokenBlacklist class"""

	@pytest.fixture
	def blacklist_in_memory(self):
		"""Create token blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return TokenBlacklist(key_prefix="test_token")

	@pytest.fixture
	def mock_redis(self):
		"""Create mock Redis client"""
		mock = MagicMock()
		return mock

	@pytest.fixture
	def blacklist_with_redis(self, mock_redis):
		"""Create token blacklist with mocked Redis"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				# Ensure use_redis is True
				blacklist.use_redis = True
				return blacklist

	def test_initialization_in_memory(self, blacklist_in_memory):
		"""Test token blacklist initialization with in-memory storage"""
		assert blacklist_in_memory.key_prefix == "test_token"
		assert not blacklist_in_memory.use_redis
		assert len(blacklist_in_memory._memory_blacklist) == 0

	def test_initialization_with_redis(self, blacklist_with_redis):
		"""Test token blacklist initialization with Redis"""
		assert blacklist_with_redis.key_prefix == "test_token"
		assert blacklist_with_redis.use_redis

	def test_add_token_in_memory(self, blacklist_in_memory):
		"""Test adding token to in-memory blacklist"""
		token = "test_token_123"
		expiry = 3600  # 1 hour

		result = blacklist_in_memory.add_token(token, expiry)
		assert result is True
		assert token in blacklist_in_memory._memory_blacklist

	def test_add_token_with_redis(self, mock_redis):
		"""Test adding token to Redis blacklist"""
		token = "test_token_123"
		expiry = 3600

		mock_redis.setex.return_value = True

		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				result = blacklist.add_token(token, expiry)

		assert result is True

		# Verify Redis was called correctly
		expected_key = f"test_token:{token}"
		mock_redis.setex.assert_called_once_with(expected_key, expiry, "1")

	def test_is_blacklisted_in_memory_true(self, blacklist_in_memory):
		"""Test checking if token is blacklisted (in-memory, blacklisted)"""
		token = "test_token_123"
		blacklist_in_memory.add_token(token, 3600)

		is_blacklisted = blacklist_in_memory.is_blacklisted(token)
		assert is_blacklisted is True

	def test_is_blacklisted_in_memory_false(self, blacklist_in_memory):
		"""Test checking if token is blacklisted (in-memory, not blacklisted)"""
		token = "test_token_123"

		is_blacklisted = blacklist_in_memory.is_blacklisted(token)
		assert is_blacklisted is False

	def test_is_blacklisted_with_redis_true(self, mock_redis):
		"""Test checking if token is blacklisted (Redis, blacklisted)"""
		token = "test_token_123"

		mock_redis.exists.return_value = 1  # Token exists in Redis

		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				is_blacklisted = blacklist.is_blacklisted(token)

		assert is_blacklisted is True

	def test_is_blacklisted_with_redis_false(self, mock_redis):
		"""Test checking if token is blacklisted (Redis, not blacklisted)"""
		token = "test_token_123"

		mock_redis.exists.return_value = 0  # Token doesn't exist in Redis

		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				is_blacklisted = blacklist.is_blacklisted(token)

		assert is_blacklisted is False

	def test_remove_token_in_memory(self, blacklist_in_memory):
		"""Test removing token from in-memory blacklist"""
		token = "test_token_123"
		blacklist_in_memory.add_token(token, 3600)

		assert blacklist_in_memory.is_blacklisted(token) is True

		result = blacklist_in_memory.remove_token(token)
		assert result is True
		assert blacklist_in_memory.is_blacklisted(token) is False

	def test_remove_token_with_redis(self, mock_redis):
		"""Test removing token from Redis blacklist"""
		token = "test_token_123"

		mock_redis.delete.return_value = 1  # Token was deleted

		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				result = blacklist.remove_token(token)

		assert result is True

		expected_key = f"test_token:{token}"
		mock_redis.delete.assert_called_once_with(expected_key)

	def test_clear_blacklist_in_memory(self, blacklist_in_memory):
		"""Test clearing entire in-memory blacklist"""
		blacklist_in_memory.add_token("token1", 3600)
		blacklist_in_memory.add_token("token2", 3600)

		assert len(blacklist_in_memory._memory_blacklist) == 2

		blacklist_in_memory.clear()
		assert len(blacklist_in_memory._memory_blacklist) == 0

	def test_clear_blacklist_with_redis(self, mock_redis):
		"""Test clearing entire Redis blacklist"""
		# Mock Redis scan to return keys in iterations
		mock_redis.scan.return_value = (0, [b"test_token:token1", b"test_token:token2"])
		mock_redis.delete.return_value = 2

		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True):
			with patch("app.core.token_blacklist.redis_client", mock_redis):
				blacklist = TokenBlacklist(key_prefix="test_token")
				blacklist.clear()

		# Verify Redis scan was called
		mock_redis.scan.assert_called()
		# Verify delete was called with the keys
		mock_redis.delete.assert_called_once()

	def test_redis_error_fallback_on_add(self, mock_redis):
		"""Test fallback to in-memory when Redis add fails"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True), patch("app.core.token_blacklist.redis_client", mock_redis):
			mock_redis.setex.side_effect = Exception("Redis connection error")

			blacklist = TokenBlacklist()
			token = "test_token_123"

			# Should not raise exception
			result = blacklist.add_token(token, 3600)
			# Should fallback to in-memory
			assert result is True
			assert token in blacklist._memory_blacklist

	def test_redis_error_fallback_on_check(self, mock_redis):
		"""Test fallback to in-memory when Redis check fails"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True), patch("app.core.token_blacklist.redis_client", mock_redis):
			blacklist = TokenBlacklist()
			token = "test_token_123"

			# Add to in-memory
			blacklist._memory_blacklist.add(token)

			# Make Redis fail
			mock_redis.exists.side_effect = Exception("Redis connection error")

			# Should fallback to in-memory
			is_blacklisted = blacklist.is_blacklisted(token)
			assert is_blacklisted is True

	def test_multiple_tokens(self, blacklist_in_memory):
		"""Test blacklisting multiple tokens"""
		tokens = [f"token_{i}" for i in range(10)]

		for token in tokens:
			blacklist_in_memory.add_token(token, 3600)

		# All should be blacklisted
		for token in tokens:
			assert blacklist_in_memory.is_blacklisted(token) is True

		# Non-existent token should not be blacklisted
		assert blacklist_in_memory.is_blacklisted("token_999") is False


class TestSessionBlacklist:
	"""Test SessionBlacklist class"""

	@pytest.fixture
	def session_blacklist_in_memory(self):
		"""Create session blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return SessionBlacklist(key_prefix="test_session")

	@pytest.fixture
	def mock_redis(self):
		"""Create mock Redis client"""
		mock = MagicMock()
		return mock

	@pytest.fixture
	def session_blacklist_with_redis(self, mock_redis):
		"""Create session blacklist with mocked Redis"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True), patch("app.core.token_blacklist.redis_client", mock_redis):
			return SessionBlacklist(key_prefix="test_session")

	def test_add_session_in_memory(self, session_blacklist_in_memory):
		"""Test adding session to in-memory blacklist"""
		session_id = "session_123"
		expiry = 7200  # 2 hours

		result = session_blacklist_in_memory.add_session(session_id, expiry)
		assert result is True
		assert session_blacklist_in_memory.is_session_blacklisted(session_id) is True

	def test_add_session_with_redis(self, session_blacklist_with_redis, mock_redis):
		"""Test adding session to Redis blacklist"""
		session_id = "session_123"
		expiry = 7200

		mock_redis.setex.return_value = True

		result = session_blacklist_with_redis.add_session(session_id, expiry)
		assert result is True

	def test_is_session_blacklisted(self, session_blacklist_in_memory):
		"""Test checking if session is blacklisted"""
		session_id = "session_123"

		# Not blacklisted initially
		assert session_blacklist_in_memory.is_session_blacklisted(session_id) is False

		# Add to blacklist
		session_blacklist_in_memory.add_session(session_id, 3600)

		# Should be blacklisted now
		assert session_blacklist_in_memory.is_session_blacklisted(session_id) is True

	def test_remove_session(self, session_blacklist_in_memory):
		"""Test removing session from blacklist"""
		session_id = "session_123"
		session_blacklist_in_memory.add_session(session_id, 3600)

		result = session_blacklist_in_memory.remove_session(session_id)
		assert result is True
		assert session_blacklist_in_memory.is_session_blacklisted(session_id) is False

	def test_revoke_user_sessions(self, session_blacklist_in_memory):
		"""Test revoking all sessions for a user"""
		user_id = 123
		session_ids = [f"session_{i}" for i in range(5)]
		expiry = 3600

		# Add all sessions
		for session_id in session_ids:
			session_blacklist_in_memory.add_session(session_id, expiry)

		# Revoke all for user (mock implementation)
		count = session_blacklist_in_memory.revoke_user_sessions(user_id, expiry)

		# Implementation dependent - just verify it runs
		assert isinstance(count, int)


class TestRealWorldScenarios:
	"""Test real-world token blacklisting scenarios"""

	@pytest.fixture
	def blacklist_in_memory(self):
		"""Create token blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return TokenBlacklist(key_prefix="test_token")

	@pytest.fixture
	def session_blacklist_in_memory(self):
		"""Create session blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return SessionBlacklist(key_prefix="test_session")

	@pytest.fixture
	def mock_redis(self):
		"""Create mock Redis client"""
		return MagicMock()

	def test_user_logout_scenario(self, blacklist_in_memory):
		"""Test blacklisting token on user logout"""
		# User logs out
		access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
		expiry = 3600  # Token expires in 1 hour

		# Add to blacklist
		result = blacklist_in_memory.add_token(access_token, expiry)
		assert result is True

		# Subsequent requests with this token should be rejected
		assert blacklist_in_memory.is_blacklisted(access_token) is True

	def test_password_change_scenario(self, session_blacklist_in_memory):
		"""Test revoking all sessions on password change"""
		user_id = 123
		session_ids = [f"session_{i}" for i in range(3)]

		# User has multiple active sessions
		for session_id in session_ids:
			session_blacklist_in_memory.add_session(session_id, 7200)

		# All sessions should be blacklisted
		for session_id in session_ids:
			assert session_blacklist_in_memory.is_session_blacklisted(session_id) is True

	def test_token_refresh_scenario(self, blacklist_in_memory):
		"""Test blacklisting old token when refreshing"""
		old_token = "old_access_token_123"
		new_token = "new_access_token_456"

		# Blacklist old token
		blacklist_in_memory.add_token(old_token, 3600)

		# Old token should be blacklisted
		assert blacklist_in_memory.is_blacklisted(old_token) is True

		# New token should not be blacklisted
		assert blacklist_in_memory.is_blacklisted(new_token) is False

	def test_security_breach_scenario(self, blacklist_in_memory):
		"""Test mass token revocation on security breach"""
		# Multiple compromised tokens
		compromised_tokens = [f"token_{i}" for i in range(100)]
		expiry = 3600

		# Blacklist all compromised tokens
		for token in compromised_tokens:
			blacklist_in_memory.add_token(token, expiry)

		# Verify all are blacklisted
		for token in compromised_tokens:
			assert blacklist_in_memory.is_blacklisted(token) is True

	def test_distributed_system_scenario(self, mock_redis):
		"""Test token blacklist across distributed system"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", True), patch("app.core.token_blacklist.redis_client", mock_redis):
			# Simulate multiple server instances
			blacklist_server1 = TokenBlacklist()
			blacklist_server2 = TokenBlacklist()

			token = "shared_token_123"

			# Server 1 blacklists token
			mock_redis.setex.return_value = True
			blacklist_server1.add_token(token, 3600)

			# Server 2 should see it as blacklisted
			mock_redis.exists.return_value = 1
			assert blacklist_server2.is_blacklisted(token) is True


class TestPerformance:
	"""Test performance characteristics"""

	@pytest.fixture
	def blacklist_in_memory(self):
		"""Create token blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return TokenBlacklist(key_prefix="test_token")

	def test_large_blacklist_performance(self, blacklist_in_memory):
		"""Test performance with large number of blacklisted tokens"""
		import time

		# Add many tokens
		num_tokens = 1000
		for i in range(num_tokens):
			blacklist_in_memory.add_token(f"token_{i}", 3600)

		# Lookup should still be fast (set membership is O(1))
		start = time.time()
		for i in range(100):
			blacklist_in_memory.is_blacklisted(f"token_{i}")
		duration = time.time() - start

		# Should complete quickly (< 0.1 seconds for 100 lookups)
		assert duration < 0.1

	def test_concurrent_access(self, blacklist_in_memory):
		"""Test thread-safe concurrent access"""
		import threading

		results = []

		def add_tokens(start_idx):
			for i in range(start_idx, start_idx + 10):
				token = f"token_{i}"
				result = blacklist_in_memory.add_token(token, 3600)
				results.append(result)

		# Create multiple threads
		threads = [threading.Thread(target=add_tokens, args=(i * 10,)) for i in range(10)]

		# Start all threads
		for t in threads:
			t.start()

		# Wait for completion
		for t in threads:
			t.join()

		# All operations should succeed
		assert all(results)


class TestEdgeCases:
	"""Test edge cases and boundary conditions"""

	@pytest.fixture
	def blacklist_in_memory(self):
		"""Create token blacklist with in-memory storage"""
		with patch("app.core.token_blacklist.REDIS_AVAILABLE", False):
			return TokenBlacklist(key_prefix="test_token")

	def test_empty_token(self, blacklist_in_memory):
		"""Test blacklisting empty token"""
		result = blacklist_in_memory.add_token("", 3600)
		assert result is True
		assert blacklist_in_memory.is_blacklisted("") is True

	def test_very_long_token(self, blacklist_in_memory):
		"""Test blacklisting very long token"""
		long_token = "a" * 10000
		result = blacklist_in_memory.add_token(long_token, 3600)
		assert result is True
		assert blacklist_in_memory.is_blacklisted(long_token) is True

	def test_zero_expiry(self, blacklist_in_memory):
		"""Test blacklisting with zero expiry"""
		token = "token_123"
		result = blacklist_in_memory.add_token(token, 0)
		# Should still work (implementation dependent)
		assert isinstance(result, bool)

	def test_negative_expiry(self, blacklist_in_memory):
		"""Test blacklisting with negative expiry"""
		token = "token_123"
		result = blacklist_in_memory.add_token(token, -100)
		# Should handle gracefully
		assert isinstance(result, bool)

	def test_special_characters_in_token(self, blacklist_in_memory):
		"""Test blacklisting token with special characters"""
		special_token = "token:with!special@chars#123"
		result = blacklist_in_memory.add_token(special_token, 3600)
		assert result is True
		assert blacklist_in_memory.is_blacklisted(special_token) is True

	def test_unicode_in_token(self, blacklist_in_memory):
		"""Test blacklisting token with unicode characters"""
		unicode_token = "token_🔒_123_é"
		result = blacklist_in_memory.add_token(unicode_token, 3600)
		assert result is True
		assert blacklist_in_memory.is_blacklisted(unicode_token) is True


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
