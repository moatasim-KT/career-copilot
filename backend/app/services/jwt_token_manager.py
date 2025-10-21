"""
Enhanced JWT Token Management Service
Provides comprehensive JWT token management with security features.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity
from ..models.database_models import User, UserSession, SecurityEvent

logger = get_logger(__name__)
settings = get_settings()


class TokenType(str):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    RESET = "reset"
    VERIFICATION = "verification"


class TokenClaims(BaseModel):
    """JWT token claims."""
    sub: str  # Subject (user ID)
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    security_level: str
    session_id: str
    token_type: str
    mfa_verified: bool = False
    iat: int  # Issued at
    exp: int  # Expires at
    iss: str = "career-copilot"  # Issuer
    aud: str = "career-copilot-api"  # Audience
    jti: str  # JWT ID (unique token identifier)


class TokenValidationResult(BaseModel):
    """Token validation result."""
    is_valid: bool
    claims: Optional[TokenClaims] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class JWTTokenManager:
    """Enhanced JWT token management with security features."""
    
    def __init__(self):
        """Initialize JWT token manager."""
        self.secret_key = settings.jwt_secret_key.get_secret_value()
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expiration_hours * 60
        self.refresh_token_expire_days = 30
        
        # Token blacklist (in production, use Redis)
        self.blacklisted_tokens: Set[str] = set()
        self.blacklisted_sessions: Set[str] = set()
        
        logger.info("JWT Token Manager initialized")
    
    async def create_access_token(
        self,
        user: User,
        session_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token with comprehensive claims.
        
        Args:
            user: User object
            session_id: Session identifier
            additional_claims: Additional claims to include
            
        Returns:
            JWT access token string
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=self.access_token_expire_minutes)
            
            # Create unique token ID
            jti = str(uuid4())
            
            # Build claims
            claims = TokenClaims(
                sub=str(user.id),
                username=user.username,
                email=user.email,
                roles=user.roles or [],
                permissions=user.permissions or [],
                security_level=user.security_level,
                session_id=session_id,
                token_type=TokenType.ACCESS,
                mfa_verified=user.mfa_enabled,
                iat=int(now.timestamp()),
                exp=int(expires_at.timestamp()),
                jti=jti
            )
            
            # Add additional claims if provided
            claims_dict = claims.dict()
            if additional_claims:
                claims_dict.update(additional_claims)
            
            # Create JWT token
            token = jwt.encode(claims_dict, self.secret_key, algorithm=self.algorithm)
            
            # Log token creation
            audit_logger.log_event(
                event_type=AuditEventType.TOKEN_REFRESHED,
                action=f"Access token created for user {user.username}",
                user_id=str(user.id),
                session_id=session_id,
                details={
                    "token_type": TokenType.ACCESS,
                    "expires_at": expires_at.isoformat(),
                    "jti": jti
                }
            )
            
            logger.debug(f"Access token created for user {user.username}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    async def create_refresh_token(
        self,
        user: User,
        session_id: str,
        token_family: Optional[str] = None
    ) -> str:
        """
        Create JWT refresh token with rotation support.
        
        Args:
            user: User object
            session_id: Session identifier
            token_family: Token family for rotation
            
        Returns:
            JWT refresh token string
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=self.refresh_token_expire_days)
            
            # Create unique token ID and family
            jti = str(uuid4())
            if not token_family:
                token_family = str(uuid4())
            
            # Build claims
            claims = {
                "sub": str(user.id),
                "session_id": session_id,
                "token_family": token_family,
                "token_type": TokenType.REFRESH,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "iss": "career-copilot",
                "aud": "career-copilot-api",
                "jti": jti
            }
            
            # Create JWT token
            token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
            
            # Store session information
            await self._store_session(user.id, session_id, token_family, expires_at)
            
            # Log token creation
            audit_logger.log_event(
                event_type=AuditEventType.TOKEN_REFRESHED,
                action=f"Refresh token created for user {user.username}",
                user_id=str(user.id),
                session_id=session_id,
                details={
                    "token_type": TokenType.REFRESH,
                    "token_family": token_family,
                    "expires_at": expires_at.isoformat(),
                    "jti": jti
                }
            )
            
            logger.debug(f"Refresh token created for user {user.username}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create refresh token"
            )
    
    async def validate_token(self, token: str) -> TokenValidationResult:
        """
        Validate JWT token with comprehensive security checks.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenValidationResult with validation details
        """
        try:
            # Check if token is blacklisted
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if token_hash in self.blacklisted_tokens:
                return TokenValidationResult(
                    is_valid=False,
                    error="Token is blacklisted"
                )
            
            # Decode and validate token
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_iat": True,
                        "verify_aud": True,
                        "verify_iss": True
                    }
                )
            except jwt.ExpiredSignatureError:
                return TokenValidationResult(
                    is_valid=False,
                    error="Token has expired"
                )
            except jwt.InvalidTokenError as e:
                return TokenValidationResult(
                    is_valid=False,
                    error=f"Invalid token: {str(e)}"
                )
            
            # Extract claims
            try:
                if payload.get("token_type") == TokenType.ACCESS:
                    claims = TokenClaims(**payload)
                else:
                    # For refresh tokens, create minimal claims
                    claims = TokenClaims(
                        sub=payload["sub"],
                        username="",
                        email="",
                        roles=[],
                        permissions=[],
                        security_level="standard",
                        session_id=payload["session_id"],
                        token_type=payload["token_type"],
                        iat=payload["iat"],
                        exp=payload["exp"],
                        jti=payload["jti"]
                    )
            except Exception as e:
                return TokenValidationResult(
                    is_valid=False,
                    error=f"Invalid token claims: {str(e)}"
                )
            
            # Check if session is blacklisted
            if claims.session_id in self.blacklisted_sessions:
                return TokenValidationResult(
                    is_valid=False,
                    error="Session is blacklisted"
                )
            
            # Validate user still exists and is active
            if claims.token_type == TokenType.ACCESS:
                user = await self._get_user_by_id(claims.sub)
                if not user or not user.is_active:
                    return TokenValidationResult(
                        is_valid=False,
                        error="User not found or inactive"
                    )
            
            # Validate session exists for refresh tokens
            if claims.token_type == TokenType.REFRESH:
                session_valid = await self._validate_session(
                    claims.sub, 
                    claims.session_id,
                    payload.get("token_family")
                )
                if not session_valid:
                    return TokenValidationResult(
                        is_valid=False,
                        error="Invalid session"
                    )
            
            return TokenValidationResult(
                is_valid=True,
                claims=claims,
                user_id=claims.sub,
                session_id=claims.session_id
            )
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return TokenValidationResult(
                is_valid=False,
                error=f"Token validation error: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token with rotation.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            Dictionary with new access and refresh tokens
        """
        try:
            # Validate refresh token
            validation_result = await self.validate_token(refresh_token)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=validation_result.error
                )
            
            claims = validation_result.claims
            if claims.token_type != TokenType.REFRESH:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type for refresh"
                )
            
            # Get user
            user = await self._get_user_by_id(claims.sub)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Blacklist old refresh token
            await self.blacklist_token(refresh_token)
            
            # Create new session ID for security
            new_session_id = str(uuid4())
            
            # Create new tokens
            new_access_token = await self.create_access_token(user, new_session_id)
            new_refresh_token = await self.create_refresh_token(user, new_session_id)
            
            # Log token refresh
            audit_logger.log_event(
                event_type=AuditEventType.TOKEN_REFRESHED,
                action=f"Tokens refreshed for user {user.username}",
                user_id=str(user.id),
                session_id=new_session_id,
                details={
                    "old_session_id": claims.session_id,
                    "new_session_id": new_session_id
                }
            )
            
            logger.info(f"Tokens refreshed for user {user.username}")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token"
            )
    
    async def blacklist_token(self, token: str) -> None:
        """
        Blacklist a JWT token.
        
        Args:
            token: JWT token to blacklist
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.blacklisted_tokens.add(token_hash)
            
            # Extract session ID if possible
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    options={"verify_signature": False}
                )
                session_id = payload.get("session_id")
                if session_id:
                    await self._invalidate_session(session_id)
            except Exception:
                pass  # Token might be malformed, but we still blacklist it
            
            logger.debug(f"Token blacklisted: {token_hash[:16]}...")
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
    
    async def blacklist_session(self, session_id: str) -> None:
        """
        Blacklist all tokens for a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            self.blacklisted_sessions.add(session_id)
            await self._invalidate_session(session_id)
            
            logger.info(f"Session blacklisted: {session_id}")
            
        except Exception as e:
            logger.error(f"Error blacklisting session: {e}")
    
    async def logout_user(self, user_id: str, session_id: Optional[str] = None) -> None:
        """
        Logout user by blacklisting all their sessions.
        
        Args:
            user_id: User identifier
            session_id: Specific session to logout (optional)
        """
        try:
            if session_id:
                # Logout specific session
                await self.blacklist_session(session_id)
            else:
                # Logout all user sessions
                await self._invalidate_all_user_sessions(user_id)
            
            # Log logout event
            audit_logger.log_event(
                event_type=AuditEventType.USER_LOGOUT,
                action=f"User logged out",
                user_id=user_id,
                session_id=session_id,
                details={
                    "logout_type": "specific_session" if session_id else "all_sessions"
                }
            )
            
            logger.info(f"User {user_id} logged out")
            
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
    
    async def create_api_key_token(
        self,
        user: User,
        key_name: str,
        permissions: List[str],
        expires_days: Optional[int] = None
    ) -> str:
        """
        Create API key token for programmatic access.
        
        Args:
            user: User object
            key_name: Name for the API key
            permissions: List of permissions for the key
            expires_days: Expiration in days (optional)
            
        Returns:
            API key token string
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=expires_days or 365)  # Default 1 year
            
            # Create unique token ID
            jti = str(uuid4())
            
            # Build claims
            claims = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "key_name": key_name,
                "permissions": permissions,
                "token_type": TokenType.API_KEY,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "iss": "career-copilot",
                "aud": "career-copilot-api",
                "jti": jti
            }
            
            # Create JWT token
            token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
            
            # Store API key information
            await self._store_api_key(user.id, key_name, token, permissions, expires_at)
            
            # Log API key creation
            audit_logger.log_event(
                event_type=AuditEventType.API_KEY_USED,
                action=f"API key created: {key_name}",
                user_id=str(user.id),
                details={
                    "key_name": key_name,
                    "permissions": permissions,
                    "expires_at": expires_at.isoformat(),
                    "jti": jti
                }
            )
            
            logger.info(f"API key created for user {user.username}: {key_name}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating API key token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def _store_session(
        self,
        user_id: str,
        session_id: str,
        token_family: str,
        expires_at: datetime
    ) -> None:
        """Store session information in database."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                user_session = UserSession(
                    user_id=user_id,
                    session_id=session_id,
                    token_family=token_family,
                    expires_at=expires_at,
                    is_active=True
                )
                session.add(user_session)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error storing session: {e}")
    
    async def _validate_session(
        self,
        user_id: str,
        session_id: str,
        token_family: str
    ) -> bool:
        """Validate session exists and is active."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                from sqlalchemy import select, and_
                
                result = await session.execute(
                    select(UserSession).where(
                        and_(
                            UserSession.user_id == user_id,
                            UserSession.session_id == session_id,
                            UserSession.token_family == token_family,
                            UserSession.is_active == True,
                            UserSession.expires_at > datetime.now(timezone.utc)
                        )
                    )
                )
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    async def _invalidate_session(self, session_id: str) -> None:
        """Invalidate session in database."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                await session.execute(
                    UserSession.__table__.update()
                    .where(UserSession.session_id == session_id)
                    .values(is_active=False)
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    async def _invalidate_all_user_sessions(self, user_id: str) -> None:
        """Invalidate all sessions for a user."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                await session.execute(
                    UserSession.__table__.update()
                    .where(UserSession.user_id == user_id)
                    .values(is_active=False)
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
    
    async def _store_api_key(
        self,
        user_id: str,
        key_name: str,
        token: str,
        permissions: List[str],
        expires_at: datetime
    ) -> None:
        """Store API key information in database."""
        try:
            from ..models.database_models import APIKey
            
            # Hash the token for storage
            key_hash = hashlib.sha256(token.encode()).hexdigest()
            
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                api_key = APIKey(
                    user_id=user_id,
                    key_name=key_name,
                    key_hash=key_hash,
                    permissions=permissions,
                    expires_at=expires_at,
                    is_active=True
                )
                session.add(api_key)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error storing API key: {e}")
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get token information without validation.
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary with token information
        """
        try:
            # Decode without verification to get claims
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            return {
                "token_type": payload.get("token_type"),
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "session_id": payload.get("session_id"),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "jti": payload.get("jti")
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return {}
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens and sessions.
        
        Returns:
            Number of cleaned up items
        """
        try:
            cleaned_count = 0
            
            # Clean up expired sessions
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                from sqlalchemy import delete
                
                result = await session.execute(
                    delete(UserSession).where(
                        UserSession.expires_at < datetime.now(timezone.utc)
                    )
                )
                cleaned_count += result.rowcount
                await session.commit()
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0


# Global instance
_jwt_token_manager: Optional[JWTTokenManager] = None


def get_jwt_token_manager() -> JWTTokenManager:
    """Get global JWT token manager instance."""
    global _jwt_token_manager
    if _jwt_token_manager is None:
        _jwt_token_manager = JWTTokenManager()
    return _jwt_token_manager