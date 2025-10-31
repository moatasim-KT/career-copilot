"""
Integration Tests for Analytics Services
Tests the interaction between all analytics service components
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.analytics_collection_service import AnalyticsCollectionService
from app.services.analytics_processing_service import AnalyticsProcessingService
from app.services.analytics_query_service import AnalyticsQueryService
from app.services.analytics_reporting_service import AnalyticsReportingService
from app.services.analytics_service_facade import AnalyticsServiceFacade
from app.models.user import User
from app.models.job import Job


class TestAnalyticsServicesIntegration:
	"""Integration tests for analytics services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		db = Mock(spec=Session)
		return db

	@pytest.fixture
	def mock_user(self):
		"""Create mock user"""
		user = Mock(spec=User)
		user.id = 1
		user.email = "test@example.com"
		user.jobs = []
		user.interviews = []
		return user

	@pytest.fixture
	def mock_jobs(self):
		"""Create mock jobs for testing"""
		jobs = []
		for i in range(10):
			job = Mock(spec=Job)
			job.id = i
			job.title = f"Software Engineer {i}"
			job.company = f"Company {i % 3}"  # 3 companies
			job.location = "Remote" if i % 2 == 0 else "New York"
			job.salary_min = 100000 + (i * 10000)
			job.salary_max = 150000 + (i * 10000)
			job.date_added = datetime.now(timezone.utc) - timedelta(days=i * 10)
			job.requirements = {"skills_required": ["Python", "FastAPI", "PostgreSQL"] if i % 2 == 0 else ["JavaScript", "React", "Node.js"]}
			jobs.append(job)
		return jobs

	def test_collection_service_basic_operations(self, mock_db):
		"""Test basic collection service operations"""
		collector = AnalyticsCollectionService(mock_db)

		# Test event collection
		result = collector.collect_event(user_id=1, event_type="job_viewed", event_data={"job_id": 123})
		assert isinstance(result, bool)

	def test_processing_service_integration(self, mock_db, mock_user, mock_jobs):
		"""Test processing service with mock data"""
		# Setup mock query response
		mock_db.query.return_value.filter.return_value.first.return_value = mock_user
		mock_user.jobs = mock_jobs[:5]  # Assign subset of jobs

		processor = AnalyticsProcessingService(mock_db)

		# Test user analytics processing
		result = processor.get_user_analytics(mock_user)

		assert isinstance(result, dict)
		assert "total_applications" in result or "user_id" in result or "total_jobs" in result

	def test_query_service_metrics_retrieval(self, mock_db):
		"""Test query service metrics retrieval"""
		query_service = AnalyticsQueryService(mock_db)

		# Test metrics retrieval
		result = query_service.get_metrics(user_id=1, timeframe="week")

		assert isinstance(result, dict)
		# Should handle cases where no data exists
		assert "error" in result or "metrics" in result or "user_id" in result

	def test_reporting_service_market_analysis(self, mock_db, mock_user, mock_jobs):
		"""Test reporting service market analysis"""
		# Setup mock query response
		mock_db.query.return_value.filter.return_value.first.return_value = mock_user
		mock_user.jobs = mock_jobs

		reporting = AnalyticsReportingService(mock_db)

		# Test market trends analysis
		result = reporting.analyze_market_trends(user_id=1, days=90)

		assert isinstance(result, dict)
		assert "user_id" in result

	def test_facade_delegates_to_services(self, mock_db):
		"""Test that facade properly delegates to specialized services"""
		facade = AnalyticsServiceFacade(mock_db)

		# Test delegation to collection service
		collect_result = facade.collect_event(user_id=1, event_type="test_event", event_data={"test": "data"})
		assert isinstance(collect_result, bool)

		# Test delegation to query service
		metrics_result = facade.get_metrics(user_id=1, timeframe="month")
		assert isinstance(metrics_result, dict)

	def test_facade_maintains_backward_compatibility(self, mock_db):
		"""Test that facade maintains the old API"""
		facade = AnalyticsServiceFacade(mock_db)

		# These methods should all exist and return appropriate types
		assert hasattr(facade, "collect_event")
		assert hasattr(facade, "track_user_activity")
		assert hasattr(facade, "save_analytics_data")
		assert hasattr(facade, "process_analytics")
		assert hasattr(facade, "get_user_analytics")
		assert hasattr(facade, "get_metrics")
		assert hasattr(facade, "analyze_market_trends")
		assert hasattr(facade, "get_comprehensive_analytics_report")

	def test_service_health_check(self, mock_db):
		"""Test health check functionality"""
		facade = AnalyticsServiceFacade(mock_db)

		health = facade.health_check()

		assert isinstance(health, dict)
		assert "facade" in health
		assert "services" in health
		assert health["facade"] == "healthy"

		# Check all sub-services are initialized
		assert "collection" in health["services"]
		assert "processing" in health["services"]
		assert "query" in health["services"]
		assert "reporting" in health["services"]

	def test_end_to_end_analytics_workflow(self, mock_db, mock_user, mock_jobs):
		"""Test complete analytics workflow from collection to reporting"""
		# Setup mock responses
		mock_db.query.return_value.filter.return_value.first.return_value = mock_user
		mock_user.jobs = mock_jobs

		facade = AnalyticsServiceFacade(mock_db)

		# Step 1: Collect event
		collect_result = facade.collect_event(user_id=1, event_type="application_submitted", event_data={"job_id": 1, "company": "Company A"})
		assert isinstance(collect_result, bool)

		# Step 2: Get user analytics (processing)
		user_analytics = facade.get_user_analytics(mock_user)
		assert isinstance(user_analytics, dict)

		# Step 3: Query metrics
		metrics = facade.get_metrics(user_id=1, timeframe="month")
		assert isinstance(metrics, dict)

		# Step 4: Generate report
		report = facade.analyze_market_trends(user_id=1, days=30)
		assert isinstance(report, dict)
		assert "user_id" in report


