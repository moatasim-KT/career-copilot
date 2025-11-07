#!/bin/bash
# Career Copilot - Quick Deployment Script

set -e

echo "🚀 Career Copilot Docker Deployment"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your actual values before proceeding."
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose first."
    exit 1
fi

echo "✅ Docker and docker-compose found"
echo ""

# Choose environment
echo "Select environment:"
echo "1) Development (hot-reload, less resources)"
echo "2) Production (optimized, full stack)"
read -p "Enter choice [1-2]: " env_choice

case $env_choice in
    1)
        COMPOSE_FILE="docker-compose.dev.yml"
        echo "📝 Using development configuration"
        ;;
    2)
        COMPOSE_FILE="docker-compose.yml"
        echo "📝 Using production configuration"
        
        # Check for SSL certificates
        if [ ! -f "deployment/nginx/ssl/cert.pem" ]; then
            echo ""
            echo "⚠️  SSL certificates not found!"
            read -p "Generate self-signed certificates? [y/N]: " gen_ssl
            if [[ $gen_ssl =~ ^[Yy]$ ]]; then
                mkdir -p deployment/nginx/ssl
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                    -keyout deployment/nginx/ssl/key.pem \
                    -out deployment/nginx/ssl/cert.pem \
                    -subj "/C=US/ST=State/L=City/O=Organization/CN=career-copilot.com"
                echo "✅ Self-signed certificates generated"
            fi
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🏗️  Building Docker images..."
docker-compose -f $COMPOSE_FILE build

echo ""
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "📊 Service Status:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Access Points:"
if [ "$COMPOSE_FILE" = "docker-compose.dev.yml" ]; then
    echo "   Frontend:    http://localhost:3000"
    echo "   Backend API: http://localhost:8002"
    echo "   API Docs:    http://localhost:8002/docs"
    echo "   Prometheus:  http://localhost:9090"
    echo "   Grafana:     http://localhost:3001 (admin/admin)"
else
    echo "   Application: https://localhost (or your domain)"
    echo "   Prometheus:  https://localhost/prometheus/ (basic auth)"
    echo "   Grafana:     https://localhost/grafana/ (basic auth)"
fi

echo ""
echo "📝 Useful Commands:"
echo "   View logs:       docker-compose -f $COMPOSE_FILE logs -f"
echo "   Stop services:   docker-compose -f $COMPOSE_FILE down"
echo "   Restart:         docker-compose -f $COMPOSE_FILE restart"
echo ""
