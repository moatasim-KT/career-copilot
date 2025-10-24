"""Minimal E2E tests package for repository-local tests.

This package keeps the top-level import surface minimal so pytest
collection and `conftest.py` can import without pulling optional
helpers or heavy dependencies.
"""

from .orchestrator import TestOrchestrator

__all__ = ["TestOrchestrator"]
__version__ = "0.1.0"
