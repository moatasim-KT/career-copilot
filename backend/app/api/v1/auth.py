"""
Authentication API endpoints for Career Copilot System.
Handles user authentication, token exchange, and user management.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr, Field

from ...core.logging import get_logger, get_audit_logger
from ...middleware.auth_middleware import (
    get_firebase_auth_manager,
    get_jwt_manager,
    get_current_user,
    require_auth,
    require_roles,
    authenticate_request
)

logger = get_logger(__name__)
audit_logger = get_audit_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models
class TokenExchangeRequest(BaseModel):
    """Request model for Firebase ID token exchange."""
    firebase_token: str = Field(..., description="Firebase ID token")


class TokenResponse(BaseModel):
    """Response model for token operations."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class UserProfileRequest(BaseModel):
    """Request model for user profile updates."""
    display_name: Optional[str] = Field(None, description="User display name")
    skills: Optional[list[str]] = Field(None, description="User skills")
    locations: Optional[list[str]] = Field(None, description="Preferred locations")
    experience_level: Optional[str] = Field(None, description="Experience level")
    job_preferences: Optional[Dict[str, Any]] = Field(None, description="Job preferences")


class UserResponse(BaseModel):
    """Response model for user information."""
    uid: str = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email")
    name: Optional[str] = Field(None, description="User display name")
    email_verified: bool = Field(..., description="Email verification status")
    profile: Optional[Dict[str, Any]] = Field(None, description="User profile data")
    roles: list[str] = Field(default=[], description="User roles")
    created_at: Optional[datetime] = Field(None, description="Account creation date")


class CustomClaimsRequest(BaseModel):
    """Request model for setting custom claims."""
    uid: str = Field(..., description="User ID")
    claims: Dict[str, Any] = Field(..., description="Custom claims to set")


