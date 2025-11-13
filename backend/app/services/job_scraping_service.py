"""Compatibility layer for legacy imports.

This module provides JobScrapingService as an alias to JobManagementSystem
to maintain backward compatibility with code that imports job_scraping_service.

This file exists because:
1. backend/app/api/v1/linkedin_jobs.py imports JobScrapingService
2. backend/app/tasks/scheduled_tasks.py imports JobScrapingService

TODO: Eventually update all imports to use JobManagementSystem directly
from job_service.py, then remove this compatibility layer.
"""

from .job_service import JobManagementSystem as JobScrapingService

__all__ = ["JobScrapingService"]
