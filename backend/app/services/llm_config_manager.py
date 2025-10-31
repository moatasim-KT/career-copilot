"""
LLM Operations Manager
Manages configuration, caching, and benchmarking for multiple LLM providers.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.config import get_settings
from ..core.logging import get_logger
from .cache_service import get_cache_service


# Re-introducing necessary components from the old llm_manager
class LLMProvider(str, Enum):
	OPENAI = "openai"
	GROQ = "groq"
	OLLAMA = "ollama"


class TaskType(str, Enum):
	CONTRACT_ANALYSIS = "contract_analysis"
	RISK_ASSESSMENT = "risk_assessment"
	LEGAL_PRECEDENT = "legal_precedent"
	NEGOTIATION = "negotiation"
	COMMUNICATION = "communication"
	GENERAL = "general"


class RoutingCriteria(str, Enum):
	COST = "cost"
	PERFORMANCE = "performance"
	QUALITY = "quality"
	SPEED = "speed"
	AVAILABILITY = "availability"


logger = get_logger(__name__)
settings = get_settings()
cache_service = get_cache_service()

# --- Data Classes from all three files ---


@dataclass
class ProviderConfig:
	provider: LLMProvider
	model_name: str
	api_key: Optional[str] = None
	base_url: Optional[str] = None
	temperature: float = 0.1
	max_tokens: int = 4000
	cost_per_token: float = 0.0
	rate_limit_rpm: int = 60
	rate_limit_tpm: int = 40000
	timeout: int = 60
	priority: int = 1
	capabilities: List[str] = field(default_factory=list)
	enabled: bool = True
	metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMManagerConfig:
	providers: Dict[str, ProviderConfig]
	task_routing: Dict[TaskType, List[str]]
	default_routing_criteria: RoutingCriteria
	cache_ttl: int
	max_retries: int
	fallback_enabled: bool
	circuit_breaker_threshold: int
	circuit_breaker_timeout: int


@dataclass
class BenchmarkTest:
	test_id: str
	name: str
	description: str
	messages: List[Dict[str, str]]
	expected_keywords: List[str] = field(default_factory=list)
	max_tokens: int = 1000
	temperature: float = 0.1
	timeout: int = 60
	weight: float = 1.0


@dataclass
class BenchmarkResult:
	test_id: str
	provider: str
	model: str
	success: bool
	response_time: float
	tokens_used: int
	cost: float
	content: str
	error: Optional[str] = None
	quality_score: float = 0.0
	timestamp: datetime = field(default_factory=datetime.now)
	metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderBenchmark:
	provider: str
	model: str
	total_tests: int
	successful_tests: int
	failed_tests: int
	avg_response_time: float
	median_response_time: float
	p95_response_time: float
	total_tokens: int
	total_cost: float
	avg_quality_score: float
	overall_score: float
	test_results: List[BenchmarkResult]
	timestamp: datetime = field(default_factory=datetime.now)


# --- All Classes from the three files combined ---


class CacheEntry:
	"""Represents a cached LLM response."""

	def __init__(self, request_hash: str, response: Dict[str, Any], metadata: Dict[str, Any] | None = None):
		self.request_hash = request_hash
		self.response = response
		self.metadata = metadata or {}
		self.created_at = datetime.now()
		self.last_accessed = datetime.now()
		self.access_count = 1
		self.cache_id = str(uuid4())

	def update_access(self):
		"""Update access statistics."""
		self.last_accessed = datetime.now()
		self.access_count += 1

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for storage."""
		return {
			"request_hash": self.request_hash,
			"response": self.response,
			"metadata": self.metadata,
			"created_at": self.created_at.isoformat(),
			"last_accessed": self.last_accessed.isoformat(),
			"access_count": self.access_count,
			"cache_id": self.cache_id,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
		"""Create from dictionary."""
		entry = cls(request_hash=data["request_hash"], response=data["response"], metadata=data.get("metadata", {}))
		entry.created_at = datetime.fromisoformat(data["created_at"])
		entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
		entry.access_count = data["access_count"]
		entry.cache_id = data["cache_id"]
		return entry


class SemanticSimilarityMatcher:
	"""Matches semantically similar requests for cache hits."""

	def __init__(self, similarity_threshold: float = 0.85):
		self.similarity_threshold = similarity_threshold
		self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english", ngram_range=(1, 2), lowercase=True)
		self.request_vectors = {}
		self.request_texts = {}
		self.fitted = False

	def _extract_request_text(self, messages: List[Dict[str, str]]) -> str:
		"""Extract text content from messages for similarity comparison."""
		text_parts = []
		for msg in messages:
			if isinstance(msg, dict) and "content" in msg:
				text_parts.append(msg["content"])
			elif isinstance(msg, str):
				text_parts.append(msg)

		return " ".join(text_parts)

	def add_request(self, request_hash: str, messages: List[Dict[str, str]]):
		"""Add a request to the similarity matcher."""
		request_text = self._extract_request_text(messages)
		self.request_texts[request_hash] = request_text

		if len(self.request_texts) >= 2:
			self._refit_vectorizer()

	def _refit_vectorizer(self):
		"""Refit the vectorizer with current request texts."""
		try:
			texts = list(self.request_texts.values())
			if len(texts) < 2:
				return

			vectors = self.vectorizer.fit_transform(texts)

			for i, (request_hash, text) in enumerate(self.request_texts.items()):
				self.request_vectors[request_hash] = vectors[i]

			self.fitted = True

		except Exception as e:
			logger.warning(f"Failed to refit similarity vectorizer: {e}")
			self.fitted = False

	def find_similar_request(self, messages: List[Dict[str, str]]) -> Optional[Tuple[str, float]]:
		"""Find a similar cached request."""
		if not self.fitted or len(self.request_vectors) == 0:
			return None

		try:
			request_text = self._extract_request_text(messages)

			new_vector = self.vectorizer.transform([request_text])

			best_match = None
			best_similarity = 0.0

			for request_hash, cached_vector in self.request_vectors.items():
				similarity = cosine_similarity(new_vector, cached_vector)[0][0]

				if similarity > best_similarity and similarity >= self.similarity_threshold:
					best_similarity = similarity
					best_match = request_hash

			if best_match:
				logger.debug(f"Found similar request with similarity {best_similarity:.3f}")
				return best_match, best_similarity

			return None

		except Exception as e:
			logger.warning(f"Error in similarity matching: {e}")
			return None

	def remove_request(self, request_hash: str):
		"""Remove a request from the matcher."""
		if request_hash in self.request_texts:
			del self.request_texts[request_hash]

		if request_hash in self.request_vectors:
			del self.request_vectors[request_hash]

		if len(self.request_texts) >= 2:
			self._refit_vectorizer()
		else:
			self.fitted = False


class CacheOptimizer:
	"""Optimizes cache performance and manages cache lifecycle."""

	def __init__(self):
		self.cache_stats = {"hits": 0, "misses": 0, "semantic_hits": 0, "evictions": 0, "total_requests": 0}
		self.optimization_history = []

	def should_cache_response(self, response: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
		"""Determine if a response should be cached."""
		if "error" in response or response.get("success", True) is False:
			return False

		content = response.get("content", "")
		if len(content) < 50:
			return False

		temperature = metadata.get("temperature", 0.1)
		if temperature > 0.8:
			return False

		if metadata.get("stream", False):
			return False

		return True

	def calculate_cache_ttl(self, response: Dict[str, Any], metadata: Dict[str, Any]) -> int:
		"""Calculate appropriate TTL for a cache entry."""
		base_ttl = 3600

		task_type = metadata.get("task_type", "")
		if "analysis" in task_type.lower():
			base_ttl *= 4

		temperature = metadata.get("temperature", 0.1)
		if temperature <= 0.1:
			base_ttl *= 2
		elif temperature >= 0.5:
			base_ttl = int(base_ttl * 0.5)

		model = metadata.get("model", "")
		if "gpt-4" in model.lower():
			base_ttl *= 3

		content = response.get("content", "").lower()
		time_sensitive_keywords = ["today", "now", "current", "latest", "recent"]
		if any(keyword in content for keyword in time_sensitive_keywords):
			base_ttl = int(base_ttl * 0.3)

		return max(300, min(base_ttl, 24 * 3600))

	def should_evict_entry(self, entry: CacheEntry) -> bool:
		"""Determine if a cache entry should be evicted."""
		now = datetime.now()

		if now - entry.created_at > timedelta(days=7):
			return True

		if now - entry.last_accessed > timedelta(hours=24) and entry.access_count < 3:
			return True

		return False

	def optimize_cache(self, cache_entries: Dict[str, CacheEntry]) -> Dict[str, Any]:
		"""Optimize cache by removing stale entries and updating statistics."""
		optimization_start = time.time()

		initial_count = len(cache_entries)
		evicted_entries = []

		for request_hash, entry in list(cache_entries.items()):
			if self.should_evict_entry(entry):
				evicted_entries.append(request_hash)

		for request_hash in evicted_entries:
			del cache_entries[request_hash]

		evicted_count = len(evicted_entries)
		self.cache_stats["evictions"] += evicted_count

		optimization_time = time.time() - optimization_start

		optimization_result = {
			"initial_entries": initial_count,
			"evicted_entries": evicted_count,
			"remaining_entries": len(cache_entries),
			"optimization_time": optimization_time,
			"timestamp": datetime.now().isoformat(),
		}

		self.optimization_history.append(optimization_result)

		if len(self.optimization_history) > 100:
			self.optimization_history = self.optimization_history[-100:]

		logger.info(f"Cache optimization completed: evicted {evicted_count} entries in {optimization_time:.3f}s")

		return optimization_result

	def get_cache_statistics(self) -> Dict[str, Any]:
		"""Get comprehensive cache statistics."""
		total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
		hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
		semantic_hit_rate = (self.cache_stats["semantic_hits"] / total_requests * 100) if total_requests > 0 else 0

		return {
			"total_requests": total_requests,
			"cache_hits": self.cache_stats["hits"],
			"cache_misses": self.cache_stats["misses"],
			"semantic_hits": self.cache_stats["semantic_hits"],
			"hit_rate": hit_rate,
			"semantic_hit_rate": semantic_hit_rate,
			"evictions": self.cache_stats["evictions"],
			"recent_optimizations": len(self.optimization_history),
		}


class QualityEvaluator:
	"""Evaluates the quality of LLM responses."""

	def __init__(self):
		self.evaluation_criteria = {"relevance": 0.3, "completeness": 0.25, "accuracy": 0.25, "clarity": 0.2}

	def evaluate_response(self, response: str, test: BenchmarkTest) -> float:
		"""Evaluate response quality based on multiple criteria."""
		scores = {}

		scores["relevance"] = self._evaluate_relevance(response, test.expected_keywords)
		scores["completeness"] = self._evaluate_completeness(response, test)
		scores["accuracy"] = self._evaluate_accuracy(response, test)
		scores["clarity"] = self._evaluate_clarity(response)

		total_score = sum(scores[criterion] * weight for criterion, weight in self.evaluation_criteria.items())

		return min(max(total_score, 0.0), 1.0)

	def _evaluate_relevance(self, response: str, expected_keywords: List[str]) -> float:
		"""Evaluate relevance based on keyword presence."""
		if not expected_keywords:
			return 0.8

		response_lower = response.lower()
		found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)

		return found_keywords / len(expected_keywords)

	def _evaluate_completeness(self, response: str, test: BenchmarkTest) -> float:
		"""Evaluate completeness based on response characteristics."""
		word_count = len(response.split())
		sentence_count = response.count(".") + response.count("!") + response.count("?")

		length_score = min(word_count / 100, 1.0)
		structure_score = min(sentence_count / 3, 1.0)

		return (length_score + structure_score) / 2

	def _evaluate_accuracy(self, response: str, test: BenchmarkTest) -> float:
		"""Evaluate accuracy (placeholder for more sophisticated checks)."""
		response_lower = response.lower()

		error_indicators = ["i don't know", "i'm not sure", "cannot determine", "insufficient information"]
		has_errors = any(indicator in response_lower for indicator in error_indicators)

		if has_errors:
			return 0.3

		confident_indicators = ["analysis shows", "based on", "indicates", "demonstrates"]
		has_confidence = any(indicator in response_lower for indicator in confident_indicators)

		return 0.9 if has_confidence else 0.7

	def _evaluate_clarity(self, response: str) -> float:
		"""Evaluate clarity and readability."""
		sentences = response.split(".")
		avg_sentence_length = np.mean([len(sentence.split()) for sentence in sentences if sentence.strip()])

		if 10 <= avg_sentence_length <= 20:
			length_score = 1.0
		elif avg_sentence_length < 5:
			length_score = 0.5
		elif avg_sentence_length > 30:
			length_score = 0.6
		else:
			length_score = 0.8

		has_structure = "\n" in response or any(marker in response for marker in ["1.", "2.", "-", "*"])
		structure_score = 1.0 if has_structure else 0.7

		return (length_score + structure_score) / 2


class BenchmarkTestSuite:
	"""Collection of benchmark tests for different scenarios."""

	def __init__(self):
		self.test_suites = {
			"contract_analysis": self._create_contract_analysis_tests(),
			"general_reasoning": self._create_general_reasoning_tests(),
			"code_generation": self._create_code_generation_tests(),
			"creative_writing": self._create_creative_writing_tests(),
			"factual_qa": self._create_factual_qa_tests(),
		}

	def _create_contract_analysis_tests(self) -> List[BenchmarkTest]:
		"""Create job application tracking benchmark tests."""
		return [
			BenchmarkTest(
				test_id="contract_risk_analysis",
				name="Contract Risk Analysis",
				description="Analyze risks in a sample contract clause",
				messages=[
					{"role": "system", "content": "You are a contract analyst. Identify risks in contract clauses."},
					{
						"role": "user",
						"content": "Analyze the risks in this clause: 'The contractor shall indemnify and hold harmless the client from any and all claims, damages, or losses arising from the contractor's performance of this agreement.'",
					},
				],
				expected_keywords=["indemnification", "liability", "risk", "claims", "damages"],
				max_tokens=500,
				weight=1.5,
			),
			BenchmarkTest(
				test_id="contract_clause_generation",
				name="Contract Clause Generation",
				description="Generate a termination clause",
				messages=[
					{"role": "system", "content": "You are a legal expert. Generate professional contract clauses."},
					{"role": "user", "content": "Generate a termination clause that allows either party to terminate with 30 days notice."},
				],
				expected_keywords=["termination", "notice", "30 days", "either party"],
				max_tokens=300,
				weight=1.3,
			),
			BenchmarkTest(
				test_id="contract_compliance_check",
				name="Contract Compliance Check",
				description="Check contract compliance with regulations",
				messages=[
					{"role": "system", "content": "You are a compliance expert. Check contracts for regulatory compliance."},
					{"role": "user", "content": "What GDPR compliance considerations should be included in a data processing agreement?"},
				],
				expected_keywords=["GDPR", "data protection", "consent", "processing", "privacy"],
				max_tokens=600,
				weight=1.4,
			),
		]

	def _create_general_reasoning_tests(self) -> List[BenchmarkTest]:
		return [
			BenchmarkTest(
				test_id="logical_reasoning",
				name="Logical Reasoning",
				description="Solve a logical reasoning problem",
				messages=[
					{
						"role": "user",
						"content": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
					}
				],
				expected_keywords=["logical", "reasoning", "conclusion", "premise"],
				max_tokens=300,
				weight=1.0,
			),
			BenchmarkTest(
				test_id="problem_solving",
				name="Problem Solving",
				description="Solve a multi-step problem",
				messages=[
					{
						"role": "user",
						"content": "A company has 100 employees. 60% work in engineering, 25% in sales, and the rest in administration. If the company grows by 20% and maintains the same proportions, how many new employees will be hired for each department?",
					}
				],
				expected_keywords=["calculation", "proportion", "engineering", "sales", "administration"],
				max_tokens=400,
				weight=1.2,
			),
		]

	def _create_code_generation_tests(self) -> List[BenchmarkTest]:
		return [
			BenchmarkTest(
				test_id="python_function",
				name="Python Function Generation",
				description="Generate a Python function",
				messages=[{"role": "user", "content": "Write a Python function that calculates the factorial of a number using recursion."}],
				expected_keywords=["def", "factorial", "recursion", "return"],
				max_tokens=200,
				weight=1.0,
			),
			BenchmarkTest(
				test_id="algorithm_explanation",
				name="Algorithm Explanation",
				description="Explain a sorting algorithm",
				messages=[{"role": "user", "content": "Explain how the quicksort algorithm works and provide a simple implementation."}],
				expected_keywords=["quicksort", "pivot", "partition", "algorithm"],
				max_tokens=500,
				weight=1.1,
			),
		]

	def _create_creative_writing_tests(self) -> List[BenchmarkTest]:
		return [
			BenchmarkTest(
				test_id="story_writing",
				name="Short Story Writing",
				description="Write a creative short story",
				messages=[{"role": "user", "content": "Write a short story about a robot who discovers emotions."}],
				expected_keywords=["robot", "emotions", "story", "character"],
				max_tokens=400,
				temperature=0.7,
				weight=0.8,
			)
		]

	def _create_factual_qa_tests(self) -> List[BenchmarkTest]:
		return [
			BenchmarkTest(
				test_id="historical_facts",
				name="Historical Facts",
				description="Answer historical questions",
				messages=[{"role": "user", "content": "When did World War II end and what were the key events that led to its conclusion?"}],
				expected_keywords=["1945", "World War II", "surrender", "events"],
				max_tokens=300,
				weight=1.0,
			),
			BenchmarkTest(
				test_id="scientific_facts",
				name="Scientific Facts",
				description="Answer scientific questions",
				messages=[{"role": "user", "content": "Explain the process of photosynthesis and its importance to life on Earth."}],
				expected_keywords=["photosynthesis", "chlorophyll", "oxygen", "carbon dioxide"],
				max_tokens=400,
				weight=1.1,
			),
		]

	def get_test_suite(self, suite_name: str) -> List[BenchmarkTest]:
		return self.test_suites.get(suite_name, [])

	def get_all_tests(self) -> List[BenchmarkTest]:
		all_tests = []
		for tests in self.test_suites.values():
			all_tests.extend(tests)
		return all_tests

	def get_available_suites(self) -> List[str]:
		return list(self.test_suites.keys())


class LLMOperationsManager:
	def __init__(self, config_path: Optional[str] = None):
		# Config Manager part
		self.config_path = config_path or self._get_default_config_path()
		self.config: Optional[LLMManagerConfig] = None
		self._load_config()

		# Cache Manager part
		self.cache_entries = {}
		self.similarity_matcher = SemanticSimilarityMatcher()
		self.cache_optimizer = CacheOptimizer()
		self.enable_semantic_matching = True
		self.max_cache_entries = 10000
		self.optimization_interval = 3600
		self.last_optimization = time.time()
		self.request_count = 0

		# Benchmark Runner part
		self.benchmark_test_suite = BenchmarkTestSuite()
		self.quality_evaluator = QualityEvaluator()
		self.benchmark_history = []
		self.max_benchmark_history = 100

	# --- Config Manager Methods ---
	def _get_default_config_path(self) -> str:
		config_dir = Path("config")
		config_dir.mkdir(exist_ok=True)
		return str(config_dir / "llm_config.json")

	def _load_config(self):
		try:
			if os.path.exists(self.config_path):
				with open(self.config_path, "r") as f:
					config_data = json.load(f)
				self.config = self._parse_config_data(config_data)
			else:
				self.config = self._create_default_config()
				self._save_config()
		except Exception as e:
			logger.error(f"Failed to load LLM configuration: {e}")
			self.config = self._create_default_config()

	def _parse_config_data(self, config_data: Dict[str, Any]) -> LLMManagerConfig:
		"""Parse configuration data from JSON."""
		providers = {}
		for provider_id, provider_data in config_data.get("providers", {}).items():
			providers[provider_id] = ProviderConfig(
				provider=LLMProvider(provider_data["provider"]),
				model_name=provider_data["model_name"],
				api_key=provider_data.get("api_key"),
				base_url=provider_data.get("base_url"),
				temperature=provider_data.get("temperature", 0.1),
				max_tokens=provider_data.get("max_tokens", 4000),
				cost_per_token=provider_data.get("cost_per_token", 0.0),
				rate_limit_rpm=provider_data.get("rate_limit_rpm", 60),
				rate_limit_tpm=provider_data.get("rate_limit_tpm", 40000),
				timeout=provider_data.get("timeout", 60),
				priority=provider_data.get("priority", 1),
				capabilities=provider_data.get("capabilities", []),
				enabled=provider_data.get("enabled", True),
				metadata=provider_data.get("metadata", {}),
			)

		task_routing = {}
		for task_type_str, provider_list in config_data.get("task_routing", {}).items():
			task_routing[TaskType(task_type_str)] = provider_list

		return LLMManagerConfig(
			providers=providers,
			task_routing=task_routing,
			default_routing_criteria=RoutingCriteria(config_data.get("default_routing_criteria", "cost")),
			cache_ttl=config_data.get("cache_ttl", 3600),
			max_retries=config_data.get("max_retries", 3),
			fallback_enabled=config_data.get("fallback_enabled", True),
			circuit_breaker_threshold=config_data.get("circuit_breaker_threshold", 5),
			circuit_breaker_timeout=config_data.get("circuit_breaker_timeout", 60),
		)

	def _create_default_config(self) -> LLMManagerConfig:
		"""Create default configuration."""
		providers = {}

		if hasattr(settings, "openai_api_key") and settings.openai_api_key:
			providers["openai-gpt4"] = ProviderConfig(
				provider=LLMProvider.OPENAI,
				model_name="gpt-4",
				temperature=0.1,
				max_tokens=4000,
				cost_per_token=0.00003,
				rate_limit_rpm=60,
				rate_limit_tpm=40000,
				priority=1,
				capabilities=["analysis", "reasoning", "complex_tasks"],
				metadata={"quality": "high", "speed": "medium"},
			)

			providers["openai-gpt35"] = ProviderConfig(
				provider=LLMProvider.OPENAI,
				model_name="gpt-3.5-turbo",
				temperature=0.1,
				max_tokens=4000,
				cost_per_token=0.000002,
				rate_limit_rpm=3500,
				rate_limit_tpm=90000,
				priority=2,
				capabilities=["generation", "communication", "simple_analysis"],
				metadata={"quality": "medium", "speed": "fast"},
			)

		if hasattr(settings, "groq_api_key") and settings.groq_api_key:
			providers["groq-mixtral"] = ProviderConfig(
				provider=LLMProvider.GROQ,
				model_name="llama3-8b-8192",
				api_key=settings.groq_api_key.get_secret_value() if hasattr(settings.groq_api_key, "get_secret_value") else settings.groq_api_key,
				temperature=0.1,
				max_tokens=4000,
				cost_per_token=0.00000027,
				rate_limit_rpm=30,
				rate_limit_tpm=6000,
				priority=1,
				capabilities=["fast_analysis", "reasoning", "generation"],
				metadata={"quality": "high", "speed": "very_fast"},
			)

			providers["groq-llama2"] = ProviderConfig(
				provider=LLMProvider.GROQ,
				model_name="llama2-70b-4096",
				api_key=settings.groq_api_key.get_secret_value() if hasattr(settings.groq_api_key, "get_secret_value") else settings.groq_api_key,
				temperature=0.1,
				max_tokens=4000,
				cost_per_token=0.00000070,
				rate_limit_rpm=30,
				rate_limit_tpm=6000,
				priority=2,
				capabilities=["generation", "communication", "simple_analysis"],
				metadata={"quality": "medium", "speed": "fast"},
			)

		if getattr(settings, "ollama_enabled", False):
			providers["ollama-local"] = ProviderConfig(
				provider=LLMProvider.OLLAMA,
				model_name=getattr(settings, "ollama_model", "llama2"),
				base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"),
				temperature=0.1,
				max_tokens=4000,
				cost_per_token=0.0,
				rate_limit_rpm=60,
				rate_limit_tpm=10000,
				priority=3,
				capabilities=["local_processing", "privacy", "generation"],
				metadata={"quality": "medium", "speed": "medium", "cost": "free"},
			)

		task_routing = {
			TaskType.CONTRACT_ANALYSIS: ["openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"],
			TaskType.RISK_ASSESSMENT: ["openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"],
			TaskType.LEGAL_PRECEDENT: ["openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"],
			TaskType.NEGOTIATION: ["openai-gpt35", "groq-llama2", "openai-gpt4", "ollama-local"],
			TaskType.COMMUNICATION: ["openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"],
			TaskType.GENERAL: ["openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"],
		}

		return LLMManagerConfig(
			providers=providers,
			task_routing=task_routing,
			default_routing_criteria=RoutingCriteria.COST,
			cache_ttl=3600,
			max_retries=3,
			fallback_enabled=True,
			circuit_breaker_threshold=5,
			circuit_breaker_timeout=60,
		)

	def _save_config(self):
		"""Save configuration to file."""
		try:
			config_data = self._config_to_dict()

			os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

			with open(self.config_path, "w") as f:
				json.dump(config_data, f, indent=2)

			logger.info(f"Saved LLM configuration to {self.config_path}")

		except Exception as e:
			logger.error(f"Failed to save LLM configuration: {e}")

	def get_config(self) -> Optional[LLMManagerConfig]:
		return self.config

	# --- Cache Manager Methods ---
	def _generate_request_hash(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
		"""Generate a hash for the request."""
		request_data = {
			"messages": messages,
			"model": model,
			"temperature": kwargs.get("temperature", 0.1),
			"max_tokens": kwargs.get("max_tokens", 1000),
			"top_p": kwargs.get("top_p", 1.0),
		}

		request_str = json.dumps(request_data, sort_keys=True)
		return hashlib.sha256(request_str.encode()).hexdigest()

	async def get_cached_response(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Optional[Dict[str, Any]]:
		"""Get cached response for a request."""
		self.request_count += 1
		self.cache_optimizer.cache_stats["total_requests"] += 1

		request_hash = self._generate_request_hash(messages, model, **kwargs)

		if request_hash in self.cache_entries:
			entry = self.cache_entries[request_hash]
			entry.update_access()

			self.cache_optimizer.cache_stats["hits"] += 1

			logger.debug(f"Cache hit for request {request_hash[:8]}")

			return {**entry.response, "cached": True, "cache_type": "exact", "cache_id": entry.cache_id, "access_count": entry.access_count}

		if self.enable_semantic_matching:
			similar_match = self.similarity_matcher.find_similar_request(messages)

			if similar_match:
				similar_hash, similarity_score = similar_match

				if similar_hash in self.cache_entries:
					entry = self.cache_entries[similar_hash]
					entry.update_access()

					self.cache_optimizer.cache_stats["semantic_hits"] += 1

					logger.debug(f"Semantic cache hit for request {request_hash[:8]} (similarity: {similarity_score:.3f})")

					return {
						**entry.response,
						"cached": True,
						"cache_type": "semantic",
						"similarity_score": similarity_score,
						"cache_id": entry.cache_id,
						"access_count": entry.access_count,
					}

		self.cache_optimizer.cache_stats["misses"] += 1
		return None

	async def cache_response(self, messages: List[Dict[str, str]], model: str, response: Dict[str, Any], **kwargs) -> bool:
		"""Cache a response."""
		try:
			metadata = {
				"model": model,
				"temperature": kwargs.get("temperature", 0.1),
				"max_tokens": kwargs.get("max_tokens", 1000),
				"task_type": kwargs.get("task_type", ""),
				"stream": kwargs.get("stream", False),
			}

			if not self.cache_optimizer.should_cache_response(response, metadata):
				return False

			request_hash = self._generate_request_hash(messages, model, **kwargs)

			cache_entry = CacheEntry(request_hash, response, metadata)

			self.cache_entries[request_hash] = cache_entry

			if self.enable_semantic_matching:
				self.similarity_matcher.add_request(request_hash, messages)

			if len(self.cache_entries) > self.max_cache_entries:
				await self._evict_entries()

			if time.time() - self.last_optimization > self.optimization_interval:
				await self._optimize_cache()

			ttl = self.cache_optimizer.calculate_cache_ttl(response, metadata)
			cache_key = f"llm_cache:{request_hash}"

			await cache_service.aset(cache_key, cache_entry.to_dict(), ttl)

			logger.debug(f"Cached response for request {request_hash[:8]} (TTL: {ttl}s)")

			return True

		except Exception as e:
			logger.error(f"Failed to cache response: {e}")
			return False

	# --- Benchmark Runner Methods ---
	async def run_benchmark(
		self,
		provider_func: callable,
		provider_name: str,
		model: str,
		test_suite_name: Optional[str] = None,
		tests: Optional[List[BenchmarkTest]] = None,
		concurrent_requests: int = 1,
	) -> ProviderBenchmark:
		"""Run benchmark tests against a provider."""
		start_time = time.time()

		if tests:
			benchmark_tests = tests
		elif test_suite_name:
			benchmark_tests = self.benchmark_test_suite.get_test_suite(test_suite_name)
		else:
			benchmark_tests = self.benchmark_test_suite.get_all_tests()

		if not benchmark_tests:
			raise ValueError("No tests to run")

		logger.info(f"Starting benchmark for {provider_name}:{model} with {len(benchmark_tests)} tests")

		if concurrent_requests > 1:
			results = await self._run_concurrent_tests(provider_func, benchmark_tests, concurrent_requests)
		else:
			results = await self._run_sequential_tests(provider_func, benchmark_tests)

		benchmark_result = self._calculate_benchmark_metrics(provider_name, model, benchmark_tests, results)

		self.benchmark_history.append(benchmark_result)
		if len(self.benchmark_history) > self.max_benchmark_history:
			self.benchmark_history = self.benchmark_history[-self.max_benchmark_history :]

		total_time = time.time() - start_time
		logger.info(f"Benchmark completed in {total_time:.2f}s - Overall score: {benchmark_result.overall_score:.3f}")

		return benchmark_result


# Global instance
_llm_operations_manager = None


def get_llm_operations_manager() -> LLMOperationsManager:
	global _llm_operations_manager
	if _llm_operations_manager is None:
		_llm_operations_manager = LLMOperationsManager()
	return _llm_operations_manager
