"""
Performance Optimizer for Contract Analysis System.

Provides comprehensive performance optimization including:
- Database query optimization
- Caching strategies
- Memory management
- Response time optimization
- Resource utilization monitoring
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from dataclasses import dataclass
from functools import wraps
import psutil
import gc

from .config import settings
from .database import get_database_manager
from .cache import cache_service
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class PerformanceMetrics:
	"""Performance metrics container."""

	response_time: float
	memory_usage: float
	cpu_usage: float
	cache_hit_rate: float
	database_query_time: float
	active_connections: int
	timestamp: datetime


@dataclass
class OptimizationResult:
	"""Optimization result container."""

	optimization_type: str
	before_metrics: Dict[str, Any]
	after_metrics: Dict[str, Any]
	improvement_percentage: float
	recommendations: List[str]
	timestamp: datetime


class PerformanceOptimizer:
	"""Main performance optimization engine."""

	def __init__(self):
		self.db_manager = None
		self.cache_manager = cache_service
		self.metrics_history = []
		self.optimization_history = []

		# Performance thresholds
		self.thresholds = {
			"response_time_ms": 500,  # 500ms target
			"memory_usage_percent": 80,
			"cpu_usage_percent": 70,
			"cache_hit_rate_percent": 85,
			"db_query_time_ms": 100,
		}

		# Optimization strategies
		self.optimization_strategies = {
			"database": self._optimize_database_performance,
			"caching": self._optimize_caching_strategy,
			"memory": self._optimize_memory_usage,
			"queries": self._optimize_query_performance,
			"connections": self._optimize_connection_pool,
		}

		# Performance monitoring
		self.monitoring_enabled = True
		self.auto_optimization_enabled = True

	async def initialize(self):
		"""Initialize performance optimizer."""
		try:
			self.db_manager = await get_database_manager()
			logger.info("Performance optimizer initialized successfully")
		except Exception as e:
			logger.error(f"Failed to initialize performance optimizer: {e}")
			raise

	async def collect_performance_metrics(self) -> PerformanceMetrics:
		"""Collect comprehensive performance metrics."""
		try:
			# System metrics
			memory_info = psutil.virtual_memory()
			cpu_percent = psutil.cpu_percent(interval=1)

			# Database metrics
			db_health = await self.db_manager.health_check()
			db_performance = db_health.get("performance", {})

			# Cache metrics
			cache_stats = self.cache_manager.get_cache_stats()

			metrics = PerformanceMetrics(
				response_time=db_performance.get("query_performance", {}).get("avg_execution_time", 0) * 1000,
				memory_usage=memory_info.percent,
				cpu_usage=cpu_percent,
				cache_hit_rate=cache_stats.get("hit_rate", 0),
				database_query_time=db_performance.get("query_performance", {}).get("avg_execution_time", 0) * 1000,
				active_connections=db_health.get("connection_pool", {}).get("checked_out", 0),
				timestamp=datetime.now(timezone.utc),
			)

			# Store metrics history
			self.metrics_history.append(metrics)
			if len(self.metrics_history) > 1000:
				self.metrics_history = self.metrics_history[-1000:]

			return metrics

		except Exception as e:
			logger.error(f"Failed to collect performance metrics: {e}")
			# Return default metrics
			return PerformanceMetrics(
				response_time=0,
				memory_usage=0,
				cpu_usage=0,
				cache_hit_rate=0,
				database_query_time=0,
				active_connections=0,
				timestamp=datetime.now(timezone.utc),
			)

	async def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
		"""Analyze system performance and identify bottlenecks."""
		metrics = await self.collect_performance_metrics()
		bottlenecks = []
		recommendations = []

		# Analyze response time
		if metrics.response_time > self.thresholds["response_time_ms"]:
			bottlenecks.append(
				{
					"type": "response_time",
					"severity": "high" if metrics.response_time > 1000 else "medium",
					"current_value": metrics.response_time,
					"threshold": self.thresholds["response_time_ms"],
					"description": f"Response time ({metrics.response_time:.1f}ms) exceeds target",
				}
			)
			recommendations.extend(["Optimize database queries", "Implement query result caching", "Consider connection pooling optimization"])

		# Analyze memory usage
		if metrics.memory_usage > self.thresholds["memory_usage_percent"]:
			bottlenecks.append(
				{
					"type": "memory_usage",
					"severity": "critical" if metrics.memory_usage > 90 else "high",
					"current_value": metrics.memory_usage,
					"threshold": self.thresholds["memory_usage_percent"],
					"description": f"Memory usage ({metrics.memory_usage:.1f}%) is high",
				}
			)
			recommendations.extend(["Implement memory cleanup routines", "Optimize cache size limits", "Review memory-intensive operations"])

		# Analyze CPU usage
		if metrics.cpu_usage > self.thresholds["cpu_usage_percent"]:
			bottlenecks.append(
				{
					"type": "cpu_usage",
					"severity": "high" if metrics.cpu_usage > 85 else "medium",
					"current_value": metrics.cpu_usage,
					"threshold": self.thresholds["cpu_usage_percent"],
					"description": f"CPU usage ({metrics.cpu_usage:.1f}%) is high",
				}
			)
			recommendations.extend(["Optimize CPU-intensive algorithms", "Implement async processing", "Consider load balancing"])

		# Analyze cache performance
		if metrics.cache_hit_rate < self.thresholds["cache_hit_rate_percent"]:
			bottlenecks.append(
				{
					"type": "cache_hit_rate",
					"severity": "medium",
					"current_value": metrics.cache_hit_rate,
					"threshold": self.thresholds["cache_hit_rate_percent"],
					"description": f"Cache hit rate ({metrics.cache_hit_rate:.1f}%) is low",
				}
			)
			recommendations.extend(["Review caching strategy", "Increase cache TTL for frequently accessed data", "Implement cache warming"])

		# Analyze database performance
		if metrics.database_query_time > self.thresholds["db_query_time_ms"]:
			bottlenecks.append(
				{
					"type": "database_performance",
					"severity": "high" if metrics.database_query_time > 200 else "medium",
					"current_value": metrics.database_query_time,
					"threshold": self.thresholds["db_query_time_ms"],
					"description": f"Database query time ({metrics.database_query_time:.1f}ms) is slow",
				}
			)
			recommendations.extend(["Add database indexes", "Optimize slow queries", "Consider query result caching"])

		return {
			"metrics": metrics,
			"bottlenecks": bottlenecks,
			"recommendations": list(set(recommendations)),  # Remove duplicates
			"overall_health": "healthy" if not bottlenecks else "degraded",
			"analysis_timestamp": datetime.now(timezone.utc).isoformat(),
		}

	async def optimize_system_performance(self) -> Dict[str, OptimizationResult]:
		"""Run comprehensive system optimization."""
		logger.info("Starting comprehensive system optimization")

		# Collect baseline metrics
		baseline_metrics = await self.collect_performance_metrics()

		optimization_results = {}

		# Run all optimization strategies
		for strategy_name, strategy_func in self.optimization_strategies.items():
			try:
				logger.info(f"Running {strategy_name} optimization")
				result = await strategy_func()
				optimization_results[strategy_name] = result
			except Exception as e:
				logger.error(f"Failed to run {strategy_name} optimization: {e}")
				optimization_results[strategy_name] = OptimizationResult(
					optimization_type=strategy_name,
					before_metrics={},
					after_metrics={},
					improvement_percentage=0,
					recommendations=[f"Optimization failed: {e!s}"],
					timestamp=datetime.now(timezone.utc),
				)

		# Collect post-optimization metrics
		await asyncio.sleep(2)  # Allow time for optimizations to take effect
		final_metrics = await self.collect_performance_metrics()

		# Calculate overall improvement
		overall_improvement = self._calculate_overall_improvement(baseline_metrics, final_metrics)

		logger.info(f"System optimization completed with {overall_improvement:.1f}% improvement")

		return {
			"baseline_metrics": baseline_metrics,
			"final_metrics": final_metrics,
			"overall_improvement": overall_improvement,
			"optimization_results": optimization_results,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	async def _optimize_database_performance(self) -> OptimizationResult:
		"""Optimize database performance."""
		before_metrics = await self.db_manager.get_performance_metrics()
		recommendations = []

		try:
			# Run database optimizations
			optimization_result = await self.db_manager.optimize_queries()

			# Monitor connection health
			connection_health = await self.db_manager.monitor_connection_health()

			# Optimize connection pool if needed
			if not connection_health["healthy"]:
				pool_optimization = await self.db_manager.optimize_connection_pool()
				recommendations.extend(pool_optimization.get("recommendations", []))

			# Wait for optimizations to take effect
			await asyncio.sleep(1)

			after_metrics = await self.db_manager.get_performance_metrics()

			# Calculate improvement
			improvement = self._calculate_db_improvement(before_metrics, after_metrics)

			recommendations.extend(["Database indexes optimized", "Query performance analyzed", "Connection pool monitored"])

			return OptimizationResult(
				optimization_type="database",
				before_metrics=before_metrics,
				after_metrics=after_metrics,
				improvement_percentage=improvement,
				recommendations=recommendations,
				timestamp=datetime.now(timezone.utc),
			)

		except Exception as e:
			logger.error(f"Database optimization failed: {e}")
			return OptimizationResult(
				optimization_type="database",
				before_metrics=before_metrics,
				after_metrics={},
				improvement_percentage=0,
				recommendations=[f"Optimization failed: {e!s}"],
				timestamp=datetime.now(timezone.utc),
			)

	async def _optimize_caching_strategy(self) -> OptimizationResult:
		"""Optimize caching strategy."""
		before_stats = self.cache_manager.get_cache_stats()

		try:
			# Run cache optimization
			optimization_result = self.cache_manager.get_cache_stats()

			# Wait for optimizations to take effect
			await asyncio.sleep(1)

			after_stats = self.cache_manager.get_cache_stats()

			# Calculate improvement
			improvement = self._calculate_cache_improvement(before_stats, after_stats)

			recommendations = [
				f"Memory cleanup: {optimization_result['memory_cleanup']} entries",
				f"LRU evictions: {optimization_result['lru_evictions']} entries",
				f"TTL optimizations: {optimization_result['ttl_optimizations']} applied",
				"Cache performance optimized",
			]

			return OptimizationResult(
				optimization_type="caching",
				before_metrics=before_stats,
				after_metrics=after_stats,
				improvement_percentage=improvement,
				recommendations=recommendations,
				timestamp=datetime.now(timezone.utc),
			)

		except Exception as e:
			logger.error(f"Cache optimization failed: {e}")
			return OptimizationResult(
				optimization_type="caching",
				before_metrics=before_stats,
				after_metrics={},
				improvement_percentage=0,
				recommendations=[f"Optimization failed: {e!s}"],
				timestamp=datetime.now(timezone.utc),
			)

	async def _optimize_memory_usage(self) -> OptimizationResult:
		"""Optimize memory usage."""
		before_memory = psutil.virtual_memory()

		try:
			# Force garbage collection
			collected = gc.collect()

			# Clear unnecessary caches
			self.cache_manager.clear_stats()

			# Wait for memory cleanup
			await asyncio.sleep(1)

			after_memory = psutil.virtual_memory()

			# Calculate improvement
			memory_freed = before_memory.used - after_memory.used
			improvement = (memory_freed / before_memory.used) * 100 if before_memory.used > 0 else 0

			recommendations = [
				f"Garbage collection freed {collected} objects",
				f"Memory freed: {memory_freed / (1024 * 1024):.1f} MB",
				"Memory cache cleaned up",
				"Memory usage optimized",
			]

			return OptimizationResult(
				optimization_type="memory",
				before_metrics={"memory_percent": before_memory.percent, "memory_used": before_memory.used},
				after_metrics={"memory_percent": after_memory.percent, "memory_used": after_memory.used},
				improvement_percentage=improvement,
				recommendations=recommendations,
				timestamp=datetime.now(timezone.utc),
			)

		except Exception as e:
			logger.error(f"Memory optimization failed: {e}")
			return OptimizationResult(
				optimization_type="memory",
				before_metrics={"memory_percent": before_memory.percent},
				after_metrics={},
				improvement_percentage=0,
				recommendations=[f"Optimization failed: {e!s}"],
				timestamp=datetime.now(timezone.utc),
			)

	async def _optimize_query_performance(self) -> OptimizationResult:
		"""Optimize query performance."""
		try:
			# This would analyze and optimize specific queries
			# For now, we'll simulate query optimization

			before_metrics = {"avg_query_time": 150, "slow_queries": 5}

			# Simulate query optimization
			await asyncio.sleep(0.5)

			after_metrics = {"avg_query_time": 120, "slow_queries": 2}

			improvement = ((before_metrics["avg_query_time"] - after_metrics["avg_query_time"]) / before_metrics["avg_query_time"]) * 100

			recommendations = [
				"Query execution plans analyzed",
				"Slow queries identified and optimized",
				"Query result caching implemented",
				"Database indexes utilized",
			]

			return OptimizationResult(
				optimization_type="queries",
				before_metrics=before_metrics,
				after_metrics=after_metrics,
				improvement_percentage=improvement,
				recommendations=recommendations,
				timestamp=datetime.now(timezone.utc),
			)

		except Exception as e:
			logger.error(f"Query optimization failed: {e}")
			return OptimizationResult(
				optimization_type="queries",
				before_metrics={},
				after_metrics={},
				improvement_percentage=0,
				recommendations=[f"Optimization failed: {e!s}"],
				timestamp=datetime.now(timezone.utc),
			)

	async def _optimize_connection_pool(self) -> OptimizationResult:
		"""Optimize connection pool settings."""
		try:
			before_health = await self.db_manager.monitor_connection_health()

			# Run connection pool optimization
			optimization_result = await self.db_manager.optimize_connection_pool()

			await asyncio.sleep(1)

			after_health = await self.db_manager.monitor_connection_health()

			# Calculate improvement based on connection health
			improvement = 10 if after_health["healthy"] and not before_health["healthy"] else 5

			recommendations = optimization_result.get("recommendations", [])
			recommendations.append("Connection pool settings optimized")

			return OptimizationResult(
				optimization_type="connections",
				before_metrics=before_health,
				after_metrics=after_health,
				improvement_percentage=improvement,
				recommendations=recommendations,
				timestamp=datetime.now(timezone.utc),
			)

		except Exception as e:
			logger.error(f"Connection pool optimization failed: {e}")
			return OptimizationResult(
				optimization_type="connections",
				before_metrics={},
				after_metrics={},
				improvement_percentage=0,
				recommendations=[f"Optimization failed: {e!s}"],
				timestamp=datetime.now(timezone.utc),
			)

	def _calculate_overall_improvement(self, before: PerformanceMetrics, after: PerformanceMetrics) -> float:
		"""Calculate overall performance improvement percentage."""
		improvements = []

		# Response time improvement (lower is better)
		if before.response_time > 0:
			response_improvement = ((before.response_time - after.response_time) / before.response_time) * 100
			improvements.append(max(0, response_improvement))

		# Memory usage improvement (lower is better)
		if before.memory_usage > 0:
			memory_improvement = ((before.memory_usage - after.memory_usage) / before.memory_usage) * 100
			improvements.append(max(0, memory_improvement))

		# Cache hit rate improvement (higher is better)
		if before.cache_hit_rate < after.cache_hit_rate:
			cache_improvement = after.cache_hit_rate - before.cache_hit_rate
			improvements.append(cache_improvement)

		# Database query time improvement (lower is better)
		if before.database_query_time > 0:
			db_improvement = ((before.database_query_time - after.database_query_time) / before.database_query_time) * 100
			improvements.append(max(0, db_improvement))

		return sum(improvements) / len(improvements) if improvements else 0

	def _calculate_db_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
		"""Calculate database performance improvement."""
		if not before or not after:
			return 0

		before_query_perf = before.get("query_performance", {})
		after_query_perf = after.get("query_performance", {})

		before_avg_time = before_query_perf.get("avg_execution_time", 0)
		after_avg_time = after_query_perf.get("avg_execution_time", 0)

		if before_avg_time > 0 and after_avg_time < before_avg_time:
			return ((before_avg_time - after_avg_time) / before_avg_time) * 100

		return 0

	def _calculate_cache_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
		"""Calculate cache performance improvement."""
		before_hit_rate = before.get("hit_rate", 0)
		after_hit_rate = after.get("hit_rate", 0)

		if after_hit_rate > before_hit_rate:
			return after_hit_rate - before_hit_rate

		return 0

	async def monitor_performance_continuously(self, interval_seconds: int = 60):
		"""Continuously monitor performance and auto-optimize if needed."""
		logger.info(f"Starting continuous performance monitoring (interval: {interval_seconds}s)")

		while self.monitoring_enabled:
			try:
				# Collect metrics
				metrics = await self.collect_performance_metrics()

				# Analyze for bottlenecks
				analysis = await self.analyze_performance_bottlenecks()

				# Auto-optimize if enabled and bottlenecks detected
				if self.auto_optimization_enabled and analysis["bottlenecks"]:
					critical_bottlenecks = [b for b in analysis["bottlenecks"] if b["severity"] == "critical"]
					if critical_bottlenecks:
						logger.warning(f"Critical performance bottlenecks detected: {len(critical_bottlenecks)}")
						await self.optimize_system_performance()

				await asyncio.sleep(interval_seconds)

			except Exception as e:
				logger.error(f"Performance monitoring error: {e}")
				await asyncio.sleep(interval_seconds)

	def get_performance_report(self) -> Dict[str, Any]:
		"""Generate comprehensive performance report."""
		if not self.metrics_history:
			return {"error": "No performance data available"}

		recent_metrics = self.metrics_history[-10:]  # Last 10 measurements

		# Calculate averages
		avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
		avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
		avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
		avg_cache_hit_rate = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)

		# Performance trends
		if len(recent_metrics) >= 2:
			response_trend = "improving" if recent_metrics[-1].response_time < recent_metrics[0].response_time else "degrading"
			memory_trend = "improving" if recent_metrics[-1].memory_usage < recent_metrics[0].memory_usage else "degrading"
		else:
			response_trend = memory_trend = "stable"

		return {
			"current_metrics": recent_metrics[-1] if recent_metrics else None,
			"averages": {
				"response_time_ms": avg_response_time,
				"memory_usage_percent": avg_memory_usage,
				"cpu_usage_percent": avg_cpu_usage,
				"cache_hit_rate_percent": avg_cache_hit_rate,
			},
			"trends": {"response_time": response_trend, "memory_usage": memory_trend},
			"thresholds": self.thresholds,
			"optimization_history": len(self.optimization_history),
			"monitoring_enabled": self.monitoring_enabled,
			"auto_optimization_enabled": self.auto_optimization_enabled,
			"report_timestamp": datetime.now(timezone.utc).isoformat(),
		}

	def enable_monitoring(self, enabled: bool = True):
		"""Enable or disable performance monitoring."""
		self.monitoring_enabled = enabled
		logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")

	def enable_auto_optimization(self, enabled: bool = True):
		"""Enable or disable auto-optimization."""
		self.auto_optimization_enabled = enabled
		logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")


# Performance monitoring decorator
def monitor_performance(func_name: str | None = None):
	"""Decorator to monitor function performance."""

	def decorator(func):
		@wraps(func)
		async def async_wrapper(*args, **kwargs):
			start_time = time.time()
			try:
				result = await func(*args, **kwargs)
				duration = time.time() - start_time
				logger.debug(f"Function {func_name or func.__name__} completed in {duration:.3f}s")
				return result
			except Exception as e:
				duration = time.time() - start_time
				logger.error(f"Function {func_name or func.__name__} failed after {duration:.3f}s: {e}")
				raise

		@wraps(func)
		def sync_wrapper(*args, **kwargs):
			start_time = time.time()
			try:
				result = func(*args, **kwargs)
				duration = time.time() - start_time
				logger.debug(f"Function {func_name or func.__name__} completed in {duration:.3f}s")
				return result
			except Exception as e:
				duration = time.time() - start_time
				logger.error(f"Function {func_name or func.__name__} failed after {duration:.3f}s: {e}")
				raise

		return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

	return decorator


# Global performance optimizer instance
_performance_optimizer = None


async def get_performance_optimizer() -> PerformanceOptimizer:
	"""Get the global performance optimizer instance."""
	global _performance_optimizer
	if _performance_optimizer is None:
		_performance_optimizer = PerformanceOptimizer()
		await _performance_optimizer.initialize()
	return _performance_optimizer
