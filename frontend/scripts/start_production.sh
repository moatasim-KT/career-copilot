#!/bin/bash

# Production Startup Script for Contract Analyzer Frontend
set -e

echo "🚀 Starting Contract Analyzer Frontend in Production Mode..."

# Set environment variables
export STREAMLIT_ENV=production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if required files exist
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "⚠️  Warning: .streamlit/secrets.toml not found. Copying from template..."
    cp .streamlit/secrets.toml.template .streamlit/secrets.toml
    echo "📝 Please edit .streamlit/secrets.toml with your actual configuration values"
fi

# Create necessary directories
mkdir -p logs data cache

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations if needed
if [ -f "scripts/migrate.py" ]; then
    echo "🗄️  Running database migrations..."
    python scripts/migrate.py
fi

# Start the application
echo "🎯 Starting Streamlit application..."
streamlit run production_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=true \
    --server.enableXsrfProtection=true \
    --browser.gatherUsageStats=false \
    --global.developmentMode=false