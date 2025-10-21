"""
Firebase Authentication Service for Career Copilot System.
Handles Firebase Admin SDK operations and user management.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger, get_audit_logger
from ..config.firebase_config import get_firebase_config

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class FirebaseUser(BaseModel):
    """Firebase user model."""
    uid: str
    email: Optional[str] = None
    email_verified: bool = False
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    phone_number: Optional[str] = None
    disabled: bool = False
    custom_claims: Dict[str, Any] = {}
    provider_data: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None


class FirebaseAuthService:
    """Service for Firebase authentication operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_config = get_firebase_config()
        self.app: Optional[firebase_admin.App] = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize Firebase Admin SDK."""
        try:
            if self.initialized:
                return True
            
            # Check if Firebase is enabled
            if not self.settings.firebase_enabled:
                logger.info("Firebase authentication is disabled")
                return False
            
            # Get service account configuration
            service_account_config = self.firebase_config.get_service_account_config()
            if not service_account_config:
                logger.warning("Firebase service account not configured")
                return False
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_config)
            
            # Check if app already exists
            try:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            except ValueError:
                # App doesn't exist, create new one
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            return False
    
    async def verify_id_token(self, id_token: str) -> Optional[FirebaseUser]:
        """Verify Firebase ID token and return user information."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            # Verify the ID token
            decoded_token = firebase_auth.verify_id_token(id_token)
            
            # Get user record for additional information
            user_record = firebase_auth.get_user(decoded_token["uid"])
            
            # Convert to FirebaseUser model
            firebase_user = FirebaseUser(
                uid=user_record.uid,
                email=user_record.email,
                email_verified=user_record.email_verified,
                display_name=user_record.display_name,
                photo_url=user_record.photo_url,
                phone_number=user_record.phone_number,
                disabled=user_record.disabled,
                custom_claims=user_record.custom_claims or {},
                provider_data=[
                    {
                        "uid": provider.uid,
                        "email": provider.email,
                        "display_name": provider.display_name,
                        "photo_url": provider.photo_url,
                        "provider_id": provider.provider_id
                    }
                    for provider in user_record.provider_data
                ],
                created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000) if user_record.user_metadata.creation_timestamp else None,
                last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else None
            )
            
            logger.info(f"Successfully verified Firebase token for user: {firebase_user.uid}")
            return firebase_user
            
        except firebase_auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            return None
        except firebase_auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired Firebase ID token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Firebase ID token: {e}")
            return None
    
    async def get_user(self, uid: str) -> Optional[FirebaseUser]:
        """Get user by UID."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            user_record = firebase_auth.get_user(uid)
            
            firebase_user = FirebaseUser(
                uid=user_record.uid,
                email=user_record.email,
                email_verified=user_record.email_verified,
                display_name=user_record.display_name,
                photo_url=user_record.photo_url,
                phone_number=user_record.phone_number,
                disabled=user_record.disabled,
                custom_claims=user_record.custom_claims or {},
                provider_data=[
                    {
                        "uid": provider.uid,
                        "email": provider.email,
                        "display_name": provider.display_name,
                        "photo_url": provider.photo_url,
                        "provider_id": provider.provider_id
                    }
                    for provider in user_record.provider_data
                ],
                created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000) if user_record.user_metadata.creation_timestamp else None,
                last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else None
            )
            
            return firebase_user
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Error getting user {uid}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[FirebaseUser]:
        """Get user by email."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            user_record = firebase_auth.get_user_by_email(email)
            
            firebase_user = FirebaseUser(
                uid=user_record.uid,
                email=user_record.email,
                email_verified=user_record.email_verified,
                display_name=user_record.display_name,
                photo_url=user_record.photo_url,
                phone_number=user_record.phone_number,
                disabled=user_record.disabled,
                custom_claims=user_record.custom_claims or {},
                provider_data=[
                    {
                        "uid": provider.uid,
                        "email": provider.email,
                        "display_name": provider.display_name,
                        "photo_url": provider.photo_url,
                        "provider_id": provider.provider_id
                    }
                    for provider in user_record.provider_data
                ],
                created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000) if user_record.user_metadata.creation_timestamp else None,
                last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else None
            )
            
            return firebase_user
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found with email: {email}")
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def create_user(
        self,
        uid: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: bool = False,
        phone_number: Optional[str] = None,
        disabled: bool = False
    ) -> Optional[FirebaseUser]:
        """Create a new user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            # Prepare user creation arguments
            user_args = {}
            if uid:
                user_args["uid"] = uid
            if email:
                user_args["email"] = email
            if password:
                user_args["password"] = password
            if display_name:
                user_args["display_name"] = display_name
            if photo_url:
                user_args["photo_url"] = photo_url
            if phone_number:
                user_args["phone_number"] = phone_number
            
            user_args["email_verified"] = email_verified
            user_args["disabled"] = disabled
            
            # Create user
            user_record = firebase_auth.create_user(**user_args)
            
            # Set default custom claims
            default_claims = {
                "roles": ["user"],
                "created_at": datetime.utcnow().isoformat(),
                "profile": {
                    "skills": [],
                    "locations": [],
                    "experience_level": "entry",
                    "job_preferences": {}
                }
            }
            
            firebase_auth.set_custom_user_claims(user_record.uid, default_claims)
            
            # Log user creation
            audit_logger.log_security_event(
                event_type="user_created",
                user_id=user_record.uid,
                details={
                    "email": email,
                    "display_name": display_name,
                    "email_verified": email_verified
                }
            )
            
            # Return created user
            return await self.get_user(user_record.uid)
            
        except firebase_auth.EmailAlreadyExistsError:
            logger.warning(f"User with email {email} already exists")
            return None
        except firebase_auth.UidAlreadyExistsError:
            logger.warning(f"User with UID {uid} already exists")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def update_user(
        self,
        uid: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: Optional[bool] = None,
        phone_number: Optional[str] = None,
        disabled: Optional[bool] = None
    ) -> Optional[FirebaseUser]:
        """Update user information."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            # Prepare update arguments
            update_args = {}
            if email is not None:
                update_args["email"] = email
            if password is not None:
                update_args["password"] = password
            if display_name is not None:
                update_args["display_name"] = display_name
            if photo_url is not None:
                update_args["photo_url"] = photo_url
            if email_verified is not None:
                update_args["email_verified"] = email_verified
            if phone_number is not None:
                update_args["phone_number"] = phone_number
            if disabled is not None:
                update_args["disabled"] = disabled
            
            # Update user
            firebase_auth.update_user(uid, **update_args)
            
            # Log user update
            audit_logger.log_security_event(
                event_type="user_updated",
                user_id=uid,
                details={"updated_fields": list(update_args.keys())}
            )
            
            # Return updated user
            return await self.get_user(uid)
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found for update: {uid}")
            return None
        except Exception as e:
            logger.error(f"Error updating user {uid}: {e}")
            return None
    
    async def delete_user(self, uid: str) -> bool:
        """Delete a user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            firebase_auth.delete_user(uid)
            
            # Log user deletion
            audit_logger.log_security_event(
                event_type="user_deleted",
                user_id=uid,
                severity="warning"
            )
            
            logger.info(f"User deleted: {uid}")
            return True
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found for deletion: {uid}")
            return False
        except Exception as e:
            logger.error(f"Error deleting user {uid}: {e}")
            return False
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for a user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            firebase_auth.set_custom_user_claims(uid, claims)
            
            # Log custom claims update
            audit_logger.log_security_event(
                event_type="custom_claims_updated",
                user_id=uid,
                details={"claims": claims}
            )
            
            logger.info(f"Custom claims set for user {uid}")
            return True
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found for custom claims: {uid}")
            return False
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
            
            # Log token revocation
            audit_logger.log_security_event(
                event_type="refresh_tokens_revoked",
                user_id=uid,
                severity="warning"
            )
            
            logger.info(f"Refresh tokens revoked for user: {uid}")
            return True
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found for token revocation: {uid}")
            return False
        except Exception as e:
            logger.error(f"Error revoking tokens for user {uid}: {e}")
            return False
    
    async def create_custom_token(self, uid: str, additional_claims: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a custom token for a user."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return None
            
            custom_token = firebase_auth.create_custom_token(uid, additional_claims)
            
            # Log custom token creation
            audit_logger.log_security_event(
                event_type="custom_token_created",
                user_id=uid,
                details={"additional_claims": additional_claims or {}}
            )
            
            return custom_token.decode('utf-8')
            
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User not found for custom token: {uid}")
            return None
        except Exception as e:
            logger.error(f"Error creating custom token for user {uid}: {e}")
            return None
    
    async def list_users(self, page_token: Optional[str] = None, max_results: int = 1000) -> Dict[str, Any]:
        """List users with pagination."""
        try:
            if not self.initialized:
                if not self.initialize():
                    return {"users": [], "next_page_token": None}
            
            # List users
            page = firebase_auth.list_users(page_token=page_token, max_results=max_results)
            
            users = []
            for user_record in page.users:
                firebase_user = FirebaseUser(
                    uid=user_record.uid,
                    email=user_record.email,
                    email_verified=user_record.email_verified,
                    display_name=user_record.display_name,
                    photo_url=user_record.photo_url,
                    phone_number=user_record.phone_number,
                    disabled=user_record.disabled,
                    custom_claims=user_record.custom_claims or {},
                    provider_data=[
                        {
                            "uid": provider.uid,
                            "email": provider.email,
                            "display_name": provider.display_name,
                            "photo_url": provider.photo_url,
                            "provider_id": provider.provider_id
                        }
                        for provider in user_record.provider_data
                    ],
                    created_at=datetime.fromtimestamp(user_record.user_metadata.creation_timestamp / 1000) if user_record.user_metadata.creation_timestamp else None,
                    last_sign_in=datetime.fromtimestamp(user_record.user_metadata.last_sign_in_timestamp / 1000) if user_record.user_metadata.last_sign_in_timestamp else None
                )
                users.append(firebase_user.dict())
            
            return {
                "users": users,
                "next_page_token": page.next_page_token
            }
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return {"users": [], "next_page_token": None}
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get Firebase authentication status."""
        return {
            "initialized": self.initialized,
            "firebase_enabled": self.settings.firebase_enabled,
            "project_id": self.firebase_config.project_id,
            "service_account_configured": bool(self.firebase_config.get_service_account_config())
        }


# Global service instance
_firebase_auth_service: Optional[FirebaseAuthService] = None


def get_firebase_auth_service() -> FirebaseAuthService:
    """Get Firebase authentication service instance."""
    global _firebase_auth_service
    if _firebase_auth_service is None:
        _firebase_auth_service = FirebaseAuthService()
    return _firebase_auth_service