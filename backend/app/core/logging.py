"""Logging configuration"""

import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from ..core.config import get_settings

settings = get_settings()

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def setup_logging():
    """
    Sets up structured logging for the application.
    Logs to console and a rotating file.
    """
    log_level = settings.log_level.upper()
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(levelname)s:     %(name)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (rotating)
    if settings.log_file:
        file_handler = RotatingFileHandler(
            settings.log_file,
            maxBytes=1024 * 1024 * 5,  # 5 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    root_logger.info(f"Logging configured with level: {log_level}")


def set_correlation_id(correlation_id: str):
    """Set correlation ID for request tracking"""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return _correlation_id.get()


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get audit logger instance"""
    return logging.getLogger("audit")
