"""
Firebase Authentication API endpoints.
Provides Firebase Auth integration with JWT token management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ...core.auth import get_current_user_optional
from ...core.iam_roles import get_iam_manager, Role, Permission
from ...services.oauth_service import get_oauth_service, FirebaseUser
from ...services.auth_service import get_authentication_system
from ...middleware.auth_middleware import get_current_user, require_auth
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Firebase Authentication"])


class FirebaseTokenRequest(BaseModel):
    """Request model for Firebase token verification."""
    id_token: str


class FirebaseTokenResponse(BaseModel):
    """Response model for Firebase token verification."""
    valid: bool
    user: Optional[dict] = None
    jwt_token: Optional[str] = None
    message: str


class CustomTokenRequest(BaseModel):
    """Request model for custom token creation."""
    uid: str
    additional_claims: Optional[dict] = None


class CustomTokenResponse(BaseModel):
    """Response model for custom token creation."""
    custom_token: str
    expires_in: int = 3600


@router.post("/firebase/verify-token", response_model=FirebaseTokenResponse)
async def verify_firebase_token(
    request: FirebaseTokenRequest,
    oauth_service = Depends(get_oauth_service)
):
    """
    Verify Firebase ID token and optionally create JWT token.
    
    This endpoint allows clients to verify their Firebase ID tokens
    and receive a JWT token for API access.
    """
    try:
        # Verify Firebase token
        firebase_user = await oauth_service.verify_firebase_token(request.id_token)
        
        if not firebase_user:
            return FirebaseTokenResponse(
                valid=False,
                message="Invalid Firebase ID token"
            )
        
        # Create JWT token for API access
        jwt_token = None
        try:
            # Create or get user in local database
            # This would typically involve syncing with your user database
            jwt_token = await oauth_service.create_access_token(
                data={"sub": firebase_user.uid, "email": firebase_user.email}
            )
        except Exception as e:
            logger.warning(f"Failed to create JWT token: {e}")
        
        return FirebaseTokenResponse(
            valid=True,
            user={
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "email_verified": firebase_user.email_verified,
                "display_name": firebase_user.display_name,
                "photo_url": firebase_user.photo_url
            },
            jwt_token=jwt_token,
            message="Firebase token verified successfully"
        )
        
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying Firebase token"
        )


@router.post("/firebase/create-custom-token", response_model=CustomTokenResponse)
async def create_custom_token(
    request: CustomTokenRequest,
    current_user = Depends(get_current_user_optional),
    oauth_service = Depends(get_oauth_service),
    iam_manager = Depends(get_iam_manager)
):
    """
    Create a custom Firebase token.
    
    This endpoint allows authorized users to create custom Firebase tokens
    for other users. Requires admin permissions.
    """
    # Check permissions
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if user has admin role (simplified check)
    user_roles = [Role.ADMIN]  # This should come from user's actual roles
    if not iam_manager.has_permission(user_roles, Permission.ADMIN_API_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        custom_token = await oauth_service.create_custom_token(
            request.uid,
            request.additional_claims
        )
        
        if not custom_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create custom token"
            )
        
        return CustomTokenResponse(
            custom_token=custom_token,
            expires_in=3600
        )
        
    except Exception as e:
        logger.error(f"Error creating custom token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating custom token"
        )


@router.get("/firebase/user/{uid}")
async def get_firebase_user_info(
    uid: str,
    current_user = Depends(get_current_user_optional),
    oauth_service = Depends(get_oauth_service)
):
    """
    Get Firebase user information by UID.
    
    Requires authentication and appropriate permissions.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        firebase_user = await oauth_service.get_firebase_user(uid)
        
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Firebase user not found"
            )
        
        return {
            "uid": firebase_user.uid,
            "email": firebase_user.email,
            "email_verified": firebase_user.email_verified,
            "display_name": firebase_user.display_name,
            "photo_url": firebase_user.photo_url,
            "custom_claims": firebase_user.custom_claims
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Firebase user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )


@router.post("/firebase/set-claims/{uid}")
async def set_user_claims(
    uid: str,
    claims: dict,
    current_user = Depends(get_current_user_optional),
    oauth_service = Depends(get_oauth_service),
    iam_manager = Depends(get_iam_manager)
):
    """
    Set custom claims for a Firebase user.
    
    Requires admin permissions.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check admin permissions
    user_roles = [Role.ADMIN]  # This should come from user's actual roles
    if not iam_manager.has_permission(user_roles, Permission.MANAGE_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await oauth_service.set_firebase_custom_claims(uid, claims)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set custom claims"
            )
        
        return {"message": "Custom claims set successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting custom claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting custom claims"
        )


@router.post("/firebase/revoke-tokens/{uid}")
async def revoke_user_tokens(
    uid: str,
    current_user = Depends(get_current_user_optional),
    oauth_service = Depends(get_oauth_service),
    iam_manager = Depends(get_iam_manager)
):
    """
    Revoke all refresh tokens for a Firebase user.
    
    Requires admin permissions.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check admin permissions
    user_roles = [Role.ADMIN]  # This should come from user's actual roles
    if not iam_manager.has_permission(user_roles, Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await oauth_service.revoke_firebase_tokens(uid)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke tokens"
            )
        
        return {"message": "Refresh tokens revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error revoking tokens"
        )


@router.get("/firebase/me")
async def get_current_firebase_user(
    request: Request,
    current_user = Depends(get_current_user)
):
    """
    Get current Firebase user information.
    
    Requires Firebase authentication.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "uid": current_user.get("uid"),
        "email": current_user.get("email"),
        "email_verified": current_user.get("email_verified", False),
        "display_name": current_user.get("name"),
        "photo_url": current_user.get("picture"),
        "provider_id": "firebase",
        "custom_claims": current_user.get("custom_claims", {}),
        "authenticated_via": current_user.get("auth_method", "firebase")
    }