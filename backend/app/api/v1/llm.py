"""
Enhanced LLM Manager API endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.llm_service import LLMService, TaskType, RoutingCriteria, get_llm_service
from ...core.dependencies import get_current_user
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/enhanced-llm", tags=["Enhanced LLM"])


class CompletionRequest(BaseModel):
	"""Request model for LLM completion."""

	prompt: str = Field(..., description="Input prompt for completion")
	task_type: TaskType = Field(default=TaskType.GENERAL, description="Type of task")
	routing_criteria: RoutingCriteria = Field(default=RoutingCriteria.COST, description="Provider selection criteria")
	preferred_provider: Optional[str] = Field(default=None, description="Preferred provider ID")
	fallback_enabled: bool = Field(default=True, description="Enable fallback to other providers")
	max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
	temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Temperature override")
	max_tokens: Optional[int] = Field(default=None, ge=1, le=8000, description="Max tokens override")


class CompletionResponse(BaseModel):
	"""Response model for LLM completion."""

	content: str
	provider: str
	model_used: str
	confidence_score: float
	processing_time: float
	token_usage: Dict[str, int]
	cost: float
	complexity_used: str
	cost_category: str
	budget_impact: Dict[str, Any]
	metadata: Dict[str, Any]
	performance_metrics: Optional[Dict[str, Any]] = None
	is_streaming: bool = False
	streaming_session_id: Optional[str] = None
	token_optimization: Optional[Dict[str, Any]] = None


class ProviderHealthResponse(BaseModel):
	"""Response model for provider health check."""

	provider_id: str
	healthy: bool
	last_checked: str


@router.post("/completion", response_model=CompletionResponse)
async def generate_completion(
	request: CompletionRequest, current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)
):
	"""
	Generate completion using enhanced LLM manager with intelligent routing.

	This endpoint provides:
	- Intelligent provider selection based on task type and criteria
	- Automatic fallback to alternative providers
	- Cost optimization and performance monitoring
	- Circuit breaker protection
	"""
	try:
		logger.info(
			f"Generating completion for user {current_user.get('user_id')} with task type {request.task_type} and criteria {request.routing_criteria}"
		)

		# Prepare kwargs for completion
		kwargs = {}
		if request.temperature is not None:
			kwargs["temperature"] = request.temperature
		if request.max_tokens is not None:
			kwargs["max_tokens"] = request.max_tokens

		# Generate completion
		response = await llm_manager.get_completion(
			prompt=request.prompt,
			task_type=request.task_type,
			routing_criteria=request.routing_criteria,
			preferred_provider=request.preferred_provider,
			fallback_enabled=request.fallback_enabled,
			max_retries=request.max_retries,
			**kwargs,
		)

		logger.info(
			f"Completion generated successfully: {response.provider.value} "
			f"({response.processing_time:.2f}s, confidence: {response.confidence_score:.2f})"
		)

		return CompletionResponse(
			content=response.content,
			provider=response.provider.value,
			model_used=response.model_used,
			confidence_score=response.confidence_score,
			processing_time=response.processing_time,
			token_usage=response.token_usage,
			cost=response.cost,
			complexity_used=response.complexity_used.value,
			cost_category=response.cost_category.value,
			budget_impact=response.budget_impact,
			metadata=response.metadata,
			performance_metrics=response.performance_metrics,
			is_streaming=response.is_streaming,
			streaming_session_id=response.streaming_session_id,
			token_optimization=response.token_optimization,
		)

	except Exception as e:
		logger.error(f"Failed to generate completion: {e}")
		raise HTTPException(status_code=500, detail=f"Completion generation failed: {e!s}")


@router.get("/providers", response_model=Dict[str, List[str]])
async def get_available_providers(current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)):
	"""Get list of available LLM providers."""
	try:
		providers = llm_manager.get_available_models()
		logger.info(f"Retrieved {sum(len(v) for v in providers.values())} available models across types")
		return providers

	except Exception as e:
		logger.error(f"Failed to get available providers: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get providers: {e!s}")


@router.get("/providers/{provider_id}", response_model=Dict[str, Any])
async def get_provider_info(provider_id: str, current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)):
	"""Get detailed information about a specific provider."""
	try:
		# LLMService does not have a direct get_provider_info.
		# We need to iterate through models to find matching provider_id.
		all_models_config = llm_manager.models
		info = None
		for model_type, model_configs in all_models_config.items():
			for model_config in model_configs:
				if model_config.provider.value == provider_id:
					info = {
						"provider_id": model_config.provider.value,
						"model_name": model_config.model_name,
						"temperature": model_config.temperature,
						"max_tokens": model_config.max_tokens,
						"cost_per_token": model_config.cost_per_token,
						"capabilities": model_config.capabilities,
						"priority": model_config.priority,
						"complexity_level": model_config.complexity_level.value,
						"tokens_per_minute": model_config.tokens_per_minute,
						"requests_per_minute": model_config.requests_per_minute,
					}
					break
			if info:
				break

		if not info:
			raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

		return info

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get provider info for {provider_id}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get provider info: {e!s}")


@router.get("/providers/{provider_id}/metrics", response_model=Dict[str, Any])
async def get_provider_metrics(provider_id: str, current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)):
	"""Get performance metrics for a specific provider."""
	try:
		health = llm_manager.get_service_health()
		if provider_id not in health:
			raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

		return health[provider_id]

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get metrics for {provider_id}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e!s}")


@router.get("/health", response_model=Dict[str, Any])
async def check_provider_health(current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)):
	"""Check health status of all providers."""
	try:
		health_results = llm_manager.get_service_health()

		logger.info(f"Health check completed for {len(health_results)} providers")
		return health_results

	except Exception as e:
		logger.error(f"Failed to check provider health: {e}")
		raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


@router.get("/best-provider", response_model=Dict[str, Any])
async def get_best_provider(
	task_type: TaskType = Query(default=TaskType.GENERAL, description="Task type"),
	criteria: RoutingCriteria = Query(default=RoutingCriteria.COST, description="Selection criteria"),
	current_user: dict = Depends(get_current_user),
	llm_manager: LLMService = Depends(get_llm_service),
):
	"""Get the best provider for a specific task type and criteria."""
	try:
		# LLMService does not have a direct get_best_provider method.
		# We will select models and return the first one as the 'best'.
		suitable_models = await llm_manager._select_models(
			task_type, llm_manager.complexity_analyzer.analyze_task_complexity(task_type.value), criteria
		)

		if not suitable_models:
			raise HTTPException(status_code=404, detail=f"No suitable provider found for task type {task_type} with criteria {criteria}")

		best_model_config = suitable_models[0]

		return {
			"best_provider": best_model_config.provider.value,
			"model_name": best_model_config.model_name,
			"task_type": task_type.value,
			"criteria": criteria.value,
			"cost_per_token": best_model_config.cost_per_token,
			"priority": best_model_config.priority,
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get best provider: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get best provider: {e!s}")

	llm_manager: LLMService = Depends(get_llm_service)
	"""Clear LLM response cache."""
	try:
		await llm_manager.clear_cache()
		logger.info(f"Cache cleared by user {current_user.get('user_id')}")

		return {"message": "Cache cleared successfully"}

	except Exception as e:
		logger.error(f"Failed to clear cache: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e!s}")


@router.get("/task-types")
async def get_task_types(current_user: dict = Depends(get_current_user)):
	"""Get available task types for routing."""
	return {
		"task_types": [task_type.value for task_type in TaskType],
		"descriptions": {
			TaskType.CONTRACT_ANALYSIS.value: "Complex job application tracking requiring high accuracy",
			TaskType.RISK_ASSESSMENT.value: "Risk evaluation and scoring tasks",
			TaskType.LEGAL_PRECEDENT.value: "Legal precedent research and analysis",
			TaskType.NEGOTIATION.value: "Contract negotiation strategy and communication",
			TaskType.COMMUNICATION.value: "General communication and correspondence",
			TaskType.GENERAL.value: "General purpose tasks",
		},
	}


@router.get("/routing-criteria")
async def get_routing_criteria(current_user: dict = Depends(get_current_user)):
	"""Get available routing criteria for provider selection."""
	return {
		"criteria": [criteria.value for criteria in RoutingCriteria],
		"descriptions": {
			RoutingCriteria.COST.value: "Optimize for lowest cost per token",
			RoutingCriteria.PERFORMANCE.value: "Optimize for fastest response time",
			RoutingCriteria.QUALITY.value: "Optimize for highest quality results",
			RoutingCriteria.SPEED.value: "Optimize for fastest processing",
			RoutingCriteria.AVAILABILITY.value: "Optimize for highest availability",
		},
	}


@router.get("/metrics/summary")
async def get_metrics_summary(current_user: dict = Depends(get_current_user), llm_manager: LLMService = Depends(get_llm_service)):
	"""Get summary of all provider metrics."""
	try:
		health_summary = llm_manager.get_service_health()

		# You would need to aggregate these metrics from the health_summary
		# For now, returning the raw health summary
		return health_summary

	except Exception as e:
		logger.error(f"Failed to get metrics summary: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {e!s}")


# Import datetime for health check response
