#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Career Copilot in Production Mode..."

# --- Configuration ---
# Set environment variables for production
export ENVIRONMENT=production
export DEBUG=false

# --- Virtual Environment ---
echo "Activating virtual environment..."
source venv/bin/activate

# --- Database Migrations ---
echo "Running database migrations..."
cd backend
alembic upgrade head
cd ..
echo "✅ Database migrations complete."

# --- Start Backend API (Gunicorn) ---
echo "Starting Backend API with Gunicorn..."
# Using Gunicorn with Uvicorn workers for production
# Adjust --workers and --bind as needed for your server
# The app is located at backend/app/main.py, and the FastAPI app instance is named 'app'
exec gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002 --log-level info --timeout 120 &
BACKEND_PID=$!
echo "Backend API started with PID: $BACKEND_PID"

# --- Start Frontend (Streamlit) ---
echo "Starting Frontend with Streamlit..."
# Streamlit will run on port 8501
exec streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo "Career Copilot is running!"
echo "Backend API: http://localhost:8002"
echo "Frontend: http://localhost:8501"

# Keep the script running to keep the background processes alive
wait $BACKEND_PID $FRONTEND_PID
