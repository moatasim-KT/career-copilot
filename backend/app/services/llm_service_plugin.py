"""
LLM Service Plugins - Provider-agnostic LLM service with plugin architecture
This module provides comprehensive plugin implementations for different LLM providers,
consolidating functionality from separate service files into a unified plugin system.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..core.config import get_settings
from ..core.exceptions import AuthenticationError, ExternalServiceError, NetworkError, RateLimitError, ValidationError
from ..core.logging import get_logger
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
metrics_collector = get_metrics_collector()


# Simplified service classes to avoid dependency issues
class ServiceStatus(str, Enum):
	UNKNOWN = "unknown"
	STARTING = "starting"
	HEALTHY = "healthy"
	DEGRADED = "degraded"
	UNHEALTHY = "unhealthy"
	STOPPED = "stopped"
	ERROR = "error"


class ServiceHealth:
	"""Simplified service health information."""

	def __init__(self, status: ServiceStatus, response_time: float = 0, error_message: Optional[str] = None):
		self.status = status
		self.response_time = response_time
		self.last_check = datetime.now()
		self.error_message = error_message


class ServiceConfig:
	"""Simplified service configuration."""

	def __init__(self, service_id: str, service_type: str = "ai_provider", config: Optional[Dict[str, Any]] = None):
		self.service_id = service_id
		self.service_type = service_type
		self.config = config or {}


class ServicePlugin:
	"""Simplified base plugin class."""

	def __init__(self, config: ServiceConfig):
		self.config = config
		self.service_id = config.service_id
		self._status = ServiceStatus.UNKNOWN

	async def start(self) -> bool:
		"""Start the service."""
		self._status = ServiceStatus.HEALTHY
		return True

	async def stop(self) -> bool:
		"""Stop the service."""
		self._status = ServiceStatus.STOPPED
		return True

	async def health_check(self) -> ServiceHealth:
		"""Check service health."""
		return ServiceHealth(self._status)


from ..utils.error_handler import ErrorCategory, ErrorSeverity, get_error_handler
from .cache_service import get_cache_service

logger = get_logger(__name__)
settings = get_settings()
cache_service = get_cache_service()
metrics_collector = get_metrics_collector()


class BaseLLMServicePlugin(ServicePlugin):
	"""Base class for LLM service plugins with comprehensive provider support."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider_name = None
		self.api_key = None
		self.base_url = None
		self.client = None
		self.rate_limiter = None
		self.circuit_breaker_state = "closed"
		self.failure_count = 0
		self.last_failure_time = None
		self.success_count = 0
		self.total_requests = 0

	async def start(self) -> bool:
		"""Start the LLM service plugin."""
		try:
			logger.info(f"Starting {self.provider_name} LLM service plugin")
			await self._initialize_client()
			await self._update_health(ServiceStatus.HEALTHY)
			return True
		except Exception as e:
			logger.error(f"Failed to start {self.provider_name} LLM service plugin: {e}")
			await self._update_health(ServiceStatus.ERROR, error_message=str(e))
			return False

	async def stop(self) -> bool:
		"""Stop the LLM service plugin."""
		try:
			logger.info(f"Stopping {self.provider_name} LLM service plugin")
			await self._cleanup_client()
			await self._update_health(ServiceStatus.STOPPED)
			return True
		except Exception as e:
			logger.error(f"Failed to stop {self.provider_name} LLM service plugin: {e}")
			return False

	async def health_check(self) -> ServiceHealth:
		"""Check health of the LLM service."""
		try:
			# Perform a lightweight health check
			health_data = await self._perform_health_check()
			status = ServiceStatus.HEALTHY if health_data.get("healthy", False) else ServiceStatus.UNHEALTHY

			return ServiceHealth(status=status, response_time=health_data.get("response_time", 0), last_check=datetime.now(), details=health_data)
		except Exception as e:
			logger.error(f"Health check failed for {self.provider_name}: {e}")
			return ServiceHealth(status=ServiceStatus.ERROR, last_check=datetime.now(), error_message=str(e))

	async def _initialize_client(self):
		"""Initialize the HTTP client for the provider."""
		pass

	async def _cleanup_client(self):
		"""Clean up the HTTP client."""
		if self.client and hasattr(self.client, "close"):
			await self.client.close()

	async def _perform_health_check(self) -> Dict[str, Any]:
		"""Perform provider-specific health check."""
		return {"healthy": True, "response_time": 0}

	def _update_metrics(self, success: bool, response_time: float):
		"""Update performance metrics."""
		self.total_requests += 1
		if success:
			self.success_count += 1
		else:
			self.failure_count += 1
			self.last_failure_time = datetime.now()

	def get_success_rate(self) -> float:
		"""Get success rate for this provider."""
		if self.total_requests == 0:
			return 1.0
		return self.success_count / self.total_requests


