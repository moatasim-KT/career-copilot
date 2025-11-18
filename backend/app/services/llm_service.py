"""
Unified LLM Service for handling multiple AI providers with intelligent model selection,
fallback, error handling, and performance monitoring.

**Multi-Provider Architecture**:
Supports 3 LLM providers with intelligent routing:
- OpenAI GPT-4 (primary, highest quality)
- Anthropic Claude (fallback, balanced performance)
- Groq (fast inference, cost-effective)

**Configuration**:
Provider priorities and capabilities defined in [[config/llm_config.json|LLM Config]].
API keys configured via [[backend/app/core/config.py|Settings]]:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GROQ_API_KEY

**Key Features**:
- Automatic model selection based on task complexity
- Intelligent fallback between providers
- Token optimization and cost tracking
- Response caching (Redis-backed)
- Streaming support for real-time responses
- Rate limiting and quota management
- Performance metrics collection

**Usage Example**:

.. code-block:: python

    from app.services.llm_service import LLMService
    from app.core.task_complexity import TaskComplexity

    # Initialize service
    llm = LLMService()

    # Simple completion (auto-selects best model)
    response = await llm.generate_completion(
        prompt="Analyze this job posting...",
        task_category="analysis",
        max_tokens=2000
    )

    # Structured output with specific complexity
    job_match = await llm.generate_structured_output(
        prompt="Match candidate skills to job requirements",
        output_schema=JobMatchSchema,
        complexity=TaskComplexity.MEDIUM
    )

    # Streaming response
    async for chunk in llm.stream_completion(
        prompt="Generate a cover letter...",
        task_category="generation"
    ):
        print(chunk.content, end="", flush=True)

    # Get cost report
    costs = llm.get_cost_report(time_period="last_24h")
    print(f"Total cost: ${costs['total_cost']:.4f}")

**Provider Selection Logic**:
1. Analyzes task complexity (LOW/MEDIUM/HIGH/CRITICAL)
2. Checks provider availability and quota
3. Selects optimal model based on cost/performance tradeoff
4. Falls back to secondary providers if primary fails

**Performance Tracking**:
- Token usage per provider
- Response times
- Cache hit rates
- Error rates
- Cost per operation

**Related Documentation**:
- [[config/llm_config.json|LLM Configuration]]
- [[docs/DEVELOPER_GUIDE|Developer Guide]] - Service Layer patterns
- [[backend/app/core/cost_tracker.py|Cost Tracker]]
- [[backend/app/core/token_optimizer.py|Token Optimizer]]
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..core.config import get_settings
from ..core.cost_tracker import CostCategory, get_cost_tracker
from ..core.logging import get_logger
from ..core.monitoring import get_performance_metrics_collector
from ..core.streaming_manager import StreamingChunk, StreamingMode, get_streaming_manager
from ..core.task_complexity import TaskComplexity, get_complexity_analyzer
from ..core.token_optimizer import OptimizationStrategy, TokenBudget, get_token_optimizer
from ..monitoring.metrics_collector import get_metrics_collector
from .cache_service import get_cache_service

logger = get_logger(__name__)
settings = get_settings()
metrics_collector = get_metrics_collector()
cache_service = get_cache_service()
complexity_analyzer = get_complexity_analyzer()
cost_tracker = get_cost_tracker()
performance_collector = get_performance_metrics_collector()
streaming_manager = get_streaming_manager()
token_optimizer = get_token_optimizer()


# --- Enums and Data Classes from llm_error_handler.py ---


class ErrorSeverity(str, Enum):
	"""Error severity levels."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class ErrorCategory(str, Enum):
	"""Error categories for classification."""

	AUTHENTICATION = "authentication"
	RATE_LIMIT = "rate_limit"
	QUOTA_EXCEEDED = "quota_exceeded"
	MODEL_NOT_FOUND = "model_not_found"
	INVALID_REQUEST = "invalid_request"
	TIMEOUT = "timeout"
	CONNECTION = "connection"
	SERVER_ERROR = "server_error"
	UNKNOWN = "unknown"


