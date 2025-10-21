"""
JWT Authentication Middleware
Handles JWT token validation, session management, and security headers.
"""

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.audit import AuditEventType, AuditSeverity, audit_logger
from ..core.config import get_settings
from ..core.logging import get_logger
from ..services.authentication_service import get_authentication_service
from ..services.authorization_service import get_authorization_service

logger = get_logger(__name__)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and session management."""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.auth_service = get_authentication_service()
        self.authz_service = get_authorization_service()
        self.security = HTTPBearer(auto_error=False)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/favicon.ico",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/health/detailed",
            "/api/v1/health/readiness",
            "/api/v1/health/liveness",
            "/api/v1/health/metrics",
            "/api/v1/health/logging",
            "/api/v1/health/services",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/monitoring/health",
            "/monitoring/health/detailed",
            "/monitoring/health/live",
            "/monitoring/health/ready",
            "/monitoring/status",
            "/monitoring/metrics",
            "/monitoring/metrics/prometheus",
            "/monitoring/metrics/performance",
            "/monitoring/alerts",
            "/monitoring/langsmith/status",
            "/monitoring/config"
        }
        
        # Paths that require specific permissions
        self.protected_paths = {
            "/api/v1/admin": ["admin"],
            "/api/v1/users": ["user_management"],
            "/api/v1/security": ["security_management"]
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with JWT authentication."""
        start_time = time.time()
        
        try:
            # Skip authentication entirely in development mode if disabled
            if self.settings.disable_auth or self.settings.development_mode:
                # Add mock authentication context for development
                request.state.current_user = None
                request.state.session_id = "dev-session"
                request.state.auth_method = "development"
                request.state.is_authenticated = False
                return await call_next(request)
            
            # Skip authentication for public paths
            if self._should_skip_auth(request.url.path):
                return await call_next(request)
            
            # Extract JWT token
            token = self._extract_jwt_token(request)
            
            if not token:
                # No token provided
                await self._log_auth_attempt(request, "no_token", False)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate token
            token_data = await self.auth_service.validate_access_token(token)
            
            if not token_data:
                # Invalid token
                await self._log_auth_attempt(request, "invalid_token", False)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check if token is expired
            if token_data.expires_at < datetime.now(timezone.utc):
                await self._log_auth_attempt(request, "token_expired", False)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check path-specific permissions
            if not await self._check_path_permissions(request.url.path, token_data):
                await self._log_auth_attempt(request, "insufficient_permissions", False, token_data.user_id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this resource"
                )
            
            # Add authentication context to request
            request.state.current_user = token_data
            request.state.session_id = token_data.session_id
            request.state.auth_method = "jwt"
            request.state.is_authenticated = True
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response, token_data)
            
            # Log successful authentication
            duration = time.time() - start_time
            await self._log_auth_attempt(request, "success", True, token_data.user_id, duration)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            await self._log_auth_attempt(request, "error", False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Check for token in cookies (for web sessions)
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            return token_cookie
        
        return None
    
    async def _check_path_permissions(self, path: str, token_data) -> bool:
        """Check if user has required permissions for the path."""
        # Check protected paths
        for protected_path, required_roles in self.protected_paths.items():
            if path.startswith(protected_path):
                # Check if user has any of the required roles
                user_roles = set(token_data.roles)
                required_roles_set = set(required_roles)
                
                if not user_roles.intersection(required_roles_set):
                    return False
        
        # For job application tracking endpoints, check specific permissions
        if path.startswith("/api/v1/contracts"):
            if "analyze_contract" not in token_data.permissions:
                return False
        
        return True
    
    def _add_security_headers(self, response, token_data):
        """Add security headers to response."""
        # Add session information
        response.headers["X-Session-ID"] = token_data.session_id
        response.headers["X-User-ID"] = str(token_data.user_id)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add cache control for authenticated responses
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        
        # Add token expiration info
        expires_in = int((token_data.expires_at - datetime.now(timezone.utc)).total_seconds())
        response.headers["X-Token-Expires-In"] = str(expires_in)
    
    async def _log_auth_attempt(
        self, 
        request: Request, 
        result: str, 
        success: bool, 
        user_id: Optional[int] = None,
        duration: Optional[float] = None
    ):
        """Log authentication attempt."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Determine severity
        if success:
            severity = AuditSeverity.LOW
        elif result in ["invalid_token", "token_expired", "insufficient_permissions"]:
            severity = AuditSeverity.MEDIUM
        else:
            severity = AuditSeverity.HIGH
        
        # Log to audit system
        audit_logger.log_event(
            event_type=AuditEventType.AUTHENTICATION_ATTEMPT,
            action=f"JWT authentication: {result}",
            result="success" if success else "failure",
            severity=severity,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            details={
                "path": request.url.path,
                "method": request.method,
                "result": result,
                "duration_ms": duration * 1000 if duration else None
            }
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


class SessionManagementMiddleware(BaseHTTPMiddleware):
    """Middleware for session management and security."""
    
    def __init__(self, app):
        super().__init__(app)
        self.session_timeout_minutes = 30
        self.active_sessions = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next):
        """Process request with session management."""
        
        # Check if user is authenticated
        if hasattr(request.state, "current_user") and request.state.is_authenticated:
            session_id = request.state.session_id
            user_id = request.state.current_user.user_id
            
            # Update session activity
            self._update_session_activity(session_id, user_id)
            
            # Check session timeout
            if self._is_session_expired(session_id):
                # Log session timeout
                audit_logger.log_event(
                    event_type=AuditEventType.SESSION_TIMEOUT,
                    action="Session expired due to inactivity",
                    user_id=user_id,
                    details={"session_id": session_id}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired due to inactivity"
                )
        
        response = await call_next(request)
        
        # Add session security headers
        if hasattr(request.state, "is_authenticated") and request.state.is_authenticated:
            response.headers["X-Session-Timeout"] = str(self.session_timeout_minutes * 60)
        
        return response
    
    def _update_session_activity(self, session_id: str, user_id: int):
        """Update session last activity time."""
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "last_activity": datetime.now(timezone.utc)
        }
    
    def _is_session_expired(self, session_id: str) -> bool:
        """Check if session has expired."""
        if session_id not in self.active_sessions:
            return True
        
        session_data = self.active_sessions[session_id]
        last_activity = session_data["last_activity"]
        
        # Check if session has been inactive for too long
        inactive_duration = datetime.now(timezone.utc) - last_activity
        return inactive_duration.total_seconds() > (self.session_timeout_minutes * 60)


# FastAPI dependencies for getting current user
async def get_current_user(request: Request):
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "current_user") or not request.state.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.current_user


async def get_current_active_user(request: Request):
    """Get current active user."""
    current_user = await get_current_user(request)
    
    # Additional checks can be added here
    # For example, checking if user account is still active
    
    return current_user


def require_roles(*required_roles: str):
    """Dependency factory for requiring specific roles."""
    
    async def role_checker(request: Request):
        """Check if current user has required roles."""
        current_user = await get_current_user(request)
        
        user_roles = set(current_user.roles)
        required_roles_set = set(required_roles)
        
        if not user_roles.intersection(required_roles_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_permissions(*required_permissions: str):
    """Dependency factory for requiring specific permissions."""
    
    async def permission_checker(request: Request):
        """Check if current user has required permissions."""
        current_user = await get_current_user(request)
        
        user_permissions = set(current_user.permissions)
        required_permissions_set = set(required_permissions)
        
        if not required_permissions_set.issubset(user_permissions):
            missing_permissions = required_permissions_set - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker