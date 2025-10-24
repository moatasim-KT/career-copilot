#!/bin/bash
# Start Celery beat
celery -A app.celery beat --loglevel=info
