import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.config.validator import run_full_validation, log_validation_results


def test_config_loading():
    """Test configuration loading and validation"""
    settings = get_settings()
    results = run_full_validation(settings)
    all_valid = log_validation_results(results)
    assert all_valid is True, "Some configuration validations failed"
