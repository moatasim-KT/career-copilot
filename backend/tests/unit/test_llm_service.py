"""
Unit tests for the consolidated LLM service functionality.
Tests core LLM service operations, error handling, and model selection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_service import (
	LLMService,
	ModelType,
	ModelProvider,
	ModelConfig,
	AIResponse,
	ErrorClassifier,
	CircuitBreaker,
	ErrorCategory,
	ErrorSeverity,
	get_llm_service,
)
from app.core.task_complexity import TaskComplexity
from app.core.cost_tracker import CostCategory


@pytest.fixture
def mock_settings():
	"""Mock settings for testing."""
	settings = MagicMock()
	settings.openai_api_key = MagicMock()
	settings.openai_api_key.get_secret_value.return_value = "test_openai_key"
	settings.anthropic_api_key = "test_anthropic_key"
	settings.groq_api_key = MagicMock()
	settings.groq_api_key.get_secret_value.return_value = "test_groq_key"
	return settings


@pytest.fixture
def mock_dependencies():
	"""Mock all external dependencies."""
	with (
		patch("app.services.llm_service.get_settings") as mock_get_settings,
		patch("app.services.llm_service.get_cache_service") as mock_cache,
		patch("app.services.llm_service.get_complexity_analyzer") as mock_complexity,
		patch("app.services.llm_service.get_cost_tracker") as mock_cost,
		patch("app.services.llm_service.get_metrics_collector") as mock_metrics,
		patch("app.services.llm_service.get_performance_metrics_collector") as mock_perf,
		patch("app.services.llm_service.get_streaming_manager") as mock_stream,
		patch("app.services.llm_service.get_token_optimizer") as mock_token,
	):
		# Configure mock settings
		mock_settings = MagicMock()
		mock_settings.openai_api_key = MagicMock()
		mock_settings.openai_api_key.get_secret_value.return_value = "test_openai_key"
		mock_settings.anthropic_api_key = "test_anthropic_key"
		mock_settings.groq_api_key = MagicMock()
		mock_settings.groq_api_key.get_secret_value.return_value = "test_groq_key"
		mock_settings.enable_redis_caching = False  # Disable Redis
		mock_get_settings.return_value = mock_settings

		# Configure mock cache - completely disable it
		mock_cache_instance = MagicMock()
		mock_cache_instance.aget = AsyncMock(return_value=None)
		mock_cache_instance.aset = AsyncMock(return_value=True)
		mock_cache_instance.enabled = False  # Disable Redis to avoid connection issues
		mock_cache.return_value = mock_cache_instance

		# Configure mock complexity analyzer
		mock_complexity_instance = MagicMock()
		mock_complexity_instance.analyze_task_complexity.return_value = TaskComplexity.SIMPLE
		mock_complexity.return_value = mock_complexity_instance

		# Configure other mocks
		mock_cost.return_value = MagicMock()
		mock_metrics.return_value = MagicMock()
		mock_perf.return_value = MagicMock()
		mock_stream.return_value = MagicMock()
		mock_token.return_value = MagicMock()

		yield {
			"settings": mock_settings,
			"cache": mock_cache_instance,
			"complexity": mock_complexity_instance,
			"cost": mock_cost.return_value,
			"metrics": mock_metrics.return_value,
			"performance": mock_perf.return_value,
			"streaming": mock_stream.return_value,
			"token": mock_token.return_value,
		}


@pytest.fixture
def llm_service(mock_dependencies):
	"""Create LLM service instance with mocked dependencies."""
	service = LLMService()

	# Mock the LLM creation method
	mock_llm = MagicMock()
	mock_response = MagicMock()
	mock_response.content = "Test response"
	mock_response.response_metadata = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}
	mock_llm.ainvoke = AsyncMock(return_value=mock_response)
	service._create_llm_instance = AsyncMock(return_value=mock_llm)

	return service


class TestLLMService:
	"""Test cases for LLM service core functionality."""

	def test_initialization(self, llm_service):
		"""Test LLM service initialization."""
		assert llm_service is not None
		assert isinstance(llm_service.models, dict)
		assert isinstance(llm_service.error_classifier, ErrorClassifier)
		assert isinstance(llm_service.circuit_breakers, dict)
		assert len(llm_service.circuit_breakers) == len(ModelProvider)

	def test_model_initialization(self, llm_service):
		"""Test model configuration initialization."""
		# Check that models are properly categorized
		assert ModelType.CONTRACT_ANALYSIS in llm_service.models
		assert ModelType.GENERAL in llm_service.models

		# Check that models have proper configuration
		for model_type, configs in llm_service.models.items():
			for config in configs:
				assert isinstance(config, ModelConfig)
				assert config.provider in ModelProvider
				assert config.cost_per_token >= 0
				assert config.max_tokens > 0

	@pytest.mark.asyncio
	async def test_analyze_with_fallback_success(self, llm_service):
		"""Test successful analysis with fallback."""
		result = await llm_service.analyze_with_fallback(model_type=ModelType.GENERAL, prompt="Test prompt")

		assert isinstance(result, AIResponse)
		assert result.content == "Test response"
		assert result.token_usage["total_tokens"] == 30
		assert result.processing_time >= 0

	@pytest.mark.asyncio
	async def test_analyze_with_fallback_with_context(self, llm_service):
		"""Test analysis with context."""
		# Mock the cache check to return None (no cached result)
		with patch.object(llm_service, "_check_cache", return_value=None):
			result = await llm_service.analyze_with_fallback(
				model_type=ModelType.CONTRACT_ANALYSIS, prompt="Analyze this contract", context="You are a legal expert"
			)

			assert isinstance(result, AIResponse)
			assert result.content == "Test response"

	@pytest.mark.skip(reason="Redis connection issues in test environment")
	@pytest.mark.asyncio
	async def test_analyze_with_fallback_cached_response(self, llm_service, mock_dependencies):
		"""Test cached response handling."""
		# Mock cached response
		cached_response = AIResponse(
			content="Cached response",
			model_used="gpt-3.5-turbo",
			provider=ModelProvider.OPENAI,
			confidence_score=0.9,
			processing_time=0.1,
			token_usage={"total_tokens": 25},
			cost=0.005,
			complexity_used=TaskComplexity.SIMPLE,
			cost_category=CostCategory.GENERAL,
			budget_impact={},
			metadata={},
		)

		# Mock the cache to return the cached response
		with patch.object(llm_service, "_check_cache", return_value=cached_response):
			result = await llm_service.analyze_with_fallback(model_type=ModelType.GENERAL, prompt="Test prompt")

			assert result.content == "Cached response"

	@pytest.mark.asyncio
	async def test_analyze_with_fallback_no_models(self, llm_service):
		"""Test behavior when no models are available."""
		# Clear models for a specific type
		llm_service.models[ModelType.GENERAL] = []

		# Mock the cache check to return None (no cached result)
		with patch.object(llm_service, "_check_cache", return_value=None):
			with pytest.raises(ValueError, match="No models available"):
				await llm_service.analyze_with_fallback(model_type=ModelType.GENERAL, prompt="Test prompt")

	@pytest.mark.asyncio
	async def test_generate_response_compatibility(self, llm_service):
		"""Test legacy generate_response method."""
		# Mock analyze_with_fallback to return an AIResponse
		mock_response = AIResponse(
			content="Test response",
			model_used="gpt-3.5-turbo",
			provider=ModelProvider.OPENAI,
			confidence_score=0.9,
			processing_time=0.1,
			token_usage={"total_tokens": 30},
			cost=0.005,
			complexity_used=TaskComplexity.SIMPLE,
			cost_category=CostCategory.GENERAL,
			budget_impact={},
			metadata={},
		)

		with patch.object(llm_service, "analyze_with_fallback", return_value=mock_response):
			result = await llm_service.generate_response("Test prompt")

			assert isinstance(result, str)
			assert result == "Test response"

	def test_get_service_health(self, llm_service):
		"""Test service health status."""
		health = llm_service.get_service_health()

		assert isinstance(health, dict)
		assert len(health) == len(ModelProvider)

		for provider, status in health.items():
			assert "state" in status
			assert "failure_count" in status
			assert "available" in status
			assert isinstance(status["available"], bool)


class TestErrorClassifier:
	"""Test cases for error classification."""

	def test_classify_rate_limit_error(self):
		"""Test rate limit error classification."""
		classifier = ErrorClassifier()
		exception = Exception("Rate limit exceeded")

		error_info = classifier.classify_error(exception, "openai")

		assert error_info.category == ErrorCategory.RATE_LIMIT
		assert error_info.severity == ErrorSeverity.MEDIUM
		assert error_info.provider == "openai"

	def test_classify_authentication_error(self):
		"""Test authentication error classification."""
		classifier = ErrorClassifier()
		exception = Exception("Invalid API key")

		error_info = classifier.classify_error(exception, "anthropic")

		assert error_info.category == ErrorCategory.AUTHENTICATION
		assert error_info.severity == ErrorSeverity.HIGH
		assert error_info.provider == "anthropic"

	def test_classify_unknown_error(self):
		"""Test unknown error classification."""
		classifier = ErrorClassifier()
		exception = Exception("Some random error")

		error_info = classifier.classify_error(exception, "groq")

		assert error_info.category == ErrorCategory.UNKNOWN
		assert error_info.severity == ErrorSeverity.MEDIUM
		assert error_info.provider == "groq"

	def test_get_retry_config(self):
		"""Test retry configuration retrieval."""
		classifier = ErrorClassifier()

		# Test rate limit retry config
		exception = Exception("Rate limit exceeded")
		error_info = classifier.classify_error(exception, "openai")
		retry_config = classifier.get_retry_config(error_info)

		assert retry_config.max_attempts == 5
		assert retry_config.base_delay == 2.0

		# Test authentication no-retry config
		auth_exception = Exception("Invalid API key")
		auth_error_info = classifier.classify_error(auth_exception, "openai")
		auth_retry_config = classifier.get_retry_config(auth_error_info)

		assert auth_retry_config.max_attempts == 1


class TestCircuitBreaker:
	"""Test cases for circuit breaker functionality."""

	def test_circuit_breaker_initialization(self):
		"""Test circuit breaker initialization."""
		cb = CircuitBreaker("test_provider")

		assert cb.provider == "test_provider"
		assert cb.failure_count == 0
		assert cb.state == "closed"
		assert cb.can_attempt() is True

	def test_circuit_breaker_failure_recording(self):
		"""Test failure recording and state changes."""
		cb = CircuitBreaker("test_provider", failure_threshold=2)

		# First failure
		cb.record_failure()
		assert cb.failure_count == 1
		assert cb.state == "closed"
		assert cb.can_attempt() is True

		# Second failure - should open circuit
		cb.record_failure()
		assert cb.failure_count == 2
		assert cb.state == "open"
		assert cb.can_attempt() is False

	def test_circuit_breaker_success_recovery(self):
		"""Test success recording and recovery."""
		cb = CircuitBreaker("test_provider", failure_threshold=2)

		# Trigger failures
		cb.record_failure()
		cb.record_failure()
		assert cb.state == "open"

		# Record success
		cb.record_success()
		assert cb.failure_count == 0
		assert cb.state == "closed"
		assert cb.can_attempt() is True

	def test_circuit_breaker_timeout_recovery(self):
		"""Test timeout-based recovery."""
		cb = CircuitBreaker("test_provider", failure_threshold=1, timeout_duration=1)

		# Trigger failure
		cb.record_failure()
		assert cb.state == "open"
		assert cb.can_attempt() is False

		# Simulate timeout passage
		import time

		time.sleep(1.1)

		# Should allow attempt (half-open state)
		assert cb.can_attempt() is True


class TestModelSelection:
	"""Test cases for model selection logic."""

	def test_filter_models_by_complexity(self, llm_service):
		"""Test model filtering by complexity."""
		# Create test models with different complexity levels
		simple_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-3.5-turbo",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.001,
			capabilities=[],
			priority=1,
			complexity_level=TaskComplexity.SIMPLE,
		)

		complex_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-4",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.01,
			capabilities=[],
			priority=1,
			complexity_level=TaskComplexity.COMPLEX,
		)

		models = [simple_model, complex_model]

		# Filter for simple tasks
		simple_filtered = llm_service._filter_models_by_complexity(models, TaskComplexity.SIMPLE)
		assert len(simple_filtered) == 2  # Both models can handle simple tasks

		# Filter for complex tasks
		complex_filtered = llm_service._filter_models_by_complexity(models, TaskComplexity.COMPLEX)
		assert len(complex_filtered) == 1  # Only complex model can handle complex tasks
		assert complex_filtered[0].model_name == "gpt-4"

	def test_sort_models_by_cost(self, llm_service):
		"""Test model sorting by cost criteria."""
		expensive_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-4",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.01,
			capabilities=[],
			priority=1,
			complexity_level=TaskComplexity.SIMPLE,
		)

		cheap_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-3.5-turbo",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.001,
			capabilities=[],
			priority=2,
			complexity_level=TaskComplexity.SIMPLE,
		)

		models = [expensive_model, cheap_model]

		# Sort by cost
		sorted_models = llm_service._sort_models_by_criteria(models, "cost", TaskComplexity.SIMPLE)
		assert sorted_models[0].model_name == "gpt-3.5-turbo"  # Cheaper model first
		assert sorted_models[1].model_name == "gpt-4"

	def test_sort_models_by_quality(self, llm_service):
		"""Test model sorting by quality criteria."""
		high_priority_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-4",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.01,
			capabilities=[],
			priority=1,  # Higher quality (lower priority number)
			complexity_level=TaskComplexity.SIMPLE,
		)

		low_priority_model = ModelConfig(
			provider=ModelProvider.OPENAI,
			model_name="gpt-3.5-turbo",
			temperature=0.1,
			max_tokens=1000,
			cost_per_token=0.001,
			capabilities=[],
			priority=2,  # Lower quality (higher priority number)
			complexity_level=TaskComplexity.SIMPLE,
		)

		models = [low_priority_model, high_priority_model]

		# Sort by quality
		sorted_models = llm_service._sort_models_by_criteria(models, "quality", TaskComplexity.SIMPLE)
		assert sorted_models[0].model_name == "gpt-4"  # Higher quality model first
		assert sorted_models[1].model_name == "gpt-3.5-turbo"


def test_get_llm_service_singleton():
	"""Test global LLM service singleton."""
	with (
		patch("app.services.llm_service.get_settings"),
		patch("app.services.llm_service.get_cache_service"),
		patch("app.services.llm_service.get_complexity_analyzer"),
		patch("app.services.llm_service.get_cost_tracker"),
		patch("app.services.llm_service.get_metrics_collector"),
		patch("app.services.llm_service.get_performance_metrics_collector"),
		patch("app.services.llm_service.get_streaming_manager"),
		patch("app.services.llm_service.get_token_optimizer"),
	):
		service1 = get_llm_service()
		service2 = get_llm_service()

		assert service1 is service2  # Should be the same instance
