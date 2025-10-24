#!/bin/bash
set -e

echo "🚀 Starting Contract Analyzer Frontend..."

# Wait for backend to be ready
echo "⏳ Waiting for backend connection..."
while ! nc -z ${BACKEND_HOST:-backend} ${BACKEND_PORT:-8000}; do
    echo "Backend not ready, waiting..."
    sleep 2
done
echo "✅ Backend connection established"

# Create necessary directories
mkdir -p logs data cache uploads temp .streamlit

# Set proper permissions
chmod 755 logs data cache uploads temp

# Log startup information
echo "📊 Frontend Configuration:"
echo "  Environment: ${STREAMLIT_ENV:-production}"
echo "  Backend URL: ${BACKEND_URL:-http://backend:8000}"
echo "  Port: 8501"

# Execute the main command
echo "🎯 Starting Streamlit application..."
exec "$@"
