"""
LangSmith integration for AI workflow tracing and debugging.

This module provides:
- Comprehensive AI operation tracing
- Workflow debugging and analysis
- Performance monitoring for AI operations
- Cost tracking and optimization insights
- Error analysis and debugging
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import structlog
from langsmith import Client as LangSmithClient
from langsmith.schemas import Run

from .config import settings

logger = structlog.get_logger(__name__)

# Global LangSmith client
_langsmith_client: Optional[LangSmithClient] = None
_langsmith_initialized = False


class LangSmithManager:
	"""Manager for LangSmith tracing and monitoring."""

	def __init__(self):
		self.settings = settings
		self.client: Optional[LangSmithClient] = None
		self.project_name = self.settings.langsmith_project
		self.enabled = self.settings.langsmith_tracing and bool(self.settings.langsmith_api_key)

	def initialize(self) -> bool:
		"""Initialize LangSmith client."""
		global _langsmith_client, _langsmith_initialized

		if _langsmith_initialized:
			return True

		if not self.enabled:
			logger.info("LangSmith tracing disabled")
			return False

		try:
			self.client = LangSmithClient(api_key=self.settings.langsmith_api_key, api_url="https://api.smith.langchain.com")

			# Test connection
			self.client.list_runs(limit=1)

			# Set environment variables for LangChain integration
			import os

			os.environ["LANGCHAIN_TRACING_V2"] = "true"
			os.environ["LANGCHAIN_API_KEY"] = self.settings.langsmith_api_key
			os.environ["LANGCHAIN_PROJECT"] = self.project_name

			_langsmith_client = self.client
			_langsmith_initialized = True

			logger.info("LangSmith initialized successfully", project=self.project_name, api_url="https://api.smith.langchain.com")
			return True

		except Exception as e:
			logger.error("Failed to initialize LangSmith", error=str(e))
			return False

	def is_enabled(self) -> bool:
		"""Check if LangSmith is enabled and initialized."""
		return self.enabled and _langsmith_initialized

	def get_client(self) -> Optional[LangSmithClient]:
		"""Get the LangSmith client."""
		return _langsmith_client


# Global manager instance
langsmith_manager = LangSmithManager()


def initialize_langsmith() -> bool:
	"""Initialize LangSmith integration."""
	return langsmith_manager.initialize()


def get_langsmith_client() -> Optional[LangSmithClient]:
	"""Get the LangSmith client instance."""
	return langsmith_manager.get_client()


def is_langsmith_enabled() -> bool:
	"""Check if LangSmith is enabled."""
	return langsmith_manager.is_enabled()


@asynccontextmanager
async def trace_ai_workflow(workflow_name: str, inputs: Dict[str, Any], workflow_type: str = "chain", metadata: Optional[Dict[str, Any]] = None):
	"""
	Context manager for tracing AI workflows with LangSmith.

	Args:
	    workflow_name: Name of the workflow
	    inputs: Input data for the workflow
	    workflow_type: Type of workflow (chain, llm, tool, etc.)
	    metadata: Additional metadata to include
	"""
	client = get_langsmith_client()
	if not client:
		yield None
		return

	run_id = None
	start_time = time.time()

	try:
		# Create run
		run = client.create_run(
			name=workflow_name, run_type=workflow_type, inputs=inputs, project_name=langsmith_manager.project_name, extra=metadata or {}
		)
		run_id = run.id

		logger.debug("Started LangSmith trace", workflow_name=workflow_name, run_id=str(run_id), workflow_type=workflow_type)

		yield run

	except Exception as e:
		duration = time.time() - start_time

		if run_id:
			try:
				client.update_run(run_id, error=str(e), end_time=datetime.now(timezone.utc))
			except Exception as update_error:
				logger.error("Failed to update LangSmith run with error", error=str(update_error))

		logger.error("AI workflow failed", workflow_name=workflow_name, run_id=str(run_id) if run_id else None, duration=duration, error=str(e))
		raise

	else:
		duration = time.time() - start_time

		if run_id:
			try:
				client.update_run(run_id, end_time=datetime.now(timezone.utc))
			except Exception as update_error:
				logger.error("Failed to update LangSmith run", error=str(update_error))

		logger.debug("Completed LangSmith trace", workflow_name=workflow_name, run_id=str(run_id) if run_id else None, duration=duration)


def trace_ai_operation(operation_name: str, operation_type: str = "llm", include_io: bool = True, include_metadata: bool = True):
	"""
	Decorator for tracing AI operations with LangSmith.

	Args:
	    operation_name: Name of the operation
	    operation_type: Type of operation (llm, chain, tool, etc.)
	    include_io: Whether to include input/output in trace
	    include_metadata: Whether to include metadata
	"""

	def decorator(func):
		@wraps(func)
		async def async_wrapper(*args, **kwargs):
			if not is_langsmith_enabled():
				return await func(*args, **kwargs)

			# Prepare inputs for tracing
			inputs = {}
			if include_io:
				inputs = {"args": str(args)[:1000] if args else "", "kwargs": {k: str(v)[:500] for k, v in kwargs.items()}}

			metadata = {}
			if include_metadata:
				metadata = {"function_name": func.__name__, "module": func.__module__, "timestamp": datetime.now(timezone.utc).isoformat()}

			# Map operation types to valid LangSmith run types
			valid_run_type = {"orchestration": "chain", "agent": "chain", "workflow": "chain", "analysis": "chain"}.get(operation_type, "chain")

			async with trace_ai_workflow(
				workflow_name=f"{operation_name}.{func.__name__}", inputs=inputs, workflow_type=valid_run_type, metadata=metadata
			) as run:
				try:
					result = await func(*args, **kwargs)

					# Update run with outputs
					if run and hasattr(run, "id") and run.id and include_io:
						client = get_langsmith_client()
						if client:
							try:
								outputs = {"result": str(result)[:1000]}
								client.update_run(run.id, outputs=outputs)
							except Exception as e:
								logger.warning("Failed to update LangSmith outputs", error=str(e))

					return result

				except Exception as e:
					# Error is already handled by the context manager
					raise

		@wraps(func)
		def sync_wrapper(*args, **kwargs):
			if not is_langsmith_enabled():
				return func(*args, **kwargs)

			# For sync functions, we'll use a simpler approach
			client = get_langsmith_client()
			if not client:
				return func(*args, **kwargs)

			inputs = {}
			if include_io:
				inputs = {"args": str(args)[:1000] if args else "", "kwargs": {k: str(v)[:500] for k, v in kwargs.items()}}

			metadata = {}
			if include_metadata:
				metadata = {"function_name": func.__name__, "module": func.__module__, "timestamp": datetime.now(timezone.utc).isoformat()}

			run_id = None
			start_time = time.time()

			try:
				# Create run
				run = client.create_run(
					name=f"{operation_name}.{func.__name__}",
					run_type=operation_type,
					inputs=inputs,
					project_name=langsmith_manager.project_name,
					extra=metadata,
				)
				run_id = run.id

				result = func(*args, **kwargs)

				# Update run with outputs
				if include_io:
					outputs = {"result": str(result)[:1000]}
					client.update_run(run_id, outputs=outputs, end_time=datetime.now(timezone.utc))
				else:
					client.update_run(run_id, end_time=datetime.now(timezone.utc))

				return result

			except Exception as e:
				if run_id:
					try:
						client.update_run(run_id, error=str(e), end_time=datetime.now(timezone.utc))
					except Exception:
						pass
				raise

		# Return appropriate wrapper
		if asyncio.iscoroutinefunction(func):
			return async_wrapper
		else:
			return sync_wrapper

	return decorator


class LangSmithMetrics:
	"""Collect and analyze LangSmith metrics."""

	def __init__(self):
		self.client = get_langsmith_client()

	async def get_recent_runs(self, hours: int = 24) -> List[Run]:
		"""Get recent runs from LangSmith."""
		if not self.client:
			return []

		try:
			from datetime import timedelta

			start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

			runs = list(self.client.list_runs(project_name=langsmith_manager.project_name, start_time=start_time, limit=1000))

			return runs

		except Exception as e:
			logger.error("Failed to fetch LangSmith runs", error=str(e))
			return []

	async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
		"""Get performance metrics from LangSmith runs."""
		runs = await self.get_recent_runs(hours)

		if not runs:
			return {}

		# Calculate metrics
		total_runs = len(runs)
		successful_runs = len([r for r in runs if r.error is None])
		failed_runs = total_runs - successful_runs

		# Calculate durations
		durations = []
		for run in runs:
			if run.start_time and run.end_time:
				duration = (run.end_time - run.start_time).total_seconds()
				durations.append(duration)

		avg_duration = sum(durations) / len(durations) if durations else 0
		max_duration = max(durations) if durations else 0
		min_duration = min(durations) if durations else 0

		# Calculate token usage (if available)
		total_tokens = 0
		total_cost = 0.0

		for run in runs:
			if run.outputs and isinstance(run.outputs, dict):
				tokens = run.outputs.get("token_usage", {})
				if isinstance(tokens, dict):
					total_tokens += tokens.get("total_tokens", 0)
					# Rough cost estimation
					total_cost += tokens.get("total_tokens", 0) * 0.00003  # ~$0.03/1K tokens

		return {
			"period_hours": hours,
			"total_runs": total_runs,
			"successful_runs": successful_runs,
			"failed_runs": failed_runs,
			"success_rate": successful_runs / total_runs if total_runs > 0 else 0,
			"average_duration_seconds": avg_duration,
			"max_duration_seconds": max_duration,
			"min_duration_seconds": min_duration,
			"total_tokens": total_tokens,
			"estimated_cost_usd": total_cost,
			"runs_per_hour": total_runs / hours if hours > 0 else 0,
		}

	async def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Analyze errors from LangSmith runs."""
		runs = await self.get_recent_runs(hours)

		failed_runs = [r for r in runs if r.error is not None]

		if not failed_runs:
			return {"total_errors": 0, "error_types": {}, "recent_errors": []}

		# Group errors by type
		error_types = {}
		recent_errors = []

		for run in failed_runs:
			error_msg = str(run.error)
			error_type = error_msg.split(":")[0] if ":" in error_msg else "Unknown"

			error_types[error_type] = error_types.get(error_type, 0) + 1

			recent_errors.append(
				{
					"run_id": str(run.id),
					"name": run.name,
					"error": error_msg[:200],
					"timestamp": run.start_time.isoformat() if run.start_time else None,
				}
			)

		# Sort by frequency
		error_types = dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True))

		# Keep only recent errors (last 10)
		recent_errors = sorted(recent_errors, key=lambda x: x["timestamp"] or "", reverse=True)[:10]

		return {
			"total_errors": len(failed_runs),
			"error_types": error_types,
			"recent_errors": recent_errors,
			"error_rate": len(failed_runs) / len(runs) if runs else 0,
		}

	async def get_cost_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Analyze AI operation costs."""
		runs = await self.get_recent_runs(hours)

		cost_by_model = {}
		cost_by_operation = {}
		total_cost = 0.0
		total_tokens = 0

		for run in runs:
			if not run.outputs or not isinstance(run.outputs, dict):
				continue

			tokens = run.outputs.get("token_usage", {})
			if not isinstance(tokens, dict):
				continue

			run_tokens = tokens.get("total_tokens", 0)
			# Rough cost estimation based on GPT-4 pricing
			run_cost = run_tokens * 0.00003

			total_tokens += run_tokens
			total_cost += run_cost

			# Group by model (if available in metadata)
			model = "unknown"
			if run.extra and isinstance(run.extra, dict):
				model = run.extra.get("model", "unknown")

			cost_by_model[model] = cost_by_model.get(model, 0) + run_cost

			# Group by operation type
			operation = run.name.split(".")[0] if "." in run.name else run.name
			cost_by_operation[operation] = cost_by_operation.get(operation, 0) + run_cost

		return {
			"period_hours": hours,
			"total_cost_usd": total_cost,
			"total_tokens": total_tokens,
			"cost_per_hour": total_cost / hours if hours > 0 else 0,
			"tokens_per_hour": total_tokens / hours if hours > 0 else 0,
			"cost_by_model": dict(sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True)),
			"cost_by_operation": dict(sorted(cost_by_operation.items(), key=lambda x: x[1], reverse=True)),
			"average_cost_per_run": total_cost / len(runs) if runs else 0,
		}


async def get_langsmith_health() -> Dict[str, Any]:
	"""Check LangSmith service health."""
	if not is_langsmith_enabled():
		return {"status": "disabled", "message": "LangSmith tracing is disabled"}

	client = get_langsmith_client()
	if not client:
		return {"status": "error", "message": "LangSmith client not initialized"}

	try:
		# Test connection by listing recent runs
		runs = list(client.list_runs(limit=1))

		return {
			"status": "healthy",
			"message": "LangSmith connection successful",
			"project": langsmith_manager.project_name,
			"api_url": "https://api.smith.langchain.com",
		}

	except Exception as e:
		return {"status": "error", "message": f"LangSmith connection failed: {e!s}"}


async def get_langsmith_metrics_summary() -> Dict[str, Any]:
	"""Get comprehensive LangSmith metrics summary."""
	if not is_langsmith_enabled():
		return {"enabled": False}

	metrics = LangSmithMetrics()

	try:
		performance = await metrics.get_performance_metrics(24)
		errors = await metrics.get_error_analysis(24)
		costs = await metrics.get_cost_analysis(24)
		health = await get_langsmith_health()

		return {
			"enabled": True,
			"health": health,
			"performance": performance,
			"errors": errors,
			"costs": costs,
			"project": langsmith_manager.project_name,
		}

	except Exception as e:
		logger.error("Failed to get LangSmith metrics", error=str(e))
		return {"enabled": True, "error": str(e)}


# Convenience functions for common tracing patterns
@trace_ai_operation("contract_analysis", "chain")
async def trace_contract_analysis(func):
	"""Trace job application tracking operations."""
	return await func()


@trace_ai_operation("document_processing", "tool")
async def trace_document_processing(func):
	"""Trace document processing operations."""
	return await func()


@trace_ai_operation("clause_extraction", "llm")
async def trace_clause_extraction(func):
	"""Trace clause extraction operations."""
	return await func()


@trace_ai_operation("risk_assessment", "chain")
async def trace_risk_assessment(func):
	"""Trace risk assessment operations."""
	return await func()
