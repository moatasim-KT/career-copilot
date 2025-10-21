#!/bin/bash
set -e

# Production entrypoint script for backend
echo "🚀 Starting Contract Analyzer Backend in Production Mode..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
while ! nc -z ${DATABASE_HOST:-db} ${DATABASE_PORT:-5432}; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✅ Database connection established"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis connection..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    echo "Redis not ready, waiting..."
    sleep 2
done
echo "✅ Redis connection established"

# Run database migrations
echo "🗄️ Running database migrations..."
python -m alembic upgrade head

# Initialize services if needed
if [ -f "backend/app/scripts/initialize_services.py" ]; then
    echo "🔧 Initializing services..."
    python backend/app/scripts/initialize_services.py
fi

# Validate configuration
if [ -f "backend/app/scripts/validate_config.py" ]; then
    echo "✅ Validating configuration..."
    python backend/app/scripts/validate_config.py
fi

# Create necessary directories
mkdir -p logs data cache uploads temp

# Set proper permissions
chmod 755 logs data cache uploads temp

# Log startup information
echo "📊 Backend Configuration:"
echo "  Environment: ${ENVIRONMENT:-production}"
echo "  Workers: ${WORKERS:-4}"
echo "  Host: ${HOST:-0.0.0.0}"
echo "  Port: ${PORT:-8000}"
echo "  Database: ${DATABASE_HOST:-db}:${DATABASE_PORT:-5432}"
echo "  Redis: ${REDIS_HOST:-redis}:${REDIS_PORT:-6379}"

# Execute the main command
echo "🎯 Starting application server..."
exec "$@"