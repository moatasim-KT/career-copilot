"""
IAM Roles and Service Account Management for Career Copilot.
Implements proper role-based access control and service account management.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timezone

from ..core.logging import get_logger

logger = get_logger(__name__)


class Role(Enum):
	"""System roles with hierarchical permissions."""

	ADMIN = "admin"
	MANAGER = "manager"
	USER = "user"
	READONLY = "readonly"
	SERVICE = "service"


class Permission(Enum):
	"""System permissions."""

	# User management
	CREATE_USER = "create_user"
	READ_USER = "read_user"
	UPDATE_USER = "update_user"
	DELETE_USER = "delete_user"

	# Job management
	CREATE_JOB = "create_job"
	READ_JOB = "read_job"
	UPDATE_JOB = "update_job"
	DELETE_JOB = "delete_job"

	# Analytics and reporting
	READ_ANALYTICS = "read_analytics"
	CREATE_REPORT = "create_report"

	# System administration
	MANAGE_SYSTEM = "manage_system"
	VIEW_LOGS = "view_logs"
	MANAGE_ROLES = "manage_roles"

	# API access
	API_ACCESS = "api_access"
	ADMIN_API_ACCESS = "admin_api_access"


@dataclass
class ServiceAccount:
	"""Service account configuration."""

	name: str
	description: str
	roles: List[Role]
	permissions: Set[Permission]
	api_key: Optional[str] = None
	created_at: Optional[datetime] = None
	last_used: Optional[datetime] = None
	is_active: bool = True


class IAMManager:
	"""IAM (Identity and Access Management) Manager."""

	def __init__(self):
		self._role_permissions = self._initialize_role_permissions()
		self._service_accounts: Dict[str, ServiceAccount] = {}
		self._initialize_default_service_accounts()

	def _initialize_role_permissions(self) -> Dict[Role, Set[Permission]]:
		"""Initialize role-permission mappings."""
		return {
			Role.ADMIN: {
				Permission.CREATE_USER,
				Permission.READ_USER,
				Permission.UPDATE_USER,
				Permission.DELETE_USER,
				Permission.CREATE_JOB,
				Permission.READ_JOB,
				Permission.UPDATE_JOB,
				Permission.DELETE_JOB,
				Permission.READ_ANALYTICS,
				Permission.CREATE_REPORT,
				Permission.MANAGE_SYSTEM,
				Permission.VIEW_LOGS,
				Permission.MANAGE_ROLES,
				Permission.API_ACCESS,
				Permission.ADMIN_API_ACCESS,
			},
			Role.MANAGER: {
				Permission.READ_USER,
				Permission.UPDATE_USER,
				Permission.CREATE_JOB,
				Permission.READ_JOB,
				Permission.UPDATE_JOB,
				Permission.DELETE_JOB,
				Permission.READ_ANALYTICS,
				Permission.CREATE_REPORT,
				Permission.API_ACCESS,
			},
			Role.USER: {
				Permission.READ_USER,
				Permission.UPDATE_USER,
				Permission.CREATE_JOB,
				Permission.READ_JOB,
				Permission.UPDATE_JOB,
				Permission.API_ACCESS,
			},
			Role.READONLY: {Permission.READ_USER, Permission.READ_JOB, Permission.READ_ANALYTICS, Permission.API_ACCESS},
			Role.SERVICE: {Permission.API_ACCESS, Permission.READ_JOB, Permission.CREATE_JOB, Permission.UPDATE_JOB},
		}

	def _initialize_default_service_accounts(self):
		"""Initialize default service accounts."""
		# Job ingestion service account
		self.create_service_account(
			name="job_ingestion_service",
			description="Service account for automated job ingestion",
			roles=[Role.SERVICE],
			additional_permissions={Permission.CREATE_JOB, Permission.UPDATE_JOB},
		)

		# Analytics service account
		self.create_service_account(
			name="analytics_service",
			description="Service account for analytics and reporting",
			roles=[Role.SERVICE],
			additional_permissions={Permission.READ_ANALYTICS, Permission.CREATE_REPORT},
		)

		# Notification service account
		self.create_service_account(
			name="notification_service",
			description="Service account for sending notifications",
			roles=[Role.SERVICE],
			additional_permissions={Permission.READ_USER, Permission.READ_JOB},
		)

	def create_service_account(
		self, name: str, description: str, roles: List[Role], additional_permissions: Optional[Set[Permission]] = None
	) -> ServiceAccount:
		"""
		Create a new service account.

		Args:
		    name: Service account name
		    description: Service account description
		    roles: List of roles to assign
		    additional_permissions: Additional permissions beyond role permissions

		Returns:
		    Created service account
		"""
		# Calculate permissions from roles
		permissions = set()
		for role in roles:
			permissions.update(self._role_permissions.get(role, set()))

		# Add additional permissions
		if additional_permissions:
			permissions.update(additional_permissions)

		service_account = ServiceAccount(
			name=name, description=description, roles=roles, permissions=permissions, created_at=datetime.now(timezone.utc), is_active=True
		)

		self._service_accounts[name] = service_account
		logger.info(f"Created service account: {name}")

		return service_account

	def get_service_account(self, name: str) -> Optional[ServiceAccount]:
		"""Get service account by name."""
		return self._service_accounts.get(name)

	def list_service_accounts(self) -> List[ServiceAccount]:
		"""List all service accounts."""
		return list(self._service_accounts.values())

	def has_permission(self, roles: List[Role], permission: Permission) -> bool:
		"""
		Check if roles have a specific permission.

		Args:
		    roles: List of user roles
		    permission: Permission to check

		Returns:
		    True if any role has the permission
		"""
		for role in roles:
			if permission in self._role_permissions.get(role, set()):
				return True
		return False

	def get_user_permissions(self, roles: List[Role]) -> Set[Permission]:
		"""
		Get all permissions for a list of roles.

		Args:
		    roles: List of user roles

		Returns:
		    Set of all permissions
		"""
		permissions = set()
		for role in roles:
			permissions.update(self._role_permissions.get(role, set()))
		return permissions

	def validate_role_hierarchy(self, user_roles: List[Role], required_role: Role) -> bool:
		"""
		Validate role hierarchy (admin > manager > user > readonly).

		Args:
		    user_roles: User's current roles
		    required_role: Required minimum role

		Returns:
		    True if user has sufficient role level
		"""
		role_hierarchy = {Role.READONLY: 1, Role.USER: 2, Role.SERVICE: 2, Role.MANAGER: 3, Role.ADMIN: 4}

		user_level = max(role_hierarchy.get(role, 0) for role in user_roles)
		required_level = role_hierarchy.get(required_role, 0)

		return user_level >= required_level

	def update_service_account_usage(self, name: str):
		"""Update service account last used timestamp."""
		if name in self._service_accounts:
			self._service_accounts[name].last_used = datetime.now(timezone.utc)

	def deactivate_service_account(self, name: str) -> bool:
		"""
		Deactivate a service account.

		Args:
		    name: Service account name

		Returns:
		    True if deactivated successfully
		"""
		if name in self._service_accounts:
			self._service_accounts[name].is_active = False
			logger.info(f"Deactivated service account: {name}")
			return True
		return False

	def activate_service_account(self, name: str) -> bool:
		"""
		Activate a service account.

		Args:
		    name: Service account name

		Returns:
		    True if activated successfully
		"""
		if name in self._service_accounts:
			self._service_accounts[name].is_active = True
			logger.info(f"Activated service account: {name}")
			return True
		return False


# Global IAM manager instance
_iam_manager: Optional[IAMManager] = None


def get_iam_manager() -> IAMManager:
	"""Get the IAM manager instance."""
	global _iam_manager
	if _iam_manager is None:
		_iam_manager = IAMManager()
	return _iam_manager


def require_permission(permission: Permission):
	"""
	Decorator to require specific permission for an endpoint.

	Args:
	    permission: Required permission
	"""

	def decorator(func):
		func._required_permission = permission
		return func

	return decorator


def require_role(role: Role):
	"""
	Decorator to require specific role for an endpoint.

	Args:
	    role: Required minimum role
	"""

	def decorator(func):
		func._required_role = role
		return func

	return decorator
