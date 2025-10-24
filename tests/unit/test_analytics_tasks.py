"""Unit tests for analytics tasks and data generation validation."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from backend.app.models.analytics import ANALYTICS_TYPES, Analytics
from backend.app.services.reporting_insights_service import ReportingInsightsService


@pytest.fixture
def mock_reporting_service():
    return Mock(spec=ReportingInsightsService)


@pytest.fixture
def mock_db():
    return Mock(spec=Session)


class TestAnalyticsTasks:
    """Test suite for analytics task execution and validation."""

    @pytest.mark.asyncio
    async def test_manual_trigger_analytics_task(self, mock_reporting_service, mock_db):
        """Test manual triggering of analytics tasks."""
        # Arrange
        analysis_type = "salary_trends"
        user_id = 1
        mock_reporting_service._save_report.return_value = True

        # Act
        result = await mock_reporting_service.run_manual_analytics(
            db=mock_db, user_id=user_id, analysis_type=analysis_type
        )

        # Assert
        assert result is not None
        mock_reporting_service._save_report.assert_called_once()
        assert mock_db.add.call_count == 1
        assert mock_db.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_analytics_data_generation(self, mock_reporting_service, mock_db):
        """Test analytics data generation process."""
        # Arrange
        user_id = 1
        mock_reporting_service._analyze_level_progression.return_value = {
            "progression_trend": "advancing",
            "primary_level": "senior",
        }

        # Act
        result = await mock_reporting_service.generate_career_insights(
            db=mock_db, user_id=user_id
        )

        # Assert
        assert result is not None
        assert "progression_trend" in result
        assert result["progression_trend"] == "advancing"
        mock_reporting_service._analyze_level_progression.assert_called_once()

    def test_trend_analysis_validation(self, mock_reporting_service):
        """Test trend analysis validation logic."""
        # Arrange
        salary_progression = [
            {"salary": 80000, "date": datetime.now() - timedelta(days=90)},
            {"salary": 85000, "date": datetime.now() - timedelta(days=60)},
            {"salary": 90000, "date": datetime.now() - timedelta(days=30)},
        ]

        # Act
        result = mock_reporting_service._analyze_salary_trend_progression(
            salary_progression
        )

        # Assert
        assert result is not None
        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["trend_direction"] in ["increasing", "decreasing", "stable"]

    @pytest.mark.asyncio
    async def test_analytics_data_accuracy(self, mock_reporting_service, mock_db):
        """Test accuracy of generated analytics data."""
        # Arrange
        user_id = 1
        mock_data = {"avg_response_time": 2.5, "success_rate": 0.95, "error_rate": 0.05}
        mock_reporting_service.get_performance_metrics.return_value = mock_data

        # Act
        result = await mock_reporting_service.validate_analytics_accuracy(
            db=mock_db, user_id=user_id
        )

        # Assert
        assert result["success_rate"] >= 0.9  # 90% minimum success rate
        assert result["error_rate"] <= 0.1  # 10% maximum error rate
        assert (
            result["avg_response_time"] < 5.0
        )  # 5 second maximum response time        assert result['error_rate'] <= 0.1    # 10% maximum error rate
        assert result["avg_response_time"] < 5.0  # 5 second maximum response time
