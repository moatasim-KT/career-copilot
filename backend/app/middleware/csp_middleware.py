"""
Content Security Policy (CSP) Middleware for Career Copilot.
Implements comprehensive CSP headers and security policies.
"""

from typing import Callable, Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy middleware.
    Adds comprehensive security headers to all responses.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Base CSP directives
        self.csp_directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],  # Unsafe-inline needed for some frameworks
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "img-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'", "https://api.openai.com", "https://api.groq.com"],
            "media-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "upgrade-insecure-requests": [],
            "block-all-mixed-content": []
        }
        
        # Development vs Production CSP
        if self.settings.environment == "development":
            # More permissive CSP for development
            self.csp_directives["script-src"].extend(["'unsafe-eval'", "localhost:*", "127.0.0.1:*"])
            self.csp_directives["connect-src"].extend(["localhost:*", "127.0.0.1:*", "ws:", "wss:"])
            self.csp_directives["style-src"].extend(["'unsafe-eval'"])
        
        # Additional security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Permissions-Policy": self._build_permissions_policy(),
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Paths that need different CSP (e.g., API documentation)
        self.special_paths = {
            "/docs": {
                "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
                "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
                "img-src": ["'self'", "data:", "https:", "https://cdn.jsdelivr.net"]
            },
            "/redoc": {
                "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
                "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com"],
                "font-src": ["'self'", "https://fonts.gstatic.com"]
            }
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add CSP and security headers to response."""
        
        response = await call_next(request)
        
        # Add CSP header
        csp_header = self._build_csp_header(request.url.path)
        if csp_header:
            response.headers["Content-Security-Policy"] = csp_header
        
        # Add other security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add CSP report URI if configured
        if self.settings.csp_report_uri:
            response.headers["Content-Security-Policy-Report-Only"] = (
                csp_header + f"; report-uri {self.settings.csp_report_uri}"
            )
        
        return response
    
    def _build_csp_header(self, path: str) -> str:
        """
        Build CSP header for the given path.
        
        Args:
            path: Request path
            
        Returns:
            CSP header string
        """
        # Check if path needs special CSP
        directives = self.csp_directives.copy()
        
        for special_path, special_directives in self.special_paths.items():
            if path.startswith(special_path):
                # Merge special directives
                for directive, sources in special_directives.items():
                    if directive in directives:
                        # Combine sources, removing duplicates
                        combined = list(directives[directive])
                        for source in sources:
                            if source not in combined:
                                combined.append(source)
                        directives[directive] = combined
                    else:
                        directives[directive] = sources
                break
        
        # Build CSP string
        csp_parts = []
        for directive, sources in directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)
        
        return "; ".join(csp_parts)
    
    def _build_permissions_policy(self) -> str:
        """
        Build Permissions Policy header.
        
        Returns:
            Permissions Policy header string
        """
        # Restrictive permissions policy
        permissions = {
            "geolocation": "self",
            "microphone": "()",
            "camera": "()",
            "payment": "()",
            "usb": "()",
            "magnetometer": "()",
            "gyroscope": "()",
            "accelerometer": "()",
            "ambient-light-sensor": "()",
            "autoplay": "self",
            "encrypted-media": "self",
            "fullscreen": "self",
            "picture-in-picture": "()",
            "sync-xhr": "()",
            "web-share": "self"
        }
        
        return ", ".join([f"{perm}={value}" for perm, value in permissions.items()])
    
    def add_trusted_source(self, directive: str, source: str):
        """
        Add a trusted source to a CSP directive.
        
        Args:
            directive: CSP directive (e.g., 'script-src')
            source: Source to add (e.g., 'https://example.com')
        """
        if directive in self.csp_directives:
            if source not in self.csp_directives[directive]:
                self.csp_directives[directive].append(source)
                logger.info(f"Added trusted source '{source}' to '{directive}'")
    
    def remove_trusted_source(self, directive: str, source: str):
        """
        Remove a trusted source from a CSP directive.
        
        Args:
            directive: CSP directive
            source: Source to remove
        """
        if directive in self.csp_directives and source in self.csp_directives[directive]:
            self.csp_directives[directive].remove(source)
            logger.info(f"Removed trusted source '{source}' from '{directive}'")
    
    def get_csp_config(self) -> Dict[str, List[str]]:
        """Get current CSP configuration."""
        return self.csp_directives.copy()
    
    def update_csp_directive(self, directive: str, sources: List[str]):
        """
        Update a CSP directive with new sources.
        
        Args:
            directive: CSP directive to update
            sources: New list of sources
        """
        self.csp_directives[directive] = sources.copy()
        logger.info(f"Updated CSP directive '{directive}' with sources: {sources}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Additional security headers middleware.
    Adds extra security headers not covered by CSP.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Additional security headers
        self.headers = {
            "X-Robots-Tag": "noindex, nofollow, nosnippet, noarchive",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Clear-Site-Data": '"cache", "cookies", "storage"' if self.settings.environment == "production" else None,
            "Expect-CT": f'max-age=86400, enforce, report-uri="{self.settings.csp_report_uri}"' if self.settings.csp_report_uri else None
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add additional security headers."""
        
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.headers.items():
            if value is not None:
                response.headers[header] = value
        
        # Add cache control for sensitive endpoints
        if self._is_sensitive_path(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
    
    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path contains sensitive data."""
        sensitive_patterns = [
            "/api/v1/auth/",
            "/api/v1/users/",
            "/api/v1/admin/",
            "/api/v1/security/"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)


# Global CSP middleware instance
_csp_middleware: Optional[CSPMiddleware] = None


def get_csp_middleware() -> Optional[CSPMiddleware]:
    """Get the CSP middleware instance."""
    return _csp_middleware


def set_csp_middleware(middleware: CSPMiddleware):
    """Set the CSP middleware instance."""
    global _csp_middleware
    _csp_middleware = middleware