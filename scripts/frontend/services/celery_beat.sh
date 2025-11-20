#!/bin/bash
# =============================================================================
# Celery Beat Launcher (Thin Wrapper)
# =============================================================================
# This script is a thin wrapper that calls the Python-based launcher
# for proper app configuration, schedule file, and PID file setup.
#
# The Python launcher ensures:
#   ✅ Correct app import (app.core.celery_app)
#   ✅ Proper schedule file location
#   ✅ PID file configuration
#   ✅ Python path configuration
#
# Direct usage of the Python launcher is preferred:
#   python backend/scripts/celery/start_celery_beat.py
# =============================================================================

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Starting Celery Beat (using Python launcher)..."

# Call Python launcher for proper configuration
cd "$PROJECT_ROOT"
exec python backend/scripts/celery/start_celery_beat.py

