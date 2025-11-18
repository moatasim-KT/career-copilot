#!/bin/bash
# Setup PostgreSQL test database for Career Copilot tests

set -e

echo "🔧 Setting up PostgreSQL test database..."

# Database configuration
DB_NAME="career_copilot_test"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo "Please start PostgreSQL:"
    echo "  - Docker: docker-compose up -d postgres"
    echo "  - macOS: brew services start postgresql"
    echo "  - Linux: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Drop test database if it exists
echo "🗑️  Dropping existing test database (if exists)..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true

# Create test database
echo "📦 Creating test database: $DB_NAME"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# Grant privileges
echo "🔐 Granting privileges..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "✅ Test database setup complete!"
echo ""
echo "You can now run tests with:"
echo "  pytest tests/ -v"
echo "  pytest tests/ --cov=app --cov-report=html"
echo ""
echo "Database connection string:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