class RetryStrategy(str, Enum):
	"""Retry strategies for different error types."""

	NO_RETRY = "no_retry"
	IMMEDIATE = "immediate"
	EXPONENTIAL_BACKOFF = "exponential_backoff"
	LINEAR_BACKOFF = "linear_backoff"


@dataclass
class ErrorInfo:
	"""Comprehensive error information."""

	error_id: str
	provider: str
	error_type: str
	category: ErrorCategory
	severity: ErrorSeverity
	message: str
	original_exception: Optional[Exception]
	timestamp: datetime
	request_id: Optional[str] = None
	model: Optional[str] = None
	retry_count: int = 0
	context: Dict[str, Any] = None

	def __post_init__(self):
		if self.context is None:
			self.context = {}


@dataclass
class RetryConfig:
	"""Configuration for retry behavior."""

	strategy: RetryStrategy
	max_attempts: int
	base_delay: float
	max_delay: float
	exponential_base: float = 2.0
	jitter: bool = True

	@classmethod
	def no_retry(cls) -> "RetryConfig":
		return cls(RetryStrategy.NO_RETRY, 1, 0, 0)

	@classmethod
	def exponential(cls, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> "RetryConfig":
		return cls(RetryStrategy.EXPONENTIAL_BACKOFF, max_attempts, base_delay, max_delay)


# --- Custom Exceptions from llm_error_handler.py ---


class LLMError(Exception):
	"""Base class for LLM-related errors."""

	def __init__(self, message: str, error_info: Optional[ErrorInfo] = None):
		super().__init__(message)
		self.error_info = error_info


class LLMAuthenticationError(LLMError):
	pass


class LLMRateLimitError(LLMError):
	pass


class LLMQuotaExceededError(LLMError):
	pass


class LLMModelNotFoundError(LLMError):
	pass


class LLMInvalidRequestError(LLMError):
	pass


class LLMTimeoutError(LLMError):
	pass


class LLMConnectionError(LLMError):
	pass


class LLMServerError(LLMError):
	pass


# --- Service-related Enums and Data Classes ---


class ModelType(Enum):
	"""Types of AI models for different use cases."""

	CONTRACT_ANALYSIS = "contract_analysis"
	NEGOTIATION = "negotiation"
	COMMUNICATION = "communication"
	GENERAL = "general"


class ModelProvider(Enum):
	"""AI model providers."""

	OPENAI = "openai"
	ANTHROPIC = "anthropic"
	GROQ = "groq"
	LOCAL = "local"


@dataclass
class ModelConfig:
	"""Configuration for an AI model."""

	provider: ModelProvider
	model_name: str
	temperature: float
	max_tokens: int
	cost_per_token: float
	capabilities: List[str]
	priority: int
	complexity_level: TaskComplexity
	tokens_per_minute: int = 10000
	requests_per_minute: int = 60


@dataclass
class AIResponse:
	"""Response from AI model."""

	content: str
	model_used: str
	provider: ModelProvider
	confidence_score: float
	processing_time: float
	token_usage: Dict[str, int]
	cost: float
	complexity_used: TaskComplexity
	cost_category: CostCategory
	budget_impact: Dict[str, Any]
	metadata: Dict[str, Any]
	performance_metrics: Optional[Dict[str, Any]] = None
	is_streaming: bool = False
	streaming_session_id: Optional[str] = None
	token_optimization: Optional[Dict[str, Any]] = None


# --- Merged and Refactored Classes ---


class CircuitBreaker:
	"""Circuit breaker for provider reliability."""

	def __init__(self, provider: str, failure_threshold: int = 5, timeout_duration: int = 60):
		self.provider = provider
		self.failure_threshold = failure_threshold
		self.timeout_duration = timeout_duration
		self.failure_count = 0
		self.last_failure_time = None
		self.state = "closed"  # closed, open, half-open

	def record_failure(self):
		self.failure_count += 1
		self.last_failure_time = datetime.now()
		if self.failure_count >= self.failure_threshold:
			self.state = "open"
			logger.warning(f"Circuit breaker opened for provider {self.provider}")

	def record_success(self):
		self.failure_count = 0
		self.state = "closed"

	def can_attempt(self) -> bool:
		if self.state == "closed":
			return True
		if self.state == "open":
			if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_duration):
				self.state = "half-open"
				return True
			return False
		return True


