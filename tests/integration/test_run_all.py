"""
Test runner for all API endpoint integration tests.
Executes comprehensive test suite and generates coverage report.
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pytest
import sys
import os
from pathlib import Path


def run_all_tests():
    """Run all API endpoint integration tests."""
    
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # Test files to run
    test_files = [
        "test_api_endpoints.py",
        "test_recommendation_endpoints.py", 
        "test_notification_endpoints.py",
        "test_auth_endpoints.py"
    ]
    
    # Pytest arguments
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
        f"--rootdir={test_dir}",  # Set root directory
    ]
    
    # Add coverage if available
    try:
        import coverage
        pytest_args.extend([
            "--cov=backend.app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    except ImportError:
        print("Coverage not available, running tests without coverage")
    
    # Add test files
    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            pytest_args.append(str(test_path))
        else:
            print(f"Warning: Test file {test_file} not found")
    
    # Run tests
    print("Running Career Copilot API Integration Tests...")
    print("=" * 60)
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All API endpoint tests passed successfully!")
        print("Task 3.3 - API endpoint tests completed")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Please review the output above.")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())