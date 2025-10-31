"""
Firebase Configuration for Career Copilot System.
Handles Firebase project setup and service account configuration.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class FirebaseConfig:
	"""Firebase configuration manager."""

	def __init__(self):
		self.settings = get_settings()
		self.project_id = self.settings.firebase_project_id or "career-copilot-system"
		self.service_account_path = self.settings.firebase_service_account_key

	def get_firebase_config(self) -> Dict[str, Any]:
		"""Get Firebase configuration for client-side initialization."""
		return {
			"apiKey": self.settings.firebase_web_api_key,
			"authDomain": self.settings.firebase_auth_domain or f"{self.project_id}.firebaseapp.com",
			"projectId": self.project_id,
			"storageBucket": f"{self.project_id}.appspot.com",
			"messagingSenderId": "123456789012",  # Would be from Firebase console
			"appId": "1:123456789012:web:abcdef123456",  # Would be from Firebase console
		}

	def get_service_account_config(self) -> Optional[Dict[str, Any]]:
		"""Get service account configuration for server-side Firebase Admin SDK."""
		if not self.service_account_path:
			logger.warning("Firebase service account key path not configured")
			return None

		try:
			service_account_path = Path(self.service_account_path)
			if not service_account_path.exists():
				logger.error(f"Firebase service account file not found: {self.service_account_path}")
				return None

			with open(service_account_path, "r") as f:
				return json.load(f)

		except Exception as e:
			logger.error(f"Error loading Firebase service account: {e}")
			return None

	def create_service_account_file(self, service_account_data: Dict[str, Any]) -> bool:
		"""Create Firebase service account file from provided data."""
		try:
			# Ensure secrets directory exists
			secrets_dir = Path("secrets")
			secrets_dir.mkdir(exist_ok=True)

			# Write service account file
			service_account_path = secrets_dir / "firebase-service-account.json"
			with open(service_account_path, "w") as f:
				json.dump(service_account_data, f, indent=2)

			# Update settings
			os.environ["FIREBASE_SERVICE_ACCOUNT_KEY"] = str(service_account_path)

			logger.info(f"Firebase service account file created: {service_account_path}")
			return True

		except Exception as e:
			logger.error(f"Error creating Firebase service account file: {e}")
			return False

	def validate_configuration(self) -> Dict[str, bool]:
		"""Validate Firebase configuration."""
		validation_results = {
			"project_id_configured": bool(self.project_id),
			"web_api_key_configured": bool(self.settings.firebase_web_api_key),
			"auth_domain_configured": bool(self.settings.firebase_auth_domain),
			"service_account_configured": bool(self.service_account_path),
			"service_account_file_exists": False,
			"service_account_valid": False,
		}

		# Check service account file
		if self.service_account_path:
			service_account_path = Path(self.service_account_path)
			validation_results["service_account_file_exists"] = service_account_path.exists()

			if service_account_path.exists():
				try:
					with open(service_account_path, "r") as f:
						service_account_data = json.load(f)

					# Validate required fields
					required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
					validation_results["service_account_valid"] = all(field in service_account_data for field in required_fields)

				except Exception as e:
					logger.error(f"Error validating service account file: {e}")

		return validation_results

	def get_firestore_security_rules(self) -> str:
		"""Get Firestore security rules for Career Copilot."""
		return """
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Jobs are user-specific
    match /jobs/{jobId} {
      allow read, write: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
    }
    
    // User profiles are user-specific
    match /profiles/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Analytics are user-specific
    match /analytics/{analyticsId} {
      allow read, write: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
    }
    
    // Recommendations are user-specific
    match /recommendations/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Allow service account access for Cloud Functions
    match /{document=**} {
      allow read, write: if request.auth.token.email.matches('.*@' + resource.__name__.split('/')[1] + '.iam.gserviceaccount.com$');
    }
  }
}
"""


# Global configuration instance
_firebase_config: Optional[FirebaseConfig] = None


def get_firebase_config() -> FirebaseConfig:
	"""Get the Firebase configuration instance."""
	global _firebase_config
	if _firebase_config is None:
		_firebase_config = FirebaseConfig()
	return _firebase_config
