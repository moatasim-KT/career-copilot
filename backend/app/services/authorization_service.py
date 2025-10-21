"""
Authorization Service for Career Copilot System.
Handles role-based access control and permissions.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from ..core.logging import get_logger, get_audit_logger
from .firebase_auth_service import get_firebase_auth_service

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class Role(Enum):
    """User roles in the system."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class Permission(Enum):
    """System permissions."""
    READ_JOBS = "read_jobs"
    WRITE_JOBS = "write_jobs"
    DELETE_JOBS = "delete_jobs"
    READ_PROFILE = "read_profile"
    WRITE_PROFILE = "write_profile"
    READ_ANALYTICS = "read_analytics"
    WRITE_ANALYTICS = "write_analytics"
    ADMIN_ACCESS = "admin_access"
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"


class AuthorizationService:
    """Service for handling authorization and permissions."""
    
    def __init__(self):
        self.firebase_service = get_firebase_auth_service()
        
        # Define role permissions
        self.role_permissions = {
            Role.USER: [
                Permission.READ_JOBS,
                Permission.WRITE_JOBS,
                Permission.READ_PROFILE,
                Permission.WRITE_PROFILE,
                Permission.READ_ANALYTICS
            ],
            Role.MODERATOR: [
                Permission.READ_JOBS,
                Permission.WRITE_JOBS,
                Permission.DELETE_JOBS,
                Permission.READ_PROFILE,
                Permission.WRITE_PROFILE,
                Permission.READ_ANALYTICS,
                Permission.WRITE_ANALYTICS
            ],
            Role.ADMIN: [
                Permission.READ_JOBS,
                Permission.WRITE_JOBS,
                Permission.DELETE_JOBS,
                Permission.READ_PROFILE,
                Permission.WRITE_PROFILE,
                Permission.READ_ANALYTICS,
                Permission.WRITE_ANALYTICS,
                Permission.ADMIN_ACCESS,
                Permission.MANAGE_USERS,
                Permission.SYSTEM_CONFIG
            ]
        }
    
    def get_user_roles(self, user_data: Dict[str, Any]) -> List[Role]:
        """Get user roles from user data."""
        try:
            custom_claims = user_data.get("custom_claims", {})
            role_strings = custom_claims.get("roles", ["user"])
            
            roles = []
            for role_str in role_strings:
                try:
                    role = Role(role_str)
                    roles.append(role)
                except ValueError:
                    logger.warning(f"Invalid role: {role_str}")
            
            # Ensure user always has at least USER role
            if not roles:
                roles = [Role.USER]
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return [Role.USER]
    
    def get_user_permissions(self, user_data: Dict[str, Any]) -> List[Permission]:
        """Get user permissions based on roles."""
        try:
            roles = self.get_user_roles(user_data)
            permissions = set()
            
            for role in roles:
                role_perms = self.role_permissions.get(role, [])
                permissions.update(role_perms)
            
            return list(permissions)
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return self.role_permissions[Role.USER]
    
    def has_permission(self, user_data: Dict[str, Any], permission: Permission) -> bool:
        """Check if user has specific permission."""
        try:
            user_permissions = self.get_user_permissions(user_data)
            return permission in user_permissions
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def has_role(self, user_data: Dict[str, Any], role: Role) -> bool:
        """Check if user has specific role."""
        try:
            user_roles = self.get_user_roles(user_data)
            return role in user_roles
            
        except Exception as e:
            logger.error(f"Error checking role: {e}")
            return False
    
    def has_any_role(self, user_data: Dict[str, Any], roles: List[Role]) -> bool:
        """Check if user has any of the specified roles."""
        try:
            user_roles = self.get_user_roles(user_data)
            return any(role in user_roles for role in roles)
            
        except Exception as e:
            logger.error(f"Error checking roles: {e}")
            return False
    
    async def assign_role(self, user_id: str, role: Role) -> bool:
        """Assign role to user."""
        try:
            # Get current user
            firebase_user = await self.firebase_service.get_user(user_id)
            if not firebase_user:
                return False
            
            # Get current custom claims
            current_claims = firebase_user.custom_claims or {}
            current_roles = current_claims.get("roles", ["user"])
            
            # Add new role if not already present
            if role.value not in current_roles:
                current_roles.append(role.value)
                
                # Update custom claims
                updated_claims = {**current_claims, "roles": current_roles}
                success = await self.firebase_service.set_custom_claims(user_id, updated_claims)
                
                if success:
                    # Log role assignment
                    audit_logger.log_security_event(
                        event_type="role_assigned",
                        user_id=user_id,
                        details={"role": role.value}
                    )
                    
                    logger.info(f"Assigned role {role.value} to user {user_id}")
                
                return success
            
            return True  # Role already assigned
            
        except Exception as e:
            logger.error(f"Error assigning role to user {user_id}: {e}")
            return False
    
    async def remove_role(self, user_id: str, role: Role) -> bool:
        """Remove role from user."""
        try:
            # Get current user
            firebase_user = await self.firebase_service.get_user(user_id)
            if not firebase_user:
                return False
            
            # Get current custom claims
            current_claims = firebase_user.custom_claims or {}
            current_roles = current_claims.get("roles", ["user"])
            
            # Remove role if present
            if role.value in current_roles:
                current_roles.remove(role.value)
                
                # Ensure user always has at least USER role
                if not current_roles:
                    current_roles = ["user"]
                
                # Update custom claims
                updated_claims = {**current_claims, "roles": current_roles}
                success = await self.firebase_service.set_custom_claims(user_id, updated_claims)
                
                if success:
                    # Log role removal
                    audit_logger.log_security_event(
                        event_type="role_removed",
                        user_id=user_id,
                        details={"role": role.value}
                    )
                    
                    logger.info(f"Removed role {role.value} from user {user_id}")
                
                return success
            
            return True  # Role not present
            
        except Exception as e:
            logger.error(f"Error removing role from user {user_id}: {e}")
            return False
    
    def check_resource_access(self, user_data: Dict[str, Any], resource_owner_id: str) -> bool:
        """Check if user can access a resource owned by another user."""
        try:
            # Users can always access their own resources
            if user_data["uid"] == resource_owner_id:
                return True
            
            # Admins and moderators can access any resource
            if self.has_any_role(user_data, [Role.ADMIN, Role.MODERATOR]):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking resource access: {e}")
            return False
    
    def get_authorization_status(self) -> Dict[str, Any]:
        """Get authorization service status."""
        return {
            "roles_configured": len(self.role_permissions),
            "available_roles": [role.value for role in Role],
            "available_permissions": [perm.value for perm in Permission]
        }


# Global service instance
_authorization_service: Optional[AuthorizationService] = None


def get_authorization_service() -> AuthorizationService:
    """Get authorization service instance."""
    global _authorization_service
    if _authorization_service is None:
        _authorization_service = AuthorizationService()
    return _authorization_service