"""
Security Management API Endpoints
Provides endpoints for JWT token management, RBAC, and audit trail access.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ...core.auth import get_current_user, get_current_superuser, User
from ...services.jwt_token_manager import get_jwt_token_manager, JWTTokenManager
from ...services.rbac_service import (
    get_rbac_service,
    RBACService,
    Permission,
    Role,
    PermissionContext,
    AccessControlResult
)
from ...services.audit_trail_service import (
    get_audit_trail_service,
    AuditTrailService,
    AuditEventType,
    AuditSeverity,
    ComplianceReport
)

router = APIRouter(prefix="/api/v1/security", tags=["security"])


# Request/Response Models
class TokenInfo(BaseModel):
    """Token information response."""
    token_type: str
    user_id: str
    username: str
    session_id: str
    issued_at: datetime
    expires_at: datetime
    jti: str


class CreateAPIKeyRequest(BaseModel):
    """Request to create API key."""
    key_name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key creation response."""
    api_key: str
    key_name: str
    permissions: List[str]
    expires_at: datetime


class RoleAssignmentRequest(BaseModel):
    """Request to assign role to user."""
    user_id: str
    role: str
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


class PermissionGrantRequest(BaseModel):
    """Request to grant permission to user."""
    user_id: str
    permission: str
    expires_at: Optional[datetime] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class PermissionCheckRequest(BaseModel):
    """Request to check user permissions."""
    user_id: str
    permissions: List[str]
    require_all: bool = True
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None


class UserPermissionsResponse(BaseModel):
    """User permissions response."""
    user_id: str
    roles: List[str]
    permissions: List[str]
    security_level: str


class AuditEventResponse(BaseModel):
    """Audit event response."""
    id: str
    timestamp: datetime
    event_type: str
    severity: str
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]


# JWT Token Management Endpoints
@router.get("/tokens/info")
async def get_token_info(
    request: Request,
    jwt_manager: JWTTokenManager = Depends(get_jwt_token_manager),
    current_user: User = Depends(get_current_user)
) -> TokenInfo:
    """Get information about the current JWT token."""
    # Extract token from request
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid token found in request"
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    token_info = jwt_manager.get_token_info(token)
    
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    return TokenInfo(**token_info)


@router.post("/tokens/api-key")
async def create_api_key(
    request_data: CreateAPIKeyRequest,
    jwt_manager: JWTTokenManager = Depends(get_jwt_token_manager),
    current_user: User = Depends(get_current_user)
) -> APIKeyResponse:
    """Create a new API key for the current user."""
    try:
        # Validate permissions
        valid_permissions = [p.value for p in Permission]
        invalid_permissions = [p for p in request_data.permissions if p not in valid_permissions]
        
        if invalid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permissions: {invalid_permissions}"
            )
        
        # Create API key
        api_key = await jwt_manager.create_api_key_token(
            user=current_user,
            key_name=request_data.key_name,
            permissions=request_data.permissions,
            expires_days=request_data.expires_days
        )
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=request_data.expires_days or 365)
        
        return APIKeyResponse(
            api_key=api_key,
            key_name=request_data.key_name,
            permissions=request_data.permissions,
            expires_at=expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.post("/tokens/revoke")
async def revoke_token(
    request: Request,
    jwt_manager: JWTTokenManager = Depends(get_jwt_token_manager),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Revoke the current JWT token."""
    # Extract token from request
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid token found in request"
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    await jwt_manager.blacklist_token(token)
    
    return {"message": "Token revoked successfully"}


@router.post("/logout")
async def logout_user(
    session_id: Optional[str] = None,
    jwt_manager: JWTTokenManager = Depends(get_jwt_token_manager),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Logout user by invalidating sessions."""
    await jwt_manager.logout_user(str(current_user.id), session_id)
    return {"message": "Logged out successfully"}


# RBAC Management Endpoints
@router.get("/permissions/available")
async def get_available_permissions(
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_user)
) -> List[str]:
    """Get list of all available permissions."""
    permissions = rbac_service.get_all_permissions()
    return [p.value for p in permissions]


@router.get("/roles/available")
async def get_available_roles(
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of all available roles with their definitions."""
    roles = rbac_service.get_all_roles()
    return {
        role_name: {
            "display_name": role_def.display_name,
            "description": role_def.description,
            "permissions": [p.value for p in role_def.permissions],
            "security_level": role_def.security_level.value
        }
        for role_name, role_def in roles.items()
    }


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_user)
) -> UserPermissionsResponse:
    """Get user's roles and permissions."""
    # Check if user can view other users' permissions
    if str(current_user.id) != user_id and not current_user.is_superuser:
        # Check if user has permission to read user data
        access_result = await rbac_service.check_permission(
            user_id=str(current_user.id),
            required_permission=Permission.USER_READ
        )
        if not access_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user data"
            )
    
    roles = await rbac_service.get_user_roles(user_id)
    permissions = await rbac_service.get_user_permissions(user_id)
    security_level = await rbac_service.get_user_security_level(user_id)
    
    return UserPermissionsResponse(
        user_id=user_id,
        roles=roles,
        permissions=[p.value for p in permissions],
        security_level=security_level.value
    )


@router.post("/permissions/check")
async def check_permissions(
    request_data: PermissionCheckRequest,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_superuser)  # Only admins can check other users' permissions
) -> AccessControlResult:
    """Check if user has specific permissions."""
    try:
        # Convert string permissions to Permission enum
        permissions = []
        for perm_str in request_data.permissions:
            try:
                permissions.append(Permission(perm_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission: {perm_str}"
                )
        
        # Create permission context
        context = PermissionContext(
            user_id=request_data.user_id,
            resource_type=request_data.resource_type,
            resource_id=request_data.resource_id,
            action=request_data.action
        )
        
        # Check permissions
        result = await rbac_service.check_multiple_permissions(
            user_id=request_data.user_id,
            required_permissions=permissions,
            require_all=request_data.require_all,
            context=context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permissions: {str(e)}"
        )


@router.post("/roles/assign")
async def assign_role(
    request_data: RoleAssignmentRequest,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, str]:
    """Assign role to user."""
    try:
        # Validate role
        try:
            role = Role(request_data.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request_data.role}"
            )
        
        success = await rbac_service.assign_role(
            user_id=request_data.user_id,
            role=role,
            assigned_by=str(current_user.id),
            expires_at=request_data.expires_at,
            reason=request_data.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role"
            )
        
        return {"message": f"Role {request_data.role} assigned to user {request_data.user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role: {str(e)}"
        )


