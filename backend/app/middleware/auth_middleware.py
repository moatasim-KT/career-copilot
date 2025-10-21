"""
Authentication middleware for Career Copilot System.
Handles Firebase ID token validation and JWT token processing.
"""

import json
import jwt
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import get_settings
from ..core.logging import get_logger, get_audit_logger
from ..config.firebase_config import get_firebase_config

logger = get_logger(__name__)
audit_logger = get_audit_logger()
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class AuthorizationError(Exception):
    """Custom authorization error."""
    pass


class FirebaseAuthManager:
    """Manages Firebase authentication and token validation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_config = get_firebase_config()
        self.app = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize Firebase Admin SDK."""
        try:
            if self.initialized:
                return True
                
            # Get service account configuration
            service_account_config = self.firebase_config.get_service_account_config()
            if not service_account_config:
                logger.warning("Firebase service account not configured - authentication disabled")
                return False
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_config)
            self.app = firebase_admin.initialize_app(cred)
            
            self.initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            return False
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user claims."""
        try:
            if not self.initialized:
                if not self.initialize():
                    raise AuthenticationError("Firebase not initialized")
            
            # Verify the ID token
            decoded_token = firebase_auth.verify_id_token(id_token)
            
            # Extract user information
            user_info = {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "firebase_claims": decoded_token
            }
            
            # Get custom claims
            user_record = firebase_auth.get_user(decoded_token["uid"])
            if user_record.custom_claims:
                user_info["custom_claims"] = user_record.custom_claims
            
            logger.info(f"Successfully verified Firebase token for user: {user_info['uid']}")
            return user_info
            
        except firebase_auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            raise AuthenticationError("Invalid authentication token")
        except firebase_auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase ID token: {e}")
            raise AuthenticationError("Authentication token expired")
        except Exception as e:
            logger.error(f"Error verifying Firebase ID token: {e}")
            raise AuthenticationError("Authentication verification failed")
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for a user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            firebase_auth.set_custom_user_claims(uid, claims)
            logger.info(f"Set custom claims for user {uid}: {claims}")
            
            # Log audit event
            audit_logger.log_security_event(
                event_type="custom_claims_updated",
                user_id=uid,
                details={"claims": claims}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting custom claims for user {uid}: {e}")
            return False
    
    async def revoke_refresh_tokens(self, uid: str) -> bool:
        """Revoke all refresh tokens for a user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            firebase_auth.revoke_refresh_tokens(uid)
            logger.info(f"Revoked refresh tokens for user: {uid}")
            
            # Log audit event
            audit_logger.log_security_event(
                event_type="refresh_tokens_revoked",
                user_id=uid,
                severity="warning"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking refresh tokens for user {uid}: {e}")
            return False


class JWTManager:
    """Manages JWT token creation and validation for internal API access."""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.jwt_secret_key.get_secret_value()
        self.algorithm = self.settings.jwt_algorithm
        self.expiration_hours = self.settings.jwt_expiration_hours
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token for authenticated user."""
        try:
            # Prepare token payload
            payload = {
                "sub": user_data["uid"],
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "email_verified": user_data.get("email_verified", False),
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
                "iss": "career-copilot-system",
                "aud": "career-copilot-api"
            }
            
            # Add custom claims if present
            if "custom_claims" in user_data:
                payload["custom_claims"] = user_data["custom_claims"]
            
            # Create JWT token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Created JWT access token for user: {user_data['uid']}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT access token: {e}")
            raise AuthenticationError("Failed to create access token")
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT access token and return user data."""
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="career-copilot-api",
                issuer="career-copilot-system"
            )
            
            # Extract user information
            user_data = {
                "uid": payload["sub"],
                "email": payload.get("email"),
                "name": payload.get("name"),
                "email_verified": payload.get("email_verified", False),
                "custom_claims": payload.get("custom_claims", {})
            }
            
            return user_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise AuthenticationError("Access token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise AuthenticationError("Invalid access token")
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            raise AuthenticationError("Token verification failed")


# Global instances
_firebase_auth_manager: Optional[FirebaseAuthManager] = None
_jwt_manager: Optional[JWTManager] = None


def get_firebase_auth_manager() -> FirebaseAuthManager:
    """Get Firebase authentication manager instance."""
    global _firebase_auth_manager
    if _firebase_auth_manager is None:
        _firebase_auth_manager = FirebaseAuthManager()
    return _firebase_auth_manager


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract and validate user from request authentication."""
    settings = get_settings()
    
    # Skip authentication if disabled
    if settings.disable_auth:
        return {
            "uid": "test-user",
            "email": "test@example.com",
            "name": "Test User",
            "email_verified": True,
            "custom_claims": {"roles": ["user"]}
        }
    
    try:
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        # Extract token
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        
        # Try JWT token first (for API access)
        try:
            jwt_manager = get_jwt_manager()
            user_data = jwt_manager.verify_access_token(token)
            return user_data
        except AuthenticationError:
            pass  # Try Firebase token
        
        # Try Firebase ID token
        firebase_manager = get_firebase_auth_manager()
        user_data = await firebase_manager.verify_id_token(token)
        
        # Create JWT token for future API calls
        jwt_manager = get_jwt_manager()
        access_token = jwt_manager.create_access_token(user_data)
        
        # Add access token to user data for client
        user_data["access_token"] = access_token
        
        return user_data
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {e}")
        return None


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for endpoint."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find request object in arguments
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        # Get current user
        user = await get_current_user(request)
        if not user:
            audit_logger.log_security_event(
                event_type="unauthorized_access_attempt",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                details={"endpoint": request.url.path},
                severity="warning"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user to kwargs
        kwargs["current_user"] = user
        
        # Log successful authentication
        audit_logger.log_security_event(
            event_type="authenticated_access",
            user_id=user["uid"],
            ip_address=request.client.host if request.client else None,
            details={"endpoint": request.url.path}
        )
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_roles(*required_roles: str) -> Callable:
    """Decorator to require specific roles for endpoint access."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user (should be set by require_auth)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check roles
            user_roles = current_user.get("custom_claims", {}).get("roles", [])
            if not any(role in user_roles for role in required_roles):
                audit_logger.log_security_event(
                    event_type="insufficient_permissions",
                    user_id=current_user["uid"],
                    details={
                        "required_roles": list(required_roles),
                        "user_roles": user_roles
                    },
                    severity="warning"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_verified_email(func: Callable) -> Callable:
    """Decorator to require verified email for endpoint access."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current user (should be set by require_auth)
        current_user = kwargs.get("current_user")
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check email verification
        if not current_user.get("email_verified", False):
            audit_logger.log_security_event(
                event_type="unverified_email_access_attempt",
                user_id=current_user["uid"],
                details={"email": current_user.get("email")},
                severity="warning"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


async def authenticate_request(request: Request) -> Dict[str, Any]:
    """Authenticate request and return user data or raise HTTPException."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


class AuthMiddleware:
    """FastAPI middleware for authentication."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add authentication context to request
            request = Request(scope, receive)
            
            # Skip authentication for health checks and public endpoints
            path = request.url.path
            if path in ["/health", "/", "/docs", "/openapi.json", "/redoc"]:
                await self.app(scope, receive, send)
                return
            
            # Get user if authenticated
            user = await get_current_user(request)
            if user:
                # Add user to request state
                scope["state"] = scope.get("state", {})
                scope["state"]["user"] = user
        
        await self.app(scope, receive, send)