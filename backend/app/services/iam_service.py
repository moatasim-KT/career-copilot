"""
IAM Service for Career Copilot System.
Manages Identity and Access Management for Google Cloud and Firebase.
"""

import subprocess
import os
from typing import Dict, List, Optional
from pathlib import Path

from ..core.config import get_settings
from ..core.logging import get_logger
from ..config.firebase_config import get_firebase_config

logger = get_logger(__name__)


class IAMService:
	"""Service for managing IAM roles and service accounts."""

	def __init__(self):
		self.settings = get_settings()
		self.firebase_config = get_firebase_config()
		self.project_id = self.firebase_config.project_id
		self.service_account_name = "career-copilot-sa"
		self.service_account_email = f"{self.service_account_name}@{self.project_id}.iam.gserviceaccount.com"

	async def setup_service_account(self) -> bool:
		"""Set up the main service account for Career Copilot."""
		try:
			# Create service account
			if not await self._create_service_account():
				return False

			# Grant required roles
			if not await self._grant_required_roles():
				return False

			# Generate and download service account key
			if not await self._create_service_account_key():
				return False

			logger.info("Service account setup completed successfully")
			return True

		except Exception as e:
			logger.error(f"Error setting up service account: {e}")
			return False

	async def _create_service_account(self) -> bool:
		"""Create the Career Copilot service account."""
		try:
			cmd = [
				"gcloud",
				"iam",
				"service-accounts",
				"create",
				self.service_account_name,
				"--display-name=Career Copilot Service Account",
				"--description=Service account for Career Copilot system operations",
				"--project",
				self.project_id,
			]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info(f"Service account created: {self.service_account_email}")
				return True
			elif "already exists" in result.stderr:
				logger.info(f"Service account already exists: {self.service_account_email}")
				return True
			else:
				logger.error(f"Failed to create service account: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error creating service account: {e}")
			return False

	async def _grant_required_roles(self) -> bool:
		"""Grant required IAM roles to the service account."""
		required_roles = [
			"roles/datastore.user",  # Firestore access
			"roles/cloudfunctions.invoker",  # Cloud Functions access
			"roles/cloudscheduler.jobRunner",  # Cloud Scheduler access
			"roles/logging.logWriter",  # Logging access
			"roles/monitoring.metricWriter",  # Monitoring access
			"roles/secretmanager.secretAccessor",  # Secret Manager access
			"roles/firebase.admin",  # Firebase Admin access
		]

		success = True
		for role in required_roles:
			if not await self._grant_role(role):
				success = False

		return success

	async def _grant_role(self, role: str) -> bool:
		"""Grant a specific IAM role to the service account."""
		try:
			cmd = [
				"gcloud",
				"projects",
				"add-iam-policy-binding",
				self.project_id,
				f"--member=serviceAccount:{self.service_account_email}",
				f"--role={role}",
			]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info(f"Granted role {role} to {self.service_account_email}")
				return True
			else:
				logger.error(f"Failed to grant role {role}: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error granting role {role}: {e}")
			return False

	async def _create_service_account_key(self) -> bool:
		"""Create and download service account key."""
		try:
			# Ensure secrets directory exists
			secrets_dir = Path("secrets")
			secrets_dir.mkdir(exist_ok=True)

			key_file_path = secrets_dir / "firebase-service-account.json"

			cmd = [
				"gcloud",
				"iam",
				"service-accounts",
				"keys",
				"create",
				str(key_file_path),
				f"--iam-account={self.service_account_email}",
				"--project",
				self.project_id,
			]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info(f"Service account key created: {key_file_path}")

				# Update environment variable
				os.environ["FIREBASE_SERVICE_ACCOUNT_KEY"] = str(key_file_path)

				return True
			else:
				logger.error(f"Failed to create service account key: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error creating service account key: {e}")
			return False

	async def setup_firebase_auth(self) -> bool:
		"""Set up Firebase Authentication configuration."""
		try:
			# Enable Firebase Authentication
			if not await self._enable_firebase_auth():
				return False

			# Configure authentication providers
			if not await self._configure_auth_providers():
				return False

			# Set up custom claims
			if not await self._setup_custom_claims():
				return False

			logger.info("Firebase Authentication setup completed")
			return True

		except Exception as e:
			logger.error(f"Error setting up Firebase Authentication: {e}")
			return False

	async def _enable_firebase_auth(self) -> bool:
		"""Enable Firebase Authentication API."""
		try:
			cmd = ["gcloud", "services", "enable", "firebase.googleapis.com", "--project", self.project_id]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info("Firebase API enabled")
				return True
			else:
				logger.error(f"Failed to enable Firebase API: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error enabling Firebase API: {e}")
			return False

	async def _configure_auth_providers(self) -> List[str]:
		"""Configure Firebase Authentication providers."""
		# This would typically be done through Firebase Console or Firebase CLI
		# For now, we'll return the list of providers to configure manually
		providers = [
			"email/password",
			"google.com",
			"github.com",  # Optional
		]

		logger.info(f"Configure these authentication providers in Firebase Console: {providers}")
		return providers

	async def _setup_custom_claims(self) -> bool:
		"""Set up custom claims structure for user roles."""
		# Custom claims are set programmatically through Firebase Admin SDK
		# This defines the structure we'll use
		custom_claims_structure = {
			"roles": ["user", "admin"],
			"permissions": ["read_jobs", "write_jobs", "read_profile", "write_profile", "read_analytics", "admin_access"],
			"subscription_level": "free",  # free, premium, enterprise
		}

		logger.info(f"Custom claims structure defined: {custom_claims_structure}")
		return True

	async def setup_firestore_security(self) -> bool:
		"""Set up Firestore security rules."""
		try:
			# Get security rules
			security_rules = self.firebase_config.get_firestore_security_rules()

			# Write rules to temporary file
			rules_file = Path("/tmp/firestore.rules")
			with open(rules_file, "w") as f:
				f.write(security_rules)

			# Deploy security rules
			cmd = ["gcloud", "firestore", "deploy", "--rules", str(rules_file), "--project", self.project_id]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info("Firestore security rules deployed successfully")
				return True
			else:
				logger.error(f"Failed to deploy Firestore rules: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error setting up Firestore security: {e}")
			return False

	async def create_jwt_signing_key(self) -> bool:
		"""Create JWT signing key for token validation."""
		try:
			# Generate a secure random key for JWT signing
			import secrets

			jwt_secret = secrets.token_urlsafe(64)

			# Store in secrets directory
			secrets_dir = Path("secrets")
			secrets_dir.mkdir(exist_ok=True)

			jwt_secret_file = secrets_dir / "jwt_secret.txt"
			with open(jwt_secret_file, "w") as f:
				f.write(jwt_secret)

			# Update environment variable
			os.environ["JWT_SECRET_KEY"] = jwt_secret

			logger.info("JWT signing key created and configured")
			return True

		except Exception as e:
			logger.error(f"Error creating JWT signing key: {e}")
			return False

	async def validate_iam_setup(self) -> Dict[str, bool]:
		"""Validate IAM setup and permissions."""
		validation_results = {
			"service_account_exists": False,
			"required_roles_granted": False,
			"service_account_key_exists": False,
			"firebase_enabled": False,
			"firestore_accessible": False,
		}

		try:
			# Check if service account exists
			cmd = ["gcloud", "iam", "service-accounts", "describe", self.service_account_email, "--project", self.project_id]

			result = subprocess.run(cmd, capture_output=True, text=True)
			validation_results["service_account_exists"] = result.returncode == 0

			# Check if service account key file exists
			if self.settings.firebase_service_account_key:
				key_path = Path(self.settings.firebase_service_account_key)
				validation_results["service_account_key_exists"] = key_path.exists()

			# Additional validation would go here

		except Exception as e:
			logger.error(f"Error validating IAM setup: {e}")

		return validation_results

	async def cleanup_iam_resources(self) -> bool:
		"""Clean up IAM resources (for development/testing only)."""
		if self.settings.environment == "production":
			logger.warning("Cleanup not allowed in production environment")
			return False

		try:
			# Delete service account
			cmd = ["gcloud", "iam", "service-accounts", "delete", self.service_account_email, "--project", self.project_id, "--quiet"]

			result = subprocess.run(cmd, capture_output=True, text=True)

			if result.returncode == 0:
				logger.info("IAM resources cleaned up successfully")
				return True
			else:
				logger.error(f"Failed to cleanup IAM resources: {result.stderr}")
				return False

		except Exception as e:
			logger.error(f"Error during IAM cleanup: {e}")
			return False


# Global service instance
_iam_service: Optional[IAMService] = None


def get_iam_service() -> IAMService:
	"""Get the IAM service instance."""
	global _iam_service
	if _iam_service is None:
		_iam_service = IAMService()
	return _iam_service
