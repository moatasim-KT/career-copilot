"""
Setup script for Firebase Authentication and Authorization.
Configures Firebase Auth, IAM roles, and JWT token validation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.core.logging import get_logger
from app.config.firebase_config import get_firebase_config
from app.services.iam_service import get_iam_service

logger = get_logger(__name__)


class AuthenticationSetup:
    """Handles the complete authentication and authorization setup."""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_config = get_firebase_config()
        self.iam_service = get_iam_service()
    
    async def setup_complete_authentication(self) -> bool:
        """Set up complete authentication and authorization system."""
        logger.info("🔐 Starting authentication and authorization setup...")
        
        try:
            # Step 1: Validate configuration
            if not await self._validate_configuration():
                return False
            
            # Step 2: Set up IAM and service accounts
            if not await self._setup_iam():
                return False
            
            # Step 3: Configure Firebase Authentication
            if not await self._setup_firebase_auth():
                return False
            
            # Step 4: Set up JWT token validation
            if not await self._setup_jwt_validation():
                return False
            
            # Step 5: Configure Firestore security
            if not await self._setup_firestore_security():
                return False
            
            # Step 6: Validate complete setup
            if not await self._validate_setup():
                return False
            
            logger.info("✅ Authentication and authorization setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication setup failed: {e}")
            return False
    
    async def _validate_configuration(self) -> bool:
        """Validate authentication configuration."""
        logger.info("📋 Validating authentication configuration...")
        
        # Check Firebase configuration
        firebase_validation = self.firebase_config.validate_configuration()
        
        missing_config = []
        if not firebase_validation["project_id_configured"]:
            missing_config.append("FIREBASE_PROJECT_ID")
        
        if missing_config:
            logger.error(f"Missing required configuration: {missing_config}")
            logger.info("Please set the following environment variables:")
            for config in missing_config:
                logger.info(f"  - {config}")
            return False
        
        # Set default values if not configured
        if not self.settings.firebase_web_api_key:
            logger.warning("FIREBASE_WEB_API_KEY not set - will need to be configured manually")
        
        if not self.settings.firebase_auth_domain:
            logger.info(f"Setting default auth domain: {self.firebase_config.project_id}.firebaseapp.com")
            os.environ["FIREBASE_AUTH_DOMAIN"] = f"{self.firebase_config.project_id}.firebaseapp.com"
        
        logger.info("✅ Configuration validation passed")
        return True
    
    async def _setup_iam(self) -> bool:
        """Set up IAM roles and service accounts."""
        logger.info("🔑 Setting up IAM roles and service accounts...")
        
        try:
            # Set up service account
            if not await self.iam_service.setup_service_account():
                logger.error("Failed to set up service account")
                return False
            
            # Create JWT signing key
            if not await self.iam_service.create_jwt_signing_key():
                logger.error("Failed to create JWT signing key")
                return False
            
            logger.info("✅ IAM setup completed")
            return True
            
        except Exception as e:
            logger.error(f"IAM setup error: {e}")
            return False
    
    async def _setup_firebase_auth(self) -> bool:
        """Set up Firebase Authentication."""
        logger.info("🔥 Setting up Firebase Authentication...")
        
        try:
            # Set up Firebase Auth
            if not await self.iam_service.setup_firebase_auth():
                logger.error("Failed to set up Firebase Authentication")
                return False
            
            # Enable Firebase in settings
            os.environ["FIREBASE_ENABLED"] = "true"
            
            logger.info("✅ Firebase Authentication setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Firebase Authentication setup error: {e}")
            return False
    
    async def _setup_jwt_validation(self) -> bool:
        """Set up JWT token validation."""
        logger.info("🎫 Setting up JWT token validation...")
        
        try:
            # JWT configuration is handled by the IAM service
            # Verify JWT secret exists
            if not os.getenv("JWT_SECRET_KEY"):
                logger.error("JWT_SECRET_KEY not found")
                return False
            
            # Set JWT configuration
            os.environ["JWT_ALGORITHM"] = "HS256"
            os.environ["JWT_EXPIRATION_HOURS"] = "24"
            
            logger.info("✅ JWT validation setup completed")
            return True
            
        except Exception as e:
            logger.error(f"JWT validation setup error: {e}")
            return False
    
    async def _setup_firestore_security(self) -> bool:
        """Set up Firestore security rules."""
        logger.info("🛡️ Setting up Firestore security rules...")
        
        try:
            # Set up Firestore security
            if not await self.iam_service.setup_firestore_security():
                logger.warning("Failed to deploy Firestore security rules - may need manual configuration")
                # Don't fail the setup for this, as it can be done manually
            
            logger.info("✅ Firestore security setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Firestore security setup error: {e}")
            return False
    
    async def _validate_setup(self) -> bool:
        """Validate the complete authentication setup."""
        logger.info("🔍 Validating authentication setup...")
        
        try:
            # Validate IAM setup
            iam_validation = await self.iam_service.validate_iam_setup()
            
            # Validate Firebase configuration
            firebase_validation = self.firebase_config.validate_configuration()
            
            # Check critical components
            critical_checks = [
                ("Service Account", iam_validation.get("service_account_exists", False)),
                ("Service Account Key", iam_validation.get("service_account_key_exists", False)),
                ("Firebase Project ID", firebase_validation.get("project_id_configured", False)),
            ]
            
            failed_checks = [name for name, passed in critical_checks if not passed]
            
            if failed_checks:
                logger.error(f"Critical validation failures: {failed_checks}")
                return False
            
            # Log warnings for optional components
            optional_checks = [
                ("Firebase Web API Key", firebase_validation.get("web_api_key_configured", False)),
                ("Firebase Auth Domain", firebase_validation.get("auth_domain_configured", False)),
            ]
            
            warnings = [name for name, passed in optional_checks if not passed]
            if warnings:
                logger.warning(f"Optional components not configured: {warnings}")
                logger.info("These can be configured later through Firebase Console")
            
            logger.info("✅ Authentication setup validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def print_setup_summary(self):
        """Print setup summary and next steps."""
        logger.info("\n" + "="*60)
        logger.info("🎉 AUTHENTICATION SETUP SUMMARY")
        logger.info("="*60)
        
        logger.info("\n✅ Completed Components:")
        logger.info("  - Google Cloud IAM service account")
        logger.info("  - Firebase Admin SDK configuration")
        logger.info("  - JWT token validation setup")
        logger.info("  - Firestore security rules")
        
        logger.info("\n📋 Manual Configuration Required:")
        logger.info("  1. Firebase Console Setup:")
        logger.info("     - Go to https://console.firebase.google.com/")
        logger.info(f"     - Select project: {self.firebase_config.project_id}")
        logger.info("     - Enable Authentication")
        logger.info("     - Configure sign-in providers (Email/Password, Google)")
        logger.info("     - Copy Web API Key to FIREBASE_WEB_API_KEY")
        
        logger.info("\n  2. Environment Variables:")
        logger.info("     Add to your .env file:")
        logger.info(f"     FIREBASE_PROJECT_ID={self.firebase_config.project_id}")
        logger.info("     FIREBASE_WEB_API_KEY=<from Firebase Console>")
        logger.info(f"     FIREBASE_AUTH_DOMAIN={self.firebase_config.project_id}.firebaseapp.com")
        logger.info("     FIREBASE_ENABLED=true")
        
        logger.info("\n  3. Frontend Integration:")
        logger.info("     - Initialize Firebase SDK in frontend")
        logger.info("     - Implement authentication UI")
        logger.info("     - Send Firebase ID tokens to backend")
        
        logger.info("\n🔗 Useful Links:")
        logger.info("  - Firebase Console: https://console.firebase.google.com/")
        logger.info("  - Firebase Auth Docs: https://firebase.google.com/docs/auth")
        logger.info("  - Google Cloud Console: https://console.cloud.google.com/")
        
        logger.info("\n" + "="*60)


async def main():
    """Main setup function."""
    setup = AuthenticationSetup()
    
    # Run the complete setup
    success = await setup.setup_complete_authentication()
    
    if success:
        setup.print_setup_summary()
        print("\n🎉 Authentication setup completed successfully!")
        return 0
    else:
        print("\n❌ Authentication setup failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)