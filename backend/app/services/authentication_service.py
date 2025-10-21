"""
Authentication Service for Career Copilot System.
Handles JWT token creation, validation, and user session management.
"""

import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.config import get_settings
from ..core.logging import get_logger, get_audit_logger
from .firebase_auth_service import get_firebase_auth_service, FirebaseUser

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class AuthenticationService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_service = get_firebase_auth_service()
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
                "name": user_data.get("display_name") or user_data.get("name"),
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
            raise Exception("Failed to create access token")
    
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
            raise Exception("Access token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise Exception("Invalid access token")
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            raise Exception("Token verification failed")
    
    async def authenticate_with_firebase_token(self, firebase_token: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with Firebase ID token and return user data with JWT token."""
        try:
            # Verify Firebase ID token
            firebase_user = await self.firebase_service.verify_id_token(firebase_token)
            if not firebase_user:
                return None
            
            # Convert FirebaseUser to dict
            user_data = {
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name,
                "email_verified": firebase_user.email_verified,
                "custom_claims": firebase_user.custom_claims,
                "photo_url": firebase_user.photo_url,
                "phone_number": firebase_user.phone_number
            }
            
            # Create JWT access token
            access_token = self.create_access_token(user_data)
            
            # Add access token to user data
            user_data["access_token"] = access_token
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error authenticating with Firebase token: {e}")
            return None
    
    async def refresh_token(self, current_token: str) -> Optional[str]:
        """Refresh JWT access token."""
        try:
            # Verify current token (even if expired, we want to check if it's valid)
            try:
                user_data = self.verify_access_token(current_token)
            except Exception:
                # Token might be expired, try to decode without verification
                payload = jwt.decode(current_token, options={"verify_signature": False})
                user_data = {
                    "uid": payload["sub"],
                    "email": payload.get("email"),
                    "name": payload.get("name"),
                    "email_verified": payload.get("email_verified", False),
                    "custom_claims": payload.get("custom_claims", {})
                }
            
            # Get fresh user data from Firebase
            firebase_user = await self.firebase_service.get_user(user_data["uid"])
            if not firebase_user:
                return None
            
            # Create new access token with fresh data
            fresh_user_data = {
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name,
                "email_verified": firebase_user.email_verified,
                "custom_claims": firebase_user.custom_claims
            }
            
            new_token = self.create_access_token(fresh_user_data)
            
            logger.info(f"Refreshed JWT token for user: {user_data['uid']}")
            return new_token
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    async def validate_user_session(self, user_id: str) -> bool:
        """Validate if user session is still valid."""
        try:
            # Check if user still exists and is not disabled
            firebase_user = await self.firebase_service.get_user(user_id)
            if not firebase_user or firebase_user.disabled:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating user session: {e}")
            return False
    
    async def revoke_user_tokens(self, user_id: str) -> bool:
        """Revoke all tokens for a user."""
        try:
            # Revoke Firebase refresh tokens
            success = await self.firebase_service.revoke_refresh_tokens(user_id)
            
            # Log token revocation
            audit_logger.log_security_event(
                event_type="user_tokens_revoked",
                user_id=user_id,
                severity="warning"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication service status."""
        firebase_status = self.firebase_service.get_auth_status()
        
        return {
            "jwt_enabled": True,
            "firebase_status": firebase_status,
            "token_expiration_hours": self.expiration_hours,
            "algorithm": self.algorithm
        }


# Global service instance
_authentication_service: Optional[AuthenticationService] = None


def get_authentication_service() -> AuthenticationService:
    """Get authentication service instance."""
    global _authentication_service
    if _authentication_service is None:
        _authentication_service = AuthenticationService()
    return _authentication_service