class OpenAIServicePlugin(BaseLLMServicePlugin):
	"""OpenAI service plugin with comprehensive error handling and monitoring."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider_name = "openai"
		self.api_key = config.config.get("api_key") or getattr(settings, "openai_api_key", None)
		self.base_url = "https://api.openai.com/v1"
		self.models = ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
		self.max_retries = 3
		self.timeout = 30

	async def _initialize_client(self):
		"""Initialize OpenAI client."""
		from openai import AsyncOpenAI

		self.client = AsyncOpenAI(
			api_key=self.api_key.get_secret_value() if hasattr(self.api_key, "get_secret_value") else self.api_key,
			base_url=self.base_url,
			max_retries=self.max_retries,
			timeout=self.timeout,
		)

	async def _perform_health_check(self) -> Dict[str, Any]:
		"""Check OpenAI service health."""
		try:
			start_time = time.time()
			# Simple models list call to check connectivity
			await self.client.models.list()
			response_time = time.time() - start_time
			return {"healthy": True, "response_time": response_time}
		except Exception as e:
			return {"healthy": False, "error": str(e), "response_time": 0}

	async def generate_completion(self, messages: List[Dict], model: str = "gpt-3.5-turbo", **kwargs) -> Dict[str, Any]:
		"""Generate completion using OpenAI."""
		try:
			start_time = time.time()

			response = await self.client.chat.completions.create(model=model, messages=messages, **kwargs)

			response_time = time.time() - start_time
			self._update_metrics(True, response_time)

			return {
				"content": response.choices[0].message.content,
				"usage": response.usage.model_dump() if response.usage else {},
				"model": response.model,
				"response_time": response_time,
			}
		except Exception as e:
			response_time = time.time() - start_time
			self._update_metrics(False, response_time)
			logger.error(f"OpenAI completion failed: {e}")
			raise


class GroqServicePlugin(BaseLLMServicePlugin):
	"""Groq service plugin with comprehensive monitoring and optimization."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider_name = "groq"
		self.api_key = config.config.get("api_key") or getattr(settings, "groq_api_key", None)
		self.base_url = "https://api.groq.com/openai/v1"
		self.models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
		self.max_retries = 3
		self.timeout = 30

	async def _initialize_client(self):
		"""Initialize Groq client (uses OpenAI-compatible API)."""
		from openai import AsyncOpenAI

		self.client = AsyncOpenAI(
			api_key=self.api_key.get_secret_value() if hasattr(self.api_key, "get_secret_value") else self.api_key,
			base_url=self.base_url,
			max_retries=self.max_retries,
			timeout=self.timeout,
		)

	async def _perform_health_check(self) -> Dict[str, Any]:
		"""Check Groq service health."""
		try:
			start_time = time.time()
			# Simple models list call to check connectivity
			await self.client.models.list()
			response_time = time.time() - start_time
			return {"healthy": True, "response_time": response_time}
		except Exception as e:
			return {"healthy": False, "error": str(e), "response_time": 0}

	async def generate_completion(self, messages: List[Dict], model: str = "llama-3.1-8b-instant", **kwargs) -> Dict[str, Any]:
		"""Generate completion using Groq."""
		try:
			start_time = time.time()

			response = await self.client.chat.completions.create(model=model, messages=messages, **kwargs)

			response_time = time.time() - start_time
			self._update_metrics(True, response_time)

			return {
				"content": response.choices[0].message.content,
				"usage": response.usage.model_dump() if response.usage else {},
				"model": response.model,
				"response_time": response_time,
			}
		except Exception as e:
			response_time = time.time() - start_time
			self._update_metrics(False, response_time)
			logger.error(f"Groq completion failed: {e}")
			raise


