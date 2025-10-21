"""
API Key Authentication Middleware
Handles API key validation and rate limiting.
"""

from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger
from ..core.security import SecurityContext, SecurityLevel
from ..services.api_key_service import get_api_key_manager
from ..services.authorization_service import get_authorization_service

logger = get_logger(__name__)


class APIKeyAuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    def __init__(self, app):
        super().__init__(app)
        self.api_key_manager = get_api_key_manager()
        self.auth_service = get_authorization_service()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with API key authentication."""
        
        # Skip authentication for certain paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # Check for API key in headers
        api_key = self._extract_api_key(request)
        
        if api_key:
            # Validate API key
            validation_result = await self.api_key_manager.validate_api_key(
                api_key=api_key,
                ip_address=request.client.host
            )
            
            if validation_result.is_valid:
                # Create security context for API key
                security_context = SecurityContext(
                    user_id=validation_result.user_data["id"],
                    username=validation_result.user_data["username"],
                    email=validation_result.user_data["email"],
                    roles=validation_result.user_data.get("roles", []),
                    permissions=validation_result.key_data.permissions,
                    security_level=SecurityLevel.STANDARD,
                    mfa_verified=False,  # API keys don't require MFA
                    session_id=validation_result.key_data.key_id,
                    is_authenticated=True,
                    auth_method="api_key"
                )
                
                # Add security context to request state
                request.state.security_context = security_context
                request.state.api_key_data = validation_result.key_data
                
                # Add rate limit headers to response
                response = await call_next(request)
                response.headers["X-RateLimit-Remaining"] = str(validation_result.rate_limit_remaining)
                if validation_result.rate_limit_reset:
                    response.headers["X-RateLimit-Reset"] = validation_result.rate_limit_reset.isoformat()
                
                return response
            else:
                # Invalid API key
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=validation_result.error_message or "Invalid API key",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
        
        # No API key provided, continue with normal processing
        return await call_next(request)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/monitoring/health",
            "/monitoring/metrics/prometheus"  # Allow Prometheus scraping without auth
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check Authorization header with ApiKey scheme
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("ApiKey "):
            return auth_header[7:]  # Remove "ApiKey " prefix
        
        return None


# Dependency for FastAPI endpoints to get current user from API key
async def get_current_user_from_api_key(request: Request) -> Optional[SecurityContext]:
    """Get current user from API key authentication."""
    
    if hasattr(request.state, "security_context"):
        return request.state.security_context
    
    return None


# Combined dependency that works with both JWT and API key authentication
async def get_current_user_or_api_key(request: Request) -> SecurityContext:
    """Get current user from either JWT token or API key."""
    
    # First check if we have API key authentication
    if hasattr(request.state, "security_context"):
        return request.state.security_context
    
    # If no API key, try JWT authentication
    from ..api.v1.security import get_current_user
    from fastapi.security import HTTPBearer
    from fastapi import Depends
    
    security = HTTPBearer()
    
    try:
        # This will raise an exception if no valid JWT token
        credentials = security(request)
        if credentials:
            return await get_current_user(credentials)
    except Exception:
        pass
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer, ApiKey"}
    )