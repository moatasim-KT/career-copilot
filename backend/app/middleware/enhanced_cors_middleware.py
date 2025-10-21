"""
Enhanced CORS Middleware with Security Hardening for Career Copilot.
Implements secure CORS configuration with additional security measures.
"""

import re
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urlparse

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class EnhancedCORSMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security hardening.
    Provides secure CORS configuration with additional validation and logging.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Parse allowed origins
        self.allowed_origins = self._parse_allowed_origins()
        
        # Allowed methods (restrictive by default)
        self.allowed_methods = {
            "GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"
        }
        
        # Allowed headers (secure defaults)
        self.allowed_headers = {
            "accept",
            "accept-encoding",
            "authorization",
            "content-type",
            "dnt",
            "origin",
            "user-agent",
            "x-csrftoken",
            "x-requested-with",
            "x-api-key",
            "x-request-id",
            "x-correlation-id",
            "cache-control",
            "pragma"
        }
        
        # Headers to expose to the client
        self.exposed_headers = {
            "x-request-id",
            "x-rate-limit-remaining",
            "x-rate-limit-reset",
            "x-correlation-id",
            "content-length",
            "content-type"
        }
        
        # Preflight cache duration (24 hours)
        self.max_age = 86400
        
        # Security settings
        self.allow_credentials = True
        self.allow_private_network = False
        
        # Suspicious origin patterns
        self.suspicious_patterns = [
            r".*\.onion$",  # Tor hidden services
            r".*localhost.*",  # Localhost variations (except configured ones)
            r".*127\.0\.0\.1.*",  # Loopback variations
            r".*192\.168\..*",  # Private networks (unless explicitly allowed)
            r".*10\..*",  # Private networks
            r".*172\.(1[6-9]|2[0-9]|3[0-1])\..*",  # Private networks
            r".*file://.*",  # File protocol
            r".*data:.*",  # Data URLs
            r".*javascript:.*",  # JavaScript URLs
            r".*vbscript:.*",  # VBScript URLs
        ]
        
        # Compile patterns for performance
        self.compiled_suspicious_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process CORS headers with enhanced security."""
        
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return await self._handle_preflight(request, origin)
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(response, request, origin)
        
        return response
    
    async def _handle_preflight(self, request: Request, origin: Optional[str]) -> Response:
        """Handle CORS preflight requests."""
        
        # Validate origin
        if not self._is_origin_allowed(origin):
            # Log suspicious preflight request
            audit_logger.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                action=f"CORS preflight from disallowed origin: {origin}",
                severity=AuditSeverity.MEDIUM,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                details={"origin": origin, "path": request.url.path}
            )
            
            # Return minimal response without CORS headers
            return StarletteResponse(status_code=403)
        
        # Validate requested method
        requested_method = request.headers.get("access-control-request-method")
        if requested_method and requested_method not in self.allowed_methods:
            logger.warning(f"CORS preflight with disallowed method: {requested_method} from {origin}")
            return StarletteResponse(status_code=405)
        
        # Validate requested headers
        requested_headers = request.headers.get("access-control-request-headers", "")
        if requested_headers:
            headers_list = [h.strip().lower() for h in requested_headers.split(",")]
            disallowed_headers = set(headers_list) - self.allowed_headers
            
            if disallowed_headers:
                logger.warning(f"CORS preflight with disallowed headers: {disallowed_headers} from {origin}")
                # Allow the request but don't include disallowed headers in response
                headers_list = [h for h in headers_list if h in self.allowed_headers]
        else:
            headers_list = []
        
        # Create preflight response
        response = StarletteResponse(status_code=200)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(headers_list) if headers_list else ""
        response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add security headers
        response.headers["Vary"] = "Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        
        # Log successful preflight
        logger.debug(f"CORS preflight approved for {origin} -> {request.url.path}")
        
        return response
    
    def _add_cors_headers(self, response: Response, request: Request, origin: Optional[str]):
        """Add CORS headers to actual response."""
        
        if not self._is_origin_allowed(origin):
            # Don't add CORS headers for disallowed origins
            return
        
        # Add basic CORS headers
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Expose-Headers"] = ", ".join(self.exposed_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add Vary header for caching
        vary_header = response.headers.get("Vary", "")
        if "Origin" not in vary_header:
            if vary_header:
                response.headers["Vary"] = f"{vary_header}, Origin"
            else:
                response.headers["Vary"] = "Origin"
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        # Log CORS response
        logger.debug(f"CORS headers added for {origin} -> {request.url.path}")
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed with enhanced security validation."""
        
        if not origin:
            # No origin header (same-origin requests or non-browser clients)
            return True
        
        # Check against suspicious patterns first
        if self._is_suspicious_origin(origin):
            return False
        
        # Check against allowed origins
        if "*" in self.allowed_origins:
            # Wildcard allowed, but still check for suspicious patterns
            return True
        
        # Exact match
        if origin in self.allowed_origins:
            return True
        
        # Pattern matching for development environments
        if self.settings.environment == "development":
            # Allow localhost variations in development
            localhost_patterns = [
                r"^https?://localhost(:\d+)?$",
                r"^https?://127\.0\.0\.1(:\d+)?$",
                r"^https?://\[::1\](:\d+)?$"
            ]
            
            for pattern in localhost_patterns:
                if re.match(pattern, origin, re.IGNORECASE):
                    return True
        
        return False
    
    def _is_suspicious_origin(self, origin: str) -> bool:
        """Check if origin matches suspicious patterns."""
        
        # Parse origin URL
        try:
            parsed = urlparse(origin)
            
            # Check for non-HTTP(S) schemes
            if parsed.scheme not in ("http", "https"):
                logger.warning(f"Suspicious origin scheme: {origin}")
                return True
            
            # Check hostname against patterns
            hostname = parsed.hostname or ""
            
            for pattern in self.compiled_suspicious_patterns:
                if pattern.search(hostname):
                    # Allow configured localhost in development
                    if (self.settings.environment == "development" and 
                        ("localhost" in hostname or "127.0.0.1" in hostname)):
                        continue
                    
                    logger.warning(f"Suspicious origin pattern matched: {origin}")
                    return True
            
            # Check for suspicious ports
            if parsed.port:
                # Common malicious ports
                suspicious_ports = {
                    1080, 1081,  # SOCKS proxies
                    3128, 8080,  # Common proxy ports
                    4444, 4445,  # Common backdoor ports
                    6666, 6667,  # IRC/malware
                    31337,       # Elite/hacker port
                }
                
                if parsed.port in suspicious_ports:
                    logger.warning(f"Suspicious origin port: {origin}")
                    return True
            
        except Exception as e:
            logger.warning(f"Error parsing origin URL {origin}: {e}")
            return True
        
        return False
    
    def _parse_allowed_origins(self) -> Set[str]:
        """Parse allowed origins from configuration."""
        origins_str = self.settings.cors_origins
        
        if not origins_str:
            return {"*"}  # Default to allow all if not configured
        
        # Split by comma and clean up
        origins = set()
        for origin in origins_str.split(","):
            origin = origin.strip()
            if origin:
                # Validate origin format
                if origin != "*":
                    try:
                        parsed = urlparse(origin)
                        if not parsed.scheme or not parsed.netloc:
                            logger.warning(f"Invalid origin format: {origin}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error parsing origin {origin}: {e}")
                        continue
                
                origins.add(origin)
        
        if not origins:
            logger.warning("No valid origins configured, defaulting to wildcard")
            origins.add("*")
        
        logger.info(f"Configured CORS origins: {origins}")
        return origins
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def add_allowed_origin(self, origin: str):
        """Add an allowed origin at runtime."""
        if origin and origin not in self.allowed_origins:
            self.allowed_origins.add(origin)
            logger.info(f"Added allowed origin: {origin}")
    
    def remove_allowed_origin(self, origin: str):
        """Remove an allowed origin at runtime."""
        if origin in self.allowed_origins:
            self.allowed_origins.remove(origin)
            logger.info(f"Removed allowed origin: {origin}")
    
    def add_allowed_header(self, header: str):
        """Add an allowed header at runtime."""
        if header:
            self.allowed_headers.add(header.lower())
            logger.info(f"Added allowed header: {header}")
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get current CORS configuration."""
        return {
            "allowed_origins": list(self.allowed_origins),
            "allowed_methods": list(self.allowed_methods),
            "allowed_headers": list(self.allowed_headers),
            "exposed_headers": list(self.exposed_headers),
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age
        }


# Global CORS middleware instance
_enhanced_cors_middleware: Optional[EnhancedCORSMiddleware] = None


def get_enhanced_cors_middleware() -> Optional[EnhancedCORSMiddleware]:
    """Get the enhanced CORS middleware instance."""
    return _enhanced_cors_middleware


def set_enhanced_cors_middleware(middleware: EnhancedCORSMiddleware):
    """Set the enhanced CORS middleware instance."""
    global _enhanced_cors_middleware
    _enhanced_cors_middleware = middleware