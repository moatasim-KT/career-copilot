"""
IAM role setup and management for Career Copilot Google Cloud deployment
"""

import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from .environment_config import config_manager

logger = logging.getLogger(__name__)


class IAMManager:
    """Manages IAM roles and service accounts for Career Copilot deployment"""
    
    def __init__(self, project_id: str, environment: str = 'production'):
        self.project_id = project_id
        self.environment = environment
        self.config = config_manager.get_environment_config(environment)
        self.service_account_name = 'career-copilot-sa'
        self.service_account_email = f"{self.service_account_name}@{project_id}.iam.gserviceaccount.com"
    
    def create_service_account(self) -> bool:
        """Create the Career Copilot service account"""
        try:
            cmd = [
                'gcloud', 'iam', 'service-accounts', 'create', self.service_account_name,
                '--display-name=Career Copilot Service Account',
                '--description=Service account for Career Copilot Cloud Functions',
                '--project', self.project_id
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
    
    def grant_iam_roles(self) -> bool:
        """Grant required IAM roles to the service account"""
        required_roles = config_manager.get_iam_roles()
        
        success = True
        for role in required_roles:
            if not self._grant_role(role):
                success = False
        
        # Grant additional environment-specific roles
        additional_roles = [
            'roles/secretmanager.secretAccessor',  # For accessing secrets
            'roles/cloudscheduler.jobRunner',      # For scheduler jobs
            'roles/cloudsql.client'                # If using Cloud SQL
        ]
        
        for role in additional_roles:
            self._grant_role(role)  # Don't fail deployment for optional roles
        
        return success
    
    def _grant_role(self, role: str) -> bool:
        """Grant a specific IAM role to the service account"""
        try:
            cmd = [
                'gcloud', 'projects', 'add-iam-policy-binding', self.project_id,
                f'--member=serviceAccount:{self.service_account_email}',
                f'--role={role}'
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
    
    def create_custom_roles(self) -> bool:
        """Create custom IAM roles if needed"""
        custom_roles = [
            {
                'role_id': 'careerCopilotFunction',
                'title': 'Career Copilot Function Role',
                'description': 'Custom role for Career Copilot Cloud Functions',
                'permissions': [
                    'datastore.entities.create',
                    'datastore.entities.delete',
                    'datastore.entities.get',
                    'datastore.entities.list',
                    'datastore.entities.update',
                    'logging.logEntries.create',
                    'monitoring.metricDescriptors.create',
                    'monitoring.metricDescriptors.get',
                    'monitoring.metricDescriptors.list',
                    'monitoring.timeSeries.create'
                ]
            }
        ]
        
        success = True
        for role_def in custom_roles:
            if not self._create_custom_role(role_def):
                success = False
        
        return success
    
    def _create_custom_role(self, role_definition: Dict[str, Any]) -> bool:
        """Create a custom IAM role"""
        try:
            # Create role definition file
            role_file = f"/tmp/{role_definition['role_id']}.yaml"
            role_yaml = f"""
title: "{role_definition['title']}"
description: "{role_definition['description']}"
stage: "GA"
includedPermissions:
{chr(10).join([f'- {perm}' for perm in role_definition['permissions']])}
"""
            
            with open(role_file, 'w') as f:
                f.write(role_yaml)
            
            cmd = [
                'gcloud', 'iam', 'roles', 'create', role_definition['role_id'],
                f'--project={self.project_id}',
                f'--file={role_file}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Created custom role: {role_definition['role_id']}")
                return True
            elif "already exists" in result.stderr:
                logger.info(f"Custom role already exists: {role_definition['role_id']}")
                return True
            else:
                logger.error(f"Failed to create custom role: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating custom role: {e}")
            return False
    
    def setup_firestore_security_rules(self) -> bool:
        """Set up Firestore security rules"""
        security_rules = """
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
    
    // Applications are user-specific
    match /applications/{applicationId} {
      allow read, write: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
    }
    
    // Analytics are user-specific
    match /analytics/{analyticsId} {
      allow read, write: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
    }
    
    // Allow service account access for Cloud Functions
    match /{document=**} {
      allow read, write: if request.auth.token.email == 
        "career-copilot-sa@" + resource.data.project_id + ".iam.gserviceaccount.com";
    }
  }
}
"""
        
        try:
            # Write rules to temporary file
            rules_file = "/tmp/firestore.rules"
            with open(rules_file, 'w') as f:
                f.write(security_rules)
            
            cmd = [
                'gcloud', 'firestore', 'deploy', '--rules', rules_file,
                '--project', self.project_id
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Firestore security rules deployed successfully")
                return True
            else:
                logger.error(f"Failed to deploy Firestore rules: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up Firestore security rules: {e}")
            return False
    
    def verify_permissions(self) -> Dict[str, bool]:
        """Verify that the service account has all required permissions"""
        verification_results = {}
        
        # Test basic permissions
        test_permissions = [
            'datastore.entities.list',
            'logging.logEntries.create',
            'monitoring.timeSeries.create'
        ]
        
        for permission in test_permissions:
            verification_results[permission] = self._test_permission(permission)
        
        return verification_results
    
    def _test_permission(self, permission: str) -> bool:
        """Test if service account has a specific permission"""
        try:
            cmd = [
                'gcloud', 'projects', 'test-iam-permissions', self.project_id,
                f'--permissions={permission}',
                f'--impersonate-service-account={self.service_account_email}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error testing permission {permission}: {e}")
            return False
    
    def cleanup_iam_resources(self) -> bool:
        """Clean up IAM resources (for development/testing)"""
        if self.environment == 'production':
            logger.warning("Cleanup not allowed in production environment")
            return False
        
        try:
            # Remove IAM policy bindings
            roles = config_manager.get_iam_roles()
            for role in roles:
                cmd = [
                    'gcloud', 'projects', 'remove-iam-policy-binding', self.project_id,
                    f'--member=serviceAccount:{self.service_account_email}',
                    f'--role={role}'
                ]
                subprocess.run(cmd, capture_output=True, text=True)
            
            # Delete service account
            cmd = [
                'gcloud', 'iam', 'service-accounts', 'delete', self.service_account_email,
                '--project', self.project_id,
                '--quiet'
            ]
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


def setup_iam(project_id: str, environment: str = 'production') -> bool:
    """Main function to set up IAM for Career Copilot deployment"""
    iam_manager = IAMManager(project_id, environment)
    
    logger.info(f"Setting up IAM for project {project_id} in {environment} environment")
    
    # Create service account
    if not iam_manager.create_service_account():
        logger.error("Failed to create service account")
        return False
    
    # Grant IAM roles
    if not iam_manager.grant_iam_roles():
        logger.error("Failed to grant all required IAM roles")
        return False
    
    # Create custom roles if needed
    iam_manager.create_custom_roles()
    
    # Set up Firestore security rules
    iam_manager.setup_firestore_security_rules()
    
    # Verify permissions
    verification_results = iam_manager.verify_permissions()
    failed_permissions = [perm for perm, success in verification_results.items() if not success]
    
    if failed_permissions:
        logger.warning(f"Some permissions could not be verified: {failed_permissions}")
    
    logger.info("IAM setup completed successfully")
    return True


if __name__ == "__main__":
    import sys
    import os
    
    project_id = os.getenv('PROJECT_ID')
    environment = os.getenv('ENVIRONMENT', 'production')
    
    if not project_id:
        print("Error: PROJECT_ID environment variable not set")
        sys.exit(1)
    
    if setup_iam(project_id, environment):
        print("✅ IAM setup completed successfully")
    else:
        print("❌ IAM setup failed")
        sys.exit(1)