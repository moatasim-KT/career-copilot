"""
Enhanced Security Headers Middleware for Career Copilot.
Implements comprehensive security headers with environment-aware configuration.
"""

from typing import Dict, List, Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware with comprehensive protection.
    Adds security headers based on environment and endpoint requirements.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Base security headers
        self.base_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen",
            "X-DNS-Prefetch-Control": "off",
        }
        
        # HSTS header (only for HTTPS)
        if self.settings.enable_https or self.settings.force_https:
            self.base_headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy
        self.csp_directives = self._build_csp_directives()
        
        # Permissions Policy
        self.permissions_policy = self._build_permissions_policy()
        
        # Feature Policy (deprecated but still supported by some browsers)
        self.feature_policy = self._build_feature_policy()
        
        # Cross-Origin policies
        self.cross_origin_headers = {
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Cache control for sensitive endpoints
        self.sensitive_cache_control = (
            "no-store, no-cache, must-revalidate, private, max-age=0"
        )
        
        # Paths that need different security headers
        self.special_paths = {
            "/docs": {
                "X-Frame-Options": "SAMEORIGIN",  # Allow embedding in same origin
                "Cross-Origin-Resource-Policy": "cross-origin"  # Allow cross-origin for docs
            },
            "/redoc": {
                "X-Frame-Options": "SAMEORIGIN",
                "Cross-Origin-Resource-Policy": "cross-origin"
            },
            "/api/v1/upload": {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        }
        
        # Sensitive paths that need extra security
        self.sensitive_paths = {
            "/api/v1/auth/",
            "/api/v1/admin/",
            "/api/v1/security/",
            "/api/v1/users/"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Add comprehensive security headers to response."""
        
        response = await call_next(request)
        
        # Add base security headers
        for header, value in self.base_headers.items():
            response.headers[header] = value
        
        # Add CSP header
        csp_header = self._get_csp_header(request.url.path)
        if csp_header:
            response.headers["Content-Security-Policy"] = csp_header
        
        # Add Permissions Policy
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy
        
        # Add Feature Policy (for older browsers)
        if self.feature_policy:
            response.headers["Feature-Policy"] = self.feature_policy
        
        # Add Cross-Origin headers
        for header, value in self.cross_origin_headers.items():
            response.headers[header] = value
        
        # Add path-specific headers
        self._add_path_specific_headers(response, request.url.path)
        
        # Add cache control for sensitive paths
        if self._is_sensitive_path(request.url.path):
            response.headers["Cache-Control"] = self.sensitive_cache_control
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Add security headers for API responses
        if request.url.path.startswith("/api/"):
            self._add_api_security_headers(response)
        
        # Add development-specific headers
        if self.settings.environment == "development":
            self._add_development_headers(response)
        
        return response
    
    def _build_csp_directives(self) -> Dict[str, List[str]]:
        """Build Content Security Policy directives."""
        
        # Base CSP directives
        directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for some CSS
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "connect-src": ["'self'"],
            "media-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "upgrade-insecure-requests": [],
            "block-all-mixed-content": []
        }
        
        # Add API endpoints to connect-src
        api_endpoints = [
            "https://api.openai.com",
            "https://api.groq.com"
        ]
        directives["connect-src"].extend(api_endpoints)
        
        # Environment-specific adjustments
        if self.settings.environment == "development":
            # More permissive CSP for development
            directives["script-src"].extend([
                "'unsafe-eval'",  # Needed for dev tools
                "localhost:*",
                "127.0.0.1:*"
            ])
            directives["connect-src"].extend([
                "localhost:*",
                "127.0.0.1:*",
                "ws:",
                "wss:"
            ])
            directives["style-src"].append("'unsafe-eval'")
        
        # Add Google Fonts if needed
        directives["style-src"].append("https://fonts.googleapis.com")
        
        return directives
    
    def _build_permissions_policy(self) -> str:
        """Build Permissions Policy header."""
        
        # Restrictive permissions policy
        permissions = {
            "accelerometer": "()",
            "ambient-light-sensor": "()",
            "autoplay": "self",
            "battery": "()",
            "camera": "()",
            "cross-origin-isolated": "self",
            "display-capture": "()",
            "document-domain": "()",
            "encrypted-media": "self",
            "execution-while-not-rendered": "()",
            "execution-while-out-of-viewport": "()",
            "fullscreen": "self",
            "geolocation": "()",
            "gyroscope": "()",
            "keyboard-map": "()",
            "magnetometer": "()",
            "microphone": "()",
            "midi": "()",
            "navigation-override": "()",
            "payment": "()",
            "picture-in-picture": "()",
            "publickey-credentials-get": "self",
            "screen-wake-lock": "()",
            "sync-xhr": "()",
            "usb": "()",
            "web-share": "self",
            "xr-spatial-tracking": "()"
        }
        
        return ", ".join([f"{perm}={value}" for perm, value in permissions.items()])
    
    def _build_feature_policy(self) -> str:
        """Build Feature Policy header (for older browsers)."""
        
        # Legacy feature policy format
        features = {
            "accelerometer": "'none'",
            "ambient-light-sensor": "'none'",
            "autoplay": "'self'",
            "battery": "'none'",
            "camera": "'none'",
            "display-capture": "'none'",
            "document-domain": "'none'",
            "encrypted-media": "'self'",
            "fullscreen": "'self'",
            "geolocation": "'none'",
            "gyroscope": "'none'",
            "magnetometer": "'none'",
            "microphone": "'none'",
            "midi": "'none'",
            "payment": "'none'",
            "picture-in-picture": "'none'",
            "sync-xhr": "'none'",
            "usb": "'none'",
            "vr": "'none'",
            "wake-lock": "'none'",
            "xr-spatial-tracking": "'none'"
        }
        
        return "; ".join([f"{feature} {value}" for feature, value in features.items()])
    
    def _get_csp_header(self, path: str) -> str:
        """Get CSP header for the given path."""
        
        # Use base directives
        directives = self.csp_directives.copy()
        
        # Path-specific CSP adjustments
        if path.startswith("/docs") or path.startswith("/redoc"):
            # API documentation needs more permissive CSP
            directives["script-src"].extend([
                "'unsafe-inline'",
                "'unsafe-eval'",
                "https://cdn.jsdelivr.net"
            ])
            directives["style-src"].extend([
                "https://cdn.jsdelivr.net",
                "https://fonts.googleapis.com"
            ])
            directives["img-src"].extend([
                "https://cdn.jsdelivr.net",
                "https://fastapi.tiangolo.com"
            ])
            directives["font-src"].append("https://fonts.gstatic.com")
        
        elif path.startswith("/api/v1/upload"):
            # File upload endpoints
            directives["form-action"] = ["'self'"]
            directives["connect-src"].append("'self'")
        
        # Build CSP string
        csp_parts = []
        for directive, sources in directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)
        
        return "; ".join(csp_parts)
    
    def _add_path_specific_headers(self, response: Response, path: str):
        """Add path-specific security headers."""
        
        for special_path, headers in self.special_paths.items():
            if path.startswith(special_path):
                for header, value in headers.items():
                    response.headers[header] = value
                break
    
    def _add_api_security_headers(self, response: Response):
        """Add security headers specific to API responses."""
        
        # Prevent caching of API responses by default
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        # Add API-specific headers
        response.headers["X-API-Version"] = "1.0"
        response.headers["X-Robots-Tag"] = "noindex, nofollow, nosnippet, noarchive"
        
        # Prevent MIME type sniffing for API responses
        response.headers["X-Content-Type-Options"] = "nosniff"
    
    def _add_development_headers(self, response: Response):
        """Add development-specific headers."""
        
        # Add development indicator
        response.headers["X-Environment"] = "development"
        
        # Less restrictive cache control in development
        if response.headers.get("Cache-Control") == self.sensitive_cache_control:
            response.headers["Cache-Control"] = "no-cache"
    
    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path is sensitive and needs extra security."""
        
        return any(sensitive in path for sensitive in self.sensitive_paths)
    
    def add_trusted_source(self, directive: str, source: str):
        """Add a trusted source to a CSP directive."""
        
        if directive in self.csp_directives:
            if source not in self.csp_directives[directive]:
                self.csp_directives[directive].append(source)
                logger.info(f"Added trusted source '{source}' to CSP directive '{directive}'")
    
    def remove_trusted_source(self, directive: str, source: str):
        """Remove a trusted source from a CSP directive."""
        
        if directive in self.csp_directives and source in self.csp_directives[directive]:
            self.csp_directives[directive].remove(source)
            logger.info(f"Removed trusted source '{source}' from CSP directive '{directive}'")
    
    def update_csp_directive(self, directive: str, sources: List[str]):
        """Update a CSP directive with new sources."""
        
        self.csp_directives[directive] = sources.copy()
        logger.info(f"Updated CSP directive '{directive}' with sources: {sources}")
    
    def get_security_headers_config(self) -> Dict[str, any]:
        """Get current security headers configuration."""
        
        return {
            "base_headers": self.base_headers.copy(),
            "csp_directives": {k: v.copy() for k, v in self.csp_directives.items()},
            "permissions_policy": self.permissions_policy,
            "cross_origin_headers": self.cross_origin_headers.copy(),
            "sensitive_paths": list(self.sensitive_paths),
            "special_paths": {k: v.copy() for k, v in self.special_paths.items()}
        }


# Global enhanced security headers middleware instance
_enhanced_security_headers_middleware: Optional[EnhancedSecurityHeadersMiddleware] = None


def get_enhanced_security_headers_middleware() -> Optional[EnhancedSecurityHeadersMiddleware]:
    """Get the enhanced security headers middleware instance."""
    return _enhanced_security_headers_middleware


def set_enhanced_security_headers_middleware(middleware: EnhancedSecurityHeadersMiddleware):
    """Set the enhanced security headers middleware instance."""
    global _enhanced_security_headers_middleware
    _enhanced_security_headers_middleware = middleware