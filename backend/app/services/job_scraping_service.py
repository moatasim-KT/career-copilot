"""Compatibility layer for legacy imports.

This module provides JobScrapingService as an alias to JobManagementSystem
to maintain backward compatibility with external scripts or documentation
that may reference the old service name.

All internal code has been migrated to use JobManagementSystem directly.
This file can be removed once all external references are updated.
"""

from .job_service import JobManagementSystem as JobScrapingService

__all__ = ["JobScrapingService"]
