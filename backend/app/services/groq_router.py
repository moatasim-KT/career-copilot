"""
GROQ Model Selection and Routing Logic
Provides intelligent model selection and routing for GROQ API based on
task requirements, performance metrics, and cost optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from .groq_service import GROQModel, GROQTaskType, GROQService
from ..core.logging import get_logger
from .cache_service import get_cache_service

logger = get_logger(__name__)
cache_service = get_cache_service()


class RoutingStrategy(str, Enum):
	"""GROQ routing strategies."""

	PERFORMANCE_BASED = "performance_based"
	COST_OPTIMIZED = "cost_optimized"
	QUALITY_FOCUSED = "quality_focused"
	LOAD_BALANCED = "load_balanced"
	ADAPTIVE = "adaptive"
	ROUND_ROBIN = "round_robin"


class ModelCapability(str, Enum):
	"""Model capabilities for routing decisions."""

	FAST_INFERENCE = "fast_inference"
	HIGH_QUALITY = "high_quality"
	LARGE_CONTEXT = "large_context"
	CODE_GENERATION = "code_generation"
	REASONING = "reasoning"
	CONVERSATION = "conversation"
	ANALYSIS = "analysis"
	SUMMARIZATION = "summarization"


@dataclass
class RoutingRule:
	"""Rule for model routing."""

	task_type: GROQTaskType
	required_capabilities: List[ModelCapability]
	preferred_models: List[GROQModel]
	fallback_models: List[GROQModel]
	min_quality_score: float = 0.7
	max_cost_per_token: float = 0.001
	max_response_time: float = 10.0
	priority: int = 1
	conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformanceMetrics:
	"""Performance metrics for model routing."""

	model: GROQModel
	task_type: GROQTaskType
	avg_response_time: float = 0.0
	avg_quality_score: float = 0.0
	avg_cost: float = 0.0
	success_rate: float = 1.0
	total_requests: int = 0
	recent_performance: List[float] = field(default_factory=list)
	last_updated: datetime = field(default_factory=datetime.now)
	availability_score: float = 1.0
	load_score: float = 0.0


@dataclass
class RoutingDecision:
	"""Result of routing decision."""

	selected_model: GROQModel
	confidence: float
	reasoning: str
	alternatives: List[GROQModel]
	estimated_cost: float
	estimated_time: float
	routing_strategy: RoutingStrategy
	metadata: Dict[str, Any] = field(default_factory=dict)


class GROQModelRouter:
	"""Intelligent GROQ model router."""

	def __init__(self, groq_service: GROQService):
		"""Initialize GROQ model router."""
		self.groq_service = groq_service
		self.routing_rules = self._initialize_routing_rules()
		self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
		self.load_balancer_state: Dict[GROQModel, int] = {model: 0 for model in GROQModel}
		self.circuit_breakers: Dict[GROQModel, Dict[str, Any]] = {}

		# Initialize performance tracking
		self._initialize_performance_tracking()

		logger.info("GROQ model router initialized")

	def _initialize_routing_rules(self) -> List[RoutingRule]:
		"""Initialize routing rules for different task types."""
		return [
			# Contract Analysis - High quality required
			RoutingRule(
				task_type=GROQTaskType.FAST_ANALYSIS,
				required_capabilities=[ModelCapability.ANALYSIS, ModelCapability.REASONING],
				preferred_models=[GROQModel.LLAMA3_8B, GROQModel.LLAMA3_70B],
				fallback_models=[GROQModel.LLAMA3_8B, GROQModel.LLAMA3_70B],
				min_quality_score=0.85,
				max_cost_per_token=0.0005,
				max_response_time=5.0,
				priority=1,
			),
			# Code Generation - Precision and context important
			RoutingRule(
				task_type=GROQTaskType.CODE_GENERATION,
				required_capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
				preferred_models=[GROQModel.LLAMA3_8B, GROQModel.LLAMA3_70B],
				fallback_models=[GROQModel.LLAMA3_8B],
				min_quality_score=0.8,
				max_cost_per_token=0.0007,
				max_response_time=8.0,
				priority=1,
			),
			# Reasoning Tasks - Quality over speed
			RoutingRule(
				task_type=GROQTaskType.REASONING,
				required_capabilities=[ModelCapability.REASONING, ModelCapability.HIGH_QUALITY],
				preferred_models=[GROQModel.LLAMA3_70B, GROQModel.LLAMA3_8B],
				fallback_models=[GROQModel.LLAMA3_70B, GROQModel.LLAMA3_8B],
				min_quality_score=0.85,
				max_cost_per_token=0.001,
				max_response_time=10.0,
				priority=1,
			),
			# Conversation - Speed and naturalness
			RoutingRule(
				task_type=GROQTaskType.CONVERSATION,
				required_capabilities=[ModelCapability.CONVERSATION, ModelCapability.FAST_INFERENCE],
				preferred_models=[GROQModel.LLAMA3_8B, GROQModel.GEMMA_7B],
				fallback_models=[GROQModel.LLAMA3_70B, GROQModel.LLAMA3_8B],
				min_quality_score=0.7,
				max_cost_per_token=0.0001,
				max_response_time=3.0,
				priority=2,
			),
			# Summarization - Efficiency focused
			RoutingRule(
				task_type=GROQTaskType.SUMMARIZATION,
				required_capabilities=[ModelCapability.SUMMARIZATION, ModelCapability.FAST_INFERENCE],
				preferred_models=[GROQModel.LLAMA3_8B, GROQModel.GEMMA_7B],
				fallback_models=[GROQModel.LLAMA3_70B, GROQModel.LLAMA3_8B],
				min_quality_score=0.75,
				max_cost_per_token=0.0002,
				max_response_time=4.0,
				priority=2,
			),
			# Classification - Speed and accuracy
			RoutingRule(
				task_type=GROQTaskType.CLASSIFICATION,
				required_capabilities=[ModelCapability.FAST_INFERENCE, ModelCapability.ANALYSIS],
				preferred_models=[GROQModel.GEMMA_7B, GROQModel.LLAMA3_8B],
				fallback_models=[GROQModel.LLAMA3_70B],
				min_quality_score=0.8,
				max_cost_per_token=0.0001,
				max_response_time=2.0,
				priority=3,
			),
			# Translation - Quality and context
			RoutingRule(
				task_type=GROQTaskType.TRANSLATION,
				required_capabilities=[ModelCapability.CONVERSATION, ModelCapability.HIGH_QUALITY],
				preferred_models=[GROQModel.LLAMA3_70B, GROQModel.LLAMA3_8B],
				fallback_models=[GROQModel.LLAMA3_8B, GROQModel.GEMMA_7B],
				min_quality_score=0.8,
				max_cost_per_token=0.0005,
				max_response_time=6.0,
				priority=2,
			),
		]

	def _initialize_performance_tracking(self):
		"""Initialize performance tracking for all models and tasks."""
		for model in GROQModel:
			for task_type in GROQTaskType:
				key = f"{model.value}:{task_type.value}"
				self.performance_metrics[key] = ModelPerformanceMetrics(model=model, task_type=task_type)

			# Initialize circuit breaker
			self.circuit_breakers[model] = {
				"state": "closed",  # closed, open, half-open
				"failure_count": 0,
				"last_failure": None,
				"failure_threshold": 5,
				"recovery_timeout": 60,
			}

	async def select_model(
		self,
		task_type: GROQTaskType,
		strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
		context: Optional[Dict[str, Any]] = None,
		constraints: Optional[Dict[str, Any]] = None,
	) -> RoutingDecision:
		"""Select optimal model for the given task and constraints."""
		context = context or {}
		constraints = constraints or {}

		# Get applicable routing rule
		routing_rule = self._get_routing_rule(task_type)
		if not routing_rule:
			# Fallback to default selection
			return await self._default_model_selection(task_type, strategy)

		# Get candidate models
		candidate_models = self._get_candidate_models(routing_rule, constraints)

		if not candidate_models:
			raise ValueError(f"No suitable models available for task type: {task_type}")

		# Apply routing strategy
		if strategy == RoutingStrategy.PERFORMANCE_BASED:
			decision = await self._performance_based_routing(candidate_models, task_type, routing_rule)
		elif strategy == RoutingStrategy.COST_OPTIMIZED:
			decision = await self._cost_optimized_routing(candidate_models, task_type, routing_rule)
		elif strategy == RoutingStrategy.QUALITY_FOCUSED:
			decision = await self._quality_focused_routing(candidate_models, task_type, routing_rule)
		elif strategy == RoutingStrategy.LOAD_BALANCED:
			decision = await self._load_balanced_routing(candidate_models, task_type, routing_rule)
		elif strategy == RoutingStrategy.ROUND_ROBIN:
			decision = await self._round_robin_routing(candidate_models, task_type, routing_rule)
		else:  # ADAPTIVE
			decision = await self._adaptive_routing(candidate_models, task_type, routing_rule, context)

		# Update load balancer state
		self.load_balancer_state[decision.selected_model] += 1

		logger.info(
			f"Selected model {decision.selected_model.value} for {task_type.value} "
			f"using {strategy.value} strategy (confidence: {decision.confidence:.2f})"
		)

		return decision

	def _get_routing_rule(self, task_type: GROQTaskType) -> Optional[RoutingRule]:
		"""Get routing rule for task type."""
		for rule in self.routing_rules:
			if rule.task_type == task_type:
				return rule
		return None

	def _get_candidate_models(self, routing_rule: RoutingRule, constraints: Dict[str, Any]) -> List[GROQModel]:
		"""Get candidate models based on routing rule and constraints."""
		candidates = []

		# Start with preferred models
		for model in routing_rule.preferred_models:
			if self._is_model_available(model, routing_rule, constraints):
				candidates.append(model)

		# Add fallback models if needed
		if len(candidates) < 2:  # Ensure we have alternatives
			for model in routing_rule.fallback_models:
				if model not in candidates and self._is_model_available(model, routing_rule, constraints):
					candidates.append(model)

		return candidates

	def _is_model_available(self, model: GROQModel, routing_rule: RoutingRule, constraints: Dict[str, Any]) -> bool:
		"""Check if model is available and meets constraints."""
		# Check if model is enabled
		model_config = self.groq_service.model_configs.get(model)
		if not model_config or not model_config.enabled:
			return False

		# Check circuit breaker
		circuit_breaker = self.circuit_breakers.get(model, {})
		if circuit_breaker.get("state") == "open":
			last_failure = circuit_breaker.get("last_failure")
			if last_failure:
				time_since_failure = (datetime.now() - last_failure).total_seconds()
				if time_since_failure < circuit_breaker.get("recovery_timeout", 60):
					return False
				else:
					# Try to recover
					circuit_breaker["state"] = "half-open"

		# Check cost constraints
		max_cost = constraints.get("max_cost_per_token", routing_rule.max_cost_per_token)
		if model_config.cost_per_token > max_cost:
			return False

		# Check performance constraints
		key = f"{model.value}:{routing_rule.task_type.value}"
		metrics = self.performance_metrics.get(key)
		if metrics:
			if metrics.avg_response_time > routing_rule.max_response_time or metrics.avg_quality_score < routing_rule.min_quality_score:
				return False

		return True

	async def _performance_based_routing(self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule) -> RoutingDecision:
		"""Route based on performance metrics."""
		best_model = candidates[0]
		best_score = 0.0

		for model in candidates:
			key = f"{model.value}:{task_type.value}"
			metrics = self.performance_metrics.get(key)

			if metrics and metrics.total_requests > 0:
				# Calculate performance score (lower response time = higher score)
				time_score = max(0, (10.0 - metrics.avg_response_time) / 10.0)
				success_score = metrics.success_rate
				availability_score = metrics.availability_score

				total_score = time_score * 0.4 + success_score * 0.4 + availability_score * 0.2
			else:
				# Use model config defaults
				model_config = self.groq_service.model_configs[model]
				total_score = model_config.speed_score

			if total_score > best_score:
				best_score = total_score
				best_model = model

		return RoutingDecision(
			selected_model=best_model,
			confidence=best_score,
			reasoning="Selected based on performance metrics",
			alternatives=[m for m in candidates if m != best_model],
			estimated_cost=self.groq_service.model_configs[best_model].cost_per_token * 1000,
			estimated_time=self.performance_metrics.get(
				f"{best_model.value}:{task_type.value}", ModelPerformanceMetrics(best_model, task_type)
			).avg_response_time
			or 2.0,
			routing_strategy=RoutingStrategy.PERFORMANCE_BASED,
		)

	async def _cost_optimized_routing(self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule) -> RoutingDecision:
		"""Route based on cost optimization."""
		# Sort by cost per token
		candidates_with_cost = [(model, self.groq_service.model_configs[model].cost_per_token) for model in candidates]
		candidates_with_cost.sort(key=lambda x: x[1])

		selected_model = candidates_with_cost[0][0]
		selected_cost = candidates_with_cost[0][1]

		return RoutingDecision(
			selected_model=selected_model,
			confidence=0.9,  # High confidence for cost-based decisions
			reasoning=f"Selected cheapest model at ${selected_cost:.8f} per token",
			alternatives=[m for m, _ in candidates_with_cost[1:]],
			estimated_cost=selected_cost * 1000,
			estimated_time=self.performance_metrics.get(
				f"{selected_model.value}:{task_type.value}", ModelPerformanceMetrics(selected_model, task_type)
			).avg_response_time
			or 3.0,
			routing_strategy=RoutingStrategy.COST_OPTIMIZED,
		)

	async def _quality_focused_routing(self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule) -> RoutingDecision:
		"""Route based on quality metrics."""
		best_model = candidates[0]
		best_quality = 0.0

		for model in candidates:
			key = f"{model.value}:{task_type.value}"
			metrics = self.performance_metrics.get(key)

			if metrics and metrics.total_requests > 0:
				quality_score = metrics.avg_quality_score
			else:
				# Use model config defaults
				model_config = self.groq_service.model_configs[model]
				quality_score = model_config.quality_score

			if quality_score > best_quality:
				best_quality = quality_score
				best_model = model

		return RoutingDecision(
			selected_model=best_model,
			confidence=best_quality,
			reasoning=f"Selected highest quality model (score: {best_quality:.2f})",
			alternatives=[m for m in candidates if m != best_model],
			estimated_cost=self.groq_service.model_configs[best_model].cost_per_token * 1000,
			estimated_time=self.performance_metrics.get(
				f"{best_model.value}:{task_type.value}", ModelPerformanceMetrics(best_model, task_type)
			).avg_response_time
			or 4.0,
			routing_strategy=RoutingStrategy.QUALITY_FOCUSED,
		)

	async def _load_balanced_routing(self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule) -> RoutingDecision:
		"""Route based on load balancing."""
		# Select model with lowest current load
		candidates_with_load = [(model, self.load_balancer_state.get(model, 0)) for model in candidates]
		candidates_with_load.sort(key=lambda x: x[1])

		selected_model = candidates_with_load[0][0]
		current_load = candidates_with_load[0][1]

		return RoutingDecision(
			selected_model=selected_model,
			confidence=0.8,
			reasoning=f"Selected model with lowest load ({current_load} requests)",
			alternatives=[m for m, _ in candidates_with_load[1:]],
			estimated_cost=self.groq_service.model_configs[selected_model].cost_per_token * 1000,
			estimated_time=self.performance_metrics.get(
				f"{selected_model.value}:{task_type.value}", ModelPerformanceMetrics(selected_model, task_type)
			).avg_response_time
			or 3.0,
			routing_strategy=RoutingStrategy.LOAD_BALANCED,
		)

	async def _round_robin_routing(self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule) -> RoutingDecision:
		"""Route using round-robin strategy."""
		# Simple round-robin based on total requests
		total_requests = sum(self.load_balancer_state.values())
		selected_index = total_requests % len(candidates)
		selected_model = candidates[selected_index]

		return RoutingDecision(
			selected_model=selected_model,
			confidence=0.7,
			reasoning="Selected using round-robin strategy",
			alternatives=[m for i, m in enumerate(candidates) if i != selected_index],
			estimated_cost=self.groq_service.model_configs[selected_model].cost_per_token * 1000,
			estimated_time=self.performance_metrics.get(
				f"{selected_model.value}:{task_type.value}", ModelPerformanceMetrics(selected_model, task_type)
			).avg_response_time
			or 3.0,
			routing_strategy=RoutingStrategy.ROUND_ROBIN,
		)

	async def _adaptive_routing(
		self, candidates: List[GROQModel], task_type: GROQTaskType, routing_rule: RoutingRule, context: Dict[str, Any]
	) -> RoutingDecision:
		"""Adaptive routing based on multiple factors."""
		scores = {}

		for model in candidates:
			key = f"{model.value}:{task_type.value}"
			metrics = self.performance_metrics.get(key)
			model_config = self.groq_service.model_configs[model]

			# Calculate composite score
			if metrics and metrics.total_requests > 0:
				performance_score = max(0, (5.0 - metrics.avg_response_time) / 5.0)
				quality_score = metrics.avg_quality_score
				cost_score = max(0, (0.001 - model_config.cost_per_token) / 0.001)
				availability_score = metrics.availability_score
			else:
				performance_score = model_config.speed_score
				quality_score = model_config.quality_score
				cost_score = max(0, (0.001 - model_config.cost_per_token) / 0.001)
				availability_score = 1.0

			# Weight based on context
			urgency = context.get("urgency", "normal")
			budget_constraint = context.get("budget_constraint", "normal")
			quality_requirement = context.get("quality_requirement", "normal")

			if urgency == "high":
				weights = [0.5, 0.2, 0.1, 0.2]  # Favor performance
			elif budget_constraint == "strict":
				weights = [0.2, 0.2, 0.5, 0.1]  # Favor cost
			elif quality_requirement == "high":
				weights = [0.2, 0.5, 0.1, 0.2]  # Favor quality
			else:
				weights = [0.3, 0.3, 0.2, 0.2]  # Balanced

			composite_score = performance_score * weights[0] + quality_score * weights[1] + cost_score * weights[2] + availability_score * weights[3]

			scores[model] = composite_score

		# Select best model
		best_model = max(scores.items(), key=lambda x: x[1])[0]
		confidence = scores[best_model]

		return RoutingDecision(
			selected_model=best_model,
			confidence=confidence,
			reasoning="Selected using adaptive multi-factor analysis",
			alternatives=[m for m in candidates if m != best_model],
			estimated_cost=self.groq_service.model_configs[best_model].cost_per_token * 1000,
			estimated_time=self.performance_metrics.get(
				f"{best_model.value}:{task_type.value}", ModelPerformanceMetrics(best_model, task_type)
			).avg_response_time
			or 3.0,
			routing_strategy=RoutingStrategy.ADAPTIVE,
			metadata={"context": context, "scores": {m.value: s for m, s in scores.items()}},
		)

	async def _default_model_selection(self, task_type: GROQTaskType, strategy: RoutingStrategy) -> RoutingDecision:
		"""Fallback model selection when no specific routing rule exists."""
		# Use the service's default model selection
		default_model = await self.groq_service.get_optimal_model(task_type, "balanced")

		return RoutingDecision(
			selected_model=default_model,
			confidence=0.6,
			reasoning="Using default model selection (no specific routing rule)",
			alternatives=[],
			estimated_cost=self.groq_service.model_configs[default_model].cost_per_token * 1000,
			estimated_time=3.0,
			routing_strategy=strategy,
		)

	def record_request_result(
		self, model: GROQModel, task_type: GROQTaskType, response_time: float, quality_score: float, cost: float, success: bool
	):
		"""Record the result of a request for performance tracking."""
		key = f"{model.value}:{task_type.value}"
		metrics = self.performance_metrics.get(key)

		if not metrics:
			metrics = ModelPerformanceMetrics(model=model, task_type=task_type)
			self.performance_metrics[key] = metrics

		# Update metrics
		metrics.total_requests += 1

		if success:
			# Update averages
			if metrics.total_requests == 1:
				metrics.avg_response_time = response_time
				metrics.avg_quality_score = quality_score
				metrics.avg_cost = cost
			else:
				alpha = 0.1  # Exponential moving average factor
				metrics.avg_response_time = (1 - alpha) * metrics.avg_response_time + alpha * response_time
				metrics.avg_quality_score = (1 - alpha) * metrics.avg_quality_score + alpha * quality_score
				metrics.avg_cost = (1 - alpha) * metrics.avg_cost + alpha * cost

			# Update recent performance
			metrics.recent_performance.append(response_time)
			if len(metrics.recent_performance) > 50:  # Keep last 50 measurements
				metrics.recent_performance = metrics.recent_performance[-50:]

			# Reset circuit breaker on success
			circuit_breaker = self.circuit_breakers.get(model, {})
			circuit_breaker["failure_count"] = 0
			circuit_breaker["state"] = "closed"
		else:
			# Handle failure
			circuit_breaker = self.circuit_breakers.get(model, {})
			circuit_breaker["failure_count"] = circuit_breaker.get("failure_count", 0) + 1
			circuit_breaker["last_failure"] = datetime.now()

			if circuit_breaker["failure_count"] >= circuit_breaker.get("failure_threshold", 5):
				circuit_breaker["state"] = "open"

		# Update success rate
		successful_requests = metrics.total_requests - circuit_breaker.get("failure_count", 0)
		metrics.success_rate = successful_requests / metrics.total_requests

		# Update availability score (simplified)
		metrics.availability_score = min(1.0, metrics.success_rate + 0.1)

		metrics.last_updated = datetime.now()

	def get_routing_statistics(self) -> Dict[str, Any]:
		"""Get comprehensive routing statistics."""
		stats = {
			"total_models": len(GROQModel),
			"active_models": len([m for m in GROQModel if self.groq_service.model_configs[m].enabled]),
			"routing_rules": len(self.routing_rules),
			"load_balancer_state": {m.value: load for m, load in self.load_balancer_state.items()},
			"circuit_breaker_states": {m.value: cb.get("state", "closed") for m, cb in self.circuit_breakers.items()},
			"performance_metrics": {},
		}

		# Add performance metrics
		for key, metrics in self.performance_metrics.items():
			if metrics.total_requests > 0:
				stats["performance_metrics"][key] = {
					"total_requests": metrics.total_requests,
					"avg_response_time": round(metrics.avg_response_time, 3),
					"avg_quality_score": round(metrics.avg_quality_score, 3),
					"avg_cost": round(metrics.avg_cost, 6),
					"success_rate": round(metrics.success_rate, 3),
					"availability_score": round(metrics.availability_score, 3),
				}

		return stats

	async def reset_routing_metrics(self):
		"""Reset all routing metrics."""
		self.performance_metrics.clear()
		self.load_balancer_state = {model: 0 for model in GROQModel}
		self.circuit_breakers = {}
		self._initialize_performance_tracking()
		logger.info("GROQ routing metrics reset")


# Global instance
_groq_router = None


def get_groq_router() -> GROQModelRouter:
	"""Get global GROQ router instance."""
	global _groq_router
	if _groq_router is None:
		from .groq_service import get_groq_service

		_groq_router = GROQModelRouter(get_groq_service())
	return _groq_router