class OllamaServicePlugin(BaseLLMServicePlugin):
	"""Ollama service plugin for local LLM deployments."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider_name = "ollama"
		self.base_url = config.config.get("base_url", "http://localhost:11434")
		self.models = ["llama2", "codellama", "mistral"]  # Common models
		self.timeout = 60  # Local models can be slower

	async def _initialize_client(self):
		"""Initialize HTTP client for Ollama."""
		self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

	async def _perform_health_check(self) -> Dict[str, Any]:
		"""Check Ollama service health."""
		try:
			start_time = time.time()
			response = await self.client.get("/api/tags")
			response_time = time.time() - start_time
			return {"healthy": response.status_code == 200, "response_time": response_time}
		except Exception as e:
			return {"healthy": False, "error": str(e), "response_time": 0}

	async def generate_completion(self, messages: List[Dict], model: str = "llama2", **kwargs) -> Dict[str, Any]:
		"""Generate completion using Ollama."""
		try:
			start_time = time.time()

			# Convert messages to Ollama format
			prompt = self._convert_messages_to_prompt(messages)

			payload = {"model": model, "prompt": prompt, "stream": False, **kwargs}

			response = await self.client.post("/api/generate", json=payload)
			response.raise_for_status()
			result = response.json()

			response_time = time.time() - start_time
			self._update_metrics(True, response_time)

			return {
				"content": result.get("response", ""),
				"usage": {
					"prompt_tokens": result.get("prompt_eval_count", 0),
					"completion_tokens": result.get("eval_count", 0),
					"total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
				},
				"model": model,
				"response_time": response_time,
			}
		except Exception as e:
			response_time = time.time() - start_time
			self._update_metrics(False, response_time)
			logger.error(f"Ollama completion failed: {e}")
			raise

	def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
		"""Convert chat messages to a single prompt for Ollama."""
		prompt_parts = []
		for msg in messages:
			role = msg.get("role", "")
			content = msg.get("content", "")
			if role == "system":
				prompt_parts.append(f"System: {content}")
			elif role == "user":
				prompt_parts.append(f"User: {content}")
			elif role == "assistant":
				prompt_parts.append(f"Assistant: {content}")
		return "\n\n".join(prompt_parts)


class AnthropicServicePlugin(BaseLLMServicePlugin):
	"""Anthropic service plugin with comprehensive Claude model support."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.provider_name = "anthropic"
		self.api_key = config.config.get("api_key") or getattr(settings, "anthropic_api_key", None)
		self.base_url = "https://api.anthropic.com"
		self.models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]
		self.max_retries = 3
		self.timeout = 60

	async def _initialize_client(self):
		"""Initialize Anthropic client using LangChain integration."""
		from langchain_anthropic import ChatAnthropic

		api_key = self.api_key.get_secret_value() if hasattr(self.api_key, "get_secret_value") else self.api_key

		# Create client for default model
		self.client = ChatAnthropic(
			api_key=api_key, model=self.config.config.get("model_name", "claude-3-opus-20240229"), timeout=self.timeout, max_retries=self.max_retries
		)

	async def _perform_health_check(self) -> Dict[str, Any]:
		"""Check Anthropic service health with minimal token usage."""
		try:
			start_time = time.time()

			# Simple test message
			test_message = [{"role": "user", "content": "ping"}]
			response = await self.generate_completion(messages=test_message, max_tokens=10)

			response_time = time.time() - start_time
			return {"healthy": True, "response_time": response_time, "model": response.get("model", "unknown")}
		except Exception as e:
			return {"healthy": False, "error": str(e), "response_time": 0}

	async def generate_completion(self, messages: List[Dict], model: str = None, **kwargs) -> Dict[str, Any]:
		"""Generate completion using Anthropic Claude models.

		Args:
			messages: List of message dicts with 'role' and 'content'
			model: Model name override (optional)
			**kwargs: Additional parameters (temperature, max_tokens, etc.)

		Returns:
			Dict with content, usage, model, and response_time
		"""
		try:
			start_time = time.time()

			# Convert dict messages to LangChain format
			from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

			langchain_messages = []
			for msg in messages:
				role = msg.get("role", "user")
				content = msg.get("content", "")

				if role == "system":
					langchain_messages.append(SystemMessage(content=content))
				elif role == "user":
					langchain_messages.append(HumanMessage(content=content))
				elif role == "assistant":
					langchain_messages.append(AIMessage(content=content))

			# Update client model if specified
			if model and model != self.client.model_name:
				from langchain_anthropic import ChatAnthropic

				api_key = self.api_key.get_secret_value() if hasattr(self.api_key, "get_secret_value") else self.api_key
				self.client = ChatAnthropic(api_key=api_key, model=model, timeout=self.timeout, max_retries=self.max_retries)

			# Apply kwargs
			if "temperature" in kwargs:
				self.client.temperature = kwargs["temperature"]
			if "max_tokens" in kwargs:
				self.client.max_tokens = kwargs["max_tokens"]

			# Generate completion
			response = await self.client.ainvoke(langchain_messages)

			response_time = time.time() - start_time
			self._update_metrics(True, response_time)

			# Extract token usage from response metadata
			usage_data = response.response_metadata.get("usage", {})

			return {
				"content": response.content,
				"usage": {
					"prompt_tokens": usage_data.get("input_tokens", 0),
					"completion_tokens": usage_data.get("output_tokens", 0),
					"total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
				},
				"model": response.response_metadata.get("model", model or self.client.model_name),
				"response_time": response_time,
			}
		except Exception as e:
			response_time = time.time() - start_time if "start_time" in locals() else 0
			self._update_metrics(False, response_time)
			logger.error(f"Anthropic completion failed: {e}")
			raise


# Export the plugin classes
__all__ = ["AnthropicServicePlugin", "GroqServicePlugin", "OllamaServicePlugin", "OpenAIServicePlugin"]
