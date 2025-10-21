"""
Frontend package - Streamlit-based user interface for job application tracking.
"""

from .app import main
from .config import FrontendConfig
from .utils.api_client import APIClient

__all__ = [
	"APIClient",
	"FrontendConfig",
	"main",
]
