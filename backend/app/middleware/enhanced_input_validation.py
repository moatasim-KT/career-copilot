"""
Enhanced Input Validation and Security Measures for Career Copilot.
Implements comprehensive input sanitization, validation, and security hardening.
"""

import re
import json
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError as PydanticValidationError

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class EnhancedInputSanitizer:
    """Enhanced input sanitization with comprehensive security patterns."""
    
    # Enhanced SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
        r"(\b(EXEC|EXECUTE)\s*\()",
        r"(\bINTO\s+OUTFILE\b)",
        r"(\bLOAD_FILE\s*\()",
        r"(\bCHAR\s*\()",
        r"(\bCONCAT\s*\()",
        r"(\bSUBSTRING\s*\()",
        r"(\bHEX\s*\()",
        r"(\bUNHEX\s*\()",
        r"(\bSLEEP\s*\()",
        r"(\bBENCHMARK\s*\()",
        r"(\bEXTRACTVALUE\s*\()",
        r"(\bUPDATEXML\s*\()",
    ]
    
    # Enhanced XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<applet[^>]*>.*?</applet>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>.*?</style>",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
        r"data:application/",
        r"on\w+\s*=",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import",
        r"<svg[^>]*>.*?</svg>",
        r"<math[^>]*>.*?</math>",
        r"<form[^>]*>.*?</form>",
        r"<input[^>]*>",
        r"<textarea[^>]*>.*?</textarea>",
        r"<select[^>]*>.*?</select>",
        r"<button[^>]*>.*?</button>",
    ]
    
    # Enhanced command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]\\]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|wget|curl|nc|telnet|ssh|ftp|chmod|chown|rm|mv|cp|mkdir|rmdir|find|grep|awk|sed|sort|uniq|head|tail|wc|tar|gzip|gunzip|zip|unzip)\b",
        r"(\.\.\/|\.\.\\)",
        r"(/etc/passwd|/etc/shadow|/proc/|/sys/|/dev/|/var/log/)",
        r"(\\windows\\|\\system32\\|\\cmd\.exe|\\powershell\.exe)",
        r"(\$\{.*\})",
        r"(\$\(.*\))",
        r"(`.*`)",
        r"(&&|\|\|)",
        r"(>|>>|<|<<)",
        r"(\|)",
        r"(;)",
        r"(&)",
    ]
    
    # Enhanced path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\.\/|\.\.\\)",
        r"(%2e%2e%2f|%2e%2e%5c|%2e%2e/|%2e%2e\\)",
        r"(\.\.%2f|\.\.%5c)",
        r"(%252e%252e%252f|%252e%252e%255c)",
        r"(\/etc\/|\\windows\\|\\system32\\)",
        r"(\/proc\/|\/sys\/|\/dev\/)",
        r"(\/var\/log\/|\/var\/www\/)",
        r"(\/home\/|\/root\/|\/tmp\/)",
        r"(c:\\|d:\\|e:\\)",
        r"(\\\\|\/\/)",
    ]
    
    # LDAP injection patterns
    LDAP_INJECTION_PATTERNS = [
        r"(\(\|)",
        r"(\)\(\&)",
        r"(\*\))",
        r"(\(\&\()",
        r"(\|\()",
        r"(\)\|)",
        r"(\(\!)",
        r"(\!\()",
    ]
    
    # NoSQL injection patterns
    NOSQL_INJECTION_PATTERNS = [
        r"(\$where)",
        r"(\$ne)",
        r"(\$in)",
        r"(\$nin)",
        r"(\$gt)",
        r"(\$gte)",
        r"(\$lt)",
        r"(\$lte)",
        r"(\$regex)",
        r"(\$exists)",
        r"(\$type)",
        r"(\$mod)",
        r"(\$all)",
        r"(\$size)",
        r"(\$elemMatch)",
        r"(\$not)",
        r"(\$or)",
        r"(\$and)",
        r"(\$nor)",
    ]
    
    # Template injection patterns
    TEMPLATE_INJECTION_PATTERNS = [
        r"(\{\{.*\}\})",
        r"(\{%.*%\})",
        r"(\$\{.*\})",
        r"(<%.*%>)",
        r"(\[\[.*\]\])",
        r"(\{\{.*\}\})",
        r"(\{#.*#\})",
        r"(\{!.*!\})",
    ]
    
    def __init__(self):
        self.settings = get_settings()
        self.max_input_length = self.settings.max_input_length
        self.strict_validation = self.settings.strict_validation
        
        # Compile regex patterns for better performance
        self._compiled_patterns = {
            'sql': [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS],
            'xss': [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS],
            'command': [re.compile(pattern, re.IGNORECASE) for pattern in self.COMMAND_INJECTION_PATTERNS],
            'path': [re.compile(pattern, re.IGNORECASE) for pattern in self.PATH_TRAVERSAL_PATTERNS],
            'ldap': [re.compile(pattern, re.IGNORECASE) for pattern in self.LDAP_INJECTION_PATTERNS],
            'nosql': [re.compile(pattern, re.IGNORECASE) for pattern in self.NOSQL_INJECTION_PATTERNS],
            'template': [re.compile(pattern, re.IGNORECASE) for pattern in self.TEMPLATE_INJECTION_PATTERNS],
        }
    
    def sanitize_string(self, value: str, context: str = "general") -> str:
        """
        Enhanced string sanitization with context awareness.
        
        Args:
            value: Input string to sanitize
            context: Context of the input (email, filename, url, etc.)
            
        Returns:
            Sanitized string
            
        Raises:
            ValueError: If malicious content is detected
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Check length
        if len(value) > self.max_input_length:
            raise ValueError(f"Input too long: {len(value)} > {self.max_input_length}")
        
        # URL decode multiple times to catch double encoding
        decoded_value = value
        for _ in range(3):  # Decode up to 3 times
            try:
                new_decoded = urllib.parse.unquote(decoded_value)
                if new_decoded == decoded_value:
                    break
                decoded_value = new_decoded
            except Exception:
                break
        
        # Check for malicious patterns
        self._check_all_injection_patterns(decoded_value)
        
        # Context-specific sanitization
        if context == "email":
            return self._sanitize_email(decoded_value)
        elif context == "filename":
            return self._sanitize_filename(decoded_value)
        elif context == "url":
            return self._sanitize_url(decoded_value)
        elif context == "html":
            return self._sanitize_html(decoded_value)
        else:
            return self._sanitize_general(decoded_value)
    
    def _check_all_injection_patterns(self, value: str):
        """Check for all types of injection patterns."""
        for pattern_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(value):
                    raise ValueError(f"Potential {pattern_type} injection detected: {pattern.pattern}")
    
    def _sanitize_general(self, value: str) -> str:
        """General sanitization for text input."""
        # Remove null bytes
        sanitized = value.replace('\x00', '')
        
        # Remove control characters except common whitespace
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    def _sanitize_email(self, value: str) -> str:
        """Sanitize email addresses."""
        # Basic email validation pattern
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        sanitized = self._sanitize_general(value)
        
        if not email_pattern.match(sanitized):
            raise ValueError("Invalid email format")
        
        return sanitized.lower()
    
    def _sanitize_filename(self, value: str) -> str:
        """Sanitize filenames."""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', value)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        if sanitized.upper() in reserved_names:
            raise ValueError(f"Reserved filename: {sanitized}")
        
        if not sanitized:
            raise ValueError("Empty filename after sanitization")
        
        return sanitized
    
    def _sanitize_url(self, value: str) -> str:
        """Sanitize URLs."""
        # Parse URL to validate structure
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(value)
            
            # Check for allowed schemes
            allowed_schemes = {'http', 'https', 'ftp', 'ftps'}
            if parsed.scheme and parsed.scheme.lower() not in allowed_schemes:
                raise ValueError(f"Disallowed URL scheme: {parsed.scheme}")
            
            # Reconstruct URL to normalize it
            sanitized = urlunparse(parsed)
            
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}")
        
        return sanitized
    
    def _sanitize_html(self, value: str) -> str:
        """Sanitize HTML content."""
        # HTML escape the content
        sanitized = html.escape(value, quote=True)
        
        # Additional checks for HTML entities that could be dangerous
        dangerous_entities = ['&lt;script', '&lt;iframe', '&lt;object', '&lt;embed']
        for entity in dangerous_entities:
            if entity in sanitized.lower():
                raise ValueError("Dangerous HTML entity detected")
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any], context_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary data with context awareness.
        
        Args:
            data: Dictionary to sanitize
            context_map: Mapping of field names to contexts
            
        Returns:
            Sanitized dictionary
        """
        if context_map is None:
            context_map = {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            sanitized_key = self.sanitize_string(str(key), "general")
            
            # Get context for this field
            context = context_map.get(key, "general")
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[sanitized_key] = self.sanitize_string(value, context)
            elif isinstance(value, dict):
                # Pass down context map for nested objects
                nested_context = {k.replace(f"{key}.", ""): v for k, v in context_map.items() if k.startswith(f"{key}.")}
                sanitized[sanitized_key] = self.sanitize_dict(value, nested_context)
            elif isinstance(value, list):
                sanitized[sanitized_key] = self.sanitize_list(value, context)
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized[sanitized_key] = value
            else:
                # Convert other types to string and sanitize
                sanitized[sanitized_key] = self.sanitize_string(str(value), context)
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], context: str = "general") -> List[Any]:
        """
        Sanitize list data.
        
        Args:
            data: List to sanitize
            context: Context for list items
            
        Returns:
            Sanitized list
        """
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item, context))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, context))
            elif isinstance(item, (int, float, bool)) or item is None:
                sanitized.append(item)
            else:
                sanitized.append(self.sanitize_string(str(item), context))
        
        return sanitized


class EnhancedInputValidationMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for comprehensive input validation and sanitization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.sanitizer = EnhancedInputSanitizer()
        self.settings = get_settings()
        
        # Paths that skip validation (for performance)
        self.skip_validation_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/metrics"
        }
        
        # Context mapping for different endpoints
        self.context_mappings = {
            "/api/v1/auth/": {
                "email": "email",
                "password": "general",
                "username": "general"
            },
            "/api/v1/upload": {
                "filename": "filename",
                "description": "general"
            },
            "/api/v1/users/": {
                "email": "email",
                "name": "general",
                "bio": "html"
            }
        }
        
        # Rate limiting for validation failures
        self.validation_failures = {}
        self.max_failures_per_ip = 10
        self.failure_window = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next):
        """Process request through enhanced input validation."""
        
        # Skip validation for certain paths
        if request.url.path in self.skip_validation_paths:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        try:
            # Check validation failure rate limiting
            if self._is_rate_limited(client_ip):
                audit_logger.log_event(
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    action="Too many validation failures",
                    severity=AuditSeverity.HIGH,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    details={"path": request.url.path, "method": request.method}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many validation failures. Please try again later."
                )
            
            # Enhanced header validation
            await self._validate_headers(request)
            
            # Enhanced query parameter validation
            await self._validate_query_params(request)
            
            # Enhanced request body validation
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request)
            
            # Continue to next middleware
            return await call_next(request)
            
        except ValueError as e:
            # Record validation failure
            self._record_validation_failure(client_ip)
            
            # Log security violation
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                action=f"Enhanced input validation failed: {str(e)}",
                severity=AuditSeverity.HIGH,
                ip_address=client_ip,
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
        
        except HTTPException:
            # Record validation failure for HTTP exceptions too
            self._record_validation_failure(client_ip)
            raise
        
        except Exception as e:
            logger.error(f"Error in enhanced input validation middleware: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Input validation error"
            )
    
    async def _validate_headers(self, request: Request):
        """Enhanced header validation."""
        dangerous_headers = [
            "x-forwarded-host",
            "x-rewrite-url", 
            "x-original-url",
            "x-forwarded-proto",
            "x-forwarded-server",
            "x-forwarded-port"
        ]
        
        for header_name, header_value in request.headers.items():
            # Check for dangerous headers
            if header_name.lower() in dangerous_headers:
                audit_logger.log_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    action=f"Dangerous header detected: {header_name}",
                    severity=AuditSeverity.MEDIUM,
                    ip_address=self._get_client_ip(request),
                    details={"header": header_name, "value": header_value}
                )
            
            # Validate header values
            try:
                self.sanitizer.sanitize_string(header_value)
            except ValueError as e:
                raise ValueError(f"Invalid header '{header_name}': {e}")
        
        # Validate User-Agent
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 1000:
            raise ValueError("User-Agent header too long")
        
        # Check for suspicious User-Agent patterns
        suspicious_ua_patterns = [
            r"sqlmap", r"nikto", r"nmap", r"masscan", r"zap", r"burp",
            r"w3af", r"skipfish", r"wfuzz", r"dirb", r"dirbuster",
            r"<script", r"javascript:", r"vbscript:"
        ]
        
        for pattern in suspicious_ua_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                raise ValueError(f"Suspicious User-Agent pattern detected: {pattern}")
    
    async def _validate_query_params(self, request: Request):
        """Enhanced query parameter validation."""
        if not request.query_params:
            return
        
        # Check number of parameters
        if len(request.query_params) > 50:
            raise ValueError("Too many query parameters")
        
        for key, value in request.query_params.items():
            try:
                # Sanitize parameter name and value
                self.sanitizer.sanitize_string(key)
                self.sanitizer.sanitize_string(value)
                
                # Additional checks for specific parameter patterns
                if key.lower() in ['callback', 'jsonp']:
                    # JSONP callback validation
                    if not re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*$', value):
                        raise ValueError(f"Invalid JSONP callback: {value}")
                
                # Check for base64 encoded payloads
                if len(value) > 100 and self._is_base64_encoded(value):
                    try:
                        import base64
                        decoded = base64.b64decode(value).decode('utf-8', errors='ignore')
                        self.sanitizer.sanitize_string(decoded)
                    except Exception:
                        pass  # Not valid base64 or contains malicious content
                
            except ValueError as e:
                raise ValueError(f"Invalid query parameter '{key}': {e}")
    
    async def _validate_request_body(self, request: Request):
        """Enhanced request body validation."""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            await self._validate_json_body(request)
        elif "application/x-www-form-urlencoded" in content_type:
            await self._validate_form_body(request)
        elif "multipart/form-data" in content_type:
            await self._validate_multipart_body(request)
    
    async def _validate_json_body(self, request: Request):
        """Enhanced JSON body validation."""
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
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
            
            # Get context mapping for this endpoint
            context_map = self._get_context_mapping(request.url.path)
            
            # Sanitize JSON data
            if isinstance(data, dict):
                self.sanitizer.sanitize_dict(data, context_map)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        self.sanitizer.sanitize_dict(item, context_map)
                    elif isinstance(item, str):
                        self.sanitizer.sanitize_string(item)
            elif isinstance(data, str):
                self.sanitizer.sanitize_string(data)
            
        except UnicodeDecodeError:
            raise ValueError("Invalid character encoding")
    
    async def _validate_form_body(self, request: Request):
        """Enhanced form body validation."""
        try:
            form_data = await request.form()
            
            context_map = self._get_context_mapping(request.url.path)
            
            for key, value in form_data.items():
                if isinstance(value, str):
                    context = context_map.get(key, "general")
                    self.sanitizer.sanitize_string(key)
                    self.sanitizer.sanitize_string(value, context)
                    
        except Exception as e:
            raise ValueError(f"Invalid form data: {e}")
    
    async def _validate_multipart_body(self, request: Request):
        """Enhanced multipart form data validation."""
        try:
            form_data = await request.form()
            
            context_map = self._get_context_mapping(request.url.path)
            
            for key, value in form_data.items():
                # Sanitize field name
                self.sanitizer.sanitize_string(key)
                
                # Validate field value (if string)
                if isinstance(value, str):
                    context = context_map.get(key, "general")
                    self.sanitizer.sanitize_string(value, context)
                # File uploads are handled separately by file upload middleware
                    
        except Exception as e:
            raise ValueError(f"Invalid multipart data: {e}")
    
    def _get_context_mapping(self, path: str) -> Dict[str, str]:
        """Get context mapping for the given path."""
        for pattern, mapping in self.context_mappings.items():
            if path.startswith(pattern):
                return mapping
        return {}
    
    def _is_base64_encoded(self, value: str) -> bool:
        """Check if a string is base64 encoded."""
        try:
            import base64
            # Check if it's valid base64
            if len(value) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]*={0,2}$', value):
                base64.b64decode(value)
                return True
        except Exception:
            pass
        return False
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited for validation failures."""
        current_time = datetime.utcnow()
        
        if client_ip not in self.validation_failures:
            return False
        
        # Clean old failures
        cutoff_time = current_time - timedelta(seconds=self.failure_window)
        self.validation_failures[client_ip] = [
            failure_time for failure_time in self.validation_failures[client_ip]
            if failure_time > cutoff_time
        ]
        
        # Check if rate limited
        return len(self.validation_failures[client_ip]) >= self.max_failures_per_ip
    
    def _record_validation_failure(self, client_ip: str):
        """Record a validation failure for rate limiting."""
        current_time = datetime.utcnow()
        
        if client_ip not in self.validation_failures:
            self.validation_failures[client_ip] = []
        
        self.validation_failures[client_ip].append(current_time)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


# Global enhanced sanitizer instance
_enhanced_input_sanitizer: Optional[EnhancedInputSanitizer] = None


def get_enhanced_input_sanitizer() -> EnhancedInputSanitizer:
    """Get the enhanced input sanitizer instance."""
    global _enhanced_input_sanitizer
    if _enhanced_input_sanitizer is None:
        _enhanced_input_sanitizer = EnhancedInputSanitizer()
    return _enhanced_input_sanitizer