@router.post("/token/exchange", response_model=TokenResponse)
async def exchange_firebase_token(
    request: TokenExchangeRequest,
    http_request: Request
) -> TokenResponse:
    """
    Exchange Firebase ID token for JWT access token.
    
    This endpoint allows clients to exchange a Firebase ID token
    for a JWT access token that can be used for API access.
    """
    try:
        # Verify Firebase ID token
        firebase_manager = get_firebase_auth_manager()
        user_data = await firebase_manager.verify_id_token(request.firebase_token)
        
        # Create JWT access token
        jwt_manager = get_jwt_manager()
        access_token = jwt_manager.create_access_token(user_data)
        
        # Log successful token exchange
        audit_logger.log_security_event(
            event_type="token_exchange_success",
            user_id=user_data["uid"],
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("User-Agent")
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours
            user=user_data
        )
        
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        
        # Log failed token exchange
        audit_logger.log_security_event(
            event_type="token_exchange_failed",
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("User-Agent"),
            details={"error": str(e)},
            severity="warning"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


@router.get("/me", response_model=UserResponse)
@require_auth
async def get_current_user_info(
    current_user: Dict[str, Any] = None
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Returns detailed information about the currently authenticated user,
    including profile data and roles.
    """
    try:
        # Extract user roles from custom claims
        custom_claims = current_user.get("custom_claims", {})
        roles = custom_claims.get("roles", ["user"])
        
        return UserResponse(
            uid=current_user["uid"],
            email=current_user.get("email"),
            name=current_user.get("name"),
            email_verified=current_user.get("email_verified", False),
            profile=custom_claims.get("profile"),
            roles=roles,
            created_at=custom_claims.get("created_at")
        )
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.put("/profile")
@require_auth
async def update_user_profile(
    profile_request: UserProfileRequest,
    current_user: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Update user profile information.
    
    Updates the user's profile data stored in Firebase custom claims.
    This includes skills, preferences, and other career-related information.
    """
    try:
        # Get current custom claims
        firebase_manager = get_firebase_auth_manager()
        current_claims = current_user.get("custom_claims", {})
        
        # Update profile data
        profile_data = current_claims.get("profile", {})
        
        if profile_request.display_name is not None:
            profile_data["display_name"] = profile_request.display_name
        if profile_request.skills is not None:
            profile_data["skills"] = profile_request.skills
        if profile_request.locations is not None:
            profile_data["locations"] = profile_request.locations
        if profile_request.experience_level is not None:
            profile_data["experience_level"] = profile_request.experience_level
        if profile_request.job_preferences is not None:
            profile_data["job_preferences"] = profile_request.job_preferences
        
        # Update last modified timestamp
        profile_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Set updated custom claims
        updated_claims = {**current_claims, "profile": profile_data}
        success = await firebase_manager.set_custom_claims(
            current_user["uid"], 
            updated_claims
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        # Log profile update
        audit_logger.log_business_event(
            event_type="profile_updated",
            user_id=current_user["uid"],
            action="update_profile",
            details={"updated_fields": list(profile_request.dict(exclude_unset=True).keys())}
        )
        
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/logout")
@require_auth
async def logout_user(
    current_user: Dict[str, Any] = None,
    http_request: Request = None
) -> Dict[str, str]:
    """
    Logout user by revoking refresh tokens.
    
    Revokes all Firebase refresh tokens for the user, effectively
    logging them out from all devices.
    """
    try:
        # Revoke Firebase refresh tokens
        firebase_manager = get_firebase_auth_manager()
        success = await firebase_manager.revoke_refresh_tokens(current_user["uid"])
        
        if not success:
            logger.warning(f"Failed to revoke tokens for user: {current_user['uid']}")
        
        # Log logout event
        audit_logger.log_security_event(
            event_type="user_logout",
            user_id=current_user["uid"],
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("User-Agent")
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/admin/claims")
@require_auth
@require_roles("admin")
async def set_user_custom_claims(
    claims_request: CustomClaimsRequest,
    current_user: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Set custom claims for a user (admin only).
    
    Allows administrators to set custom claims for users,
    including roles and permissions.
    """
    try:
        firebase_manager = get_firebase_auth_manager()
        success = await firebase_manager.set_custom_claims(
            claims_request.uid,
            claims_request.claims
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set custom claims"
            )
        
        # Log admin action
        audit_logger.log_security_event(
            event_type="custom_claims_set_by_admin",
            user_id=current_user["uid"],
            details={
                "target_user": claims_request.uid,
                "claims": claims_request.claims
            },
            severity="info"
        )
        
        return {"message": "Custom claims set successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting custom claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set custom claims"
        )


@router.get("/validate")
async def validate_token(
    current_user: Dict[str, Any] = Depends(authenticate_request)
) -> Dict[str, Any]:
    """
    Validate authentication token.
    
    Simple endpoint to validate if the provided token is valid
    and return basic user information.
    """
    return {
        "valid": True,
        "user": {
            "uid": current_user["uid"],
            "email": current_user.get("email"),
            "email_verified": current_user.get("email_verified", False)
        }
    }


@router.get("/status")
async def auth_status() -> Dict[str, Any]:
    """
    Get authentication system status.
    
    Returns information about the authentication system configuration
    and health status.
    """
    try:
        firebase_manager = get_firebase_auth_manager()
        firebase_initialized = firebase_manager.initialized or firebase_manager.initialize()
        
        return {
            "firebase_enabled": firebase_initialized,
            "jwt_enabled": True,
            "auth_required": not get_settings().disable_auth,
            "status": "healthy" if firebase_initialized else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {
            "firebase_enabled": False,
            "jwt_enabled": True,
            "auth_required": not get_settings().disable_auth,
            "status": "error",
            "error": str(e)
        }


# Health check endpoint for authentication system
@router.get("/health")
async def auth_health_check() -> Dict[str, str]:
    """Authentication system health check."""
    try:
        # Test Firebase connection
        firebase_manager = get_firebase_auth_manager()
        if not firebase_manager.initialized:
            firebase_manager.initialize()
        
        # Test JWT manager
        jwt_manager = get_jwt_manager()
        test_token = jwt_manager.create_access_token({
            "uid": "health-check",
            "email": "health@example.com"
        })
        jwt_manager.verify_access_token(test_token)
        
        return {"status": "healthy"}
        
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication system unhealthy"
        )