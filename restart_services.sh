#!/bin/bash

# Kill existing processes
echo "Stopping services..."
pkill -f "uvicorn"
pkill -f "next dev"
pkill -f "celery"

# Wait a moment
sleep 2

# Start Backend
echo "Starting Backend..."
cd backend
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../data/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
nohup npm run dev > ../data/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID"

echo "Services restarted!"
