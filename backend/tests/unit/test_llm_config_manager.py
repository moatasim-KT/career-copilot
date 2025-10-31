"""
Unit tests for the consolidated LLM config manager functionality.
Tests configuration management, caching, and benchmarking capabilities.
"""

import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.llm_config_manager import (
	LLMOperationsManager,
	ProviderConfig,
	LLMManagerConfig,
	BenchmarkTest,
	CacheEntry,
	SemanticSimilarityMatcher,
	CacheOptimizer,
	QualityEvaluator,
	BenchmarkTestSuite,
	LLMProvider,
	TaskType,
	get_llm_operations_manager,
)


@pytest.fixture
def temp_config_file():
	"""Create a temporary config file for testing."""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
		config_data = {
			"providers": {
				"test-openai": {
					"provider": "openai",
					"model_name": "gpt-3.5-turbo",
					"temperature": 0.1,
					"max_tokens": 1000,
					"cost_per_token": 0.001,
					"enabled": True,
				}
			},
			"task_routing": {"general": ["test-openai"]},
			"default_routing_criteria": "cost",
			"cache_ttl": 3600,
			"max_retries": 3,
			"fallback_enabled": True,
			"circuit_breaker_threshold": 5,
			"circuit_breaker_timeout": 60,
		}
		json.dump(config_data, f)
		temp_path = f.name

	yield temp_path

	# Cleanup
	if os.path.exists(temp_path):
		os.unlink(temp_path)


@pytest.fixture
def mock_settings():
	"""Mock settings for testing."""
	settings = MagicMock()
	settings.openai_api_key = "test_openai_key"
	settings.groq_api_key = MagicMock()
	settings.groq_api_key.get_secret_value.return_value = "test_groq_key"
	settings.ollama_enabled = False
	return settings


@pytest.fixture
def llm_operations_manager(temp_config_file, mock_settings):
	"""Create LLM operations manager with mocked dependencies."""
	with (
		patch("app.services.llm_config_manager.get_settings", return_value=mock_settings),
		patch("app.services.llm_config_manager.get_cache_service") as mock_cache,
	):
		mock_cache_service = MagicMock()
		mock_cache_service.aget = AsyncMock(return_value=None)
		mock_cache_service.aset = AsyncMock(return_value=True)
		mock_cache.return_value = mock_cache_service

		manager = LLMOperationsManager(config_path=temp_config_file)
		return manager


