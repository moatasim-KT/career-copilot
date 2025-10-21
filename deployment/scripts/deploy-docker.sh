#!/bin/bash
# Docker deployment script with monitoring and scaling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_MODE=${1:-production}
SCALE_WORKERS=${2:-3}

echo -e "${GREEN}🚀 Contract Analyzer Docker Deployment${NC}"
echo "Mode: $DEPLOYMENT_MODE"
echo "Workers: $SCALE_WORKERS"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo ""

# Check environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.template .env
    echo -e "${RED}❌ Please configure .env file with your API keys and restart.${NC}"
    exit 1
fi

# Validate required environment variables
echo -e "${YELLOW}🔍 Validating environment variables...${NC}"
source .env

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment validated${NC}"
echo ""

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose build --parallel
echo -e "${GREEN}✅ Images built${NC}"
echo ""

# Create network if not exists
echo -e "${YELLOW}🌐 Creating Docker network...${NC}"
docker network create contract-analyzer-network 2>/dev/null || echo "Network already exists"
echo ""

# Deploy based on mode
case $DEPLOYMENT_MODE in
    development)
        echo -e "${YELLOW}🚀 Starting development environment...${NC}"
        docker-compose up -d
        ;;
    
    production)
        echo -e "${YELLOW}🚀 Starting production environment...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ;;
    
    monitoring)
        echo -e "${YELLOW}🚀 Starting with monitoring stack...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
        ;;
    
    scaled)
        echo -e "${YELLOW}🚀 Starting with horizontal scaling ($SCALE_WORKERS workers)...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale worker=$SCALE_WORKERS
        ;;
    
    full)
        echo -e "${YELLOW}🚀 Starting full stack (production + monitoring + scaling)...${NC}"
        docker-compose \
            -f docker-compose.yml \
            -f docker-compose.prod.yml \
            -f docker-compose.monitoring.yml \
            -f docker-compose.scale.yml \
            up -d --scale worker=$SCALE_WORKERS
        ;;
    
    *)
        echo -e "${RED}❌ Invalid deployment mode: $DEPLOYMENT_MODE${NC}"
        echo "Valid modes: development, production, monitoring, scaled, full"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"
BACKEND_HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "")
if [ -n "$BACKEND_HEALTH" ]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

FRONTEND_HEALTH=$(curl -s http://localhost:8501/_stcore/health || echo "")
if [ -n "$FRONTEND_HEALTH" ]; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
fi

echo ""

# Display service URLs
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Service URLs:"
echo "  Frontend:    http://localhost:8501"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Health:      http://localhost:8000/health"

if [ "$DEPLOYMENT_MODE" = "monitoring" ] || [ "$DEPLOYMENT_MODE" = "full" ]; then
    echo ""
    echo "Monitoring URLs:"
    echo "  Grafana:     http://localhost:3000 (admin/admin)"
    echo "  Prometheus:  http://localhost:9090"
    echo "  AlertManager: http://localhost:9093"
fi

if [ "$DEPLOYMENT_MODE" = "scaled" ] || [ "$DEPLOYMENT_MODE" = "full" ]; then
    echo ""
    echo "Scaling URLs:"
    echo "  HAProxy Stats: http://localhost:8404/stats"
fi

echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
