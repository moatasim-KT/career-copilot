#!/bin/bash

# Start the backend
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start the frontend
cd ../frontend
npm run start