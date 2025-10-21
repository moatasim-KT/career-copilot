"""Logging configuration"""

import logging
import sys
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from datetime import datetime
from ..core.config import get_settings

settings = get_settings()

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def setup_logging():
    """
    Sets up structured logging for the application.
    Logs to console and a rotating file with appropriate levels.
    """
    log_level = settings.log_level.upper()
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Ensure log directory exists
    if settings.log_file:
        log_dir = os.path.dirname(settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # File handler (rotating) with detailed format
        file_handler = RotatingFileHandler(
            settings.log_file,
            maxBytes=1024 * 1024 * 10,  # 10 MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file for errors and above
        error_log_file = settings.log_file.replace(".log", "_error.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=1024 * 1024 * 10,  # 10 MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    root_logger.info(f"Logging configured with level: {log_level}")
    root_logger.info(f"Log file: {settings.log_file if settings.log_file else 'Console only'}")


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
