"""
AI Manager for coordinating AI services and model selection.
"""

from ..services.ai_service_manager import AIServiceManager, ModelType, get_ai_service_manager

# Re-export for backward compatibility
def get_ai_manager() -> AIServiceManager:
    """Get AI manager instance."""
    return get_ai_service_manager()

# Re-export ModelType
__all__ = ["get_ai_manager", "ModelType"]