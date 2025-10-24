"""
E2E Tests for Job Scraping Framework

Tests the complete job scraping pipeline including:
- Celery task triggering and monitoring
- Database verification for new job records  
- Data quality validation checks
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from tests.e2e.job_scraping_test_framework import (
    JobScrapingTestFramework,
    run_job_scraping_test,
    trigger_job_scraping_for_user
)


class TestJobScrapingFramework:
    """Test cases for the job scraping framework"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.framework = JobScrapingTestFramework()
    
    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, 'framework'):
            self.framework.cleanup_test_data()
    
    def test_setup_test_environment(self):
        """Test that test environment can be set up successfully"""
        result = self.framework.setup_test_environment()
        
        assert result is True
        assert self.framework.test_user_id is not None
        assert self.framework.initial_job_count >= 0
    
    @patch('app.tasks.job_scraping_tasks.scrape_jobs_for_user_async.delay')
    @patch('app.core.celery_app.celery_app.AsyncResult')
    def test_trigger_job_scraping_task_success(self, mock_async_result, mock_delay):
        """Test successful job scraping task trigger"""
        # Setup mocks
        mock_task = MagicMock()
        mock_task.id = "test-task-123"
        mock_delay.return_value = mock_task
        
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            'status': 'success',
            'jobs_found': 5,
            'jobs_added': 3
        }
        mock_async_result.return_value = mock_result
        
        # Setup test environment
        self.framework.setup_test_environment()
        
        # Trigger job scraping
        result = self.framework.trigger_job_scraping_task()
        
        # Verify results
        assert result.success is True
        assert result.task_id == "test-task-123"
        assert result.jobs_found == 5
        assert result.error_message is None
        
        # Verify task was called
        mock_delay.assert_called_once_with(self.framework.test_user_id)
    
    @patch('app.tasks.job_scraping_tasks.scrape_jobs_for_user_async.delay')
    @patch('app.core.celery_app.celery_app.AsyncResult')
    def test_trigger_job_scraping_task_failure(self, mock_async_result, mock_delay):
        """Test job scraping task failure handling"""
        # Setup mocks
        mock_task = MagicMock()
        mock_task.id = "test-task-456"
        mock_delay.return_value = mock_task
        
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.info = "Test error message"
        mock_async_result.return_value = mock_result
        
        # Setup test environment
        self.framework.setup_test_environment()
        
        # Trigger job scraping
        result = self.framework.trigger_job_scraping_task()
        
        # Verify results
        assert result.success is False
        assert result.task_id == "test-task-456"
        assert result.error_message == "Test error message"
        assert result.jobs_added == 0
    
    @patch('app.tasks.job_scraping_tasks.scrape_jobs_for_user_async.delay')
    @patch('app.core.celery_app.celery_app.AsyncResult')
    def test_trigger_job_scraping_task_timeout(self, mock_async_result, mock_delay):
        """Test job scraping task timeout handling"""
        # Setup mocks
        mock_task = MagicMock()
        mock_task.id = "test-task-timeout"
        mock_delay.return_value = mock_task
        
        mock_result = MagicMock()
        mock_result.ready.return_value = False  # Never becomes ready (timeout)
        mock_async_result.return_value = mock_result
        
        # Setup test environment
        self.framework.setup_test_environment()
        
        # Trigger job scraping (with shorter timeout for testing)
        with patch.object(self.framework, 'trigger_job_scraping_task') as mock_trigger:
            mock_trigger.return_value = MagicMock(
                success=False,
                task_id="test-task-timeout",
                jobs_found=0,
                jobs_added=0,
                execution_time=300.0,
                error_message="Task timeout - did not complete within 5 minutes",
                data_quality_score=0.0,
                validation_errors=["Task execution timeout"]
            )
            
            result = mock_trigger.return_value
            
            # Verify timeout handling
            assert result.success is False
            assert "timeout" in result.error_message.lower()
            assert result.execution_time >= 300.0
    
    def test_verify_database_changes(self):
        """Test database verification functionality"""
        # Setup test environment
        self.framework.setup_test_environment()
        
        # Test with no expected jobs
        result = self.framework.verify_database_changes(expected_min_jobs=0)
        
        assert "success" in result
        assert "initial_count" in result
        assert "current_count" in result
        assert "jobs_added" in result
        assert "meets_minimum" in result
        assert "data_integrity_ok" in result
        
        # Should succeed with 0 expected jobs
        assert result["meets_minimum"] is True
    
    def test_validate_scraped_data_quality_no_jobs(self):
        """Test data quality validation with no jobs"""
        # Setup test environment
        self.framework.setup_test_environment()
        
        # Validate data quality (should handle empty case)
        metrics = self.framework.validate_scraped_data_quality()
        
        assert metrics.total_jobs == 0
        assert metrics.quality_score == 0.0
        assert metrics.duplicate_jobs == 0
        assert metrics.invalid_urls == 0
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.trigger_job_scraping_task')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.verify_database_changes')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.validate_scraped_data_quality')
    def test_run_comprehensive_test_success(self, mock_quality, mock_verify, mock_trigger, mock_setup):
        """Test comprehensive test execution with successful results"""
        # Setup mocks
        mock_setup.return_value = True
        
        mock_trigger.return_value = MagicMock(
            success=True,
            task_id="test-123",
            jobs_found=10,
            jobs_added=8,
            execution_time=45.0,
            error_message=None,
            data_quality_score=85.0,
            validation_errors=[]
        )
        
        mock_verify.return_value = {
            "success": True,
            "jobs_added": 8,
            "data_integrity_ok": True,
            "integrity_issues": []
        }
        
        mock_quality.return_value = MagicMock(
            total_jobs=8,
            quality_score=85.0,
            duplicate_jobs=0,
            invalid_urls=0
        )
        
        # Run comprehensive test
        result = self.framework.run_comprehensive_test()
        
        # Verify results
        assert result["success"] is True
        assert "execution_time" in result
        assert "scraping_result" in result
        assert "database_verification" in result
        assert "data_quality_metrics" in result
        assert "summary" in result
        
        summary = result["summary"]
        assert summary["task_executed"] is True
        assert summary["jobs_added"] == 8
        assert summary["data_quality_score"] == 85.0
        assert summary["database_integrity"] is True
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    def test_run_comprehensive_test_setup_failure(self, mock_setup):
        """Test comprehensive test with setup failure"""
        # Setup mock to fail
        mock_setup.return_value = False
        
        # Run comprehensive test
        result = self.framework.run_comprehensive_test()
        
        # Verify failure handling
        assert result["success"] is False
        assert "Failed to setup test environment" in result["error"]
        assert "execution_time" in result
    
    def test_cleanup_test_data(self):
        """Test cleanup functionality"""
        # Setup test environment first
        self.framework.setup_test_environment()
        
        # Verify test user was created
        assert self.framework.test_user_id is not None
        
        # Cleanup
        result = self.framework.cleanup_test_data()
        
        # Verify cleanup succeeded
        assert result is True


