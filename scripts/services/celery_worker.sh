#!/bin/bash
# Start Celery worker
celery -A app.celery worker --loglevel=info --concurrency=4
