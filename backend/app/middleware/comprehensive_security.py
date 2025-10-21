"""
Comprehensive security middleware that integrates all security measures.
"""

import time
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.audit import AuditEventType, AuditSeverity, audit_logger
from ..core.logging import get_logger
from ..core.security import SecurityMiddleware
from ..utils.sanitization import RequestSanitizer

logger = get_logger(__name__)


class ComprehensiveSecurityMiddleware(BaseHTTPMiddleware):
	"""
	Comprehensive security middleware that applies all security measures
	to incoming requests.
	"""

	def __init__(self, app):
		super().__init__(app)
		self.security_middleware = SecurityMiddleware(app)
		self.request_sanitizer = RequestSanitizer()

		# Security headers to add to all responses
		self.security_headers = {
			"X-Content-Type-Options": "nosniff",
			"X-Frame-Options": "DENY",
			"X-XSS-Protection": "1; mode=block",
			"Referrer-Policy": "strict-origin-when-cross-origin",
			"Content-Security-Policy": (
				"default-src 'self'; "
				"script-src 'self' 'unsafe-inline'; "
				"style-src 'self' 'unsafe-inline'; "
				"img-src 'self' data: https:; "
				"font-src 'self'; "
				"connect-src 'self'; "
				"frame-ancestors 'none';"
			),
			"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
			"Permissions-Policy": ("geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()"),
		}

		# Paths that don't require API key authentication
		self.public_paths = {"/health", "/docs", "/openapi.json", "/redoc"}

		# Paths that require special handling
		self.sensitive_paths = {"/security", "/admin", "/api/admin"}

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		"""Process request through comprehensive security checks."""
		start_time = time.time()

		try:
			# Add request ID for tracking
			request_id = self._generate_request_id()
			request.state.request_id = request_id

			# Perform security validation
			await self._validate_request_security(request)

			# Sanitize request data
			await self._sanitize_request(request)

			# Process the request
			response = await call_next(request)

			# Add security headers to response
			self._add_security_headers(response)

			# Log successful request
			duration = time.time() - start_time
			self._log_request(request, response, duration)

			return response

		except HTTPException as e:
			# Handle security-related HTTP exceptions
			duration = time.time() - start_time

			# Log security violation
			audit_logger.log_event(
				event_type=AuditEventType.SECURITY_VIOLATION,
				action=f"Request blocked: {e.detail}",
				severity=AuditSeverity.HIGH,
				ip_address=self._get_client_ip(request),
				user_agent=request.headers.get("user-agent"),
				details={"status_code": e.status_code, "path": str(request.url.path), "method": request.method, "duration_ms": duration * 1000},
			)

			# Return security error response
			return JSONResponse(
				status_code=e.status_code,
				content={"error": e.detail, "request_id": getattr(request.state, "request_id", None)},
				headers=self.security_headers,
			)

		except Exception as e:
			# Handle unexpected errors
			duration = time.time() - start_time

			logger.error(f"Unexpected error in security middleware: {e}")

			# Log error
			audit_logger.log_event(
				event_type=AuditEventType.ERROR_OCCURRED,
				action=f"Security middleware error: {e!s}",
				severity=AuditSeverity.HIGH,
				ip_address=self._get_client_ip(request),
				details={"error": str(e), "path": str(request.url.path), "method": request.method, "duration_ms": duration * 1000},
			)

			# Return generic error response
			return JSONResponse(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				content={"error": "Internal server error", "request_id": getattr(request.state, "request_id", None)},
				headers=self.security_headers,
			)

	async def _validate_request_security(self, request: Request) -> None:
		"""Perform comprehensive security validation on the request."""

		# Check if path requires authentication
		path = request.url.path
		requires_auth = path not in self.public_paths

		# Enhanced validation for sensitive paths
		if any(sensitive in path for sensitive in self.sensitive_paths):
			requires_auth = True

			# Additional checks for admin paths
			if "/admin" in path:
				await self._validate_admin_access(request)

		# Perform security middleware validation
		if requires_auth:
			key_info = self.security_middleware.validate_request(request)
			if key_info:
				request.state.api_key_info = key_info
				request.state.user_id = key_info.get("name", "unknown")

		# Additional security checks
		await self._check_request_size(request)
		await self._check_content_type(request)
		await self._validate_headers(request)

	async def _validate_admin_access(self, request: Request) -> None:
		"""Validate access to admin endpoints."""
		# This would implement additional admin-specific security checks
		# For now, we'll just ensure API key has admin scope

		api_key = self._extract_api_key(request)
		if not api_key:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access requires API key")

		key_info = self.security_middleware.api_key_manager.validate_api_key(api_key)
		if not key_info or "admin" not in key_info.get("scopes", []):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access denied")

	async def _check_request_size(self, request: Request) -> None:
		"""Check request size limits."""
		content_length = request.headers.get("content-length")
		if content_length:
			try:
				size = int(content_length)
				max_size = 100 * 1024 * 1024  # 100MB

				if size > max_size:
					raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request too large")
			except ValueError:
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content-length header")

	async def _check_content_type(self, request: Request) -> None:
		"""Validate content type for requests with body."""
		if request.method in ["POST", "PUT", "PATCH"]:
			content_type = request.headers.get("content-type", "")

			# Allow common content types
			allowed_types = ["application/json", "application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]

			if content_type and not any(allowed in content_type for allowed in allowed_types):
				# Log suspicious content type
				audit_logger.log_event(
					event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
					action=f"Unusual content type: {content_type}",
					severity=AuditSeverity.MEDIUM,
					ip_address=self._get_client_ip(request),
					details={"content_type": content_type},
				)

	async def _validate_headers(self, request: Request) -> None:
		"""Validate request headers for security issues."""

		# Check for suspicious headers
		suspicious_headers = ["x-forwarded-host", "x-forwarded-proto", "x-rewrite-url", "x-original-url"]

		for header in suspicious_headers:
			if header in request.headers:
				audit_logger.log_event(
					event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
					action=f"Suspicious header detected: {header}",
					severity=AuditSeverity.MEDIUM,
					ip_address=self._get_client_ip(request),
					details={"header": header, "value": request.headers[header]},
				)

		# Validate User-Agent
		user_agent = request.headers.get("user-agent", "")
		if not user_agent:
			audit_logger.log_event(
				event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
				action="Missing User-Agent header",
				severity=AuditSeverity.LOW,
				ip_address=self._get_client_ip(request),
			)
		elif len(user_agent) > 1000:  # Unusually long user agent
			audit_logger.log_event(
				event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
				action="Unusually long User-Agent header",
				severity=AuditSeverity.MEDIUM,
				ip_address=self._get_client_ip(request),
				details={"user_agent_length": len(user_agent)},
			)

	async def _sanitize_request(self, request: Request) -> None:
		"""Sanitize request data."""

		# Sanitize query parameters
		if request.query_params:
			try:
				sanitized_params = self.request_sanitizer.sanitize_query_params(dict(request.query_params))
				# Note: FastAPI query_params is immutable, so we can't modify it
				# In a real implementation, you might need to modify the request object

			except ValueError as e:
				# Malicious query parameters detected
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query parameters")

	def _add_security_headers(self, response: Response) -> None:
		"""Add security headers to response."""
		for header, value in self.security_headers.items():
			response.headers[header] = value

		# Add additional headers based on response type
		if hasattr(response, "media_type"):
			if response.media_type == "application/json":
				response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
				response.headers["Pragma"] = "no-cache"

	def _log_request(self, request: Request, response: Response, duration: float) -> None:
		"""Log request details for monitoring."""

		# Log to audit system for certain paths or status codes
		if response.status_code >= 400 or any(sensitive in request.url.path for sensitive in self.sensitive_paths):
			severity = AuditSeverity.HIGH if response.status_code >= 500 else AuditSeverity.MEDIUM

			audit_logger.log_event(
				event_type=AuditEventType.FILE_ACCESS if "file" in request.url.path else AuditEventType.UNAUTHORIZED_ACCESS,
				action=f"{request.method} {request.url.path}",
				severity=severity,
				ip_address=self._get_client_ip(request),
				user_agent=request.headers.get("user-agent"),
				details={"status_code": response.status_code, "duration_ms": duration * 1000, "user_id": getattr(request.state, "user_id", None)},
			)

	def _get_client_ip(self, request: Request) -> str:
		"""Extract client IP address."""
		# Check for forwarded headers
		forwarded_for = request.headers.get("x-forwarded-for")
		if forwarded_for:
			return forwarded_for.split(",")[0].strip()

		real_ip = request.headers.get("x-real-ip")
		if real_ip:
			return real_ip

		return request.client.host if request.client else "unknown"

	def _extract_api_key(self, request: Request) -> Optional[str]:
		"""Extract API key from request."""
		# Check Authorization header
		auth_header = request.headers.get("authorization")
		if auth_header and auth_header.startswith("Bearer "):
			return auth_header[7:]

		# Check custom API key header
		return request.headers.get("x-api-key")

	def _generate_request_id(self) -> str:
		"""Generate unique request ID."""
		import secrets

		return secrets.token_urlsafe(16)



