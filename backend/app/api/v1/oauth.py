"""OAuth authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.base_client import OAuthError
from ...core.database import get_db
from ...core.config import get_settings
from ...services.oauth_service import get_oauth_service
from ...dependencies import get_current_user
from ...models.user import User
from ...schemas.oauth import OAuthLoginResponse, OAuthStatusResponse, OAuthDisconnectRequest, OAuthDisconnectResponse
from ...schemas.password import SetPasswordRequest, SetPasswordResponse
from ...core.security import get_password_hash
from typing import Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["oauth"])


@router.get("/api/v1/auth/oauth/{provider}/login")
async def oauth_login(provider: str, redirect_url: Optional[str] = Query(None)):
    """Initiate OAuth login flow for specified provider"""
    if not settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is not enabled")
    
    if provider not in ['google', 'linkedin', 'github']:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")
    
    try:
        # Get the appropriate redirect URI based on provider
        if provider == 'google':
            redirect_uri = settings.google_redirect_uri
        elif provider == 'linkedin':
            redirect_uri = settings.linkedin_redirect_uri
        elif provider == 'github':
            redirect_uri = settings.github_redirect_uri
        
        # Generate authorization URL
        if provider == 'google':
            auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={settings.google_client_id}&redirect_uri={redirect_uri}&scope=openid email profile&response_type=code&access_type=offline"
        elif provider == 'linkedin':
            auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={settings.linkedin_client_id}&redirect_uri={redirect_uri}&scope=r_liteprofile r_emailaddress"
        elif provider == 'github':
            auth_url = f"https://github.com/login/oauth/authorize?client_id={settings.github_client_id}&redirect_uri={redirect_uri}&scope=user:email"
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"OAuth login initiation failed for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth login")


@router.get("/api/v1/auth/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from provider"""
    if not settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is not enabled")
    
    if error:
        logger.error(f"OAuth error from {provider}: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    try:
        # Handle the OAuth callback
        oauth_service_instance = get_oauth_service()
        oauth_data = await oauth_service_instance.oauth_login(provider, code, state)
        
        # Create or link user account
        user, access_token = oauth_service_instance.create_or_link_user(oauth_data, db)
        
        logger.info(f"OAuth login successful for {provider} user: {user.email}")
        
        # In a real application, you might want to redirect to the frontend with the token
        # For now, return the token directly
        return OAuthLoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            email=user.email,
            oauth_provider=user.oauth_provider,
            profile_picture_url=user.profile_picture_url
        )
        
    except OAuthError as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")
    except ValueError as e:
        logger.error(f"OAuth user creation error for {provider}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected OAuth callback error for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")


@router.post("/api/v1/auth/oauth/disconnect")
async def disconnect_oauth(
    request: OAuthDisconnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect OAuth account from current user"""
    if not settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is not enabled")
    
    if request.provider not in ['google', 'linkedin', 'github']:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {request.provider}")
    
    try:
        oauth_service_instance = get_oauth_service()
        success = oauth_service_instance.disconnect_oauth_account(current_user.id, request.provider, db)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"No {request.provider} account linked to this user")
        
        logger.info(f"OAuth account disconnected: {request.provider} for user {current_user.id}")
        return OAuthDisconnectResponse(message=f"{request.provider.title()} account disconnected successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth disconnect error for {request.provider}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to disconnect OAuth account")


@router.get("/api/v1/auth/oauth/status")
async def oauth_status(current_user: User = Depends(get_current_user)) -> OAuthStatusResponse:
    """Get OAuth connection status for current user"""
    return OAuthStatusResponse(
        oauth_enabled=settings.oauth_enabled,
        connected_provider=current_user.oauth_provider,
        oauth_id=current_user.oauth_id,
        profile_picture_url=current_user.profile_picture_url,
        available_providers=['google', 'linkedin', 'github'] if settings.oauth_enabled else []
    )


@router.post("/api/v1/auth/oauth/set-password")
async def set_password_for_oauth_user(
    request: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SetPasswordResponse:
    """Set password for OAuth user to enable account disconnection"""
    if not settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is not enabled")
    
    # Validate passwords match
    try:
        request.validate_passwords_match()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user is OAuth user
    if not current_user.oauth_provider:
        raise HTTPException(status_code=400, detail="This endpoint is only for OAuth users")
    
    # Check if user already has a password (not a placeholder)
    if not current_user.hashed_password.startswith('oauth_'):
        raise HTTPException(status_code=400, detail="User already has a password set")
    
    try:
        # Set the password
        current_user.hashed_password = get_password_hash(request.password)
        current_user.updated_at = current_user.updated_at
        db.commit()
        
        logger.info(f"Password set for OAuth user {current_user.id}")
        return SetPasswordResponse(message="Password set successfully. You can now disconnect your OAuth account if desired.")
        
    except Exception as e:
        logger.error(f"Failed to set password for OAuth user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set password")