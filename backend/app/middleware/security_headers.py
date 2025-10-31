"""
Security Headers Middleware
Adds security headers to all responses
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
	"""Add security headers to all responses"""

	async def dispatch(self, request: Request, call_next):
		response = await call_next(request)

		# Prevent clickjacking
		response.headers["X-Frame-Options"] = "DENY"

		# Prevent MIME sniffing
		response.headers["X-Content-Type-Options"] = "nosniff"

		# Enable XSS protection
		response.headers["X-XSS-Protection"] = "1; mode=block"

		# Strict Transport Security (HTTPS only)
		response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

		# Content Security Policy
		response.headers["Content-Security-Policy"] = (
			"default-src 'self'; "
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
			"style-src 'self' 'unsafe-inline'; "
			"img-src 'self' data: https:; "
			"font-src 'self' data:; "
			"connect-src 'self'; "
			"frame-ancestors 'none';"
		)

		# Referrer Policy
		response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

		# Permissions Policy
		response.headers["Permissions-Policy"] = (
			"geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
		)

		return response
