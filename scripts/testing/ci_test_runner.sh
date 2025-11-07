#!/bin/bash

# CI/CD Test Runner Script for CareerCopilot
# This script is designed to run in CI/CD environments

set -e  # Exit on error

# Default values
ENVIRONMENT="test"
PARALLEL=true
WORKERS=4
REPORT_DIR="test-reports"
SUITE="all"
TIMEOUT=300

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -e|--environment)
            ENVIRONMENT="$2"
            shift
            shift
            ;;
        -s|--suite)
            SUITE="$2"
            shift
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift
            shift
            ;;
        -r|--report-dir)
            REPORT_DIR="$2"
            shift
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Python version
    python3 --version || {
        echo "Python 3 is required"
        exit 1
    }
    
    # Check pip
    pip3 --version || {
        echo "pip3 is required"
        exit 1
    }
    
    # Check virtualenv
    python3 -m venv --help > /dev/null || {
        echo "python3-venv is required"
        exit 1
    }
}

# Function to setup virtual environment
setup_venv() {
    echo "Setting up virtual environment..."
    
    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate venv
    source venv/bin/activate
    
    # Install requirements
    pip install -r requirements.txt
    pip install -r requirements-test.txt
}

# Function to setup test environment
setup_test_env() {
    echo "Setting up test environment: $ENVIRONMENT"
    
    # Load environment variables
    if [ -f ".env.$ENVIRONMENT" ]; then
        export $(cat .env.$ENVIRONMENT | xargs)
    fi
    
    # Setup test database if needed
    if [ "$ENVIRONMENT" = "test" ]; then
        python scripts/setup_test_db.py
    fi
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    
    # Use the unified test orchestrator
    CMD="python scripts/test_orchestrator.py run"
    
    # Add suite if specified
    if [ "$SUITE" != "all" ]; then
        CMD="$CMD --suite $SUITE"
    fi
    
    # Add parallel execution options
    if [ "$PARALLEL" = true ]; then
        CMD="$CMD --parallel --workers $WORKERS"
    fi
    
    # Add timeout
    CMD="$CMD --timeout $TIMEOUT"
    
    # Add coverage
    CMD="$CMD --coverage"
    
    # Add output directory
    CMD="$CMD --output $REPORT_DIR"
    
    # Run tests
    echo "Executing: $CMD"
    eval $CMD
}

# Function to generate reports
generate_reports() {
    echo "Generating test reports..."
    
    # Create report directory if it doesn't exist
    mkdir -p "$REPORT_DIR"
    
    # Generate coverage report if coverage data exists
    if [ -f ".coverage" ]; then
        echo "Generating coverage reports..."
        coverage xml -o "$REPORT_DIR/coverage.xml"
        coverage html -d "$REPORT_DIR/coverage_html"
        coverage report
    else
        echo "No coverage data found, skipping coverage reports"
    fi
    
    echo "Test reports available in: $REPORT_DIR"
}

# Main execution
main() {
    check_prerequisites
    setup_venv
    setup_test_env
    run_tests
    generate_reports
}

# Run main function
main