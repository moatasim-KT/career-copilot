"""
Cache Management Utilities

This module provides utility functions and decorators for easy cache management
in agent execution workflows.
"""

import asyncio
import functools
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from contextlib import asynccontextmanager

from ..core.agent_cache_manager import get_agent_cache_manager, AgentType
from ..core.logging import get_logger

logger = get_logger(__name__)
agent_cache_manager = get_agent_cache_manager()


def cached_agent_execution(
	agent_type: AgentType, cache_key_fields: Optional[List[str]] = None, ttl_override: Optional[int] = None, enable_timeout: bool = True
):
	"""
	Decorator for caching agent execution results.

	Args:
	    agent_type: Type of agent for cache configuration
	    cache_key_fields: Specific fields from input to use for cache key
	    ttl_override: Override default TTL for this execution
	    enable_timeout: Whether to apply timeout handling
	"""

	def decorator(func: Callable) -> Callable:
		@functools.wraps(func)
		async def wrapper(*args, **kwargs):
			# Extract task input from arguments
			task_input = None
			if args and isinstance(args[0], dict):
				task_input = args[0]
			elif "task_input" in kwargs:
				task_input = kwargs["task_input"]
			elif len(args) > 1 and isinstance(args[1], dict):
				task_input = args[1]

			if not task_input:
				logger.warning(f"No task input found for cached execution of {func.__name__}")
				return await func(*args, **kwargs)

			# Create cache key input
			cache_input = task_input
			if cache_key_fields:
				cache_input = {k: v for k, v in task_input.items() if k in cache_key_fields}

			# Try to get cached result
			cached_result = await agent_cache_manager.get_cached_result(agent_type, cache_input)
			if cached_result is not None:
				logger.debug(f"Using cached result for {func.__name__}")
				return cached_result

			# Execute function with optional timeout
			start_time = time.time()

			if enable_timeout:
				# Execute with timeout
				result = await agent_cache_manager.execute_with_timeout(agent_type=agent_type, coro=func(*args, **kwargs))
			else:
				# Execute without timeout
				result = await func(*args, **kwargs)

			execution_time = time.time() - start_time

			# Cache result if successful
			if result.get("success", True) and "error" not in result:
				metadata = {
					"function_name": func.__name__,
					"execution_timestamp": datetime.now(timezone.utc).isoformat(),
					"ttl_override": ttl_override,
				}

				# Override TTL if specified
				if ttl_override:
					original_config = agent_cache_manager.cache_configs[agent_type]
					original_ttl = original_config.cache_ttl_seconds
					original_config.cache_ttl_seconds = ttl_override

					try:
						await agent_cache_manager.cache_result(
							agent_type=agent_type, task_input=cache_input, result=result, execution_time=execution_time, metadata=metadata
						)
					finally:
						# Restore original TTL
						original_config.cache_ttl_seconds = original_ttl
				else:
					await agent_cache_manager.cache_result(
						agent_type=agent_type, task_input=cache_input, result=result, execution_time=execution_time, metadata=metadata
					)

			return result

		return wrapper

	return decorator


def timeout_handler(agent_type: AgentType, retry_count: int = 0, custom_timeout: Optional[int] = None):
	"""
	Decorator for handling agent execution timeouts.

	Args:
	    agent_type: Type of agent for timeout configuration
	    retry_count: Current retry attempt number
	    custom_timeout: Custom timeout override
	"""

	def decorator(func: Callable) -> Callable:
		@functools.wraps(func)
		async def wrapper(*args, **kwargs):
			timeout_seconds = custom_timeout or agent_cache_manager.get_timeout_for_agent(agent_type, retry_count)

			try:
				result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
				return result

			except asyncio.TimeoutError:
				logger.warning(f"Function {func.__name__} timed out after {timeout_seconds}s")

				return {
					"success": False,
					"error": f"Execution timed out after {timeout_seconds} seconds",
					"error_type": "timeout",
					"timeout_seconds": timeout_seconds,
					"retry_count": retry_count,
					"function_name": func.__name__,
				}

		return wrapper

	return decorator