class TestLLMOperationsManager:
	"""Test cases for LLM operations manager."""

	def test_initialization(self, llm_operations_manager):
		"""Test manager initialization."""
		assert llm_operations_manager.config is not None
		assert isinstance(llm_operations_manager.config, LLMManagerConfig)
		assert isinstance(llm_operations_manager.similarity_matcher, SemanticSimilarityMatcher)
		assert isinstance(llm_operations_manager.cache_optimizer, CacheOptimizer)
		assert isinstance(llm_operations_manager.benchmark_test_suite, BenchmarkTestSuite)
		assert isinstance(llm_operations_manager.quality_evaluator, QualityEvaluator)

	def test_config_loading(self, llm_operations_manager):
		"""Test configuration loading from file."""
		config = llm_operations_manager.get_config()

		assert config is not None
		assert "test-openai" in config.providers
		assert config.providers["test-openai"].provider == LLMProvider.OPENAI
		assert config.providers["test-openai"].model_name == "gpt-3.5-turbo"
		assert config.cache_ttl == 3600
		assert config.max_retries == 3

	def test_default_config_creation(self, mock_settings):
		"""Test default configuration creation."""
		with (
			patch("app.services.llm_config_manager.get_settings", return_value=mock_settings),
			patch("app.services.llm_config_manager.get_cache_service"),
		):
			# Create manager without existing config file
			manager = LLMOperationsManager(config_path="/nonexistent/path.json")

			assert manager.config is not None
			assert len(manager.config.providers) > 0
			assert TaskType.GENERAL in manager.config.task_routing

	@pytest.mark.asyncio
	async def test_cache_response_success(self, llm_operations_manager):
		"""Test successful response caching."""
		messages = [{"role": "user", "content": "Test message"}]
		model = "gpt-3.5-turbo"
		response = {"content": "This is a comprehensive test response that is long enough to be cached by the system", "success": True}

		result = await llm_operations_manager.cache_response(messages=messages, model=model, response=response, temperature=0.1)

		assert result is True
		assert len(llm_operations_manager.cache_entries) == 1

	@pytest.mark.asyncio
	async def test_cache_response_should_not_cache(self, llm_operations_manager):
		"""Test response that should not be cached."""
		messages = [{"role": "user", "content": "Test message"}]
		model = "gpt-3.5-turbo"
		response = {"content": "Error", "error": "Some error"}

		result = await llm_operations_manager.cache_response(messages=messages, model=model, response=response)

		assert result is False
		assert len(llm_operations_manager.cache_entries) == 0

	@pytest.mark.asyncio
	async def test_get_cached_response_exact_match(self, llm_operations_manager):
		"""Test exact cache hit."""
		messages = [{"role": "user", "content": "Test message"}]
		model = "gpt-3.5-turbo"
		response = {"content": "This is a comprehensive test response that is long enough to be cached by the system", "success": True}

		# Cache the response first
		await llm_operations_manager.cache_response(messages, model, response)

		# Try to get cached response
		cached = await llm_operations_manager.get_cached_response(messages, model)

		assert cached is not None
		assert cached["content"] == "This is a comprehensive test response that is long enough to be cached by the system"
		assert cached["cached"] is True
		assert cached["cache_type"] == "exact"

	@pytest.mark.asyncio
	async def test_get_cached_response_miss(self, llm_operations_manager):
		"""Test cache miss."""
		messages = [{"role": "user", "content": "Test message"}]
		model = "gpt-3.5-turbo"

		cached = await llm_operations_manager.get_cached_response(messages, model)

		assert cached is None


class TestProviderConfig:
	"""Test cases for provider configuration."""

	def test_provider_config_creation(self):
		"""Test provider configuration creation."""
		config = ProviderConfig(provider=LLMProvider.OPENAI, model_name="gpt-4", temperature=0.1, max_tokens=2000, cost_per_token=0.01)

		assert config.provider == LLMProvider.OPENAI
		assert config.model_name == "gpt-4"
		assert config.temperature == 0.1
		assert config.max_tokens == 2000
		assert config.cost_per_token == 0.01
		assert config.enabled is True  # Default value


class TestCacheEntry:
	"""Test cases for cache entry functionality."""

	def test_cache_entry_creation(self):
		"""Test cache entry creation."""
		response = {"content": "Test response"}
		metadata = {"model": "gpt-3.5-turbo"}

		entry = CacheEntry("test_hash", response, metadata)

		assert entry.request_hash == "test_hash"
		assert entry.response == response
		assert entry.metadata == metadata
		assert entry.access_count == 1
		assert isinstance(entry.created_at, datetime)

	def test_cache_entry_update_access(self):
		"""Test cache entry access update."""
		entry = CacheEntry("test_hash", {"content": "Test"})
		original_access_time = entry.last_accessed
		original_count = entry.access_count

		entry.update_access()

		assert entry.access_count == original_count + 1
		assert entry.last_accessed > original_access_time

	def test_cache_entry_serialization(self):
		"""Test cache entry to/from dict conversion."""
		response = {"content": "Test response"}
		metadata = {"model": "gpt-3.5-turbo"}

		entry = CacheEntry("test_hash", response, metadata)
		entry_dict = entry.to_dict()

		assert "request_hash" in entry_dict
		assert "response" in entry_dict
		assert "metadata" in entry_dict
		assert "created_at" in entry_dict

		# Test deserialization
		restored_entry = CacheEntry.from_dict(entry_dict)
		assert restored_entry.request_hash == entry.request_hash
		assert restored_entry.response == entry.response
		assert restored_entry.metadata == entry.metadata


