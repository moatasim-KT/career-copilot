from dotenv import load_dotenv

load_dotenv()

"""
Core package - Essential application components and utilities.
"""

from .config import get_settings
from .exceptions import (DocumentProcessingError, InvalidFileTypeError,
                         ResourceExhaustionError, SecurityError,
                         ValidationError, WorkflowExecutionError)

__all__ = [
                         "DocumentProcessingError",
                         "InvalidFileTypeError",
                         "ResourceExhaustionError",
                         "SecurityError",
                         "ValidationError",
                         "WorkflowExecutionError",
                         "get_settings",
]
