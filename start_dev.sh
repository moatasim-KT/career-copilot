#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Career Copilot in Development Mode..."

# --- Configuration ---
# Set environment variables for development
export ENVIRONMENT=development
export DEBUG=true

# --- Virtual Environment ---
echo "Activating virtual environment..."
source venv/bin/activate

# --- Database Migrations ---
echo "Running database migrations..."
cd backend
alembic upgrade head
cd ..
echo "✅ Database migrations complete."

# --- Seed Data (Optional) ---
read -p "Do you want to seed test data? (y/N): " seed_choice
if [[ "$seed_choice" =~ ^[Yy]$ ]]; then
    echo "Seeding test data..."
    python backend/scripts/seed_data.py
    echo "✅ Test data seeded."
else
    echo "Skipping data seeding."
fi

# --- Start Backend API (Uvicorn with reload) ---
echo "Starting Backend API with Uvicorn (reload enabled)..."
# The app is located at backend/app/main.py, and the FastAPI app instance is named 'app'
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!
echo "Backend API started with PID: $BACKEND_PID"

# --- Start Frontend (Streamlit) ---
echo "Starting Frontend with Streamlit..."
# Streamlit will run on port 8501
exec streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo "Career Copilot is running in development mode!"
echo "Backend API: http://localhost:8002/docs"
echo "Frontend: http://localhost:8501"

# Keep the script running to keep the background processes alive
wait $BACKEND_PID $FRONTEND_PID