class CacheContext:
	"""Context manager for cache operations."""

	def __init__(self, agent_type: AgentType):
		self.agent_type = agent_type
		self.start_time = None
		self.cache_hit = False
		self.execution_time = 0.0

	async def __aenter__(self):
		self.start_time = time.time()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		if self.start_time:
			self.execution_time = time.time() - self.start_time

		# Log cache performance
		if self.cache_hit:
			logger.debug(f"Cache hit for {self.agent_type.value} (saved {self.execution_time:.2f}s)")
		else:
			logger.debug(f"Cache miss for {self.agent_type.value} (execution: {self.execution_time:.2f}s)")


@asynccontextmanager
async def cache_context(agent_type: AgentType):
	"""Async context manager for cache operations."""
	context = CacheContext(agent_type)
	async with context:
		yield context


class CacheInvalidationManager:
	"""Manager for coordinated cache invalidation."""

	def __init__(self):
		self.invalidation_rules = {}
		self.dependency_graph = {}

	def add_invalidation_rule(self, trigger_agent: AgentType, affected_agents: List[AgentType], condition: Optional[Callable] = None):
		"""Add rule for cache invalidation when an agent executes."""
		self.invalidation_rules[trigger_agent] = {"affected_agents": affected_agents, "condition": condition}

	def add_dependency(self, dependent_agent: AgentType, dependency_agent: AgentType):
		"""Add dependency relationship between agents."""
		if dependent_agent not in self.dependency_graph:
			self.dependency_graph[dependent_agent] = []
		self.dependency_graph[dependent_agent].append(dependency_agent)

	async def invalidate_dependent_caches(self, trigger_agent: AgentType, execution_result: Dict[str, Any]):
		"""Invalidate caches based on rules and dependencies."""
		invalidated_agents = []

		# Check invalidation rules
		if trigger_agent in self.invalidation_rules:
			rule = self.invalidation_rules[trigger_agent]

			# Check condition if specified
			should_invalidate = True
			if rule["condition"]:
				should_invalidate = rule["condition"](execution_result)

			if should_invalidate:
				for affected_agent in rule["affected_agents"]:
					await agent_cache_manager.invalidate_cache(affected_agent)
					invalidated_agents.append(affected_agent)

		# Check dependency graph
		for dependent_agent, dependencies in self.dependency_graph.items():
			if trigger_agent in dependencies:
				await agent_cache_manager.invalidate_cache(dependent_agent)
				invalidated_agents.append(dependent_agent)

		if invalidated_agents:
			logger.info(f"Invalidated caches for {invalidated_agents} due to {trigger_agent.value} execution")

		return invalidated_agents


class CacheWarmupManager:
	"""Manager for cache warmup operations."""

	def __init__(self):
		self.warmup_tasks = {}

	def add_warmup_task(self, agent_type: AgentType, warmup_func: Callable, warmup_inputs: List[Dict[str, Any]], priority: int = 1):
		"""Add cache warmup task."""
		self.warmup_tasks[agent_type] = {"function": warmup_func, "inputs": warmup_inputs, "priority": priority}

	async def warmup_cache(self, agent_type: Optional[AgentType] = None):
		"""Perform cache warmup for specified agent or all agents."""
		tasks_to_run = {}

		if agent_type:
			if agent_type in self.warmup_tasks:
				tasks_to_run[agent_type] = self.warmup_tasks[agent_type]
		else:
			tasks_to_run = self.warmup_tasks.copy()

		# Sort by priority
		sorted_tasks = sorted(tasks_to_run.items(), key=lambda x: x[1]["priority"], reverse=True)

		warmup_results = {}

		for agent_type, task_info in sorted_tasks:
			logger.info(f"Starting cache warmup for {agent_type.value}")

			warmup_func = task_info["function"]
			warmup_inputs = task_info["inputs"]

			results = []
			for input_data in warmup_inputs:
				try:
					result = await warmup_func(input_data)
					results.append({"success": True, "input": input_data})
				except Exception as e:
					logger.error(f"Warmup failed for {agent_type.value}: {e}")
					results.append({"success": False, "input": input_data, "error": str(e)})

			warmup_results[agent_type] = results
			logger.info(f"Completed cache warmup for {agent_type.value}: {len(results)} tasks")

		return warmup_results


