#!/usr/bin/env python3
"""
Celery worker startup script
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.celery_app import celery_app

if __name__ == "__main__":
	# Start Celery worker
	celery_app.start(
		argv=[
			"worker",
			"--loglevel=info",
			"--concurrency=4",
			"--queues=resume_parsing,content_generation,job_scraping,notifications,analytics,high_priority,low_priority,celery",
			"--hostname=worker@%h",
		]
	)
