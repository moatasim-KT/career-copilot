"""
FastAPI Dependencies

This module provides dependency injection for the application.
"""

from .core.service_integration import ServiceRegistry

# Global service registry instance
service_registry = ServiceRegistry()

def get_service_registry():
    """Get the global service registry instance."""
    return service_registry