class CacheMetricsCollector:
	"""Collector for cache performance metrics."""

	def __init__(self):
		self.metrics = {"cache_operations": 0, "cache_hits": 0, "cache_misses": 0, "timeout_events": 0, "execution_times": [], "cache_sizes": []}

	def record_cache_operation(self, hit: bool, execution_time: float):
		"""Record cache operation metrics."""
		self.metrics["cache_operations"] += 1

		if hit:
			self.metrics["cache_hits"] += 1
		else:
			self.metrics["cache_misses"] += 1

		self.metrics["execution_times"].append(execution_time)

		# Keep only recent execution times
		if len(self.metrics["execution_times"]) > 1000:
			self.metrics["execution_times"] = self.metrics["execution_times"][-1000:]

	def record_timeout_event(self, agent_type: AgentType, timeout_seconds: int):
		"""Record timeout event."""
		self.metrics["timeout_events"] += 1
		logger.warning(f"Timeout recorded for {agent_type.value}: {timeout_seconds}s")

	def get_performance_summary(self) -> Dict[str, Any]:
		"""Get cache performance summary."""
		total_ops = self.metrics["cache_operations"]
		hit_rate = (self.metrics["cache_hits"] / total_ops * 100) if total_ops > 0 else 0

		avg_execution_time = 0.0
		if self.metrics["execution_times"]:
			avg_execution_time = sum(self.metrics["execution_times"]) / len(self.metrics["execution_times"])

		return {
			"total_operations": total_ops,
			"cache_hit_rate": hit_rate,
			"cache_hits": self.metrics["cache_hits"],
			"cache_misses": self.metrics["cache_misses"],
			"timeout_events": self.metrics["timeout_events"],
			"average_execution_time": avg_execution_time,
			"recent_execution_times": self.metrics["execution_times"][-10:],
		}


# Global instances
cache_invalidation_manager = CacheInvalidationManager()
cache_warmup_manager = CacheWarmupManager()
cache_metrics_collector = CacheMetricsCollector()


# Utility functions
async def clear_agent_cache(agent_type: Optional[AgentType] = None) -> int:
	"""Clear cache for specific agent type or all agents."""
	return await agent_cache_manager.invalidate_cache(agent_type)


async def get_cache_status() -> Dict[str, Any]:
	"""Get comprehensive cache status."""
	stats = agent_cache_manager.get_cache_statistics()
	performance = cache_metrics_collector.get_performance_summary()

	return {"cache_statistics": stats, "performance_metrics": performance, "timestamp": datetime.now(timezone.utc).isoformat()}


async def optimize_cache_performance() -> Dict[str, Any]:
	"""Perform cache optimization operations."""
	results = {"cleanup_count": 0, "optimization_actions": [], "performance_improvements": {}}

	# Clean up expired entries
	cleanup_count = await agent_cache_manager.cleanup_expired_entries()
	results["cleanup_count"] = cleanup_count
	results["optimization_actions"].append("expired_cleanup")

	# Additional optimization logic can be added here

	return results


def configure_cache_invalidation_rules():
	"""Configure default cache invalidation rules."""
	# Contract analyzer affects all other agents
	cache_invalidation_manager.add_invalidation_rule(
		trigger_agent=AgentType.CONTRACT_ANALYZER,
		affected_agents=[AgentType.RISK_ASSESSOR, AgentType.LEGAL_PRECEDENT, AgentType.NEGOTIATION, AgentType.COMMUNICATION],
	)

	# Risk assessor affects negotiation and communication
	cache_invalidation_manager.add_invalidation_rule(
		trigger_agent=AgentType.RISK_ASSESSOR, affected_agents=[AgentType.NEGOTIATION, AgentType.COMMUNICATION]
	)

	# Set up dependencies
	cache_invalidation_manager.add_dependency(AgentType.RISK_ASSESSOR, AgentType.CONTRACT_ANALYZER)
	cache_invalidation_manager.add_dependency(AgentType.NEGOTIATION, AgentType.RISK_ASSESSOR)
	cache_invalidation_manager.add_dependency(AgentType.COMMUNICATION, AgentType.NEGOTIATION)


# Initialize default configuration
configure_cache_invalidation_rules()
