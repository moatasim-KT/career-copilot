"""Logging configuration"""

import logging
import sys
from contextvars import ContextVar

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str):
    """Set correlation ID for request tracking"""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return _correlation_id.get()


def get_audit_logger() -> logging.Logger:
    """Get audit logger instance"""
    return logging.getLogger("audit")
