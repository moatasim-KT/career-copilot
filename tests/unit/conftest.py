"""Shared fixtures for analytics testing."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from backend.app.services.reporting_insights_service import ReportingInsightsService


@pytest.fixture
def test_config():
    """Load test configuration."""
    config_path = Path(__file__).parent / 'analytics_test_config.json'
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def mock_analytics_data():
    """Generate mock analytics data for testing."""
    return {
        'user_id': 1,
        'timestamp': datetime.now().isoformat(),
        'analytics_type': 'career_insights',
        'data': {
            'trend': 'increasing',
            'confidence': 0.95,
            'metrics': {
                'applications': 50,
                'responses': 25,
                'interviews': 10
            }
        },
        'metadata': {
            'source': 'automated_analysis',
            'version': '1.0'
        }
    }


@pytest.fixture
def mock_reporting_service():
    """Create a mock reporting service with common methods."""
    service = Mock(spec=ReportingInsightsService)
    
    # Configure common mock behaviors
    service.generate_career_insights.return_value = {
        'progression_trend': 'advancing',
        'primary_level': 'senior'
    }
    
    service._analyze_salary_trend_progression.return_value = {
        'trend_direction': 'increasing',
        'trend_percentage': 7.5
    }
    
    service.validate_data_accuracy.return_value = {
        'mape': 3.5,
        'rmse': 8.0,
        'accuracy_score': 0.97
    }
    
    return service


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    return session


@pytest.fixture
async def async_reporting_service():
    """Create an async mock reporting service."""
    service = AsyncMock(spec=ReportingInsightsService)
    
    async def mock_run_manual_analytics(*args, **kwargs):
        return {'status': 'success', 'timestamp': datetime.now().isoformat()}
    
    service.run_manual_analytics.side_effect = mock_run_manual_analytics
    return service