"""Compatibility layer for legacy imports.

Provides JobScraperService as an alias to the consolidated JobManagementSystem.
This avoids refactoring all call sites that import job_scraper_service.
"""

from .job_service import JobManagementSystem as JobScraperService

__all__ = ["JobScraperService"]
