"""
Logging Service for centralized logging.
"""

import logging
from typing import Dict, Any, Optional

class LoggingService:
    """Service for centralized logging."""

    def __init__(self, logger_name: str = "app"):
        self.logger = logging.getLogger(logger_name)

    def log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a message."""
        self.logger.log(level, message, extra=extra)

_service = None

def get_logging_service() -> "LoggingService":
    """Get the logging service."""
    global _service
    if _service is None:
        _service = LoggingService()
    return _service