class TestSemanticSimilarityMatcher:
	"""Test cases for semantic similarity matching."""

	def test_similarity_matcher_initialization(self):
		"""Test similarity matcher initialization."""
		matcher = SemanticSimilarityMatcher(similarity_threshold=0.8)

		assert matcher.similarity_threshold == 0.8
		assert matcher.fitted is False
		assert len(matcher.request_texts) == 0

	def test_extract_request_text(self):
		"""Test request text extraction."""
		matcher = SemanticSimilarityMatcher()
		messages = [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "What is the weather?"}]

		text = matcher._extract_request_text(messages)

		assert "helpful assistant" in text
		assert "weather" in text

	def test_add_request(self):
		"""Test adding requests to matcher."""
		matcher = SemanticSimilarityMatcher()
		messages = [{"role": "user", "content": "Test message"}]

		matcher.add_request("hash1", messages)

		assert "hash1" in matcher.request_texts
		assert matcher.request_texts["hash1"] == "Test message"

	def test_remove_request(self):
		"""Test removing requests from matcher."""
		matcher = SemanticSimilarityMatcher()
		messages = [{"role": "user", "content": "Test message"}]

		matcher.add_request("hash1", messages)
		matcher.remove_request("hash1")

		assert "hash1" not in matcher.request_texts


class TestCacheOptimizer:
	"""Test cases for cache optimizer."""

	def test_cache_optimizer_initialization(self):
		"""Test cache optimizer initialization."""
		optimizer = CacheOptimizer()

		assert optimizer.cache_stats["hits"] == 0
		assert optimizer.cache_stats["misses"] == 0
		assert len(optimizer.optimization_history) == 0

	def test_should_cache_response_valid(self):
		"""Test valid response caching decision."""
		optimizer = CacheOptimizer()
		response = {
			"content": "This is a comprehensive response that is definitely long enough to be cached by the system and meets all requirements",
			"success": True,
		}
		metadata = {"temperature": 0.1}

		should_cache = optimizer.should_cache_response(response, metadata)

		assert should_cache is True

	def test_should_cache_response_invalid(self):
		"""Test invalid response caching decision."""
		optimizer = CacheOptimizer()

		# Test error response
		error_response = {"content": "Error", "error": "Some error"}
		assert optimizer.should_cache_response(error_response, {}) is False

		# Test short response
		short_response = {"content": "Hi"}
		assert optimizer.should_cache_response(short_response, {}) is False

		# Test high temperature
		high_temp_response = {"content": "Long enough response"}
		high_temp_metadata = {"temperature": 0.9}
		assert optimizer.should_cache_response(high_temp_response, high_temp_metadata) is False

	def test_calculate_cache_ttl(self):
		"""Test cache TTL calculation."""
		optimizer = CacheOptimizer()
		response = {"content": "Analysis shows that this is important"}
		metadata = {"task_type": "analysis", "temperature": 0.1, "model": "gpt-4"}

		ttl = optimizer.calculate_cache_ttl(response, metadata)

		assert ttl > 3600  # Should be longer than base TTL due to analysis task and low temperature

	def test_should_evict_entry_old(self):
		"""Test eviction decision for old entries."""
		optimizer = CacheOptimizer()

		# Create old entry
		entry = CacheEntry("test_hash", {"content": "Test"})
		entry.created_at = datetime.now() - timedelta(days=8)
		entry.last_accessed = datetime.now() - timedelta(days=8)

		should_evict = optimizer.should_evict_entry(entry)

		assert should_evict is True

	def test_should_evict_entry_recent(self):
		"""Test eviction decision for recent entries."""
		optimizer = CacheOptimizer()

		# Create recent entry
		entry = CacheEntry("test_hash", {"content": "Test"})
		entry.access_count = 5

		should_evict = optimizer.should_evict_entry(entry)

		assert should_evict is False


