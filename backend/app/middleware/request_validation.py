"""
Request validation middleware for comprehensive input validation and security.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..models.validation_models import ValidationError


logger = logging.getLogger(__name__)

# Configuration constants
MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100MB
MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB for JSON payloads
MAX_FORM_SIZE = 50 * 1024 * 1024  # 50MB for form data
MAX_QUERY_PARAMS = 100
MAX_HEADERS = 100
MAX_HEADER_SIZE = 8192  # 8KB per header
MAX_URL_LENGTH = 2048
MAX_REQUEST_DURATION = 300  # 5 minutes

# Rate limiting (simple in-memory implementation)
REQUEST_RATE_LIMIT = 1000  # requests per minute per IP
RATE_LIMIT_WINDOW = 60  # seconds

# Security patterns to block
MALICIOUS_PATTERNS = [
    # XSS patterns
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',
    r'onload\s*=',
    r'onerror\s*=',
    r'onclick\s*=',
    
    # SQL injection patterns
    r'union\s+select',
    r'drop\s+table',
    r'delete\s+from',
    r'insert\s+into',
    r'update\s+.*\s+set',
    
    # Command injection patterns
    r';\s*rm\s+',
    r';\s*cat\s+',
    r';\s*ls\s+',
    r'`.*`',
    r'\$\(.*\)',
    
    # Path traversal
    r'\.\./',
    r'\.\.\\',
    
    # LDAP injection
    r'\(\|\(',
    r'\)\(\&',
]

# Blocked user agents
BLOCKED_USER_AGENTS = {
    'sqlmap', 'nikto', 'nmap', 'masscan', 'zap', 'burp',
    'w3af', 'skipfish', 'wfuzz', 'dirb', 'dirbuster'
}

# Allowed content types
ALLOWED_CONTENT_TYPES = {
    'application/json',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'text/plain',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request validation and security."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_store: Dict[str, Dict[str, Any]] = {}
        self.blocked_ips: Set[str] = set()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process and validate incoming requests."""
        start_time = time.time()
        
        try:
            # Basic security checks
            await self._validate_basic_security(request)
            
            # Rate limiting
            await self._check_rate_limit(request)
            
            # Request size validation
            await self._validate_request_size(request)
            
            # Content validation
            await self._validate_content(request)
            
            # URL and headers validation
            await self._validate_url_and_headers(request)
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            duration = time.time() - start_time
            if duration > 10:  # Log slow requests
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration:.2f}s from {self._get_client_ip(request)}"
                )
            
            return response
            
        except ValidationError as e:
            logger.warning(
                f"Validation error: {e.message} for {request.method} {request.url.path} "
                f"from {self._get_client_ip(request)}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "validation_error",
                    "message": e.message,
                    "field": e.field,
                    "code": e.code,
                    "timestamp": time.time()
                }
            )
            
        except HTTPException as e:
            logger.warning(
                f"HTTP error {e.status_code}: {e.detail} for {request.method} {request.url.path} "
                f"from {self._get_client_ip(request)}"
            )
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in request validation: {str(e)} "
                f"for {request.method} {request.url.path} from {self._get_client_ip(request)}",
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An internal error occurred during request validation",
                    "timestamp": time.time()
                }
            )
    
    async def _validate_basic_security(self, request: Request) -> None:
        """Perform basic security validation."""
        client_ip = self._get_client_ip(request)
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=403,
                detail="Access denied: IP address is blocked"
            )
        
        # Check user agent
        user_agent = request.headers.get('user-agent', '').lower()
        for blocked_agent in BLOCKED_USER_AGENTS:
            if blocked_agent in user_agent:
                logger.warning(f"Blocked user agent detected: {user_agent} from {client_ip}")
                self.blocked_ips.add(client_ip)
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: Blocked user agent"
                )
        
        # Check for suspicious headers
        suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'x-originating-ip']
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                if self._contains_malicious_patterns(value):
                    logger.warning(f"Malicious pattern in header {header}: {value} from {client_ip}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid header value: {header}"
                    )
    
    async def _check_rate_limit(self, request: Request) -> None:
        """Check rate limiting for the client IP."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_store(current_time)
        
        # Check current rate
        if client_ip not in self.rate_limit_store:
            self.rate_limit_store[client_ip] = {
                'requests': [],
                'blocked_until': 0
            }
        
        client_data = self.rate_limit_store[client_ip]
        
        # Check if client is temporarily blocked
        if current_time < client_data['blocked_until']:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        client_data['requests'].append(current_time)
        
        # Count requests in the current window
        window_start = current_time - RATE_LIMIT_WINDOW
        recent_requests = [
            req_time for req_time in client_data['requests']
            if req_time > window_start
        ]
        client_data['requests'] = recent_requests
        
        # Check rate limit
        if len(recent_requests) > REQUEST_RATE_LIMIT:
            # Block client for 5 minutes
            client_data['blocked_until'] = current_time + 300
            logger.warning(f"Rate limit exceeded for {client_ip}, blocking for 5 minutes")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Access blocked for 5 minutes."
            )
    
    async def _validate_request_size(self, request: Request) -> None:
        """Validate request size limits."""
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    raise ValidationError(
                        f"Request size {size} bytes exceeds maximum allowed size of {MAX_REQUEST_SIZE} bytes",
                        "content-length",
                        "REQUEST_TOO_LARGE"
                    )
            except ValueError:
                raise ValidationError(
                    "Invalid content-length header",
                    "content-length",
                    "INVALID_CONTENT_LENGTH"
                )
        
        # Check URL length
        url_length = len(str(request.url))
        if url_length > MAX_URL_LENGTH:
            raise ValidationError(
                f"URL length {url_length} exceeds maximum of {MAX_URL_LENGTH}",
                "url",
                "URL_TOO_LONG"
            )
        
        # Check number of query parameters
        if len(request.query_params) > MAX_QUERY_PARAMS:
            raise ValidationError(
                f"Too many query parameters: {len(request.query_params)} (max {MAX_QUERY_PARAMS})",
                "query_params",
                "TOO_MANY_PARAMS"
            )
        
        # Check number of headers
        if len(request.headers) > MAX_HEADERS:
            raise ValidationError(
                f"Too many headers: {len(request.headers)} (max {MAX_HEADERS})",
                "headers",
                "TOO_MANY_HEADERS"
            )
    
    async def _validate_content(self, request: Request) -> None:
        """Validate request content."""
        content_type = request.headers.get('content-type', '').split(';')[0].strip()
        
        # Skip validation for GET requests and other methods without body
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return
        
        # Check allowed content types
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            # Allow some flexibility for multipart boundaries
            if not content_type.startswith('multipart/'):
                raise ValidationError(
                    f"Content type '{content_type}' is not allowed",
                    "content-type",
                    "INVALID_CONTENT_TYPE"
                )
        
        # Validate JSON content size
        if content_type == 'application/json':
            content_length = request.headers.get('content-length')
            if content_length:
                try:
                    size = int(content_length)
                    if size > MAX_JSON_SIZE:
                        raise ValidationError(
                            f"JSON payload size {size} bytes exceeds maximum of {MAX_JSON_SIZE} bytes",
                            "json_size",
                            "JSON_TOO_LARGE"
                        )
                except ValueError:
                    pass
        
        # Validate form data size
        elif content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
            content_length = request.headers.get('content-length')
            if content_length:
                try:
                    size = int(content_length)
                    if size > MAX_FORM_SIZE:
                        raise ValidationError(
                            f"Form data size {size} bytes exceeds maximum of {MAX_FORM_SIZE} bytes",
                            "form_size",
                            "FORM_TOO_LARGE"
                        )
                except ValueError:
                    pass
    
    async def _validate_url_and_headers(self, request: Request) -> None:
        """Validate URL and headers for security issues."""
        # Validate URL path
        path = request.url.path
        if self._contains_malicious_patterns(path):
            raise ValidationError(
                "URL path contains potentially malicious content",
                "url_path",
                "MALICIOUS_URL"
            )
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if self._contains_malicious_patterns(key) or self._contains_malicious_patterns(value):
                raise ValidationError(
                    f"Query parameter contains potentially malicious content: {key}",
                    "query_params",
                    "MALICIOUS_QUERY_PARAM"
                )
        
        # Validate headers
        for name, value in request.headers.items():
            if len(value) > MAX_HEADER_SIZE:
                raise ValidationError(
                    f"Header '{name}' value exceeds maximum size of {MAX_HEADER_SIZE} bytes",
                    "headers",
                    "HEADER_TOO_LARGE"
                )
            
            if self._contains_malicious_patterns(value):
                logger.warning(f"Malicious pattern in header {name}: {value}")
                raise ValidationError(
                    f"Header '{name}' contains potentially malicious content",
                    "headers",
                    "MALICIOUS_HEADER"
                )
    
    def _contains_malicious_patterns(self, text: str) -> bool:
        """Check if text contains malicious patterns."""
        import re
        
        text_lower = text.lower()
        for pattern in MALICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            'x-forwarded-for',
            'x-real-ip',
            'x-client-ip',
            'cf-connecting-ip'  # Cloudflare
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                # Take the first IP in case of multiple
                ip = request.headers[header].split(',')[0].strip()
                if self._is_valid_ip(ip):
                    return ip
        
        # Fall back to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _cleanup_rate_limit_store(self, current_time: float) -> None:
        """Clean up old entries from rate limit store."""
        cutoff_time = current_time - RATE_LIMIT_WINDOW * 2  # Keep some history
        
        for client_ip in list(self.rate_limit_store.keys()):
            client_data = self.rate_limit_store[client_ip]
            
            # Remove old requests
            client_data['requests'] = [
                req_time for req_time in client_data['requests']
                if req_time > cutoff_time
            ]
            
            # Remove clients with no recent activity and not blocked
            if (not client_data['requests'] and 
                current_time > client_data.get('blocked_until', 0)):
                del self.rate_limit_store[client_ip]


class ContentValidationMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for validating request content."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate request content before processing."""
        
        # Skip validation for certain paths
        skip_paths = ['/health', '/metrics', '/docs', '/openapi.json']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        try:
            # Validate JSON content if present
            if request.headers.get('content-type', '').startswith('application/json'):
                await self._validate_json_content(request)
            
            return await call_next(request)
            
        except ValidationError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "content_validation_error",
                    "message": e.message,
                    "field": e.field,
                    "code": e.code,
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            logger.error(f"Error in content validation: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "content_validation_failed",
                    "message": "Failed to validate request content",
                    "timestamp": time.time()
                }
            )
    
    async def _validate_json_content(self, request: Request) -> None:
        """Validate JSON content structure and size."""
        try:
            # Read body (this consumes the stream, so we need to be careful)
            body = await request.body()
            
            if not body:
                return  # Empty body is OK for some endpoints
            
            # Check JSON size
            if len(body) > MAX_JSON_SIZE:
                raise ValidationError(
                    f"JSON payload size {len(body)} bytes exceeds maximum of {MAX_JSON_SIZE} bytes",
                    "json_content",
                    "JSON_TOO_LARGE"
                )
            
            # Parse JSON to validate structure
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Invalid JSON format: {str(e)}",
                    "json_content",
                    "INVALID_JSON"
                )
            
            # Validate JSON depth (prevent deeply nested objects)
            max_depth = 10
            if self._get_json_depth(json_data) > max_depth:
                raise ValidationError(
                    f"JSON nesting depth exceeds maximum of {max_depth}",
                    "json_content",
                    "JSON_TOO_DEEP"
                )
            
            # Check for suspicious content in JSON values
            self._validate_json_values(json_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating JSON content: {str(e)}")
            raise ValidationError(
                "Failed to validate JSON content",
                "json_content",
                "JSON_VALIDATION_FAILED"
            )
    
    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum depth of a JSON object."""
        if current_depth > 20:  # Prevent infinite recursion
            return current_depth
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(value, current_depth + 1)
                for value in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth
    
    def _validate_json_values(self, obj: Any, path: str = "") -> None:
        """Recursively validate JSON values for malicious content."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Validate key
                if isinstance(key, str) and self._contains_malicious_content(key):
                    raise ValidationError(
                        f"JSON key contains potentially malicious content: {current_path}",
                        "json_content",
                        "MALICIOUS_JSON_KEY"
                    )
                
                # Recursively validate value
                self._validate_json_values(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                self._validate_json_values(item, current_path)
                
        elif isinstance(obj, str):
            if self._contains_malicious_content(obj):
                raise ValidationError(
                    f"JSON value contains potentially malicious content at: {path}",
                    "json_content",
                    "MALICIOUS_JSON_VALUE"
                )
    
    def _contains_malicious_content(self, text: str) -> bool:
        """Check if text contains malicious patterns."""
        import re
        
        # More specific patterns for JSON content
        json_malicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'<iframe[^>]*>',
            r'eval\s*\(',
            r'Function\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
        ]
        
        text_lower = text.lower()
        for pattern in json_malicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False


# Utility functions for request validation
def validate_request_size(content_length: Optional[str], max_size: int = MAX_REQUEST_SIZE) -> None:
    """Validate request content length."""
    if content_length:
        try:
            size = int(content_length)
            if size > max_size:
                raise ValidationError(
                    f"Request size {size} bytes exceeds maximum of {max_size} bytes",
                    "content_length",
                    "REQUEST_TOO_LARGE"
                )
        except ValueError:
            raise ValidationError(
                "Invalid content-length header",
                "content_length",
                "INVALID_CONTENT_LENGTH"
            )


def validate_file_upload_request(
    filename: str,
    file_size: int,
    mime_type: str,
    content: Optional[bytes] = None
) -> None:
    """Validate file upload request parameters."""
    from .validation_models import FileContentValidator
    
    # Use the validators from validation_models
    FileContentValidator.validate_filename(filename)
    FileContentValidator.validate_file_size(file_size)
    FileContentValidator.validate_mime_type(mime_type)
    
    # Additional content validation if provided
    if content is not None:
        # Verify actual size matches declared size
        actual_size = len(content)
        if actual_size != file_size:
            raise ValidationError(
                f"Actual file size {actual_size} does not match declared size {file_size}",
                "file_content",
                "SIZE_MISMATCH"
            )
        
        # Basic file signature validation
        if not _validate_file_signature(content, mime_type):
            raise ValidationError(
                f"File content does not match declared MIME type {mime_type}",
                "file_content",
                "MIME_TYPE_MISMATCH"
            )


def _validate_file_signature(content: bytes, mime_type: str) -> bool:
    """Validate file signature matches MIME type."""
    if not content:
        return False
    
    # File signatures (magic numbers)
    signatures = {
        'application/pdf': [b'%PDF'],
        'application/msword': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [
            b'PK\x03\x04'  # ZIP signature (DOCX is a ZIP file)
        ],
        'text/plain': [],  # No specific signature for text files
        'text/rtf': [b'{\\rtf'],
        'application/rtf': [b'{\\rtf'],
    }
    
    expected_signatures = signatures.get(mime_type, [])
    
    # If no signatures defined, assume valid (like for text files)
    if not expected_signatures:
        return True
    
    # Check if content starts with any expected signature
    for signature in expected_signatures:
        if content.startswith(signature):
            return True
    
    return False


__all__ = [
    'RequestValidationMiddleware',
    'ContentValidationMiddleware',
    'validate_request_size',
    'validate_file_upload_request',
    'ValidationError',
]