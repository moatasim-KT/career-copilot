"""
Firebase Authentication Middleware for Career Copilot.
Handles Firebase ID token validation and user authentication.
"""

from typing import Callable, Optional
import time

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger
from ..services.firebase_auth_service import get_firebase_auth_service, FirebaseUser

logger = get_logger(__name__)


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle Firebase authentication.
    Validates Firebase ID tokens and sets user context.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.firebase_service = get_firebase_auth_service()
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/api/v1/health",
            "/api/v1/connection-test",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through Firebase authentication."""
        start_time = time.time()
        
        try:
            # Skip authentication for public paths
            if self._is_public_path(request.url.path):
                return await call_next(request)
            
            # Extract Firebase ID token
            firebase_token = self._extract_firebase_token(request)
            
            if firebase_token:
                # Verify Firebase token
                firebase_user = await self.firebase_service.verify_id_token(firebase_token)
                
                if firebase_user:
                    # Set Firebase user in request state
                    request.state.firebase_user = firebase_user
                    request.state.user_id = firebase_user.uid
                    request.state.authenticated_via = "firebase"
                    
                    logger.debug(f"Firebase authentication successful for user: {firebase_user.uid}")
                else:
                    # Invalid Firebase token
                    logger.warning("Invalid Firebase ID token provided")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Firebase authentication token",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            else:
                # No Firebase token provided - let other auth middleware handle it
                pass
            
            # Continue to next middleware/endpoint
            response = await call_next(request)
            
            # Log successful request
            duration = time.time() - start_time
            if hasattr(request.state, 'firebase_user'):
                logger.info(
                    f"Firebase authenticated request completed",
                    extra={
                        "user_id": request.state.firebase_user.uid,
                        "path": request.url.path,
                        "method": request.method,
                        "duration_ms": duration * 1000,
                        "status_code": response.status_code
                    }
                )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in Firebase auth middleware: {e}")
            # Don't block request for Firebase errors in development
            return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public and doesn't require authentication."""
        # Exact match
        if path in self.public_paths:
            return True
        
        # Pattern matching for API documentation paths
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True
        
        return False
    
    def _extract_firebase_token(self, request: Request) -> Optional[str]:
        """
        Extract Firebase ID token from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Firebase ID token if found, None otherwise
        """
        # Check Authorization header for Firebase token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Simple heuristic to identify Firebase tokens (they're typically longer)
            # Firebase ID tokens are JWT tokens that are usually 800+ characters
            if len(token) > 500:
                return token
        
        # Check custom Firebase header
        firebase_token = request.headers.get("x-firebase-token")
        if firebase_token:
            return firebase_token
        
        return None


def get_firebase_user(request: Request) -> Optional[FirebaseUser]:
    """
    Get Firebase user from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        FirebaseUser if authenticated via Firebase, None otherwise
    """
    return getattr(request.state, 'firebase_user', None)


def require_firebase_auth(request: Request) -> FirebaseUser:
    """
    Require Firebase authentication for an endpoint.
    
    Args:
        request: FastAPI request object
        
    Returns:
        FirebaseUser object
        
    Raises:
        HTTPException: If user is not authenticated via Firebase
    """
    firebase_user = get_firebase_user(request)
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return firebase_user