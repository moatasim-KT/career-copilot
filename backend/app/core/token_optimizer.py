"""
Token usage optimization for AI services.
Implements intelligent token management, prompt optimization, and cost reduction strategies.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any

from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from .logging import get_logger
from .monitoring import get_performance_metrics_collector
from .task_complexity import TaskComplexity

logger = get_logger(__name__)


class OptimizationStrategy(Enum):
	"""Token optimization strategies."""

	AGGRESSIVE = "aggressive"  # Maximum token reduction
	BALANCED = "balanced"  # Balance between quality and efficiency
	CONSERVATIVE = "conservative"  # Minimal optimization, preserve quality
	ADAPTIVE = "adaptive"  # Adapt based on context and requirements


class CompressionTechnique(Enum):
	"""Text compression techniques for token optimization."""

	WHITESPACE_REMOVAL = "whitespace_removal"
	REDUNDANCY_ELIMINATION = "redundancy_elimination"
	ABBREVIATION = "abbreviation"
	SUMMARIZATION = "summarization"
	CONTEXT_PRUNING = "context_pruning"


@dataclass
class OptimizationResult:
	"""Result of token optimization."""

	original_tokens: int
	optimized_tokens: int
	reduction_percentage: float
	techniques_used: list[CompressionTechnique]
	quality_score: float  # Estimated quality retention (0-1)
	optimization_time: float
	metadata: dict[str, Any]


@dataclass
class TokenBudget:
	"""Token budget configuration."""

	max_prompt_tokens: int
	max_completion_tokens: int
	max_total_tokens: int
	reserved_tokens: int = 100  # Reserve tokens for system overhead
	emergency_threshold: float = 0.9  # Trigger aggressive optimization at 90% usage


class TokenOptimizer:
	"""Optimizes token usage for AI requests with multiple strategies."""

	def __init__(self):
		"""Initialize token optimizer."""
		self.performance_collector = get_performance_metrics_collector()
		self.optimization_cache: dict[str, OptimizationResult] = {}
		self.cache_ttl = 3600  # 1 hour cache TTL

		# Common abbreviations for technical content
		self.abbreviations = {
			"contract": "ctr",
			"agreement": "agr",
			"clause": "cl",
			"section": "sec",
			"paragraph": "para",
			"document": "doc",
			"analysis": "anal",
			"recommendation": "rec",
			"requirement": "req",
			"specification": "spec",
			"implementation": "impl",
			"configuration": "config",
			"application": "app",
			"development": "dev",
			"environment": "env",
			"performance": "perf",
			"optimization": "opt",
		}

		# Stop words for aggressive optimization
		self.stop_words = {
			"the",
			"a",
			"an",
			"and",
			"or",
			"but",
			"in",
			"on",
			"at",
			"to",
			"for",
			"of",
			"with",
			"by",
			"from",
			"up",
			"about",
			"into",
			"through",
			"during",
			"before",
			"after",
			"above",
			"below",
			"between",
			"among",
			"within",
		}

		logger.info("Token optimizer initialized")

	def estimate_tokens(self, text: str) -> int:
		"""Estimate token count for text (rough approximation)."""
		# Simple estimation: ~4 characters per token on average
		# More sophisticated tokenizers could be used for better accuracy
		return max(1, len(text) // 4)

	def optimize_messages(
		self,
		messages: list[BaseMessage],
		budget: TokenBudget,
		strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
		preserve_quality: bool = True,
	) -> Tuple[List[BaseMessage], OptimizationResult]:
		"""Optimize a list of messages for token efficiency."""
		start_time = time.time()

		# Calculate original token count
		original_text = " ".join([msg.content for msg in messages])
		original_tokens = self.estimate_tokens(original_text)

		# Check cache first
		cache_key = self._generate_cache_key(original_text, strategy, budget)
		cached_result = self._get_cached_optimization(cache_key)
		if cached_result:
			return messages, cached_result

		# Apply optimization based on strategy
		optimized_messages = []
		techniques_used = []

		for message in messages:
			optimized_content, msg_techniques = self._optimize_content(message.content, strategy, preserve_quality)
			techniques_used.extend(msg_techniques)

			# Create new message with optimized content
			if isinstance(message, HumanMessage):
				optimized_messages.append(HumanMessage(content=optimized_content))
			elif isinstance(message, SystemMessage):
				optimized_messages.append(SystemMessage(content=optimized_content))
			else:
				# Preserve original message type
				optimized_messages.append(type(message)(content=optimized_content))

		# Calculate optimization results
		optimized_text = " ".join([msg.content for msg in optimized_messages])
		optimized_tokens = self.estimate_tokens(optimized_text)

		reduction_percentage = ((original_tokens - optimized_tokens) / original_tokens * 100) if original_tokens > 0 else 0
		quality_score = self._estimate_quality_retention(original_text, optimized_text, techniques_used)

		optimization_time = time.time() - start_time

		result = OptimizationResult(
			original_tokens=original_tokens,
			optimized_tokens=optimized_tokens,
			reduction_percentage=reduction_percentage,
			techniques_used=list(set(techniques_used)),
			quality_score=quality_score,
			optimization_time=optimization_time,
			metadata={
				"strategy": strategy.value,
				"budget_max_tokens": budget.max_total_tokens,
				"budget_utilization": optimized_tokens / budget.max_total_tokens if budget.max_total_tokens > 0 else 0,
			},
		)

		# Cache the result
		self._cache_optimization(cache_key, result)

		logger.info(
			f"Token optimization: {original_tokens} -> {optimized_tokens} tokens "
			f"({reduction_percentage:.1f}% reduction) using {strategy.value} strategy"
		)

		return optimized_messages, result

	def _optimize_content(self, content: str, strategy: OptimizationStrategy, preserve_quality: bool) -> tuple[str, list[CompressionTechnique]]:
		"""Optimize content based on strategy."""
		techniques_used = []
		optimized = content

		# Apply optimizations based on strategy
		if strategy in [OptimizationStrategy.AGGRESSIVE, OptimizationStrategy.ADAPTIVE]:
			# Aggressive whitespace removal
			optimized = self._remove_excessive_whitespace(optimized)
			techniques_used.append(CompressionTechnique.WHITESPACE_REMOVAL)

			# Remove redundant phrases
			optimized = self._eliminate_redundancy(optimized)
			techniques_used.append(CompressionTechnique.REDUNDANCY_ELIMINATION)

			if not preserve_quality:
				# Apply abbreviations
				optimized = self._apply_abbreviations(optimized)
				techniques_used.append(CompressionTechnique.ABBREVIATION)

				# Remove stop words in non-critical contexts
				optimized = self._remove_stop_words(optimized)

		elif strategy == OptimizationStrategy.BALANCED:
			# Moderate optimizations
			optimized = self._remove_excessive_whitespace(optimized)
			techniques_used.append(CompressionTechnique.WHITESPACE_REMOVAL)

			optimized = self._eliminate_redundancy(optimized)
			techniques_used.append(CompressionTechnique.REDUNDANCY_ELIMINATION)

			# Light abbreviation for common terms
			optimized = self._apply_selective_abbreviations(optimized)
			techniques_used.append(CompressionTechnique.ABBREVIATION)

		elif strategy == OptimizationStrategy.CONSERVATIVE:
			# Minimal optimizations
			optimized = self._remove_excessive_whitespace(optimized)
			techniques_used.append(CompressionTechnique.WHITESPACE_REMOVAL)

		return optimized, techniques_used

	def _remove_excessive_whitespace(self, text: str) -> str:
		"""Remove excessive whitespace while preserving structure."""
		# Replace multiple spaces with single space
		text = re.sub(r" +", " ", text)

		# Replace multiple newlines with double newline (preserve paragraph breaks)
		text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

		# Remove trailing/leading whitespace from lines
		lines = [line.strip() for line in text.split("\n")]
		text = "\n".join(lines)

		return text.strip()

	def _eliminate_redundancy(self, text: str) -> str:
		"""Remove redundant phrases and repetitive content."""
		# Remove common redundant phrases
		redundant_patterns = [
			r"\b(please note that|it should be noted that|it is important to note that)\b",
			r"\b(as mentioned (above|before|previously))\b",
			r"\b(in other words|that is to say)\b",
			r"\b(furthermore|moreover|additionally)\s*,?\s*",
			r"\b(in conclusion|to conclude|in summary)\s*,?\s*",
		]

		for pattern in redundant_patterns:
			text = re.sub(pattern, "", text, flags=re.IGNORECASE)

		# Remove duplicate sentences (simple check)
		sentences = text.split(".")
		unique_sentences = []
		seen = set()

		for sentence in sentences:
			sentence = sentence.strip()
			if sentence and sentence.lower() not in seen:
				unique_sentences.append(sentence)
				seen.add(sentence.lower())

		return ". ".join(unique_sentences)

	def _apply_abbreviations(self, text: str) -> str:
		"""Apply abbreviations to reduce token count."""
		for full_word, abbrev in self.abbreviations.items():
			# Use word boundaries to avoid partial matches
			pattern = r"\b" + re.escape(full_word) + r"\b"
			text = re.sub(pattern, abbrev, text, flags=re.IGNORECASE)

		return text

	def _apply_selective_abbreviations(self, text: str) -> str:
		"""Apply only safe abbreviations that don't impact readability."""
		safe_abbreviations = {"document": "doc", "configuration": "config", "application": "app", "development": "dev", "environment": "env"}

		for full_word, abbrev in safe_abbreviations.items():
			pattern = r"\b" + re.escape(full_word) + r"\b"
			text = re.sub(pattern, abbrev, text, flags=re.IGNORECASE)

		return text

	def _remove_stop_words(self, text: str) -> str:
		"""Remove stop words from non-critical contexts."""
		words = text.split()
		filtered_words = []

		for i, word in enumerate(words):
			# Keep stop words at sentence beginnings and in quotes
			is_sentence_start = i == 0 or words[i - 1].endswith((".", "!", "?"))
			is_in_quotes = '"' in text[: text.find(word)] and text[: text.find(word)].count('"') % 2 == 1

			if word.lower() not in self.stop_words or is_sentence_start or is_in_quotes:
				filtered_words.append(word)

		return " ".join(filtered_words)

	def _estimate_quality_retention(self, original: str, optimized: str, techniques: list[CompressionTechnique]) -> float:
		"""Estimate quality retention after optimization."""
		base_quality = 1.0

		# Deduct quality based on techniques used
		quality_impact = {
			CompressionTechnique.WHITESPACE_REMOVAL: 0.0,  # No quality impact
			CompressionTechnique.REDUNDANCY_ELIMINATION: 0.05,  # Minimal impact
			CompressionTechnique.ABBREVIATION: 0.1,  # Some readability impact
			CompressionTechnique.SUMMARIZATION: 0.2,  # Moderate information loss
			CompressionTechnique.CONTEXT_PRUNING: 0.3,  # Significant information loss
		}

		for technique in techniques:
			base_quality -= quality_impact.get(technique, 0.1)

		# Adjust based on compression ratio
		compression_ratio = len(optimized) / len(original) if len(original) > 0 else 1.0
		if compression_ratio < 0.5:  # Very aggressive compression
			base_quality -= 0.2
		elif compression_ratio < 0.7:  # Moderate compression
			base_quality -= 0.1

		return max(0.0, min(1.0, base_quality))

	def optimize_for_budget(
		self, messages: list[BaseMessage], budget: TokenBudget, task_complexity: TaskComplexity = TaskComplexity.MEDIUM
	) -> tuple[list[BaseMessage], OptimizationResult]:
		"""Optimize messages to fit within token budget."""
		current_tokens = sum(self.estimate_tokens(msg.content) for msg in messages)

		# Check if optimization is needed
		if current_tokens <= budget.max_total_tokens - budget.reserved_tokens:
			# No optimization needed
			result = OptimizationResult(
				original_tokens=current_tokens,
				optimized_tokens=current_tokens,
				reduction_percentage=0.0,
				techniques_used=[],
				quality_score=1.0,
				optimization_time=0.0,
				metadata={"optimization_needed": False},
			)
			return messages, result

		# Determine optimization strategy based on budget pressure
		budget_utilization = current_tokens / budget.max_total_tokens

		if budget_utilization > budget.emergency_threshold:
			strategy = OptimizationStrategy.AGGRESSIVE
			preserve_quality = False
		elif budget_utilization > 0.8:
			strategy = OptimizationStrategy.BALANCED
			preserve_quality = True
		else:
			strategy = OptimizationStrategy.CONSERVATIVE
			preserve_quality = True

		# Adjust strategy based on task complexity
		if task_complexity == TaskComplexity.COMPLEX:
			# Be more conservative with complex tasks
			if strategy == OptimizationStrategy.AGGRESSIVE:
				strategy = OptimizationStrategy.BALANCED
			preserve_quality = True

		return self.optimize_messages(messages, budget, strategy, preserve_quality)

	def adaptive_optimization(
		self, messages: list[BaseMessage], budget: TokenBudget, performance_history: dict[str, Any] | None = None
	) -> tuple[list[BaseMessage], OptimizationResult]:
		"""Apply adaptive optimization based on performance history."""
		# Use performance history to inform optimization decisions
		if performance_history:
			avg_success_rate = performance_history.get("success_rate", 0.9)
			avg_quality_score = performance_history.get("quality_score", 0.8)

			# Adjust strategy based on historical performance
			if avg_success_rate > 0.95 and avg_quality_score > 0.9:
				# High performance, can be more aggressive
				strategy = OptimizationStrategy.BALANCED
			elif avg_success_rate < 0.8 or avg_quality_score < 0.7:
				# Poor performance, be more conservative
				strategy = OptimizationStrategy.CONSERVATIVE
			else:
				strategy = OptimizationStrategy.BALANCED
		else:
			strategy = OptimizationStrategy.BALANCED

		return self.optimize_messages(messages, budget, strategy, preserve_quality=True)

	def _generate_cache_key(self, text: str, strategy: OptimizationStrategy, budget: TokenBudget) -> str:
		"""Generate cache key for optimization result."""
		content_hash = hashlib.sha256(text.encode()).hexdigest()
		key_data = f"{content_hash}:{strategy.value}:{budget.max_total_tokens}"
		return hashlib.sha256(key_data.encode()).hexdigest()

	def _get_cached_optimization(self, cache_key: str) -> Optional[OptimizationResult]:
		"""Get cached optimization result if available and not expired."""
		if cache_key in self.optimization_cache:
			# Simple TTL check (in production, use proper cache with expiration)
			return self.optimization_cache[cache_key]
		return None

	def _cache_optimization(self, cache_key: str, result: OptimizationResult):
		"""Cache optimization result."""
		# Simple in-memory cache (in production, use Redis or similar)
		self.optimization_cache[cache_key] = result

		# Prevent cache from growing too large
		if len(self.optimization_cache) > 1000:
			# Remove oldest entries (simple FIFO)
			oldest_keys = list(self.optimization_cache.keys())[:100]
			for key in oldest_keys:
				del self.optimization_cache[key]

	def get_optimization_stats(self) -> dict[str, Any]:
		"""Get optimization statistics."""
		if not self.optimization_cache:
			return {"cache_size": 0, "total_optimizations": 0}

		results = list(self.optimization_cache.values())

		return {
			"cache_size": len(self.optimization_cache),
			"total_optimizations": len(results),
			"average_reduction": sum(r.reduction_percentage for r in results) / len(results),
			"average_quality_score": sum(r.quality_score for r in results) / len(results),
			"most_used_techniques": self._get_technique_frequency(results),
			"optimization_time_stats": {
				"average": sum(r.optimization_time for r in results) / len(results),
				"max": max(r.optimization_time for r in results),
				"min": min(r.optimization_time for r in results),
			},
		}

	def _get_technique_frequency(self, results: list[OptimizationResult]) -> dict[str, int]:
		"""Get frequency of optimization techniques used."""
		frequency = {}
		for result in results:
			for technique in result.techniques_used:
				frequency[technique.value] = frequency.get(technique.value, 0) + 1
		return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))

	def clear_cache(self):
		"""Clear optimization cache."""
		self.optimization_cache.clear()
		logger.info("Token optimization cache cleared")


# Global token optimizer instance
_token_optimizer = None


def get_token_optimizer() -> TokenOptimizer:
	"""Get the global token optimizer instance."""
	global _token_optimizer
	if _token_optimizer is None:
		_token_optimizer = TokenOptimizer()
	return _token_optimizer
