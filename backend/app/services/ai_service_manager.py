"""
AI Service Manager - Compatibility layer for consolidated LLM Service
This module provides backward compatibility for code that expects ai_service_manager.
"""

from .llm_service import LLMService, ModelType, get_llm_service
from ..core.logging import get_logger

logger = get_logger(__name__)

# Re-export ModelType for backward compatibility
__all__ = ['ModelType', 'get_ai_service_manager', 'AIServiceManager']

# Alias for backward compatibility
AIServiceManager = LLMService

def get_ai_service_manager() -> LLMService:
    """
    Get the AI service manager instance.
    This is a compatibility function that returns the consolidated LLM service.
    """
    return get_llm_service()