"""
AI Manager for coordinating AI services and model selection.
"""

from ..services.llm_service import LLMService, ModelType, get_llm_service


# Re-export for backward compatibility
def get_ai_manager() -> LLMService:
	"""Get AI manager instance."""
	return get_llm_service()


# Re-export ModelType
__all__ = ["get_ai_manager", "ModelType"]
