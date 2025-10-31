"""
Role-Based Access Control (RBAC) Service
Provides comprehensive role and permission management.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..core.config import get_settings
from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..core.audit import audit_logger, AuditEventType, AuditSeverity
from ..models.database_models import User, RoleAssignment, PermissionGrant

logger = get_logger(__name__)
settings = get_settings()


class Permission(str, Enum):
	"""System permissions."""

	# Contract permissions
	CONTRACT_READ = "contract:read"
	CONTRACT_WRITE = "contract:write"
	CONTRACT_DELETE = "contract:delete"
	CONTRACT_ANALYZE = "contract:analyze"
	CONTRACT_EXPORT = "contract:export"

	# User management permissions
	USER_READ = "user:read"
	USER_WRITE = "user:write"
	USER_DELETE = "user:delete"
	USER_MANAGE_ROLES = "user:manage_roles"
	USER_MANAGE_PERMISSIONS = "user:manage_permissions"

	# System permissions
	SYSTEM_ADMIN = "system:admin"
	SYSTEM_MONITOR = "system:monitor"
	SYSTEM_CONFIG = "system:config"
	SYSTEM_BACKUP = "system:backup"
	SYSTEM_RESTORE = "system:restore"

	# Analytics permissions
	ANALYTICS_READ = "analytics:read"
	ANALYTICS_WRITE = "analytics:write"
	ANALYTICS_EXPORT = "analytics:export"
	ANALYTICS_DELETE = "analytics:delete"

	# API permissions
	API_READ = "api:read"
	API_WRITE = "api:write"
	API_ADMIN = "api:admin"

	# Audit permissions
	AUDIT_READ = "audit:read"
	AUDIT_WRITE = "audit:write"
	AUDIT_DELETE = "audit:delete"

	# Integration permissions
	INTEGRATION_DOCUSIGN = "integration:docusign"
	INTEGRATION_SLACK = "integration:slack"
	INTEGRATION_EMAIL = "integration:email"


class Role(str, Enum):
	"""System roles."""

	SUPER_ADMIN = "super_admin"
	ADMIN = "admin"
	MANAGER = "manager"
	ANALYST = "analyst"
	USER = "user"
	READONLY = "readonly"
	GUEST = "guest"


class SecurityLevel(str, Enum):
	"""Security clearance levels."""

	PUBLIC = "public"
	INTERNAL = "internal"
	CONFIDENTIAL = "confidential"
	RESTRICTED = "restricted"
	TOP_SECRET = "top_secret"


class PermissionContext(BaseModel):
	"""Context for permission evaluation."""

	user_id: str
	resource_type: Optional[str] = None
	resource_id: Optional[str] = None
	action: Optional[str] = None
	ip_address: Optional[str] = None
	user_agent: Optional[str] = None
	additional_context: Dict[str, Any] = {}


class RoleDefinition(BaseModel):
	"""Role definition with permissions and metadata."""

	name: str
	display_name: str
	description: str
	permissions: List[Permission]
	security_level: SecurityLevel
	is_system_role: bool = True
	created_at: datetime
	updated_at: datetime


class AccessControlResult(BaseModel):
	"""Result of access control check."""

	allowed: bool
	reason: str
	required_permissions: List[Permission]
	user_permissions: List[Permission]
	security_level_met: bool
	context_validated: bool


class RBACService:
	"""Role-Based Access Control service."""

	def __init__(self):
		"""Initialize RBAC service."""
		self.role_definitions = self._initialize_role_definitions()
		self.permission_hierarchy = self._initialize_permission_hierarchy()
		logger.info("RBAC Service initialized")

	def _initialize_role_definitions(self) -> Dict[str, RoleDefinition]:
		"""Initialize default role definitions."""
		now = datetime.now(timezone.utc)

		return {
			Role.SUPER_ADMIN: RoleDefinition(
				name=Role.SUPER_ADMIN,
				display_name="Super Administrator",
				description="Full system access with all permissions",
				permissions=list(Permission),  # All permissions
				security_level=SecurityLevel.TOP_SECRET,
				created_at=now,
				updated_at=now,
			),
			Role.ADMIN: RoleDefinition(
				name=Role.ADMIN,
				display_name="Administrator",
				description="Administrative access with most permissions",
				permissions=[
					Permission.CONTRACT_READ,
					Permission.CONTRACT_WRITE,
					Permission.CONTRACT_DELETE,
					Permission.CONTRACT_ANALYZE,
					Permission.CONTRACT_EXPORT,
					Permission.USER_READ,
					Permission.USER_WRITE,
					Permission.USER_MANAGE_ROLES,
					Permission.SYSTEM_MONITOR,
					Permission.SYSTEM_CONFIG,
					Permission.ANALYTICS_READ,
					Permission.ANALYTICS_WRITE,
					Permission.ANALYTICS_EXPORT,
					Permission.API_READ,
					Permission.API_WRITE,
					Permission.AUDIT_READ,
					Permission.INTEGRATION_DOCUSIGN,
					Permission.INTEGRATION_SLACK,
					Permission.INTEGRATION_EMAIL,
				],
				security_level=SecurityLevel.RESTRICTED,
				created_at=now,
				updated_at=now,
			),
			Role.MANAGER: RoleDefinition(
				name=Role.MANAGER,
				display_name="Manager",
				description="Management access with contract and user permissions",
				permissions=[
					Permission.CONTRACT_READ,
					Permission.CONTRACT_WRITE,
					Permission.CONTRACT_ANALYZE,
					Permission.CONTRACT_EXPORT,
					Permission.USER_READ,
					Permission.ANALYTICS_READ,
					Permission.ANALYTICS_WRITE,
					Permission.API_READ,
					Permission.INTEGRATION_DOCUSIGN,
					Permission.INTEGRATION_SLACK,
					Permission.INTEGRATION_EMAIL,
				],
				security_level=SecurityLevel.CONFIDENTIAL,
				created_at=now,
				updated_at=now,
			),
			Role.ANALYST: RoleDefinition(
				name=Role.ANALYST,
				display_name="Analyst",
				description="Analysis access with job application tracking permissions",
				permissions=[
					Permission.CONTRACT_READ,
					Permission.CONTRACT_ANALYZE,
					Permission.CONTRACT_EXPORT,
					Permission.ANALYTICS_READ,
					Permission.API_READ,
				],
				security_level=SecurityLevel.INTERNAL,
				created_at=now,
				updated_at=now,
			),
			Role.USER: RoleDefinition(
				name=Role.USER,
				display_name="User",
				description="Standard user access with basic contract permissions",
				permissions=[
					Permission.CONTRACT_READ,
					Permission.CONTRACT_WRITE,
					Permission.CONTRACT_ANALYZE,
					Permission.ANALYTICS_READ,
					Permission.API_READ,
				],
				security_level=SecurityLevel.INTERNAL,
				created_at=now,
				updated_at=now,
			),
			Role.READONLY: RoleDefinition(
				name=Role.READONLY,
				display_name="Read Only",
				description="Read-only access to contracts and analytics",
				permissions=[
					Permission.CONTRACT_READ,
					Permission.ANALYTICS_READ,
				],
				security_level=SecurityLevel.INTERNAL,
				created_at=now,
				updated_at=now,
			),
			Role.GUEST: RoleDefinition(
				name=Role.GUEST,
				display_name="Guest",
				description="Limited guest access",
				permissions=[],
				security_level=SecurityLevel.PUBLIC,
				created_at=now,
				updated_at=now,
			),
		}

	def _initialize_permission_hierarchy(self) -> Dict[Permission, List[Permission]]:
		"""Initialize permission hierarchy (permissions that imply others)."""
		return {
			Permission.SYSTEM_ADMIN: list(Permission),  # Admin implies all permissions
			Permission.CONTRACT_DELETE: [Permission.CONTRACT_WRITE, Permission.CONTRACT_READ],
			Permission.CONTRACT_WRITE: [Permission.CONTRACT_READ],
			Permission.USER_DELETE: [Permission.USER_WRITE, Permission.USER_READ],
			Permission.USER_WRITE: [Permission.USER_READ],
			Permission.USER_MANAGE_ROLES: [Permission.USER_READ],
			Permission.USER_MANAGE_PERMISSIONS: [Permission.USER_READ],
			Permission.ANALYTICS_DELETE: [Permission.ANALYTICS_WRITE, Permission.ANALYTICS_READ],
			Permission.ANALYTICS_WRITE: [Permission.ANALYTICS_READ],
			Permission.API_ADMIN: [Permission.API_WRITE, Permission.API_READ],
			Permission.API_WRITE: [Permission.API_READ],
			Permission.AUDIT_DELETE: [Permission.AUDIT_WRITE, Permission.AUDIT_READ],
			Permission.AUDIT_WRITE: [Permission.AUDIT_READ],
		}

	async def check_permission(
		self, user_id: str, required_permission: Permission, context: Optional[PermissionContext] = None
	) -> AccessControlResult:
		"""
		Check if user has required permission.

		Args:
		    user_id: User identifier
		    required_permission: Required permission
		    context: Permission context for evaluation

		Returns:
		    AccessControlResult with decision and details
		"""
		try:
			# Get user permissions
			user_permissions = await self.get_user_permissions(user_id)

			# Check direct permission
			has_permission = required_permission in user_permissions

			# Check implied permissions through hierarchy
			if not has_permission:
				for perm in user_permissions:
					if perm in self.permission_hierarchy:
						implied_permissions = self.permission_hierarchy[perm]
						if required_permission in implied_permissions:
							has_permission = True
							break

			# Check security level if context provided
			security_level_met = True
			if context and context.resource_type:
				user_security_level = await self.get_user_security_level(user_id)
				required_security_level = self._get_required_security_level(context.resource_type, context.action)
				security_level_met = self._check_security_level(user_security_level, required_security_level)

			# Validate context-specific rules
			context_validated = True
			if context:
				context_validated = await self._validate_context_rules(user_id, required_permission, context)

			# Final decision
			allowed = has_permission and security_level_met and context_validated

			# Log access attempt
			await self._log_access_attempt(user_id, required_permission, allowed, context)

			return AccessControlResult(
				allowed=allowed,
				reason=self._get_access_reason(has_permission, security_level_met, context_validated),
				required_permissions=[required_permission],
				user_permissions=user_permissions,
				security_level_met=security_level_met,
				context_validated=context_validated,
			)

		except Exception as e:
			logger.error(f"Error checking permission: {e}")
			return AccessControlResult(
				allowed=False,
				reason=f"Permission check error: {e!s}",
				required_permissions=[required_permission],
				user_permissions=[],
				security_level_met=False,
				context_validated=False,
			)

	async def check_multiple_permissions(
		self, user_id: str, required_permissions: List[Permission], require_all: bool = True, context: Optional[PermissionContext] = None
	) -> AccessControlResult:
		"""
		Check multiple permissions for a user.

		Args:
		    user_id: User identifier
		    required_permissions: List of required permissions
		    require_all: Whether all permissions are required (AND) or any (OR)
		    context: Permission context

		Returns:
		    AccessControlResult with decision and details
		"""
		try:
			results = []
			for permission in required_permissions:
				result = await self.check_permission(user_id, permission, context)
				results.append(result)

			if require_all:
				# All permissions must be granted
				allowed = all(result.allowed for result in results)
				reason = "All required permissions granted" if allowed else "Missing required permissions"
			else:
				# Any permission is sufficient
				allowed = any(result.allowed for result in results)
				reason = "At least one required permission granted" if allowed else "No required permissions granted"

			# Combine user permissions
			all_user_permissions = set()
			for result in results:
				all_user_permissions.update(result.user_permissions)

			return AccessControlResult(
				allowed=allowed,
				reason=reason,
				required_permissions=required_permissions,
				user_permissions=list(all_user_permissions),
				security_level_met=all(result.security_level_met for result in results),
				context_validated=all(result.context_validated for result in results),
			)

		except Exception as e:
			logger.error(f"Error checking multiple permissions: {e}")
			return AccessControlResult(
				allowed=False,
				reason=f"Multiple permission check error: {e!s}",
				required_permissions=required_permissions,
				user_permissions=[],
				security_level_met=False,
				context_validated=False,
			)

	async def get_user_roles(self, user_id: str) -> List[str]:
		"""
		Get active roles for a user.

		Args:
		    user_id: User identifier

		Returns:
		    List of active role names
		"""
		try:
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				from sqlalchemy import select, and_, or_

				result = await session.execute(
					select(RoleAssignment.role).where(
						and_(
							RoleAssignment.user_id == user_id,
							RoleAssignment.is_active == True,
							or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > datetime.now(timezone.utc)),
						)
					)
				)

				roles = [row[0] for row in result.fetchall()]

				# Also get roles from user table
				user_result = await session.execute(select(User.roles).where(User.id == user_id))
				user_roles = user_result.scalar_one_or_none() or []

				# Combine and deduplicate
				all_roles = list(set(roles + user_roles))

				logger.debug(f"User {user_id} has roles: {all_roles}")
				return all_roles

		except Exception as e:
			logger.error(f"Error getting user roles: {e}")
			return []

	async def get_user_permissions(self, user_id: str) -> List[Permission]:
		"""
		Get effective permissions for a user.

		Args:
		    user_id: User identifier

		Returns:
		    List of effective permissions
		"""
		try:
			permissions = set()

			# Get permissions from roles
			user_roles = await self.get_user_roles(user_id)
			for role_name in user_roles:
				if role_name in self.role_definitions:
					role_def = self.role_definitions[role_name]
					permissions.update(role_def.permissions)

			# Get direct permission grants
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				from sqlalchemy import select, and_, or_

				result = await session.execute(
					select(PermissionGrant.permission).where(
						and_(
							PermissionGrant.user_id == user_id,
							PermissionGrant.is_active == True,
							or_(PermissionGrant.expires_at.is_(None), PermissionGrant.expires_at > datetime.now(timezone.utc)),
						)
					)
				)

				direct_permissions = [row[0] for row in result.fetchall()]
				permissions.update(direct_permissions)

				# Also get permissions from user table
				user_result = await session.execute(select(User.permissions).where(User.id == user_id))
				user_permissions = user_result.scalar_one_or_none() or []
				permissions.update(user_permissions)

			# Convert to Permission enum values
			valid_permissions = []
			for perm in permissions:
				try:
					valid_permissions.append(Permission(perm))
				except ValueError:
					logger.warning(f"Invalid permission found: {perm}")

			logger.debug(f"User {user_id} has permissions: {valid_permissions}")
			return valid_permissions

		except Exception as e:
			logger.error(f"Error getting user permissions: {e}")
			return []

	async def get_user_security_level(self, user_id: str) -> SecurityLevel:
		"""
		Get user's security clearance level.

		Args:
		    user_id: User identifier

		Returns:
		    User's security level
		"""
		try:
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				from sqlalchemy import select

				result = await session.execute(select(User.security_level).where(User.id == user_id))

				security_level = result.scalar_one_or_none()
				if security_level:
					return SecurityLevel(security_level)

				return SecurityLevel.INTERNAL  # Default level

		except Exception as e:
			logger.error(f"Error getting user security level: {e}")
			return SecurityLevel.INTERNAL

	async def assign_role(
		self, user_id: str, role: Role, assigned_by: str, expires_at: Optional[datetime] = None, reason: Optional[str] = None
	) -> bool:
		"""
		Assign a role to a user.

		Args:
		    user_id: User identifier
		    role: Role to assign
		    assigned_by: User ID of who is assigning the role
		    expires_at: Optional expiration date
		    reason: Reason for assignment

		Returns:
		    True if successful
		"""
		try:
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				# Check if role assignment already exists
				from sqlalchemy import select, and_

				existing = await session.execute(
					select(RoleAssignment).where(
						and_(RoleAssignment.user_id == user_id, RoleAssignment.role == role.value, RoleAssignment.is_active == True)
					)
				)

				if existing.scalar_one_or_none():
					logger.warning(f"Role {role.value} already assigned to user {user_id}")
					return True

				# Create new role assignment
				role_assignment = RoleAssignment(
					user_id=user_id, role=role.value, assigned_by=assigned_by, expires_at=expires_at, reason=reason, is_active=True
				)

				session.add(role_assignment)
				await session.commit()

				# Log role assignment
				audit_logger.log_event(
					event_type=AuditEventType.USER_CREATED,
					action=f"Role {role.value} assigned to user {user_id}",
					user_id=assigned_by,
					details={
						"target_user_id": user_id,
						"role": role.value,
						"expires_at": expires_at.isoformat() if expires_at else None,
						"reason": reason,
					},
				)

				logger.info(f"Role {role.value} assigned to user {user_id} by {assigned_by}")
				return True

		except Exception as e:
			logger.error(f"Error assigning role: {e}")
			return False

	async def revoke_role(self, user_id: str, role: Role, revoked_by: str, reason: Optional[str] = None) -> bool:
		"""
		Revoke a role from a user.

		Args:
		    user_id: User identifier
		    role: Role to revoke
		    revoked_by: User ID of who is revoking the role
		    reason: Reason for revocation

		Returns:
		    True if successful
		"""
		try:
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				from sqlalchemy import and_

				# Deactivate role assignment
				await session.execute(
					RoleAssignment.__table__.update()
					.where(and_(RoleAssignment.user_id == user_id, RoleAssignment.role == role.value, RoleAssignment.is_active == True))
					.values(is_active=False)
				)

				await session.commit()

				# Log role revocation
				audit_logger.log_event(
					event_type=AuditEventType.USER_CREATED,
					action=f"Role {role.value} revoked from user {user_id}",
					user_id=revoked_by,
					details={"target_user_id": user_id, "role": role.value, "reason": reason},
				)

				logger.info(f"Role {role.value} revoked from user {user_id} by {revoked_by}")
				return True

		except Exception as e:
			logger.error(f"Error revoking role: {e}")
			return False

	async def grant_permission(
		self,
		user_id: str,
		permission: Permission,
		granted_by: str,
		expires_at: Optional[datetime] = None,
		resource_type: Optional[str] = None,
		resource_id: Optional[str] = None,
		conditions: Optional[Dict[str, Any]] = None,
	) -> bool:
		"""
		Grant a specific permission to a user.

		Args:
		    user_id: User identifier
		    permission: Permission to grant
		    granted_by: User ID of who is granting the permission
		    expires_at: Optional expiration date
		    resource_type: Optional resource type restriction
		    resource_id: Optional specific resource restriction
		    conditions: Optional conditions for the permission

		Returns:
		    True if successful
		"""
		try:
			db_manager = await get_database_manager()
			async with db_manager.get_session() as session:
				permission_grant = PermissionGrant(
					user_id=user_id,
					permission=permission.value,
					granted_by=granted_by,
					expires_at=expires_at,
					resource_type=resource_type,
					resource_id=resource_id,
					conditions=conditions or {},
					is_active=True,
				)

				session.add(permission_grant)
				await session.commit()

				# Log permission grant
				audit_logger.log_event(
					event_type=AuditEventType.USER_CREATED,
					action=f"Permission {permission.value} granted to user {user_id}",
					user_id=granted_by,
					details={
						"target_user_id": user_id,
						"permission": permission.value,
						"resource_type": resource_type,
						"resource_id": resource_id,
						"expires_at": expires_at.isoformat() if expires_at else None,
						"conditions": conditions,
					},
				)

				logger.info(f"Permission {permission.value} granted to user {user_id} by {granted_by}")
				return True

		except Exception as e:
			logger.error(f"Error granting permission: {e}")
			return False

	def get_role_definition(self, role: Role) -> Optional[RoleDefinition]:
		"""Get role definition."""
		return self.role_definitions.get(role)

	def get_all_roles(self) -> Dict[str, RoleDefinition]:
		"""Get all role definitions."""
		return self.role_definitions

	def get_all_permissions(self) -> List[Permission]:
		"""Get all available permissions."""
		return list(Permission)

	def _get_required_security_level(self, resource_type: str, action: Optional[str]) -> SecurityLevel:
		"""Get required security level for resource and action."""
		# Define security requirements for different resources
		security_requirements = {
			"contract_analysis": {
				"read": SecurityLevel.INTERNAL,
				"write": SecurityLevel.INTERNAL,
				"delete": SecurityLevel.CONFIDENTIAL,
				"analyze": SecurityLevel.INTERNAL,
			},
			"user": {
				"read": SecurityLevel.INTERNAL,
				"write": SecurityLevel.CONFIDENTIAL,
				"delete": SecurityLevel.RESTRICTED,
				"manage_roles": SecurityLevel.RESTRICTED,
			},
			"system": {
				"admin": SecurityLevel.TOP_SECRET,
				"config": SecurityLevel.RESTRICTED,
				"monitor": SecurityLevel.CONFIDENTIAL,
			},
			"audit": {
				"read": SecurityLevel.CONFIDENTIAL,
				"write": SecurityLevel.RESTRICTED,
				"delete": SecurityLevel.TOP_SECRET,
			},
		}

		if resource_type in security_requirements and action:
			return security_requirements[resource_type].get(action, SecurityLevel.INTERNAL)

		return SecurityLevel.INTERNAL

	def _check_security_level(self, user_level: SecurityLevel, required_level: SecurityLevel) -> bool:
		"""Check if user security level meets requirement."""
		level_hierarchy = {
			SecurityLevel.PUBLIC: 0,
			SecurityLevel.INTERNAL: 1,
			SecurityLevel.CONFIDENTIAL: 2,
			SecurityLevel.RESTRICTED: 3,
			SecurityLevel.TOP_SECRET: 4,
		}

		user_clearance = level_hierarchy.get(user_level, 0)
		required_clearance = level_hierarchy.get(required_level, 0)

		return user_clearance >= required_clearance

	async def _validate_context_rules(self, user_id: str, permission: Permission, context: PermissionContext) -> bool:
		"""Validate context-specific access rules."""
		try:
			# Resource ownership check
			if context.resource_type and context.resource_id:
				if await self._check_resource_ownership(user_id, context.resource_type, context.resource_id):
					return True

			# Time-based restrictions
			if not self._check_time_restrictions(user_id, permission):
				return False

			# IP-based restrictions
			if context.ip_address and not self._check_ip_restrictions(user_id, context.ip_address):
				return False

			return True

		except Exception as e:
			logger.error(f"Error validating context rules: {e}")
			return False

	async def _check_resource_ownership(self, user_id: str, resource_type: str, resource_id: str) -> bool:
		"""Check if user owns the resource."""
		try:
			if resource_type == "contract_analysis":
				db_manager = await get_database_manager()
				async with db_manager.get_session() as session:
					from sqlalchemy import select
					from ..models.database_models import ContractAnalysis

					result = await session.execute(select(ContractAnalysis.user_id).where(ContractAnalysis.id == resource_id))

					owner_id = result.scalar_one_or_none()
					return str(owner_id) == user_id if owner_id else False

			return False

		except Exception as e:
			logger.error(f"Error checking resource ownership: {e}")
			return False

	def _check_time_restrictions(self, user_id: str, permission: Permission) -> bool:
		"""Check time-based access restrictions."""
		# Implement time-based restrictions if needed
		# For example, certain permissions only during business hours
		return True

	def _check_ip_restrictions(self, user_id: str, ip_address: str) -> bool:
		"""Check IP-based access restrictions."""
		# Implement IP-based restrictions if needed
		# For example, admin access only from certain IP ranges
		return True

	async def _log_access_attempt(self, user_id: str, permission: Permission, allowed: bool, context: Optional[PermissionContext]) -> None:
		"""Log access attempt for audit purposes."""
		try:
			event_type = AuditEventType.UNAUTHORIZED_ACCESS if not allowed else AuditEventType.FILE_ACCESS
			severity = AuditSeverity.HIGH if not allowed else AuditSeverity.LOW

			audit_logger.log_event(
				event_type=event_type,
				action=f"Permission check: {permission.value}",
				result="denied" if not allowed else "granted",
				severity=severity,
				user_id=user_id,
				ip_address=context.ip_address if context else None,
				user_agent=context.user_agent if context else None,
				details={
					"permission": permission.value,
					"resource_type": context.resource_type if context else None,
					"resource_id": context.resource_id if context else None,
					"action": context.action if context else None,
				},
			)

		except Exception as e:
			logger.error(f"Error logging access attempt: {e}")

	def _get_access_reason(self, has_permission: bool, security_level_met: bool, context_validated: bool) -> str:
		"""Get human-readable reason for access decision."""
		if has_permission and security_level_met and context_validated:
			return "Access granted"

		reasons = []
		if not has_permission:
			reasons.append("insufficient permissions")
		if not security_level_met:
			reasons.append("insufficient security clearance")
		if not context_validated:
			reasons.append("context validation failed")

		return f"Access denied: {', '.join(reasons)}"


# Global instance
_rbac_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
	"""Get global RBAC service instance."""
	global _rbac_service
	if _rbac_service is None:
		_rbac_service = RBACService()
	return _rbac_service
