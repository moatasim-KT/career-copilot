"""
Input Validation and Security Middleware for Career Copilot.
Implements comprehensive input sanitization and validation.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class InputSanitizer:
    """Input sanitization utilities."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
        r"(\b(EXEC|EXECUTE)\s*\()",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]\\]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|wget|curl|nc|telnet|ssh|ftp)\b",
        r"(\.\.\/|\.\.\\)",
        r"(/etc/passwd|/etc/shadow|/proc/)",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\.\/|\.\.\\)",
        r"(%2e%2e%2f|%2e%2e%5c)",
        r"(\/etc\/|\\windows\\|\\system32\\)",
    ]
    
    def __init__(self):
        self.settings = get_settings()
        self.max_input_length = self.settings.max_input_length
        self.strict_validation = self.settings.strict_validation
    
    def sanitize_string(self, value: str) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: Input string to sanitize
            
        Returns:
            Sanitized string
            
        Raises:
            ValueError: If malicious content is detected
        """
        if not isinstance(value, str):
            return str(value)
        
        # Check length
        if len(value) > self.max_input_length:
            raise ValueError(f"Input too long: {len(value)} > {self.max_input_length}")
        
        # URL decode
        decoded_value = unquote(value)
        
        # Check for malicious patterns
        self._check_sql_injection(decoded_value)
        self._check_xss(decoded_value)
        self._check_command_injection(decoded_value)
        self._check_path_traversal(decoded_value)
        
        # Basic sanitization
        sanitized = decoded_value.strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized
    
    def _check_sql_injection(self, value: str):
        """Check for SQL injection patterns."""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potential SQL injection detected: {pattern}")
    
    def _check_xss(self, value: str):
        """Check for XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potential XSS detected: {pattern}")
    
    def _check_command_injection(self, value: str):
        """Check for command injection patterns."""
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potential command injection detected: {pattern}")
    
    def _check_path_traversal(self, value: str):
        """Check for path traversal patterns."""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"Potential path traversal detected: {pattern}")
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary data.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            sanitized_key = self.sanitize_string(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[sanitized_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[sanitized_key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[sanitized_key] = self.sanitize_list(value)
            else:
                sanitized[sanitized_key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Sanitize list data.
        
        Args:
            data: List to sanitize
            
        Returns:
            Sanitized list
        """
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive input validation and sanitization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.sanitizer = InputSanitizer()
        self.settings = get_settings()
        
        # Paths that skip validation (for performance)
        self.skip_validation_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through input validation."""
        
        # Skip validation for certain paths
        if request.url.path in self.skip_validation_paths:
            return await call_next(request)
        
        try:
            # Validate and sanitize query parameters
            await self._validate_query_params(request)
            
            # Validate and sanitize request body for POST/PUT/PATCH
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request)
            
            # Validate headers
            await self._validate_headers(request)
            
            # Continue to next middleware
            return await call_next(request)
            
        except ValueError as e:
            # Log security violation
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                action=f"Input validation failed: {str(e)}",
                severity=AuditSeverity.HIGH,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected"
            )
        
        except Exception as e:
            logger.error(f"Error in input validation middleware: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Input validation error"
            )
    
    async def _validate_query_params(self, request: Request):
        """Validate query parameters."""
        if not request.query_params:
            return
        
        for key, value in request.query_params.items():
            try:
                self.sanitizer.sanitize_string(key)
                self.sanitizer.sanitize_string(value)
            except ValueError as e:
                raise ValueError(f"Invalid query parameter '{key}': {e}")
    
    async def _validate_request_body(self, request: Request):
        """Validate request body."""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            await self._validate_json_body(request)
        elif "application/x-www-form-urlencoded" in content_type:
            await self._validate_form_body(request)
        elif "multipart/form-data" in content_type:
            await self._validate_multipart_body(request)
    
    async def _validate_json_body(self, request: Request):
        """Validate JSON request body."""
        try:
            # Get raw body
            body = await request.body()
            
            if not body:
                return
            
            # Check size
            if len(body) > self.settings.max_file_size_bytes:
                raise ValueError("Request body too large")
            
            # Parse JSON
            try:
                data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format")
            
            # Sanitize JSON data
            if isinstance(data, dict):
                self.sanitizer.sanitize_dict(data)
            elif isinstance(data, list):
                self.sanitizer.sanitize_list(data)
            elif isinstance(data, str):
                self.sanitizer.sanitize_string(data)
            
        except UnicodeDecodeError:
            raise ValueError("Invalid character encoding")
    
    async def _validate_form_body(self, request: Request):
        """Validate form-encoded request body."""
        try:
            form_data = await request.form()
            
            for key, value in form_data.items():
                if isinstance(value, str):
                    self.sanitizer.sanitize_string(key)
                    self.sanitizer.sanitize_string(value)
                    
        except Exception as e:
            raise ValueError(f"Invalid form data: {e}")
    
    async def _validate_multipart_body(self, request: Request):
        """Validate multipart form data."""
        try:
            form_data = await request.form()
            
            for key, value in form_data.items():
                # Validate field name
                self.sanitizer.sanitize_string(key)
                
                # Validate field value (if string)
                if isinstance(value, str):
                    self.sanitizer.sanitize_string(value)
                # File uploads are handled separately by file upload middleware
                    
        except Exception as e:
            raise ValueError(f"Invalid multipart data: {e}")
    
    async def _validate_headers(self, request: Request):
        """Validate request headers."""
        dangerous_headers = [
            "x-forwarded-host",
            "x-rewrite-url", 
            "x-original-url"
        ]
        
        for header_name in dangerous_headers:
            if header_name in request.headers:
                audit_logger.log_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    action=f"Dangerous header detected: {header_name}",
                    severity=AuditSeverity.MEDIUM,
                    ip_address=self._get_client_ip(request),
                    details={"header": header_name, "value": request.headers[header_name]}
                )
        
        # Validate User-Agent length
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 1000:
            raise ValueError("User-Agent header too long")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


# Global sanitizer instance
_input_sanitizer: Optional[InputSanitizer] = None


def get_input_sanitizer() -> InputSanitizer:
    """Get the input sanitizer instance."""
    global _input_sanitizer
    if _input_sanitizer is None:
        _input_sanitizer = InputSanitizer()
    return _input_sanitizer