@router.post("/roles/revoke")
async def revoke_role(
    user_id: str,
    role: str,
    reason: Optional[str] = None,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, str]:
    """Revoke role from user."""
    try:
        # Validate role
        try:
            role_enum = Role(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
        
        success = await rbac_service.revoke_role(
            user_id=user_id,
            role=role_enum,
            revoked_by=str(current_user.id),
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke role"
            )
        
        return {"message": f"Role {role} revoked from user {user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke role: {str(e)}"
        )


@router.post("/permissions/grant")
async def grant_permission(
    request_data: PermissionGrantRequest,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, str]:
    """Grant specific permission to user."""
    try:
        # Validate permission
        try:
            permission = Permission(request_data.permission)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission: {request_data.permission}"
            )
        
        success = await rbac_service.grant_permission(
            user_id=request_data.user_id,
            permission=permission,
            granted_by=str(current_user.id),
            expires_at=request_data.expires_at,
            resource_type=request_data.resource_type,
            resource_id=request_data.resource_id,
            conditions=request_data.conditions
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to grant permission"
            )
        
        return {"message": f"Permission {request_data.permission} granted to user {request_data.user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {str(e)}"
        )


# Audit Trail Endpoints
@router.get("/audit/events")
async def get_audit_events(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_types: Optional[List[str]] = Query(None, description="Filter by event types"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
    current_user: User = Depends(get_current_user)
) -> List[AuditEventResponse]:
    """Get audit events with filtering options."""
    # Check if user has permission to read audit logs
    rbac_service = get_rbac_service()
    access_result = await rbac_service.check_permission(
        user_id=str(current_user.id),
        required_permission=Permission.AUDIT_READ
    )
    
    if not access_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read audit logs"
        )
    
    try:
        # Convert string event types to enum
        event_type_enums = None
        if event_types:
            event_type_enums = []
            for event_type in event_types:
                try:
                    event_type_enums.append(AuditEventType(event_type))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid event type: {event_type}"
                    )
        
        # Convert string severity to enum
        severity_enum = None
        if severity:
            try:
                severity_enum = AuditSeverity(severity)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity: {severity}"
                )
        
        events = await audit_service.get_audit_events(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            event_types=event_type_enums,
            severity=severity_enum,
            limit=limit,
            offset=offset
        )
        
        return [
            AuditEventResponse(
                id=event.id,
                timestamp=event.timestamp,
                event_type=event.event_type.value,
                severity=event.severity.value,
                user_id=event.user_id,
                session_id=event.session_id,
                ip_address=event.ip_address,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action.value,
                result=event.result.value,
                details=event.details
            )
            for event in events
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit events: {str(e)}"
        )


@router.get("/audit/compliance-report")
async def generate_compliance_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
    current_user: User = Depends(get_current_superuser)
) -> ComplianceReport:
    """Generate compliance audit report."""
    try:
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        # Limit report period to 1 year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report period cannot exceed 1 year"
            )
        
        report = await audit_service.generate_compliance_report(start_date, end_date)
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.post("/audit/cleanup")
async def cleanup_old_audit_events(
    audit_service: AuditTrailService = Depends(get_audit_trail_service),
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, int]:
    """Clean up old audit events based on retention policy."""
    try:
        cleaned_count = await audit_service.cleanup_old_events()
        return {"cleaned_events": cleaned_count}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audit events: {str(e)}"
        )