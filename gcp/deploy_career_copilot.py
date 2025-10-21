#!/usr/bin/env python3
"""
Comprehensive deployment orchestration script for Career Copilot on Google Cloud
"""

import os
import sys
import subprocess
import logging
import time
from typing import Dict, Any, List
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from .environment_config import config_manager
from .iam_setup import setup_iam
from .scheduler_setup import setup_scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CareerCopilotDeployer:
    """Orchestrates the complete deployment of Career Copilot to Google Cloud"""
    
    def __init__(self, project_id: str, region: str = "us-central1", environment: str = "production"):
        self.project_id = project_id
        self.region = region
        self.environment = environment
        self.config = config_manager.get_environment_config(environment)
        
        # Validate environment configuration
        if not config_manager.validate_environment(environment):
            raise ValueError(f"Invalid configuration for environment: {environment}")
    
    def check_prerequisites(self) -> bool:
        """Check that all prerequisites are met"""
        logger.info("Checking deployment prerequisites...")
        
        prerequisites = [
            ("gcloud", "Google Cloud SDK"),
            ("python", "Python 3.7+"),
            ("pip", "Python package manager")
        ]
        
        missing = []
        for cmd, description in prerequisites:
            if not self._command_exists(cmd):
                missing.append(f"{description} ({cmd})")
        
        if missing:
            logger.error(f"Missing prerequisites: {', '.join(missing)}")
            return False
        
        # Check gcloud authentication
        try:
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                                  capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                logger.error("No active gcloud authentication found. Run 'gcloud auth login'")
                return False
        except Exception as e:
            logger.error(f"Error checking gcloud authentication: {e}")
            return False
        
        # Set project
        try:
            subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], 
                         check=True, capture_output=True)
            logger.info(f"Set gcloud project to {self.project_id}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set gcloud project: {e}")
            return False
        
        logger.info("✅ All prerequisites met")
        return True
    
    def enable_apis(self) -> bool:
        """Enable required Google Cloud APIs"""
        logger.info("Enabling required Google Cloud APIs...")
        
        required_apis = config_manager.get_required_apis()
        
        for api in required_apis:
            try:
                logger.info(f"Enabling {api}...")
                subprocess.run([
                    'gcloud', 'services', 'enable', api,
                    f'--project={self.project_id}'
                ], check=True, capture_output=True)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to enable {api}: {e}")
                return False
        
        # Wait for APIs to be fully enabled
        logger.info("Waiting for APIs to be fully enabled...")
        time.sleep(30)
        
        logger.info("✅ All required APIs enabled")
        return True
    
    def setup_iam_roles(self) -> bool:
        """Set up IAM roles and service accounts"""
        logger.info("Setting up IAM roles and service accounts...")
        
        try:
            success = setup_iam(self.project_id, self.environment)
            if success:
                logger.info("✅ IAM setup completed")
                return True
            else:
                logger.error("❌ IAM setup failed")
                return False
        except Exception as e:
            logger.error(f"Error during IAM setup: {e}")
            return False
    
    def create_firestore_database(self) -> bool:
        """Create Firestore database if it doesn't exist"""
        logger.info("Setting up Firestore database...")
        
        try:
            # Check if database already exists
            result = subprocess.run([
                'gcloud', 'firestore', 'databases', 'list',
                f'--project={self.project_id}',
                '--format=json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                databases = json.loads(result.stdout)
                if databases:
                    logger.info("✅ Firestore database already exists")
                    return True
            
            # Create database
            logger.info("Creating Firestore database...")
            subprocess.run([
                'gcloud', 'firestore', 'databases', 'create',
                f'--location={self.region}',
                '--type=firestore-native',
                f'--project={self.project_id}'
            ], check=True, capture_output=True)
            
            logger.info("✅ Firestore database created")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Firestore database: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting up Firestore: {e}")
            return False
    
    def deploy_cloud_functions(self) -> bool:
        """Deploy all Cloud Functions"""
        logger.info("Deploying Cloud Functions...")
        
        functions_config = self.config.get('functions', {})
        env_vars = config_manager.get_environment_variables(self.environment)
        env_vars_str = ','.join([f"{k}={v}" for k, v in env_vars.items()])
        
        service_account = f"career-copilot-sa@{self.project_id}.iam.gserviceaccount.com"
        
        functions = [
            {
                'name': 'career-copilot-api',
                'entry_point': 'career_copilot_api',
                'trigger': 'http',
                'allow_unauthenticated': True,
                'memory': functions_config.get('memory', '1Gi'),
                'timeout': functions_config.get('timeout', '540s'),
                'max_instances': functions_config.get('max_instances', 10)
            },
            {
                'name': 'job-ingestion-scheduler',
                'entry_point': 'job_ingestion_scheduler',
                'trigger': 'http',
                'allow_unauthenticated': False,
                'memory': '512Mi',
                'timeout': '540s',
                'max_instances': 5
            },
            {
                'name': 'morning-briefing-scheduler',
                'entry_point': 'morning_briefing_scheduler',
                'trigger': 'http',
                'allow_unauthenticated': False,
                'memory': '512Mi',
                'timeout': '300s',
                'max_instances': 3
            },
            {
                'name': 'evening-update-scheduler',
                'entry_point': 'evening_update_scheduler',
                'trigger': 'http',
                'allow_unauthenticated': False,
                'memory': '512Mi',
                'timeout': '300s',
                'max_instances': 3
            }
        ]
        
        for func in functions:
            try:
                logger.info(f"Deploying function {func['name']}...")
                
                cmd = [
                    'gcloud', 'functions', 'deploy', func['name'],
                    '--gen2',
                    '--runtime=python311',
                    f'--region={self.region}',
                    '--source=.',
                    f'--entry-point={func["entry_point"]}',
                    f'--trigger={func["trigger"]}',
                    f'--service-account={service_account}',
                    f'--memory={func["memory"]}',
                    f'--timeout={func["timeout"]}',
                    f'--max-instances={func["max_instances"]}',
                    f'--set-env-vars={env_vars_str}'
                ]
                
                if func['allow_unauthenticated']:
                    cmd.append('--allow-unauthenticated')
                else:
                    cmd.append('--no-allow-unauthenticated')
                
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"✅ Function {func['name']} deployed successfully")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to deploy function {func['name']}: {e}")
                return False
        
        logger.info("✅ All Cloud Functions deployed")
        return True
    
    def setup_cloud_scheduler(self) -> bool:
        """Set up Cloud Scheduler jobs"""
        logger.info("Setting up Cloud Scheduler jobs...")
        
        try:
            success = setup_scheduler(self.project_id, self.region, self.environment)
            if success:
                logger.info("✅ Cloud Scheduler setup completed")
                return True
            else:
                logger.error("❌ Cloud Scheduler setup failed")
                return False
        except Exception as e:
            logger.error(f"Error during Cloud Scheduler setup: {e}")
            return False
    
    def create_firestore_indexes(self) -> bool:
        """Create Firestore indexes for optimal performance"""
        logger.info("Creating Firestore indexes...")
        
        indexes = [
            {
                'collection': 'jobs',
                'fields': [
                    {'field': 'user_id', 'order': 'ascending'},
                    {'field': 'status', 'order': 'ascending'},
                    {'field': 'created_at', 'order': 'descending'}
                ]
            },
            {
                'collection': 'applications',
                'fields': [
                    {'field': 'user_id', 'order': 'ascending'},
                    {'field': 'applied_at', 'order': 'descending'}
                ]
            },
            {
                'collection': 'analytics',
                'fields': [
                    {'field': 'user_id', 'order': 'ascending'},
                    {'field': 'type', 'order': 'ascending'},
                    {'field': 'generated_at', 'order': 'descending'}
                ]
            }
        ]
        
        for index in indexes:
            try:
                cmd = ['gcloud', 'firestore', 'indexes', 'composite', 'create']
                cmd.append(f'--collection-group={index["collection"]}')
                
                for field in index['fields']:
                    cmd.append(f'--field-config=field-path={field["field"]},order={field["order"]}')
                
                cmd.extend([f'--project={self.project_id}', '--quiet'])
                
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"✅ Index created for {index['collection']}")
                
            except subprocess.CalledProcessError as e:
                # Index might already exist, which is fine
                if "already exists" in str(e):
                    logger.info(f"Index for {index['collection']} already exists")
                else:
                    logger.warning(f"Failed to create index for {index['collection']}: {e}")
        
        logger.info("✅ Firestore indexes setup completed")
        return True
    
    def validate_deployment(self) -> bool:
        """Validate the deployment"""
        logger.info("Validating deployment...")
        
        try:
            validator = DeploymentValidator(self.project_id, self.region, self.environment)
            results = validator.run_full_validation()
            
            summary = results.get('summary', {})
            overall_status = summary.get('overall_status', 'FAIL')
            
            if overall_status in ['PASS', 'PASS_WITH_WARNINGS']:
                logger.info(f"✅ Deployment validation {overall_status}")
                return True
            else:
                logger.error(f"❌ Deployment validation {overall_status}")
                
                # Print critical failures
                critical_failures = summary.get('critical_failures', [])
                if critical_failures:
                    logger.error(f"Critical failures: {', '.join(critical_failures)}")
                
                return False
                
        except Exception as e:
            logger.error(f"Error during deployment validation: {e}")
            return False
    
    def deploy(self) -> bool:
        """Execute the complete deployment process"""
        logger.info(f"🚀 Starting Career Copilot deployment to Google Cloud")
        logger.info(f"Project: {self.project_id}")
        logger.info(f"Region: {self.region}")
        logger.info(f"Environment: {self.environment}")
        logger.info("=" * 60)
        
        deployment_steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Enable APIs", self.enable_apis),
            ("Setup IAM", self.setup_iam_roles),
            ("Create Firestore Database", self.create_firestore_database),
            ("Deploy Cloud Functions", self.deploy_cloud_functions),
            ("Setup Cloud Scheduler", self.setup_cloud_scheduler),
            ("Create Firestore Indexes", self.create_firestore_indexes),
            ("Validate Deployment", self.validate_deployment)
        ]
        
        for step_name, step_func in deployment_steps:
            logger.info(f"📋 Step: {step_name}")
            
            try:
                if not step_func():
                    logger.error(f"❌ Step failed: {step_name}")
                    return False
                    
                logger.info(f"✅ Step completed: {step_name}")
                
            except Exception as e:
                logger.error(f"❌ Step failed with exception: {step_name} - {e}")
                return False
        
        logger.info("=" * 60)
        logger.info("🎉 Career Copilot deployment completed successfully!")
        logger.info(f"🌐 API URL: https://{self.region}-{self.project_id}.cloudfunctions.net/career-copilot-api")
        
        # Print next steps
        logger.info("\n📋 Next steps:")
        logger.info("1. Test the API endpoints")
        logger.info("2. Configure your frontend to use the API URL")
        logger.info("3. Set up monitoring alerts (run: python gcp/setup_monitoring.py)")
        logger.info("4. Run health checks (run: python gcp/monitoring_health_check.py)")
        logger.info("5. Configure your domain (if applicable)")
        
        return True
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH"""
        try:
            subprocess.run([command, '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Career Copilot to Google Cloud')
    parser.add_argument('--project-id', required=True, help='Google Cloud Project ID')
    parser.add_argument('--region', default='us-central1', help='Google Cloud Region')
    parser.add_argument('--environment', default='production', 
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only run validation, skip deployment')
    
    args = parser.parse_args()
    
    # Set environment variables for other scripts
    os.environ['PROJECT_ID'] = args.project_id
    os.environ['REGION'] = args.region
    os.environ['ENVIRONMENT'] = args.environment
    
    try:
        deployer = CareerCopilotDeployer(args.project_id, args.region, args.environment)
        
        if args.validate_only:
            success = deployer.validate_deployment()
        else:
            success = deployer.deploy()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Deployment failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()