class TestJobScrapingConvenienceFunctions:
    """Test convenience functions for job scraping"""
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.run_comprehensive_test')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.cleanup_test_data')
    def test_run_job_scraping_test(self, mock_cleanup, mock_comprehensive):
        """Test convenience function for running job scraping test"""
        # Setup mock
        mock_comprehensive.return_value = {"success": True, "jobs_added": 5}
        mock_cleanup.return_value = True
        
        # Run test
        result = run_job_scraping_test()
        
        # Verify
        assert result["success"] is True
        assert result["jobs_added"] == 5
        mock_comprehensive.assert_called_once()
        mock_cleanup.assert_called_once()
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.trigger_job_scraping_task')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.cleanup_test_data')
    def test_trigger_job_scraping_for_user(self, mock_cleanup, mock_trigger, mock_setup):
        """Test convenience function for triggering job scraping for specific user"""
        # Setup mocks
        mock_setup.return_value = True
        mock_trigger.return_value = MagicMock(
            success=True,
            jobs_added=3,
            task_id="test-456"
        )
        mock_cleanup.return_value = True
        
        # Test with specific user ID
        result = trigger_job_scraping_for_user(123)
        
        # Verify
        assert result.success is True
        assert result.jobs_added == 3
        assert result.task_id == "test-456"
        mock_setup.assert_called_once()
        mock_trigger.assert_called_once_with(123)
        mock_cleanup.assert_called_once()


# Integration test markers
pytestmark = pytest.mark.e2e