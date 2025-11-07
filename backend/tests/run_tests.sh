#!/bin/bash
# Setup test environment and run tests with proper fixtures

set -e

echo "🔧 Setting up test environment..."

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your venv first: source venv/bin/activate"
fi

# Install test dependencies if needed
echo "📦 Checking test dependencies..."
python -m pip install -q pytest pytest-asyncio pytest-cov pytest-xdist 2>/dev/null || true

# Remove old test database if it exists
if [ -f "test_career_copilot.db" ]; then
    echo "🗑️  Removing old test database..."
    rm -f test_career_copilot.db*
fi

# Seed test data
echo "🌱 Seeding test database with user_id=1..."
python tests/seed_test_data.py || echo "⚠️  Warning: Seeding failed (will be handled by fixtures)"

# Run tests
echo ""
echo "🧪 Running tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $# -eq 0 ]; then
    # No arguments - run all tests
    pytest tests/ -v --tb=short
else
    # Run specific tests
    pytest "$@"
fi

exit_code=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $exit_code -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "❌ Tests failed with exit code $exit_code"
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "   - Check tests/README.md for documentation"
    echo "   - Ensure test user fixtures are being used"
    echo "   - Try removing test database: rm test_career_copilot.db*"
fi

exit $exit_code