class ErrorClassifier:
	"""Classifies errors and determines appropriate handling strategies."""

	def __init__(self):
		self.classification_rules = {
			"authentication": {
				"keywords": ["unauthorized", "invalid api key", "authentication", "forbidden"],
				"status_codes": [401, 403],
				"category": ErrorCategory.AUTHENTICATION,
				"severity": ErrorSeverity.HIGH,
				"retry_config": RetryConfig.no_retry(),
			},
			"rate_limit": {
				"keywords": ["rate limit", "too many requests", "quota exceeded"],
				"status_codes": [429],
				"category": ErrorCategory.RATE_LIMIT,
				"severity": ErrorSeverity.MEDIUM,
				"retry_config": RetryConfig.exponential(max_attempts=5, base_delay=2.0, max_delay=120.0),
			},
			"model_not_found": {
				"keywords": ["model not found", "model does not exist", "invalid model"],
				"status_codes": [404],
				"category": ErrorCategory.MODEL_NOT_FOUND,
				"severity": ErrorSeverity.HIGH,
				"retry_config": RetryConfig.no_retry(),
			},
			"invalid_request": {
				"keywords": ["invalid request", "bad request", "validation error"],
				"status_codes": [400],
				"category": ErrorCategory.INVALID_REQUEST,
				"severity": ErrorSeverity.MEDIUM,
				"retry_config": RetryConfig.no_retry(),
			},
			"timeout": {
				"keywords": ["timeout", "timed out", "deadline exceeded"],
				"status_codes": [408, 504],
				"category": ErrorCategory.TIMEOUT,
				"severity": ErrorSeverity.MEDIUM,
				"retry_config": RetryConfig.exponential(max_attempts=3, base_delay=1.0, max_delay=30.0),
			},
			"connection": {
				"keywords": ["connection", "network", "unreachable", "dns"],
				"status_codes": [502, 503],
				"category": ErrorCategory.CONNECTION,
				"severity": ErrorSeverity.MEDIUM,
				"retry_config": RetryConfig.exponential(max_attempts=3, base_delay=2.0, max_delay=60.0),
			},
			"server_error": {
				"keywords": ["internal server error", "service unavailable"],
				"status_codes": [500, 502, 503, 504],
				"category": ErrorCategory.SERVER_ERROR,
				"severity": ErrorSeverity.HIGH,
				"retry_config": RetryConfig.exponential(max_attempts=3, base_delay=5.0, max_delay=120.0),
			},
		}

	def classify_error(self, exception: Exception, provider: str, context: Dict[str, Any] | None = None) -> ErrorInfo:
		error_message = str(exception).lower()
		status_code = getattr(exception, "status_code", None)
		for error_type, rules in self.classification_rules.items():
			if any(keyword in error_message for keyword in rules["keywords"]) or (status_code and status_code in rules["status_codes"]):
				return self._create_error_info(exception, provider, error_type, rules, context)
		return ErrorInfo(
			error_id=str(uuid.uuid4()),
			provider=provider,
			error_type="unknown",
			category=ErrorCategory.UNKNOWN,
			severity=ErrorSeverity.MEDIUM,
			message=str(exception),
			original_exception=exception,
			timestamp=datetime.now(),
			context=context or {},
		)

	def _create_error_info(
		self, exception: Exception, provider: str, error_type: str, rules: Dict[str, Any], context: Dict[str, Any] | None = None
	) -> ErrorInfo:
		return ErrorInfo(
			error_id=str(uuid.uuid4()),
			provider=provider,
			error_type=error_type,
			category=rules["category"],
			severity=rules["severity"],
			message=str(exception),
			original_exception=exception,
			timestamp=datetime.now(),
			context=context or {},
		)

	def get_retry_config(self, error_info: ErrorInfo) -> RetryConfig:
		for error_type, rules in self.classification_rules.items():
			if error_info.error_type == error_type:
				return rules["retry_config"]
		return RetryConfig.exponential(max_attempts=2, base_delay=1.0, max_delay=10.0)