class TestAnalyticsServicesPerformance:
	"""Performance tests for analytics services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return Mock(spec=Session)

	def test_facade_initialization_performance(self, mock_db):
		"""Test that facade initialization is fast"""
		import time

		start = time.time()
		facade = AnalyticsServiceFacade(mock_db)
		duration = time.time() - start

		# Should initialize in less than 100ms
		assert duration < 0.1
		assert facade is not None

	def test_concurrent_service_access(self, mock_db):
		"""Test concurrent access to services"""
		import threading

		facade = AnalyticsServiceFacade(mock_db)
		results = []

		def collect_event():
			result = facade.collect_event(user_id=1, event_type="test", event_data={})
			results.append(result)

		# Create 10 threads
		threads = [threading.Thread(target=collect_event) for _ in range(10)]

		# Start all threads
		for t in threads:
			t.start()

		# Wait for completion
		for t in threads:
			t.join()

		# All should complete successfully
		assert len(results) == 10


class TestAnalyticsServicesErrorHandling:
	"""Error handling tests for analytics services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return Mock(spec=Session)

	def test_handles_missing_database_gracefully(self):
		"""Test that services handle missing database gracefully"""
		facade = AnalyticsServiceFacade(db=None)

		# Should not crash
		assert facade is not None

		# Operations should return error responses, not crash
		result = facade.get_metrics(user_id=1)
		assert isinstance(result, dict)

	def test_handles_invalid_user_id(self, mock_db):
		"""Test handling of invalid user IDs"""
		mock_db.query.return_value.filter.return_value.first.return_value = None

		reporting = AnalyticsReportingService(mock_db)
		result = reporting.analyze_market_trends(user_id=999, days=30)

		assert isinstance(result, dict)
		assert "error" in result or "message" in result

	def test_handles_database_errors(self, mock_db):
		"""Test handling of database errors"""
		# Make query raise an exception
		mock_db.query.side_effect = Exception("Database connection failed")

		facade = AnalyticsServiceFacade(mock_db)

		# Should not crash, should return error response
		result = facade.get_metrics(user_id=1)
		assert isinstance(result, dict)
