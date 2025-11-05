"""Compatibility layer for legacy imports.

Provides JobScraperService as an alias to the existing JobScrapingService.
This avoids refactoring all call sites that import job_scraper_service.
"""

from .job_scraping_service import JobScrapingService as JobScraperService

__all__ = ["JobScraperService"]
