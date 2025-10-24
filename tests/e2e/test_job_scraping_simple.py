"""
Simple E2E Tests for Job Scraping Framework

Tests the job scraping framework with minimal dependencies
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import time


class TestJobScrapingFrameworkSimple:
    """Simple test cases for the job scraping framework"""
    
    @patch('tests.e2e.job_scraping_test_framework.get_db')
    @patch('tests.e2e.job_scraping_test_framework.User')
    @patch('tests.e2e.job_scraping_test_framework.Job')
    def test_setup_test_environment_success(self, mock_job, mock_user, mock_get_db):
        """Test successful test environment setup"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock user query
        mock_user_instance = MagicMock()
        mock_user_instance.id = 123
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_instance
        
        # Mock job count query
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import JobScrapingTestFramework
        
        framework = JobScrapingTestFramework()
        result = framework.setup_test_environment()
        
        assert result is True
        assert framework.test_user_id == 123
        assert framework.initial_job_count == 5
    
    @patch('tests.e2e.job_scraping_test_framework.get_db')
    @patch('tests.e2e.job_scraping_test_framework.User')
    @patch('tests.e2e.job_scraping_test_framework.Job')
    def test_setup_test_environment_create_user(self, mock_job, mock_user, mock_get_db):
        """Test test environment setup when user needs to be created"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock user query - no existing user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock new user creation
        mock_new_user = MagicMock()
        mock_new_user.id = 456
        mock_user.return_value = mock_new_user
        
        # Mock job count query
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import JobScrapingTestFramework
        
        framework = JobScrapingTestFramework()
        result = framework.setup_test_environment()
        
        assert result is True
        assert framework.test_user_id == 456
        assert framework.initial_job_count == 0
        
        # Verify user was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @patch('tests.e2e.job_scraping_test_framework.get_db')
    def test_setup_test_environment_failure(self, mock_get_db):
        """Test test environment setup failure handling"""
        # Mock database session to raise exception
        mock_get_db.side_effect = Exception("Database connection failed")
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import JobScrapingTestFramework
        
        framework = JobScrapingTestFramework()
        result = framework.setup_test_environment()
        
        assert result is False
    
    def test_job_scraping_result_dataclass(self):
        """Test JobScrapingResult dataclass"""
        from tests.e2e.job_scraping_test_framework import JobScrapingResult
        
        result = JobScrapingResult(
            success=True,
            task_id="test-123",
            jobs_found=10,
            jobs_added=8,
            execution_time=45.5,
            error_message=None,
            data_quality_score=85.0,
            validation_errors=[]
        )
        
        assert result.success is True
        assert result.task_id == "test-123"
        assert result.jobs_found == 10
        assert result.jobs_added == 8
        assert result.execution_time == 45.5
        assert result.error_message is None
        assert result.data_quality_score == 85.0
        assert result.validation_errors == []
    
    def test_data_quality_metrics_dataclass(self):
        """Test DataQualityMetrics dataclass"""
        from tests.e2e.job_scraping_test_framework import DataQualityMetrics
        
        metrics = DataQualityMetrics(
            total_jobs=100,
            jobs_with_title=95,
            jobs_with_company=98,
            jobs_with_description=80,
            jobs_with_location=75,
            jobs_with_tech_stack=60,
            jobs_with_salary=40,
            duplicate_jobs=2,
            invalid_urls=1,
            quality_score=82.5
        )
        
        assert metrics.total_jobs == 100
        assert metrics.jobs_with_title == 95
        assert metrics.jobs_with_company == 98
        assert metrics.jobs_with_description == 80
        assert metrics.jobs_with_location == 75
        assert metrics.jobs_with_tech_stack == 60
        assert metrics.jobs_with_salary == 40
        assert metrics.duplicate_jobs == 2
        assert metrics.invalid_urls == 1
        assert metrics.quality_score == 82.5
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.trigger_job_scraping_task')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.verify_database_changes')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.validate_scraped_data_quality')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.cleanup_test_data')
    def test_run_job_scraping_test_success(self, mock_cleanup, mock_quality, mock_verify, mock_trigger, mock_setup):
        """Test successful comprehensive job scraping test"""
        # Setup mocks
        mock_setup.return_value = True
        mock_cleanup.return_value = True
        
        mock_scraping_result = MagicMock()
        mock_scraping_result.success = True
        mock_scraping_result.jobs_added = 5
        mock_trigger.return_value = mock_scraping_result
        
        mock_verify.return_value = {"success": True, "data_integrity_ok": True}
        
        mock_quality_metrics = MagicMock()
        mock_quality_metrics.quality_score = 85.0
        mock_quality.return_value = mock_quality_metrics
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import run_job_scraping_test
        
        result = run_job_scraping_test()
        
        # Verify calls were made
        mock_setup.assert_called_once()
        mock_trigger.assert_called_once()
        mock_verify.assert_called_once()
        mock_quality.assert_called_once()
        mock_cleanup.assert_called_once()
        
        # Verify result structure
        assert "success" in result
        assert "execution_time" in result
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.cleanup_test_data')
    def test_run_job_scraping_test_setup_failure(self, mock_cleanup, mock_setup):
        """Test job scraping test with setup failure"""
        # Setup mocks
        mock_setup.return_value = False
        mock_cleanup.return_value = True
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import run_job_scraping_test
        
        result = run_job_scraping_test()
        
        # Verify setup was called but failed
        mock_setup.assert_called_once()
        mock_cleanup.assert_called_once()
        
        # Verify failure result
        assert result["success"] is False
        assert "Failed to setup test environment" in result["error"]
    
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.setup_test_environment')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.trigger_job_scraping_task')
    @patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.cleanup_test_data')
    def test_trigger_job_scraping_for_user(self, mock_cleanup, mock_trigger, mock_setup):
        """Test triggering job scraping for specific user"""
        # Setup mocks
        mock_setup.return_value = True
        mock_cleanup.return_value = True
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.jobs_added = 3
        mock_result.task_id = "test-456"
        mock_trigger.return_value = mock_result
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import trigger_job_scraping_for_user
        
        result = trigger_job_scraping_for_user(123)
        
        # Verify calls
        mock_setup.assert_called_once()
        mock_trigger.assert_called_once_with(123)
        mock_cleanup.assert_called_once()
        
        # Verify result
        assert result.success is True
        assert result.jobs_added == 3
        assert result.task_id == "test-456"


class TestJobScrapingFrameworkIntegration:
    """Integration-style tests with more realistic scenarios"""
    
    @patch('tests.e2e.job_scraping_test_framework.time.sleep')  # Speed up tests
    @patch('tests.e2e.job_scraping_test_framework.celery_app')
    @patch('tests.e2e.job_scraping_test_framework.scrape_jobs_for_user_async')
    @patch('tests.e2e.job_scraping_test_framework.get_db')
    def test_trigger_job_scraping_task_with_monitoring(self, mock_get_db, mock_task, mock_celery, mock_sleep):
        """Test job scraping task trigger with realistic monitoring"""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 8]  # Before and after counts
        
        # Mock Celery task
        mock_task_instance = MagicMock()
        mock_task_instance.id = "test-task-789"
        mock_task.delay.return_value = mock_task_instance
        
        # Mock Celery result
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            'status': 'success',
            'jobs_found': 10,
            'jobs_added': 3
        }
        mock_celery.AsyncResult.return_value = mock_result
        
        # Mock data quality validation
        with patch('tests.e2e.job_scraping_test_framework.JobScrapingTestFramework.validate_scraped_data_quality') as mock_quality:
            mock_quality_metrics = MagicMock()
            mock_quality_metrics.quality_score = 90.0
            mock_quality.return_value = mock_quality_metrics
            
            # Import and test
            from tests.e2e.job_scraping_test_framework import JobScrapingTestFramework
            
            framework = JobScrapingTestFramework()
            framework.test_user_id = 123  # Set directly to avoid setup complexity
            
            result = framework.trigger_job_scraping_task()
            
            # Verify task was triggered
            mock_task.delay.assert_called_once_with(123)
            
            # Verify result
            assert result.success is True
            assert result.task_id == "test-task-789"
            assert result.jobs_found == 10
            assert result.data_quality_score == 90.0
    
    @patch('tests.e2e.job_scraping_test_framework.get_db')
    def test_verify_database_changes_with_integrity_check(self, mock_get_db):
        """Test database verification with integrity checking"""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock job queries
        mock_db.query.return_value.filter.return_value.count.return_value = 10  # Current count
        
        # Mock recent jobs with some integrity issues
        mock_job1 = MagicMock()
        mock_job1.id = 1
        mock_job1.title = "Software Engineer"
        mock_job1.company = "Test Corp"
        mock_job1.source_url = "https://example.com/job1"
        
        mock_job2 = MagicMock()
        mock_job2.id = 2
        mock_job2.title = ""  # Missing title - integrity issue
        mock_job2.company = "Another Corp"
        mock_job2.source_url = "https://example.com/job2"
        
        mock_job3 = MagicMock()
        mock_job3.id = 3
        mock_job3.title = "Data Scientist"
        mock_job3.company = ""  # Missing company - integrity issue
        mock_job3.source_url = None  # Missing URL - integrity issue
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_job1, mock_job2, mock_job3]
        
        # Import and test
        from tests.e2e.job_scraping_test_framework import JobScrapingTestFramework
        
        framework = JobScrapingTestFramework()
        framework.test_user_id = 123
        framework.initial_job_count = 5
        
        result = framework.verify_database_changes(expected_min_jobs=2)
        
        # Verify results
        assert result["success"] is False  # Should fail due to integrity issues
        assert result["jobs_added"] == 5  # 10 - 5 = 5
        assert result["meets_minimum"] is True  # 5 >= 2
        assert result["data_integrity_ok"] is False  # Has integrity issues
        assert len(result["integrity_issues"]) == 3  # Three issues found
        
        # Check specific integrity issues
        issues = result["integrity_issues"]
        assert any("Job 2 missing title" in issue for issue in issues)
        assert any("Job 3 missing company" in issue for issue in issues)
        assert any("Job 3 missing source URL" in issue for issue in issues)


# Test markers
pytestmark = pytest.mark.e2e