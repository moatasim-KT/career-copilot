"""
Rate Limiting Middleware for Authentication Endpoints
Implements sliding window rate limiting with Redis backend
"""

import time
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

try:
	from app.utils.redis_client import redis_client

	REDIS_AVAILABLE = True
except ImportError:
	REDIS_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
	"""
	Rate limiter using sliding window algorithm with Redis.
	Falls back to in-memory storage if Redis is unavailable.
	"""

	def __init__(self, requests: int = 5, window: int = 60, key_prefix: str = "rate_limit"):
		"""
		Initialize rate limiter.

		Args:
		    requests: Number of requests allowed in the window
		    window: Time window in seconds
		    key_prefix: Prefix for Redis keys
		"""
		self.requests = requests
		self.window = window
		self.key_prefix = key_prefix
		self.use_redis = REDIS_AVAILABLE and redis_client is not None

		# Fallback in-memory storage
		self._memory_store: dict = {}

		if not self.use_redis:
			logger.warning("Redis not available, using in-memory rate limiting (not recommended for production)")

	def _get_client_key(self, request: Request) -> str:
		"""Get unique client identifier from request."""
		# Try to get real IP from headers (if behind proxy)
		forwarded_for = request.headers.get("X-Forwarded-For")
		if forwarded_for:
			client_ip = forwarded_for.split(",")[0].strip()
		else:
			client_ip = request.client.host if request.client else "unknown"

		# Include endpoint in key for per-endpoint limits
		endpoint = request.url.path

		return f"{self.key_prefix}:{client_ip}:{endpoint}"

	def _check_rate_limit_redis(self, key: str) -> tuple[bool, int, int]:
		"""
		Check rate limit using Redis sliding window.

		Returns:
		    Tuple of (is_allowed, remaining_requests, retry_after_seconds)
		"""
		try:
			current_time = time.time()
			window_start = current_time - self.window

			# Remove old entries
			redis_client.zremrangebyscore(key, 0, window_start)

			# Count requests in current window
			current_requests = redis_client.zcard(key)

			if current_requests < self.requests:
				# Allow request and add to window
				redis_client.zadd(key, {str(current_time): current_time})
				redis_client.expire(key, self.window)

				remaining = self.requests - current_requests - 1
				return True, remaining, 0
			else:
				# Rate limit exceeded
				# Get oldest request in window to calculate retry after
				oldest = redis_client.zrange(key, 0, 0, withscores=True)
				if oldest:
					oldest_time = oldest[0][1]
					retry_after = int(oldest_time + self.window - current_time) + 1
				else:
					retry_after = self.window

				return False, 0, retry_after

		except Exception as e:
			logger.error(f"Redis rate limit check failed: {e}")
			# On error, allow request (fail open)
			return True, self.requests, 0

	def _check_rate_limit_memory(self, key: str) -> tuple[bool, int, int]:
		"""
		Check rate limit using in-memory storage (fallback).

		Returns:
		    Tuple of (is_allowed, remaining_requests, retry_after_seconds)
		"""
		current_time = time.time()
		window_start = current_time - self.window

		# Initialize if doesn't exist
		if key not in self._memory_store:
			self._memory_store[key] = []

		# Remove old entries
		self._memory_store[key] = [timestamp for timestamp in self._memory_store[key] if timestamp > window_start]

		current_requests = len(self._memory_store[key])

		if current_requests < self.requests:
			# Allow request
			self._memory_store[key].append(current_time)
			remaining = self.requests - current_requests - 1
			return True, remaining, 0
		else:
			# Rate limit exceeded
			oldest_time = min(self._memory_store[key])
			retry_after = int(oldest_time + self.window - current_time) + 1
			return False, 0, retry_after

	def check_rate_limit(self, request: Request) -> tuple[bool, int, int]:
		"""
		Check if request is within rate limit.

		Returns:
		    Tuple of (is_allowed, remaining_requests, retry_after_seconds)
		"""
		key = self._get_client_key(request)

		if self.use_redis:
			return self._check_rate_limit_redis(key)
		else:
			return self._check_rate_limit_memory(key)

	async def __call__(self, request: Request, call_next: Callable):
		"""Middleware callable."""
		is_allowed, remaining, retry_after = self.check_rate_limit(request)

		if not is_allowed:
			logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} on {request.url.path}")

			return JSONResponse(
				status_code=status.HTTP_429_TOO_MANY_REQUESTS,
				content={"detail": "Rate limit exceeded. Too many requests.", "retry_after": retry_after},
				headers={
					"X-RateLimit-Limit": str(self.requests),
					"X-RateLimit-Remaining": "0",
					"X-RateLimit-Reset": str(int(time.time()) + retry_after),
					"Retry-After": str(retry_after),
				},
			)

		# Add rate limit headers to response
		response = await call_next(request)
		response.headers["X-RateLimit-Limit"] = str(self.requests)
		response.headers["X-RateLimit-Remaining"] = str(remaining)
		response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window)

		return response


def rate_limit(requests: int = 5, window: int = 60, key_prefix: str = "rate_limit"):
	"""
	Decorator for rate limiting specific endpoints.

	Args:
	    requests: Number of requests allowed in the window
	    window: Time window in seconds
	    key_prefix: Prefix for rate limit keys

	Example:
	    @router.post("/login")
	    @rate_limit(requests=5, window=60)
	    async def login(credentials: LoginCredentials):
	        ...
	"""

	def decorator(func: Callable):
		@wraps(func)
		async def wrapper(*args, **kwargs):
			# Get request from kwargs
			request = kwargs.get("request")
			if not request:
				# Try to find in args
				for arg in args:
					if isinstance(arg, Request):
						request = arg
						break

			if not request:
				logger.warning("Rate limit decorator: Request object not found")
				return await func(*args, **kwargs)

			# Check rate limit
			limiter = RateLimiter(requests=requests, window=window, key_prefix=key_prefix)
			is_allowed, _remaining, retry_after = limiter.check_rate_limit(request)

			if not is_allowed:
				logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} on {request.url.path}")
				raise HTTPException(
					status_code=status.HTTP_429_TOO_MANY_REQUESTS,
					detail={"message": "Rate limit exceeded. Too many requests.", "retry_after": retry_after},
					headers={
						"X-RateLimit-Limit": str(requests),
						"X-RateLimit-Remaining": "0",
						"X-RateLimit-Reset": str(int(time.time()) + retry_after),
						"Retry-After": str(retry_after),
					},
				)

			# Call original function
			return await func(*args, **kwargs)

		return wrapper

	return decorator


# Pre-configured rate limiters for common use cases
strict_rate_limiter = RateLimiter(requests=3, window=60, key_prefix="strict")  # 3 req/min
auth_rate_limiter = RateLimiter(requests=5, window=60, key_prefix="auth")  # 5 req/min
api_rate_limiter = RateLimiter(requests=100, window=60, key_prefix="api")  # 100 req/min
