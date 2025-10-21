#!/usr/bin/env python3
"""
Test script to verify configuration loading and validation.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.config.validator import run_full_validation, log_validation_results


def test_config_loading():
    """Test configuration loading and validation"""
    print("=" * 80)
    print("Testing Configuration Loading")
    print("=" * 80)
    print()
    
    try:
        # Load settings
        print("Loading settings...")
        settings = get_settings()
        print("✓ Settings loaded successfully")
        print()
        
        # Run validation
        print("Running configuration validation...")
        results = run_full_validation(settings)
        all_valid = log_validation_results(results)
        print()
        
        # Display key configuration values
        print("Key Configuration Values:")
        print("-" * 80)
        print(f"Environment: {settings.environment}")
        print(f"Database: {settings.database_url}")
        print(f"JWT Algorithm: {settings.jwt_algorithm}")
        print(f"JWT Expiration: {settings.jwt_expiration_hours} hours")
        print(f"Scheduler Enabled: {settings.enable_scheduler}")
        print(f"Job Scraping Enabled: {settings.enable_job_scraping}")
        print(f"SMTP Enabled: {settings.smtp_enabled}")
        print(f"Debug Mode: {settings.debug}")
        print("-" * 80)
        print()
        
        if all_valid:
            print("✓ All configuration validations passed!")
            return 0
        else:
            print("✗ Some configuration validations failed")
            return 1
            
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_config_loading())
