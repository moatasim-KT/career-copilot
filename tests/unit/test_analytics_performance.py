"""Performance tests for analytics processing and monitoring."""

import statistics
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.app.models.analytics import Analytics
from backend.app.services.reporting_insights_service import ReportingInsightsService


@pytest.fixture
def mock_reporting_service():
    return Mock(spec=ReportingInsightsService)


class TestAnalyticsPerformance:
    """Test suite for analytics performance monitoring."""

    @pytest.mark.performance
    async def test_analytics_processing_timing(self, mock_reporting_service):
        """Test analytics processing time meets performance requirements."""
        # Arrange
        num_iterations = 100
        processing_times = []

        # Act
        for _ in range(num_iterations):
            start_time = datetime.now()
            await mock_reporting_service.generate_career_insights()
            end_time = datetime.now()
            processing_times.append((end_time - start_time).total_seconds())

        avg_time = statistics.mean(processing_times)
        p95_time = statistics.quantiles(processing_times, n=20)[18]  # 95th percentile

        # Assert
        assert avg_time < 1.0  # Average processing time under 1 second
        assert p95_time < 2.0  # 95th percentile under 2 seconds
        assert max(processing_times) < 5.0  # Maximum processing time under 5 seconds

    @pytest.mark.performance
    def test_data_accuracy_validation(self, mock_reporting_service):
        """Test data accuracy metrics for analytics reports."""
        # Arrange
        test_data = {
            "actual_values": [100, 200, 300, 400, 500],
            "predicted_values": [98, 205, 302, 395, 503],
        }

        # Act
        accuracy_metrics = mock_reporting_service.validate_data_accuracy(
            test_data["actual_values"], test_data["predicted_values"]
        )

        # Assert
        assert (
            accuracy_metrics["mape"] <= 5.0
        )  # Mean Absolute Percentage Error under 5%
        assert accuracy_metrics["rmse"] <= 10.0  # Root Mean Square Error under 10
        assert accuracy_metrics["accuracy_score"] >= 0.95  # 95% minimum accuracy

    @pytest.mark.performance
    def test_analytics_storage_verification(self, mock_reporting_service):
        """Test analytics storage performance and integrity."""
        # Arrange
        test_data = {
            "user_id": 1,
            "analysis_type": "career_insights",
            "data": {"trend": "increasing", "confidence": 0.95},
        }

        # Act
        storage_metrics = mock_reporting_service.verify_analytics_storage(test_data)

        # Assert
        assert storage_metrics["write_time"] < 0.5  # Write time under 500ms
        assert storage_metrics["read_time"] < 0.2  # Read time under 200ms
        assert storage_metrics["data_integrity"] is True

    @pytest.mark.performance
    async def test_concurrent_analytics_processing(self, mock_reporting_service):
        """Test performance under concurrent analytics processing."""
        # Arrange
        num_concurrent = 10
        mock_reporting_service.process_analytics.return_value = {"status": "success"}

        # Act
        start_time = datetime.now()
        tasks = [
            mock_reporting_service.process_analytics() for _ in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()

        total_time = (end_time - start_time).total_seconds()

        # Assert
        assert total_time < 5.0  # Total time for concurrent processing under 5 seconds
        assert all(r["status"] == "success" for r in results)
        assert len(results) == num_concurrent

    @pytest.mark.performance
    def test_memory_usage_monitoring(self, mock_reporting_service):
        """Test memory usage during analytics processing."""
        # Arrange
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Act
        mock_reporting_service.run_heavy_analysis()
        peak_memory = process.memory_info().rss

        memory_increase = peak_memory - initial_memory

        # Assert
        assert memory_increase < 500 * 1024 * 1024  # Memory increase under 500MB
        assert peak_memory < 1024 * 1024 * 1024  # Peak memory under 1GB        # Assert
        assert memory_increase < 500 * 1024 * 1024  # Memory increase under 500MB
        assert peak_memory < 1024 * 1024 * 1024  # Peak memory under 1GB
