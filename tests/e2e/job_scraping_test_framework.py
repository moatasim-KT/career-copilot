"""
Job Scraping Test Framework

This module provides comprehensive testing for the job scraping pipeline including:
- Celery task triggering and monitoring
- Database verification for new job records
- Data quality validation checks
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.tasks.job_scraping_tasks import (
    scrape_jobs_for_user_async,
    scrape_jobs_for_all_users,
    batch_scrape_jobs
)
from app.core.celery_app import celery_app
from tests.e2e.base import BaseE2ETest


@dataclass
class JobScrapingResult:
    """Result of job scraping test execution"""
    success: bool
    task_id: Optional[str]
    jobs_found: int
    jobs_added: int
    execution_time: float
    error_message: Optional[str]
    data_quality_score: float
    validation_errors: List[str]


@dataclass
class DataQualityMetrics:
    """Metrics for evaluating scraped job data quality"""
    total_jobs: int
    jobs_with_title: int
    jobs_with_company: int
    jobs_with_description: int
    jobs_with_location: int
    jobs_with_tech_stack: int
    jobs_with_salary: int
    duplicate_jobs: int
    invalid_urls: int
    quality_score: float


class JobScrapingTestFramework(BaseE2ETest):
    """
    Test framework for job scraping functionality
    
    Provides methods to:
    - Trigger Celery job scraping tasks
    - Verify database changes
    - Validate data quality
    - Monitor task execution
    """
    
    def __init__(self):
        super().__init__()
        self.db: Session = next(get_db())
        self.test_user_id: Optional[int] = None
        self.initial_job_count: int = 0
        
    def setup_test_environment(self) -> bool:
        """
        Set up test environment with test user and baseline data
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create or get test user for scraping
            test_user = self.db.query(User).filter(
                User.email == "test_scraping@example.com"
            ).first()
            
            if not test_user:
                test_user = User(
                    email="test_scraping@example.com",
                    name="Test Scraping User",
                    skills=["Python", "FastAPI", "React", "PostgreSQL"],
                    preferred_locations=["San Francisco", "Remote"],
                    experience_level="mid"
                )
                self.db.add(test_user)
                self.db.commit()
                self.db.refresh(test_user)
            
            self.test_user_id = test_user.id
            
            # Record initial job count for comparison
            self.initial_job_count = self.db.query(Job).filter(
                Job.user_id == self.test_user_id
            ).count()
            
            self.logger.info(f"Test environment setup complete. User ID: {self.test_user_id}, Initial jobs: {self.initial_job_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def trigger_job_scraping_task(self, user_id: Optional[int] = None) -> JobScrapingResult:
        """
        Trigger Celery job scraping task and monitor execution
        
        Args:
            user_id: User ID to scrape jobs for (defaults to test user)
            
        Returns:
            JobScrapingResult: Results of the scraping operation
        """
        target_user_id = user_id or self.test_user_id
        start_time = time.time()
        
        try:
            self.logger.info(f"Triggering job scraping task for user {target_user_id}")
            
            # Record jobs before scraping
            jobs_before = self.db.query(Job).filter(
                Job.user_id == target_user_id
            ).count()
            
            # Trigger the Celery task
            task = scrape_jobs_for_user_async.delay(target_user_id)
            task_id = task.id
            
            self.logger.info(f"Job scraping task submitted with ID: {task_id}")
            
            # Monitor task execution with timeout
            timeout = 300  # 5 minutes
            poll_interval = 5  # 5 seconds
            elapsed = 0
            
            while elapsed < timeout:
                task_result = celery_app.AsyncResult(task_id)
                
                if task_result.ready():
                    break
                    
                # Log progress if available
                if task_result.state == 'PROGRESS':
                    meta = task_result.info
                    self.logger.info(f"Task progress: {meta.get('status', 'Unknown')}")
                
                time.sleep(poll_interval)
                elapsed += poll_interval
            
            execution_time = time.time() - start_time
            
            # Get final task result
            task_result = celery_app.AsyncResult(task_id)
            
            if not task_result.ready():
                return JobScrapingResult(
                    success=False,
                    task_id=task_id,
                    jobs_found=0,
                    jobs_added=0,
                    execution_time=execution_time,
                    error_message="Task timeout - did not complete within 5 minutes",
                    data_quality_score=0.0,
                    validation_errors=["Task execution timeout"]
                )
            
            if task_result.successful():
                result_data = task_result.result
                
                # Count jobs after scraping
                jobs_after = self.db.query(Job).filter(
                    Job.user_id == target_user_id
                ).count()
                
                jobs_added = jobs_after - jobs_before
                
                # Perform data quality validation
                quality_metrics = self.validate_scraped_data_quality(target_user_id)
                
                return JobScrapingResult(
                    success=True,
                    task_id=task_id,
                    jobs_found=result_data.get('jobs_found', 0),
                    jobs_added=jobs_added,
                    execution_time=execution_time,
                    error_message=None,
                    data_quality_score=quality_metrics.quality_score,
                    validation_errors=[]
                )
            else:
                error_msg = str(task_result.info) if task_result.info else "Unknown error"
                return JobScrapingResult(
                    success=False,
                    task_id=task_id,
                    jobs_found=0,
                    jobs_added=0,
                    execution_time=execution_time,
                    error_message=error_msg,
                    data_quality_score=0.0,
                    validation_errors=[error_msg]
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Exception during job scraping: {str(e)}"
            self.logger.error(error_msg)
            
            return JobScrapingResult(
                success=False,
                task_id=None,
                jobs_found=0,
                jobs_added=0,
                execution_time=execution_time,
                error_message=error_msg,
                data_quality_score=0.0,
                validation_errors=[error_msg]
            )
    
    def verify_database_changes(self, user_id: Optional[int] = None, expected_min_jobs: int = 0) -> Dict[str, Any]:
        """
        Verify that job scraping resulted in expected database changes
        
        Args:
            user_id: User ID to check (defaults to test user)
            expected_min_jobs: Minimum number of jobs expected to be added
            
        Returns:
            Dict containing verification results
        """
        target_user_id = user_id or self.test_user_id
        
        try:
            # Get current job count
            current_job_count = self.db.query(Job).filter(
                Job.user_id == target_user_id
            ).count()
            
            jobs_added = current_job_count - self.initial_job_count
            
            # Get recent jobs (added in last hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_jobs = self.db.query(Job).filter(
                and_(
                    Job.user_id == target_user_id,
                    Job.created_at >= recent_cutoff,
                    Job.source == "scraped"
                )
            ).all()
            
            # Verify job data integrity
            integrity_issues = []
            for job in recent_jobs:
                if not job.title or not job.title.strip():
                    integrity_issues.append(f"Job {job.id} missing title")
                if not job.company or not job.company.strip():
                    integrity_issues.append(f"Job {job.id} missing company")
                if not job.source_url:
                    integrity_issues.append(f"Job {job.id} missing source URL")
            
            verification_result = {
                "success": jobs_added >= expected_min_jobs and len(integrity_issues) == 0,
                "initial_count": self.initial_job_count,
                "current_count": current_job_count,
                "jobs_added": jobs_added,
                "recent_jobs_count": len(recent_jobs),
                "expected_min_jobs": expected_min_jobs,
                "integrity_issues": integrity_issues,
                "meets_minimum": jobs_added >= expected_min_jobs,
                "data_integrity_ok": len(integrity_issues) == 0
            }
            
            self.logger.info(f"Database verification: {verification_result}")
            return verification_result
            
        except Exception as e:
            error_msg = f"Database verification failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "initial_count": self.initial_job_count,
                "current_count": 0,
                "jobs_added": 0,
                "recent_jobs_count": 0,
                "expected_min_jobs": expected_min_jobs,
                "integrity_issues": [error_msg],
                "meets_minimum": False,
                "data_integrity_ok": False
            }
    
    def validate_scraped_data_quality(self, user_id: Optional[int] = None) -> DataQualityMetrics:
        """
        Validate the quality of scraped job data
        
        Args:
            user_id: User ID to validate data for (defaults to test user)
            
        Returns:
            DataQualityMetrics: Quality metrics for the scraped data
        """
        target_user_id = user_id or self.test_user_id
        
        try:
            # Get recent scraped jobs (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = self.db.query(Job).filter(
                and_(
                    Job.user_id == target_user_id,
                    Job.created_at >= recent_cutoff,
                    Job.source == "scraped"
                )
            ).all()
            
            total_jobs = len(recent_jobs)
            
            if total_jobs == 0:
                return DataQualityMetrics(
                    total_jobs=0,
                    jobs_with_title=0,
                    jobs_with_company=0,
                    jobs_with_description=0,
                    jobs_with_location=0,
                    jobs_with_tech_stack=0,
                    jobs_with_salary=0,
                    duplicate_jobs=0,
                    invalid_urls=0,
                    quality_score=0.0
                )
            
            # Count jobs with required fields
            jobs_with_title = sum(1 for job in recent_jobs if job.title and job.title.strip())
            jobs_with_company = sum(1 for job in recent_jobs if job.company and job.company.strip())
            jobs_with_description = sum(1 for job in recent_jobs if job.description and len(job.description.strip()) > 50)
            jobs_with_location = sum(1 for job in recent_jobs if job.location and job.location.strip())
            jobs_with_tech_stack = sum(1 for job in recent_jobs if job.tech_stack and len(job.tech_stack) > 0)
            jobs_with_salary = sum(1 for job in recent_jobs if job.salary_range and job.salary_range.strip())
            
            # Check for duplicates (same company + title combination)
            job_signatures = [(job.company, job.title) for job in recent_jobs if job.company and job.title]
            unique_signatures = set(job_signatures)
            duplicate_jobs = len(job_signatures) - len(unique_signatures)
            
            # Check for invalid URLs
            invalid_urls = 0
            for job in recent_jobs:
                if job.source_url:
                    if not (job.source_url.startswith('http://') or job.source_url.startswith('https://')):
                        invalid_urls += 1
            
            # Calculate quality score (weighted average)
            weights = {
                'title': 0.25,
                'company': 0.25,
                'description': 0.15,
                'location': 0.10,
                'tech_stack': 0.10,
                'salary': 0.05,
                'no_duplicates': 0.05,
                'valid_urls': 0.05
            }
            
            scores = {
                'title': jobs_with_title / total_jobs,
                'company': jobs_with_company / total_jobs,
                'description': jobs_with_description / total_jobs,
                'location': jobs_with_location / total_jobs,
                'tech_stack': jobs_with_tech_stack / total_jobs,
                'salary': jobs_with_salary / total_jobs,
                'no_duplicates': 1.0 - (duplicate_jobs / total_jobs),
                'valid_urls': 1.0 - (invalid_urls / total_jobs)
            }
            
            quality_score = sum(weights[key] * scores[key] for key in weights.keys()) * 100
            
            metrics = DataQualityMetrics(
                total_jobs=total_jobs,
                jobs_with_title=jobs_with_title,
                jobs_with_company=jobs_with_company,
                jobs_with_description=jobs_with_description,
                jobs_with_location=jobs_with_location,
                jobs_with_tech_stack=jobs_with_tech_stack,
                jobs_with_salary=jobs_with_salary,
                duplicate_jobs=duplicate_jobs,
                invalid_urls=invalid_urls,
                quality_score=quality_score
            )
            
            self.logger.info(f"Data quality metrics: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Data quality validation failed: {e}")
            return DataQualityMetrics(
                total_jobs=0,
                jobs_with_title=0,
                jobs_with_company=0,
                jobs_with_description=0,
                jobs_with_location=0,
                jobs_with_tech_stack=0,
                jobs_with_salary=0,
                duplicate_jobs=0,
                invalid_urls=0,
                quality_score=0.0
            )
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive job scraping test including all validation steps
        
        Returns:
            Dict containing comprehensive test results
        """
        test_start_time = time.time()
        
        try:
            # Setup test environment
            if not self.setup_test_environment():
                return {
                    "success": False,
                    "error": "Failed to setup test environment",
                    "execution_time": time.time() - test_start_time
                }
            
            # Trigger job scraping
            scraping_result = self.trigger_job_scraping_task()
            
            # Verify database changes
            db_verification = self.verify_database_changes(expected_min_jobs=0)
            
            # Validate data quality
            quality_metrics = self.validate_scraped_data_quality()
            
            # Determine overall success
            overall_success = (
                scraping_result.success and
                db_verification["success"] and
                quality_metrics.quality_score >= 70.0  # Minimum 70% quality score
            )
            
            comprehensive_result = {
                "success": overall_success,
                "execution_time": time.time() - test_start_time,
                "scraping_result": scraping_result,
                "database_verification": db_verification,
                "data_quality_metrics": quality_metrics,
                "summary": {
                    "task_executed": scraping_result.success,
                    "jobs_added": scraping_result.jobs_added,
                    "data_quality_score": quality_metrics.quality_score,
                    "database_integrity": db_verification["data_integrity_ok"]
                }
            }
            
            self.logger.info(f"Comprehensive test completed: {comprehensive_result['summary']}")
            return comprehensive_result
            
        except Exception as e:
            error_msg = f"Comprehensive test failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "execution_time": time.time() - test_start_time
            }
    
    def cleanup_test_data(self) -> bool:
        """
        Clean up test data created during testing
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            if self.test_user_id:
                # Delete test jobs
                test_jobs = self.db.query(Job).filter(
                    Job.user_id == self.test_user_id
                ).all()
                
                for job in test_jobs:
                    self.db.delete(job)
                
                # Delete test user
                test_user = self.db.query(User).filter(
                    User.id == self.test_user_id
                ).first()
                
                if test_user:
                    self.db.delete(test_user)
                
                self.db.commit()
                self.logger.info(f"Cleaned up test data for user {self.test_user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup test data: {e}")
            self.db.rollback()
            return False
        finally:
            self.db.close()


# Convenience functions for direct testing
def run_job_scraping_test() -> Dict[str, Any]:
    """
    Convenience function to run job scraping test
    
    Returns:
        Dict containing test results
    """
    framework = JobScrapingTestFramework()
    try:
        return framework.run_comprehensive_test()
    finally:
        framework.cleanup_test_data()


def trigger_job_scraping_for_user(user_id: int) -> JobScrapingResult:
    """
    Convenience function to trigger job scraping for a specific user
    
    Args:
        user_id: User ID to scrape jobs for
        
    Returns:
        JobScrapingResult: Results of the scraping operation
    """
    framework = JobScrapingTestFramework()
    try:
        framework.setup_test_environment()
        return framework.trigger_job_scraping_task(user_id)
    finally:
        framework.cleanup_test_data()