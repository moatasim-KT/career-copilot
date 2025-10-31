"""
LLM Service Plugins - Compatibility layer for service integration
This module provides plugin classes for different LLM providers that integrate with the service manager.
"""

from typing import Any, Dict
from ..core.service_integration import ServicePlugin, ServiceConfig
from ..core.logging import get_logger
from .llm_service import get_llm_service, ModelProvider

logger = get_logger(__name__)


class BaseLLMServicePlugin(ServicePlugin):
	"""Base class for LLM service plugins."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.llm_service = get_llm_service()
		self.provider = None

	async def start(self) -> bool:
		"""Start the LLM service plugin."""
		try:
			logger.info(f"Starting {self.provider} LLM service plugin")
			return True
		except Exception as e:
			logger.error(f"Failed to start {self.provider} LLM service plugin: {e}")
			return False

	async def stop(self) -> bool:
		"""Stop the LLM service plugin."""
		try:
			logger.info(f"Stopping {self.provider} LLM service plugin")
			return True
		except Exception as e:
			logger.error(f"Failed to stop {self.provider} LLM service plugin: {e}")
			return False

	async def health_check(self) -> Dict[str, Any]:
		"""Check health of the LLM service."""
		try:
			health_status = self.llm_service.get_service_health()
			provider_health = health_status.get(self.provider, {})

			return {
				"status": "healthy" if provider_health.get("available", False) else "unhealthy",
				"provider": self.provider,
				"circuit_breaker_state": provider_health.get("state", "unknown"),
				"failure_count": provider_health.get("failure_count", 0),
			}
		except Exception as e:
			logger.error(f"Health check failed for {self.provider}: {e}")
			return {"status": "unhealthy", "provider": self.provider, "error": str(e)}


class OpenAIServicePlugin(BaseLLMServicePlugin):
	"""OpenAI service plugin."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider = ModelProvider.OPENAI.value


class GroqServicePlugin(BaseLLMServicePlugin):
	"""Groq service plugin."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider = ModelProvider.GROQ.value


class OllamaServicePlugin(BaseLLMServicePlugin):
	"""Ollama service plugin."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider = ModelProvider.LOCAL.value  # Ollama is treated as local provider


# Export the plugin classes
__all__ = ["OpenAIServicePlugin", "GroqServicePlugin", "OllamaServicePlugin"]
