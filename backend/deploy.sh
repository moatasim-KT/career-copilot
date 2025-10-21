#!/bin/bash

# Production deployment script for Career Co-Pilot

set -e

echo "🚀 Starting Career Co-Pilot deployment..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env.production not found"
fi

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start database and wait for it to be ready
echo "🗄️  Starting database..."
docker-compose -f docker-compose.prod.yml up -d postgres redis
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start all services
echo "▶️  Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Health check
echo "🏥 Running health check..."
curl -f http://localhost:8000/api/v1/health || {
    echo "❌ Health check failed!"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
}

echo "✅ Deployment completed successfully!"
echo "📊 Application is running at http://localhost:8000"
echo "📝 View logs: docker-compose -f docker-compose.prod.yml logs -f"