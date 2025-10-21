"""
Cloud Scheduler setup and management for Career Copilot
"""

import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .environment_config import config_manager

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages Cloud Scheduler jobs for Career Copilot"""
    
    def __init__(self, project_id: str, region: str, environment: str = 'production'):
        self.project_id = project_id
        self.region = region
        self.environment = environment
        self.config = config_manager.get_environment_config(environment)
        self.service_account_email = f"career-copilot-sa@{project_id}.iam.gserviceaccount.com"
    
    def create_scheduler_jobs(self) -> bool:
        """Create all scheduler jobs for Career Copilot"""
        scheduler_config = self.config.get('scheduler', {})
        
        jobs = [
            {
                'name': 'job-ingestion-cron',
                'description': 'Automated job ingestion for all users',
                'schedule': scheduler_config.get('job_ingestion', '0 */4 * * *'),
                'function_name': 'job-ingestion-scheduler',
                'timeout': '540s'
            },
            {
                'name': 'morning-briefing-cron',
                'description': 'Daily morning briefings with job recommendations',
                'schedule': scheduler_config.get('morning_briefing', '0 8 * * *'),
                'function_name': 'morning-briefing-scheduler',
                'timeout': '300s'
            },
            {
                'name': 'evening-update-cron',
                'description': 'Daily evening summaries for users with applications',
                'schedule': scheduler_config.get('evening_update', '0 18 * * *'),
                'function_name': 'evening-update-scheduler',
                'timeout': '300s'
            }
        ]
        
        success = True
        for job in jobs:
            if not self._create_scheduler_job(job):
                success = False
        
        return success
    
    def _create_scheduler_job(self, job_config: Dict[str, str]) -> bool:
        """Create a single scheduler job"""
        try:
            # Delete existing job if it exists
            self._delete_scheduler_job(job_config['name'])
            
            function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{job_config['function_name']}"
            
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'create', 'http', job_config['name'],
                f'--location={self.region}',
                f'--schedule={job_config["schedule"]}',
                f'--uri={function_url}',
                '--http-method=POST',
                f'--oidc-service-account-email={self.service_account_email}',
                '--time-zone=UTC',
                f'--description={job_config["description"]}',
                f'--attempt-deadline={job_config.get("timeout", "300s")}',
                '--max-retry-attempts=3',
                '--min-backoff-duration=5s',
                '--max-backoff-duration=300s'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Created scheduler job: {job_config['name']}")
                return True
            else:
                logger.error(f"Failed to create scheduler job {job_config['name']}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating scheduler job {job_config['name']}: {e}")
            return False
    
    def _delete_scheduler_job(self, job_name: str) -> bool:
        """Delete a scheduler job if it exists"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'delete', job_name,
                f'--location={self.region}',
                '--quiet'
            ]
            
            subprocess.run(cmd, capture_output=True, text=True)
            return True
            
        except Exception as e:
            logger.debug(f"Job {job_name} may not exist: {e}")
            return True
    
    def list_scheduler_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduler jobs"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'list',
                f'--location={self.region}',
                '--format=json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                jobs = json.loads(result.stdout)
                return [job for job in jobs if 'career-copilot' in job.get('name', '')]
            else:
                logger.error(f"Failed to list scheduler jobs: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing scheduler jobs: {e}")
            return []
    
    def get_job_status(self, job_name: str) -> Dict[str, Any]:
        """Get status of a specific scheduler job"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'describe', job_name,
                f'--location={self.region}',
                '--format=json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get job status for {job_name}: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting job status for {job_name}: {e}")
            return {}
    
    def pause_job(self, job_name: str) -> bool:
        """Pause a scheduler job"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'pause', job_name,
                f'--location={self.region}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Paused scheduler job: {job_name}")
                return True
            else:
                logger.error(f"Failed to pause job {job_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error pausing job {job_name}: {e}")
            return False
    
    def resume_job(self, job_name: str) -> bool:
        """Resume a paused scheduler job"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'resume', job_name,
                f'--location={self.region}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Resumed scheduler job: {job_name}")
                return True
            else:
                logger.error(f"Failed to resume job {job_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error resuming job {job_name}: {e}")
            return False
    
    def run_job_now(self, job_name: str) -> bool:
        """Manually trigger a scheduler job"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'run', job_name,
                f'--location={self.region}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Triggered scheduler job: {job_name}")
                return True
            else:
                logger.error(f"Failed to trigger job {job_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering job {job_name}: {e}")
            return False
    
    def update_job_schedule(self, job_name: str, new_schedule: str) -> bool:
        """Update the schedule of a scheduler job"""
        try:
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'update', 'http', job_name,
                f'--location={self.region}',
                f'--schedule={new_schedule}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Updated schedule for job {job_name} to {new_schedule}")
                return True
            else:
                logger.error(f"Failed to update schedule for job {job_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating schedule for job {job_name}: {e}")
            return False
    
    def get_job_logs(self, job_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution logs for a scheduler job"""
        try:
            # Get job executions
            cmd = [
                'gcloud', 'logging', 'read',
                f'resource.type="cloud_scheduler_job" AND resource.labels.job_id="{job_name}"',
                f'--project={self.project_id}',
                f'--limit={limit}',
                '--format=json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get logs for job {job_name}: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting logs for job {job_name}: {e}")
            return []
    
    def validate_schedules(self) -> Dict[str, bool]:
        """Validate that all scheduler jobs are properly configured"""
        validation_results = {}
        
        jobs = self.list_scheduler_jobs()
        expected_jobs = ['job-ingestion-cron', 'morning-briefing-cron', 'evening-update-cron']
        
        for expected_job in expected_jobs:
            job_exists = any(expected_job in job.get('name', '') for job in jobs)
            validation_results[expected_job] = job_exists
            
            if job_exists:
                # Check if job is enabled
                job_status = self.get_job_status(expected_job)
                is_enabled = job_status.get('state') == 'ENABLED'
                validation_results[f"{expected_job}_enabled"] = is_enabled
        
        return validation_results
    
    def cleanup_scheduler_jobs(self) -> bool:
        """Clean up all scheduler jobs (for development/testing)"""
        if self.environment == 'production':
            logger.warning("Cleanup not allowed in production environment")
            return False
        
        try:
            jobs = self.list_scheduler_jobs()
            
            for job in jobs:
                job_name = job.get('name', '').split('/')[-1]  # Extract job name from full path
                self._delete_scheduler_job(job_name)
            
            logger.info("Scheduler jobs cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during scheduler cleanup: {e}")
            return False


def setup_scheduler(project_id: str, region: str, environment: str = 'production') -> bool:
    """Main function to set up Cloud Scheduler for Career Copilot"""
    scheduler_manager = SchedulerManager(project_id, region, environment)
    
    logger.info(f"Setting up Cloud Scheduler for project {project_id} in {region}")
    
    # Create scheduler jobs
    if not scheduler_manager.create_scheduler_jobs():
        logger.error("Failed to create all scheduler jobs")
        return False
    
    # Validate setup
    validation_results = scheduler_manager.validate_schedules()
    failed_validations = [job for job, success in validation_results.items() if not success]
    
    if failed_validations:
        logger.warning(f"Some scheduler validations failed: {failed_validations}")
    
    logger.info("Cloud Scheduler setup completed successfully")
    return True


if __name__ == "__main__":
    import sys
    import os
    
    project_id = os.getenv('PROJECT_ID')
    region = os.getenv('REGION', 'us-central1')
    environment = os.getenv('ENVIRONMENT', 'production')
    
    if not project_id:
        print("Error: PROJECT_ID environment variable not set")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        scheduler_manager = SchedulerManager(project_id, region, environment)
        
        if command == 'list':
            jobs = scheduler_manager.list_scheduler_jobs()
            print(f"Found {len(jobs)} scheduler jobs:")
            for job in jobs:
                print(f"  - {job.get('name', 'Unknown')}: {job.get('state', 'Unknown')}")
        
        elif command == 'validate':
            results = scheduler_manager.validate_schedules()
            print("Scheduler validation results:")
            for job, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {job}")
        
        elif command == 'run' and len(sys.argv) > 2:
            job_name = sys.argv[2]
            if scheduler_manager.run_job_now(job_name):
                print(f"✅ Triggered job: {job_name}")
            else:
                print(f"❌ Failed to trigger job: {job_name}")
        
        else:
            print("Usage: python scheduler_setup.py [list|validate|run <job_name>]")
    
    else:
        if setup_scheduler(project_id, region, environment):
            print("✅ Cloud Scheduler setup completed successfully")
        else:
            print("❌ Cloud Scheduler setup failed")
            sys.exit(1)