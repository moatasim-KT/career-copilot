"""
Fallback provider manager for intelligent LLM provider switching.
Implements provider fallback chains (OpenAI → Groq → Gemini) with health monitoring.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import (
	ErrorCategory,
	ErrorSeverity,
	ExternalServiceError,
)

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
	"""Provider health status."""

	HEALTHY = "healthy"
	DEGRADED = "degraded"
	UNHEALTHY = "unhealthy"
	UNKNOWN = "unknown"


class FallbackStrategy(str, Enum):
	"""Fallback strategy types."""

	SEQUENTIAL = "sequential"  # Try providers in order
	PARALLEL = "parallel"  # Try multiple providers simultaneously
	ADAPTIVE = "adaptive"  # Adapt based on provider performance


@dataclass
class ProviderHealth:
	"""Provider health information."""

	provider_name: str
	status: ProviderStatus
	last_check: datetime
	response_time: float
	success_rate: float
	error_count: int
	consecutive_failures: int
	last_error: Optional[str] = None
	metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackConfig:
	"""Configuration for fallback behavior."""

	strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL
	max_parallel_attempts: int = 2
	health_check_interval: int = 300  # 5 minutes
	failure_threshold: int = 3
	recovery_threshold: int = 2
	timeout_per_provider: float = 30.0

	# Provider priority order (higher number = higher priority)
	provider_priorities: Dict[str, int] = field(
		default_factory=lambda: {
			"openai": 100,
			"groq": 80,
			"gemini": 60,
			"ollama": 40,
		}
	)

	# Provider capabilities mapping
	provider_capabilities: Dict[str, List[str]] = field(
		default_factory=lambda: {
			"openai": ["analysis", "reasoning", "complex_tasks", "high_quality"],
			"groq": ["fast_analysis", "reasoning", "generation", "speed"],
			"gemini": ["analysis", "reasoning", "multimodal", "generation"],
			"ollama": ["local_processing", "privacy", "generation", "free"],
		}
	)


class ProviderHealthMonitor:
	"""Monitor provider health and performance."""

	def __init__(self, config: FallbackConfig):
		self.config = config
		self.provider_health: Dict[str, ProviderHealth] = {}
		self.health_history: Dict[str, List[Dict[str, Any]]] = {}
		self.last_health_check = datetime.now(timezone.utc)

	def update_provider_health(self, provider_name: str, success: bool, response_time: float, error: Optional[str] = None):
		"""Update provider health based on execution result."""
		now = datetime.now(timezone.utc)

		if provider_name not in self.provider_health:
			self.provider_health[provider_name] = ProviderHealth(
				provider_name=provider_name,
				status=ProviderStatus.UNKNOWN,
				last_check=now,
				response_time=response_time,
				success_rate=1.0 if success else 0.0,
				error_count=0 if success else 1,
				consecutive_failures=0 if success else 1,
				last_error=error,
			)
		else:
			health = self.provider_health[provider_name]

			# Update metrics
			health.last_check = now
			health.response_time = (health.response_time * 0.8) + (response_time * 0.2)  # Moving average

			if success:
				health.consecutive_failures = 0
				health.success_rate = min(1.0, health.success_rate + 0.1)
			else:
				health.consecutive_failures += 1
				health.error_count += 1
				health.success_rate = max(0.0, health.success_rate - 0.2)
				health.last_error = error

			# Update status based on metrics
			health.status = self._calculate_provider_status(health)

		# Record in history
		if provider_name not in self.health_history:
			self.health_history[provider_name] = []

		self.health_history[provider_name].append(
			{
				"timestamp": now.isoformat(),
				"success": success,
				"response_time": response_time,
				"error": error,
				"status": self.provider_health[provider_name].status.value,
			}
		)

		# Keep only last 100 entries
		self.health_history[provider_name] = self.health_history[provider_name][-100:]

	def _calculate_provider_status(self, health: ProviderHealth) -> ProviderStatus:
		"""Calculate provider status based on health metrics."""
		if health.consecutive_failures >= self.config.failure_threshold:
			return ProviderStatus.UNHEALTHY
		elif health.success_rate < 0.7 or health.response_time > 10.0:
			return ProviderStatus.DEGRADED
		elif health.success_rate >= 0.9 and health.response_time < 5.0:
			return ProviderStatus.HEALTHY
		else:
			return ProviderStatus.DEGRADED

	def get_provider_health(self, provider_name: str) -> Optional[ProviderHealth]:
		"""Get health information for a provider."""
		return self.provider_health.get(provider_name)

	def get_healthy_providers(self) -> List[str]:
		"""Get list of healthy providers."""
		healthy = []
		for name, health in self.provider_health.items():
			if health.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]:
				healthy.append(name)
		return healthy

	def get_provider_ranking(self, required_capabilities: Optional[List[str]] = None) -> List[str]:
		"""Get providers ranked by health and priority."""
		providers = []

		for name, health in self.provider_health.items():
			# Skip unhealthy providers
			if health.status == ProviderStatus.UNHEALTHY:
				continue

			# Check capabilities if specified
			if required_capabilities:
				provider_caps = self.config.provider_capabilities.get(name, [])
				if not any(cap in provider_caps for cap in required_capabilities):
					continue

			# Calculate score based on health and priority
			priority = self.config.provider_priorities.get(name, 0)
			health_score = {
				ProviderStatus.HEALTHY: 100,
				ProviderStatus.DEGRADED: 50,
				ProviderStatus.UNHEALTHY: 0,
				ProviderStatus.UNKNOWN: 25,
			}[health.status]

			# Factor in success rate and response time
			performance_score = (health.success_rate * 50) + max(0, 50 - health.response_time * 5)

			total_score = priority + health_score + performance_score
			providers.append((name, total_score))

		# Sort by score (highest first)
		providers.sort(key=lambda x: x[1], reverse=True)
		return [name for name, _ in providers]

	def should_perform_health_check(self) -> bool:
		"""Check if health check should be performed."""
		return (datetime.now(timezone.utc) - self.last_health_check).total_seconds() > self.config.health_check_interval

	async def perform_health_checks(self, providers: Dict[str, Any]):
		"""Perform health checks on all providers."""
		if not self.should_perform_health_check():
			return

		logger.info("Performing provider health checks")

		for provider_name, provider in providers.items():
			try:
				start_time = time.time()

				# Perform health check
				if hasattr(provider, "health_check"):
					is_healthy = await provider.health_check()
				else:
					# Fallback health check
					is_healthy = await self._basic_health_check(provider)

				response_time = time.time() - start_time

				self.update_provider_health(
					provider_name, success=is_healthy, response_time=response_time, error=None if is_healthy else "Health check failed"
				)

			except Exception as e:
				response_time = time.time() - start_time
				self.update_provider_health(provider_name, success=False, response_time=response_time, error=str(e))
				logger.warning(f"Health check failed for provider {provider_name}: {e}")

		self.last_health_check = datetime.now(timezone.utc)

	async def _basic_health_check(self, provider: Any) -> bool:
		"""Basic health check for providers without dedicated health check method."""
		try:
			# Try a simple completion request
			if hasattr(provider, "generate_completion"):
				result = await provider.generate_completion([{"role": "user", "content": "Hello"}])
				return bool(result and result.content)
			return True
		except Exception:
			return False


class FallbackProviderManager:
	"""Manages fallback between multiple LLM providers."""

	def __init__(self, config: Optional[FallbackConfig] = None):
		self.config = config or FallbackConfig()
		self.health_monitor = ProviderHealthMonitor(self.config)
		self.providers: Dict[str, Any] = {}
		self.fallback_chains: Dict[str, List[str]] = {}

		# Default fallback chains
		self._setup_default_fallback_chains()

		logger.info(f"Fallback provider manager initialized with strategy: {self.config.strategy}")

	def _setup_default_fallback_chains(self):
		"""Setup default fallback chains for different task types."""
		self.fallback_chains = {
			"contract_analysis": ["openai", "groq", "gemini"],
			"risk_assessment": ["openai", "groq", "gemini"],
			"legal_precedent": ["openai", "gemini", "groq"],
			"negotiation": ["openai", "gemini", "groq"],
			"communication": ["groq", "openai", "gemini"],
			"general": ["groq", "openai", "gemini", "ollama"],
		}

	def register_provider(self, name: str, provider: Any):
		"""Register a provider with the fallback manager."""
		self.providers[name] = provider
		logger.info(f"Registered provider: {name}")

	def set_fallback_chain(self, task_type: str, provider_chain: List[str]):
		"""Set custom fallback chain for a task type."""
		self.fallback_chains[task_type] = provider_chain
		logger.info(f"Set fallback chain for {task_type}: {provider_chain}")

	async def execute_with_fallback(
		self,
		task_type: str,
		func_name: str,
		*args,
		required_capabilities: Optional[List[str]] = None,
		preferred_provider: Optional[str] = None,
		**kwargs,
	) -> Tuple[Any, str, Dict[str, Any]]:
		"""
		Execute function with fallback logic.

		Returns:
		    Tuple of (result, provider_used, execution_metadata)
		"""
		# Perform health checks if needed
		await self.health_monitor.perform_health_checks(self.providers)

		# Determine provider order
		provider_order = self._get_provider_order(task_type, required_capabilities, preferred_provider)

		if not provider_order:
			raise ExternalServiceError(
				"No healthy providers available", service_name="llm_providers", severity=ErrorSeverity.HIGH, category=ErrorCategory.EXTERNAL_SERVICE
			)

		execution_metadata = {
			"task_type": task_type,
			"provider_order": provider_order,
			"attempts": [],
			"strategy": self.config.strategy.value,
		}

		# Execute based on strategy
		if self.config.strategy == FallbackStrategy.SEQUENTIAL:
			return await self._execute_sequential(provider_order, func_name, args, kwargs, execution_metadata)
		elif self.config.strategy == FallbackStrategy.PARALLEL:
			return await self._execute_parallel(provider_order, func_name, args, kwargs, execution_metadata)
		else:  # ADAPTIVE
			return await self._execute_adaptive(provider_order, func_name, args, kwargs, execution_metadata)

	def _get_provider_order(self, task_type: str, required_capabilities: Optional[List[str]], preferred_provider: Optional[str]) -> List[str]:
		"""Get ordered list of providers to try."""
		# Start with preferred provider if specified and healthy
		provider_order = []

		if preferred_provider and preferred_provider in self.providers:
			health = self.health_monitor.get_provider_health(preferred_provider)
			if not health or health.status != ProviderStatus.UNHEALTHY:
				provider_order.append(preferred_provider)

		# Get fallback chain for task type
		fallback_chain = self.fallback_chains.get(task_type, self.fallback_chains["general"])

		# Get healthy providers ranked by performance
		ranked_providers = self.health_monitor.get_provider_ranking(required_capabilities)

		# Combine fallback chain with ranked providers
		for provider in fallback_chain:
			if provider in ranked_providers and provider not in provider_order:
				provider_order.append(provider)

		# Add any remaining healthy providers
		for provider in ranked_providers:
			if provider not in provider_order:
				provider_order.append(provider)

		return provider_order

	async def _execute_sequential(
		self, provider_order: List[str], func_name: str, args: tuple, kwargs: dict, metadata: Dict[str, Any]
	) -> Tuple[Any, str, Dict[str, Any]]:
		"""Execute with sequential fallback."""
		last_exception = None

		for provider_name in provider_order:
			if provider_name not in self.providers:
				continue

			provider = self.providers[provider_name]

			try:
				start_time = time.time()

				# Execute function on provider
				if hasattr(provider, func_name):
					func = getattr(provider, func_name)

					# Set timeout
					result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout_per_provider)

					execution_time = time.time() - start_time

					# Update health
					self.health_monitor.update_provider_health(provider_name, True, execution_time)

					# Record successful attempt
					metadata["attempts"].append(
						{
							"provider": provider_name,
							"success": True,
							"execution_time": execution_time,
							"error": None,
						}
					)

					metadata["successful_provider"] = provider_name
					metadata["total_execution_time"] = execution_time

					logger.info(f"Successfully executed {func_name} with provider {provider_name}")
					return result, provider_name, metadata

				else:
					raise AttributeError(f"Provider {provider_name} does not have method {func_name}")

			except Exception as e:
				execution_time = time.time() - start_time
				last_exception = e

				# Update health
				self.health_monitor.update_provider_health(provider_name, False, execution_time, str(e))

				# Record failed attempt
				metadata["attempts"].append(
					{
						"provider": provider_name,
						"success": False,
						"execution_time": execution_time,
						"error": str(e),
					}
				)

				logger.warning(f"Provider {provider_name} failed for {func_name}: {e}")
				continue

		# All providers failed
		metadata["all_providers_failed"] = True
		raise ExternalServiceError(
			f"All providers failed for {func_name}. Last error: {last_exception}",
			service_name="llm_providers",
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.EXTERNAL_SERVICE,
			details=metadata,
		)

	async def _execute_parallel(
		self, provider_order: List[str], func_name: str, args: tuple, kwargs: dict, metadata: Dict[str, Any]
	) -> Tuple[Any, str, Dict[str, Any]]:
		"""Execute with parallel attempts (race condition)."""
		# Limit parallel attempts
		providers_to_try = provider_order[: self.config.max_parallel_attempts]

		async def try_provider(provider_name: str):
			"""Try a single provider."""
			if provider_name not in self.providers:
				return None, provider_name, Exception(f"Provider {provider_name} not found")

			provider = self.providers[provider_name]

			try:
				start_time = time.time()

				if hasattr(provider, func_name):
					func = getattr(provider, func_name)
					result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout_per_provider)

					execution_time = time.time() - start_time

					# Update health
					self.health_monitor.update_provider_health(provider_name, True, execution_time)

					return result, provider_name, None
				else:
					raise AttributeError(f"Provider {provider_name} does not have method {func_name}")

			except Exception as e:
				execution_time = time.time() - start_time

				# Update health
				self.health_monitor.update_provider_health(provider_name, False, execution_time, str(e))

				return None, provider_name, e

		# Execute in parallel
		tasks = [try_provider(provider) for provider in providers_to_try]

		try:
			# Wait for first successful result
			done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

			# Cancel remaining tasks
			for task in pending:
				task.cancel()

			# Check results
			for task in done:
				result, provider_name, error = await task

				metadata["attempts"].append(
					{
						"provider": provider_name,
						"success": error is None,
						"error": str(error) if error else None,
					}
				)

				if error is None:
					metadata["successful_provider"] = provider_name
					logger.info(f"Successfully executed {func_name} with provider {provider_name} (parallel)")
					return result, provider_name, metadata

			# If we get here, all parallel attempts failed
			# Fall back to sequential for remaining providers
			remaining_providers = provider_order[self.config.max_parallel_attempts :]
			if remaining_providers:
				return await self._execute_sequential(remaining_providers, func_name, args, kwargs, metadata)

		except Exception as e:
			logger.error(f"Parallel execution failed: {e}")

		# All attempts failed
		metadata["all_providers_failed"] = True
		raise ExternalServiceError(
			f"All parallel providers failed for {func_name}",
			service_name="llm_providers",
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.EXTERNAL_SERVICE,
			details=metadata,
		)

	async def _execute_adaptive(
		self, provider_order: List[str], func_name: str, args: tuple, kwargs: dict, metadata: Dict[str, Any]
	) -> Tuple[Any, str, Dict[str, Any]]:
		"""Execute with adaptive strategy based on provider performance."""
		# For now, use sequential with dynamic reordering
		# In the future, this could implement more sophisticated logic

		# Reorder providers based on recent performance
		adaptive_order = self.health_monitor.get_provider_ranking()
		adaptive_order = [p for p in adaptive_order if p in provider_order]

		metadata["adaptive_reordering"] = True
		metadata["original_order"] = provider_order
		metadata["adaptive_order"] = adaptive_order

		return await self._execute_sequential(adaptive_order, func_name, args, kwargs, metadata)

	def get_provider_health_status(self) -> Dict[str, Dict[str, Any]]:
		"""Get health status for all providers."""
		status = {}
		for name, health in self.health_monitor.provider_health.items():
			status[name] = {
				"status": health.status.value,
				"success_rate": health.success_rate,
				"response_time": health.response_time,
				"consecutive_failures": health.consecutive_failures,
				"last_error": health.last_error,
				"last_check": health.last_check.isoformat(),
			}
		return status

	def get_fallback_chains(self) -> Dict[str, List[str]]:
		"""Get current fallback chains."""
		return self.fallback_chains.copy()


# Global fallback manager instance
_fallback_manager: Optional[FallbackProviderManager] = None


def get_fallback_manager() -> FallbackProviderManager:
	"""Get the global fallback manager instance."""
	global _fallback_manager
	if _fallback_manager is None:
		_fallback_manager = FallbackProviderManager()
	return _fallback_manager