class TestQualityEvaluator:
	"""Test cases for quality evaluator."""

	def test_quality_evaluator_initialization(self):
		"""Test quality evaluator initialization."""
		evaluator = QualityEvaluator()

		assert "relevance" in evaluator.evaluation_criteria
		assert "completeness" in evaluator.evaluation_criteria
		assert "accuracy" in evaluator.evaluation_criteria
		assert "clarity" in evaluator.evaluation_criteria

	def test_evaluate_relevance(self):
		"""Test relevance evaluation."""
		evaluator = QualityEvaluator()
		response = "This contract contains important clauses about liability and indemnification"
		keywords = ["contract", "liability", "indemnification"]

		relevance_score = evaluator._evaluate_relevance(response, keywords)

		assert relevance_score == 1.0  # All keywords found

	def test_evaluate_relevance_partial(self):
		"""Test partial relevance evaluation."""
		evaluator = QualityEvaluator()
		response = "This contract contains important clauses"
		keywords = ["contract", "liability", "indemnification"]

		relevance_score = evaluator._evaluate_relevance(response, keywords)

		assert relevance_score == 1 / 3  # Only one keyword found

	def test_evaluate_completeness(self):
		"""Test completeness evaluation."""
		evaluator = QualityEvaluator()
		test = BenchmarkTest("test", "Test", "Description", [])

		# Long, well-structured response
		long_response = "This is a comprehensive analysis. " * 20 + "It covers multiple aspects. " * 10
		completeness_score = evaluator._evaluate_completeness(long_response, test)

		assert completeness_score > 0.5

	def test_evaluate_accuracy(self):
		"""Test accuracy evaluation."""
		evaluator = QualityEvaluator()
		test = BenchmarkTest("test", "Test", "Description", [])

		# Confident response
		confident_response = "Analysis shows that this demonstrates clear patterns"
		accuracy_score = evaluator._evaluate_accuracy(confident_response, test)

		assert accuracy_score == 0.9

		# Uncertain response
		uncertain_response = "I don't know the answer to this question"
		accuracy_score = evaluator._evaluate_accuracy(uncertain_response, test)

		assert accuracy_score == 0.3

	def test_evaluate_response_overall(self):
		"""Test overall response evaluation."""
		evaluator = QualityEvaluator()
		test = BenchmarkTest("test", "Test", "Description", [], expected_keywords=["analysis", "important"])

		response = "This analysis shows important findings. " * 10

		score = evaluator.evaluate_response(response, test)

		assert 0.0 <= score <= 1.0
		assert score > 0.5  # Should be a decent score


class TestBenchmarkTestSuite:
	"""Test cases for benchmark test suite."""

	def test_benchmark_test_suite_initialization(self):
		"""Test benchmark test suite initialization."""
		suite = BenchmarkTestSuite()

		assert "contract_analysis" in suite.test_suites
		assert "general_reasoning" in suite.test_suites
		assert "code_generation" in suite.test_suites
		assert "creative_writing" in suite.test_suites
		assert "factual_qa" in suite.test_suites

	def test_get_test_suite(self):
		"""Test getting specific test suite."""
		suite = BenchmarkTestSuite()

		contract_tests = suite.get_test_suite("contract_analysis")

		assert len(contract_tests) > 0
		assert all(isinstance(test, BenchmarkTest) for test in contract_tests)

	def test_get_all_tests(self):
		"""Test getting all tests."""
		suite = BenchmarkTestSuite()

		all_tests = suite.get_all_tests()

		assert len(all_tests) > 0
		assert all(isinstance(test, BenchmarkTest) for test in all_tests)

	def test_get_available_suites(self):
		"""Test getting available test suites."""
		suite = BenchmarkTestSuite()

		available_suites = suite.get_available_suites()

		assert "contract_analysis" in available_suites
		assert "general_reasoning" in available_suites
		assert len(available_suites) == 5


def test_get_llm_operations_manager_singleton():
	"""Test global LLM operations manager singleton."""
	with patch("app.services.llm_config_manager.get_settings"), patch("app.services.llm_config_manager.get_cache_service"):
		manager1 = get_llm_operations_manager()
		manager2 = get_llm_operations_manager()

		assert manager1 is manager2  # Should be the same instance