class LLMService:
	"""
	Unified LLM Service for handling multiple AI providers with intelligent model selection,
	fallback, error handling, and performance monitoring.
	"""

	def __init__(self):
		self.models = self._initialize_models()
		self.error_classifier = ErrorClassifier()
		self.circuit_breakers = {provider.value: CircuitBreaker(provider.value) for provider in ModelProvider}
		self.fallback_chains = {
			ModelProvider.OPENAI.value: [ModelProvider.GROQ.value, ModelProvider.ANTHROPIC.value, ModelProvider.LOCAL.value],
			ModelProvider.ANTHROPIC.value: [ModelProvider.OPENAI.value, ModelProvider.GROQ.value, ModelProvider.LOCAL.value],
			ModelProvider.GROQ.value: [ModelProvider.OPENAI.value, ModelProvider.ANTHROPIC.value, ModelProvider.LOCAL.value],
			ModelProvider.LOCAL.value: [ModelProvider.OPENAI.value, ModelProvider.GROQ.value, ModelProvider.ANTHROPIC.value],
		}
		self.cache_ttl = 3600  # 1 hour

	def _initialize_models(self) -> Dict[ModelType, List[ModelConfig]]:
		models = {ModelType.CONTRACT_ANALYSIS: [], ModelType.NEGOTIATION: [], ModelType.COMMUNICATION: [], ModelType.GENERAL: []}
		# OpenAI models
		if hasattr(settings, "openai_api_key") and settings.openai_api_key:
			models[ModelType.CONTRACT_ANALYSIS].append(
				ModelConfig(
					provider=ModelProvider.OPENAI,
					model_name="gpt-4-turbo-preview",
					temperature=0.1,
					max_tokens=4000,
					cost_per_token=0.00001,
					capabilities=["analysis", "reasoning", "json", "long_context"],
					priority=1,
					complexity_level=TaskComplexity.COMPLEX,
					tokens_per_minute=15000,
					requests_per_minute=30,
				)
			)
			models[ModelType.GENERAL].append(
				ModelConfig(
					provider=ModelProvider.OPENAI,
					model_name="gpt-3.5-turbo",
					temperature=0.2,
					max_tokens=2000,
					cost_per_token=0.000002,
					capabilities=["generation", "reasoning"],
					priority=3,
					complexity_level=TaskComplexity.SIMPLE,
					tokens_per_minute=40000,
					requests_per_minute=60,
				)
			)
		# Anthropic models
		if hasattr(settings, "anthropic_api_key") and settings.anthropic_api_key:
			models[ModelType.CONTRACT_ANALYSIS].append(
				ModelConfig(
					provider=ModelProvider.ANTHROPIC,
					model_name="claude-3-opus-20240229",
					temperature=0.1,
					max_tokens=4000,
					cost_per_token=0.000075,
					capabilities=["analysis", "reasoning", "long_context"],
					priority=1,
					complexity_level=TaskComplexity.COMPLEX,
					tokens_per_minute=8000,
					requests_per_minute=15,
				)
			)
		# Groq models
		if hasattr(settings, "groq_api_key") and settings.groq_api_key:
			models[ModelType.COMMUNICATION].append(
				ModelConfig(
					provider=ModelProvider.GROQ,
					model_name="mixtral-8x7b-32768",
					temperature=0.3,
					max_tokens=2000,
					cost_per_token=0.0000002,
					capabilities=["generation", "speed"],
					priority=4,
					complexity_level=TaskComplexity.SIMPLE,
					tokens_per_minute=100000,
					requests_per_minute=200,
				)
			)
		return models

	async def analyze_with_fallback(
		self,
		model_type: ModelType,
		prompt: str,
		criteria: str = "cost",
		max_retries: int = 3,
		context: Optional[str] = None,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
		budget_limit: Optional[float] = None,
		enable_streaming: bool = False,
		streaming_mode: StreamingMode = StreamingMode.BUFFERED,
		token_budget: Optional[TokenBudget] = None,
		optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
	) -> Union[AIResponse, AsyncGenerator[StreamingChunk, None]]:
		task_info = await self._prepare_task_analysis(model_type, prompt, context)
		messages, task_complexity, cost_category = task_info["messages"], task_info["task_complexity"], task_info["cost_category"]

		messages, optimization_result = await self._handle_token_optimization(messages, token_budget, task_complexity)

		if not enable_streaming:
			cached_result = await self._check_cache(model_type, task_complexity, prompt)
			if cached_result:
				return cached_result

		models = await self._select_models(model_type, task_complexity, criteria)

		if enable_streaming:
			return self._handle_streaming_request(
				models, messages, model_type, task_complexity, cost_category, streaming_mode, user_id, session_id, budget_limit, optimization_result
			)

		cache_key = f"ai_response:{model_type.value}:{task_complexity.value}:{hash(prompt)}"
		return await self._handle_regular_request(
			models,
			messages,
			model_type,
			task_complexity,
			cost_category,
			max_retries,
			user_id,
			session_id,
			budget_limit,
			optimization_result,
			cache_key,
		)

	async def _prepare_task_analysis(self, model_type: ModelType, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
		task_complexity = complexity_analyzer.analyze_task_complexity(prompt=prompt, context=context, task_type=model_type.value)
		cost_category = self._map_model_type_to_cost_category(model_type)
		messages = [HumanMessage(content=prompt)]
		if context:
			messages.insert(0, SystemMessage(content=context))
		return {"task_complexity": task_complexity, "cost_category": cost_category, "messages": messages}

	async def _handle_token_optimization(self, messages: List[BaseMessage], token_budget: Optional[TokenBudget], task_complexity: TaskComplexity):
		if not token_budget:
			return messages, None
		optimized_messages, optimization_result = token_optimizer.optimize_for_budget(messages, token_budget, task_complexity)
		logger.info(f"Token optimization: {optimization_result.reduction_percentage:.1f}% reduction")
		return optimized_messages, optimization_result

	async def _check_cache(self, model_type: ModelType, task_complexity: TaskComplexity, prompt: str) -> Optional[AIResponse]:
		cache_key = f"ai_response:{model_type.value}:{task_complexity.value}:{hash(prompt)}"
		cached_response = await cache_service.aget(cache_key)
		if cached_response:
			logger.info("Returning cached AI response")
			return cached_response
		return None

	async def _select_models(self, model_type: ModelType, task_complexity: TaskComplexity, criteria: str) -> List[ModelConfig]:
		available_models = self.models.get(model_type, [])
		if not available_models:
			raise ValueError(f"No models available for {model_type.value}")
		suitable_models = self._filter_models_by_complexity(available_models, task_complexity)
		return self._sort_models_by_criteria(suitable_models, criteria, task_complexity)

	def _map_model_type_to_cost_category(self, model_type: ModelType) -> CostCategory:
		return getattr(CostCategory, model_type.name, CostCategory.GENERAL)

	def _filter_models_by_complexity(self, models: List[ModelConfig], task_complexity: TaskComplexity) -> List[ModelConfig]:
		# Map complexity levels to numeric values for comparison
		complexity_order = {TaskComplexity.SIMPLE: 1, TaskComplexity.MEDIUM: 2, TaskComplexity.COMPLEX: 3}

		task_level = complexity_order.get(task_complexity, 1)

		# A model can handle tasks at its level or below
		return [m for m in models if complexity_order.get(m.complexity_level, 1) >= task_level]

	def _sort_models_by_criteria(self, models: List[ModelConfig], criteria: str, task_complexity: TaskComplexity) -> List[ModelConfig]:
		if criteria == "cost":
			return sorted(models, key=lambda m: m.cost_per_token)
		elif criteria == "quality":
			return sorted(models, key=lambda m: m.priority)
		# Add other criteria as needed
		return sorted(models, key=lambda m: m.priority)

	async def _handle_regular_request(
		self,
		sorted_models,
		messages,
		model_type,
		task_complexity,
		cost_category,
		max_retries,
		user_id,
		session_id,
		budget_limit,
		optimization_result,
		cache_key,
	):
		last_error = None
		attempted_providers = set()

		for model_config in sorted_models:
			provider = model_config.provider.value
			if provider in attempted_providers:
				continue

			circuit_breaker = self.circuit_breakers[provider]
			if not circuit_breaker.can_attempt():
				logger.warning(f"Circuit breaker open for {provider}")
				continue

			for attempt in range(max_retries):
				try:
					# Simplified call for brevity
					response = await self._call_model_with_performance_tracking(
						model_config, messages, task_complexity, cost_category, user_id, session_id, {}, optimization_result
					)
					circuit_breaker.record_success()
					await cache_service.aset(cache_key, response, self.cache_ttl)
					return response
				except Exception as e:
					last_error = e
					error_info = self.error_classifier.classify_error(e, provider)
					logger.warning(f"Attempt {attempt + 1} for {provider} failed: {error_info.message}")

					retry_config = self.error_classifier.get_retry_config(error_info)
					if attempt < retry_config.max_attempts - 1:
						delay = retry_config.base_delay * (retry_config.exponential_base**attempt)
						await asyncio.sleep(delay)
					else:
						circuit_breaker.record_failure()
						break  # Move to next provider

			attempted_providers.add(provider)

		raise Exception(f"All AI models failed. Last error: {last_error}")

	async def _handle_streaming_request(
		self,
		sorted_models,
		messages,
		model_type,
		task_complexity,
		cost_category,
		streaming_mode,
		user_id,
		session_id,
		budget_limit,
		optimization_result,
	):
		# Simplified streaming logic for brevity
		for model_config in sorted_models:
			provider = model_config.provider.value
			circuit_breaker = self.circuit_breakers[provider]
			if not circuit_breaker.can_attempt():
				continue
			try:
				llm = await self._create_llm_instance(model_config)
				streaming_session = streaming_manager.create_streaming_session(
					provider=provider, model=model_config.model_name, operation=model_type.value, mode=streaming_mode
				)
				async for chunk in streaming_manager.stream_llm_response(llm, messages, streaming_session):
					yield chunk
				circuit_breaker.record_success()
				return
			except Exception as e:
				logger.error(f"Streaming failed for {model_config.model_name}: {e}")
				circuit_breaker.record_failure()
		raise Exception("All models failed for streaming request")

	async def _create_llm_instance(self, model_config: ModelConfig):
		"""Create LLM instance using the unified plugin architecture."""
		from ..core.service_integration import ServiceConfig
		from .llm_service_plugin import AnthropicServicePlugin, GroqServicePlugin, OllamaServicePlugin, OpenAIServicePlugin

		# Define plugin registry mapping providers to plugin classes
		plugin_registry = {
			ModelProvider.OPENAI: (OpenAIServicePlugin, "_openai_plugin"),
			ModelProvider.ANTHROPIC: (AnthropicServicePlugin, "_anthropic_plugin"),
			ModelProvider.GROQ: (GroqServicePlugin, "_groq_plugin"),
			ModelProvider.LOCAL: (OllamaServicePlugin, "_ollama_plugin"),
		}

		# Get plugin class and instance attribute name
		plugin_info = plugin_registry.get(model_config.provider)
		if not plugin_info:
			raise ValueError(f"No plugin available for provider: {model_config.provider}")

		plugin_class, plugin_attr = plugin_info

		# Check if plugin instance already exists
		if not hasattr(self, plugin_attr) or getattr(self, plugin_attr) is None:
			# Build plugin configuration
			plugin_config = self._build_plugin_config(model_config)
			config = ServiceConfig(service_id=model_config.provider.value, service_type="ai_provider", config=plugin_config)

			# Create and start plugin
			plugin = plugin_class(config)
			await plugin.start()
			setattr(self, plugin_attr, plugin)

		return getattr(self, plugin_attr)

	def _build_plugin_config(self, model_config: ModelConfig) -> dict:
		"""Build configuration dict for plugin initialization."""
		config = {
			"model_name": model_config.model_name,
			"temperature": model_config.temperature,
			"max_tokens": model_config.max_tokens,
		}

		# Add provider-specific API keys
		if model_config.provider == ModelProvider.OPENAI:
			config["api_key"] = settings.openai_api_key
		elif model_config.provider == ModelProvider.ANTHROPIC:
			config["api_key"] = settings.anthropic_api_key
		elif model_config.provider == ModelProvider.GROQ:
			config["api_key"] = settings.groq_api_key
		elif model_config.provider == ModelProvider.LOCAL:
			config["base_url"] = getattr(settings, "ollama_base_url", "http://localhost:11434")

		return config

	async def _call_model_with_performance_tracking(
		self, model_config, messages, task_complexity, cost_category, user_id, session_id, request_context, optimization_result
	):
		"""Call model with performance tracking using unified plugin architecture."""
		llm_plugin = await self._create_llm_instance(model_config)

		# Convert LangChain messages to dict format for plugins
		messages_dict = []
		for msg in messages:
			if hasattr(msg, "type") and hasattr(msg, "content"):
				messages_dict.append({"role": msg.type, "content": msg.content})
			else:
				messages_dict.append(msg)

		# Prepare kwargs for the plugin
		kwargs = {
			"temperature": model_config.temperature,
			"max_tokens": model_config.max_tokens,
		}

		# All providers now use plugin generate_completion method
		result = await llm_plugin.generate_completion(messages=messages_dict, model=model_config.model_name, **kwargs)

		token_usage = result.get("usage", {})
		cost = token_usage.get("total_tokens", 0) * model_config.cost_per_token
		confidence_score = self._calculate_confidence_from_content(result.get("content", ""), model_config)

		return AIResponse(
			content=result["content"],
			model_used=result.get("model", model_config.model_name),
			provider=model_config.provider.value,
			token_usage=token_usage,
			cost=cost,
			confidence_score=confidence_score,
			processing_time=result.get("response_time", 0),
			task_complexity=task_complexity,
			cost_category=cost_category,
			user_id=user_id,
			session_id=session_id,
			request_context=request_context,
			optimization_result=optimization_result,
		)

	def _extract_token_usage(self, response) -> Dict[str, int]:
		if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
			usage = response.response_metadata["token_usage"]
			return {
				"prompt_tokens": usage.get("prompt_tokens", 0),
				"completion_tokens": usage.get("completion_tokens", 0),
				"total_tokens": usage.get("total_tokens", 0),
			}
		return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

	def _calculate_confidence(self, response, model_config: ModelConfig) -> float:
		# Simplified confidence logic
		return 0.9 if "gpt-4" in model_config.model_name or "claude-3" in model_config.model_name else 0.75

	def _calculate_confidence_from_content(self, content: str, model_config: ModelConfig) -> float:
		"""Calculate confidence score from response content."""
		# Simplified confidence logic based on content length and model
		base_confidence = 0.9 if "gpt-4" in model_config.model_name or "claude-3" in model_config.model_name else 0.75

		# Adjust based on content length (longer responses might be more confident)
		content_length = len(content.strip())
		if content_length > 500:
			base_confidence += 0.05
		elif content_length < 50:
			base_confidence -= 0.1

		return min(1.0, max(0.1, base_confidence))

	def get_service_health(self) -> Dict[str, Dict[str, Any]]:
		"""
		Get health status of all AI service providers.
		Returns circuit breaker states and provider availability.
		"""
		health_status = {}

		for provider, circuit_breaker in self.circuit_breakers.items():
			health_status[provider] = {
				"state": circuit_breaker.state,
				"failure_count": circuit_breaker.failure_count,
				"last_failure_time": circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None,
				"available": circuit_breaker.can_attempt(),
			}

		return health_status

	async def generate_response(self, prompt: str, **kwargs) -> str:
		"""
		Compatibility method for legacy code that expects generate_response.
		Maps to the new analyze_with_fallback method.
		"""
		model_type = kwargs.get("model_type", ModelType.GENERAL)
		context = kwargs.get("context")
		user_id = kwargs.get("user_id")

		response = await self.analyze_with_fallback(model_type=model_type, prompt=prompt, context=context, user_id=user_id)

		return response.content


# Global instance
_llm_service = None


def get_llm_service() -> LLMService:
	"""Get global LLM service instance."""
	global _llm_service
	if _llm_service is None:
		_llm_service = LLMService()
	return _llm_service
