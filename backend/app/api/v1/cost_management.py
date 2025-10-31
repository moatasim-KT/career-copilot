"""
Cost management API endpoints for LLM usage tracking and budget management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.cost_tracker import CostCategory, BudgetPeriod, BudgetLimit, get_cost_tracker
from ...core.task_complexity import TaskComplexity, get_complexity_analyzer
from ...services.ai_service_manager import ModelType, get_ai_service_manager
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cost-management", tags=["cost-management"])

cost_tracker = get_cost_tracker()
complexity_analyzer = get_complexity_analyzer()
ai_service_manager = get_ai_service_manager()


class CostEstimateRequest(BaseModel):
	"""Request for cost estimation."""

	model_type: ModelType
	prompt: str
	context: Optional[str] = None


class ComplexityAnalysisRequest(BaseModel):
	"""Request for complexity analysis."""

	prompt: str
	context: Optional[str] = None


class BudgetLimitRequest(BaseModel):
	"""Request to create/update budget limit."""

	category: Optional[CostCategory] = None
	period: BudgetPeriod
	limit: float = Field(..., gt=0, description="Budget limit in USD")
	user_id: Optional[str] = None
	alert_threshold: float = Field(0.8, ge=0.0, le=1.0)
	hard_limit: bool = True


class ModelOptimizationRequest(BaseModel):
	"""Request for model optimization."""

	model_type: ModelType
	prompt: str
	context: Optional[str] = None
	budget_constraint: Optional[float] = Field(None, gt=0)
	quality_threshold: Optional[float] = Field(None, gt=0)


@router.post("/estimate-cost")
async def estimate_cost(request: CostEstimateRequest) -> Dict[str, Any]:
	"""
	Estimate cost for an LLM request without executing it.

	Returns cost estimates for all suitable models.
	"""
	try:
		estimate = await ai_service_manager.get_cost_estimate(model_type=request.model_type, prompt=request.prompt, context=request.context)
		return estimate
	except Exception as e:
		logger.error(f"Cost estimation failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-complexity")
async def analyze_complexity(request: ComplexityAnalysisRequest) -> Dict[str, Any]:
	"""
	Analyze task complexity for different model types.

	Returns complexity analysis and recommended providers.
	"""
	try:
		analysis = await ai_service_manager.get_complexity_analysis(prompt=request.prompt, context=request.context)
		return analysis
	except Exception as e:
		logger.error(f"Complexity analysis failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget-status")
async def get_budget_status(user_id: Optional[str] = Query(None, description="User ID for user-specific budgets")) -> Dict[str, Any]:
	"""
	Get current budget status for all applicable budget limits.
	"""
	try:
		status = await ai_service_manager.get_budget_status(user_id=user_id)
		return status
	except Exception as e:
		logger.error(f"Budget status retrieval failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget-limits")
async def create_budget_limit(request: BudgetLimitRequest) -> Dict[str, str]:
	"""
	Create a new budget limit.
	"""
	try:
		budget_limit = BudgetLimit(
			category=request.category,
			period=request.period,
			limit=Decimal(str(request.limit)),
			user_id=request.user_id,
			alert_threshold=request.alert_threshold,
			hard_limit=request.hard_limit,
		)

		cost_tracker.add_budget_limit(budget_limit)

		return {
			"message": "Budget limit created successfully",
			"category": request.category.value if request.category else "all",
			"period": request.period.value,
			"limit": str(request.limit),
		}
	except Exception as e:
		logger.error(f"Budget limit creation failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.delete("/budget-limits")
async def remove_budget_limit(
	period: BudgetPeriod, category: Optional[CostCategory] = Query(None), user_id: Optional[str] = Query(None)
) -> Dict[str, str]:
	"""
	Remove a budget limit.
	"""
	try:
		cost_tracker.remove_budget_limit(category=category, period=period, user_id=user_id)

		return {"message": "Budget limit removed successfully", "category": category.value if category else "all", "period": period.value}
	except Exception as e:
		logger.error(f"Budget limit removal failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-summary")
async def get_cost_summary(
	start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
	end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
	category: Optional[CostCategory] = Query(None, description="Filter by category"),
	user_id: Optional[str] = Query(None, description="Filter by user ID"),
) -> Dict[str, Any]:
	"""
	Get cost summary for specified period and filters.
	"""
	try:
		summary = await cost_tracker.get_cost_summary(start_date=start_date, end_date=end_date, category=category, user_id=user_id)
		return summary
	except Exception as e:
		logger.error(f"Cost summary retrieval failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-model-selection")
async def optimize_model_selection(request: ModelOptimizationRequest) -> Dict[str, Any]:
	"""
	Optimize model selection based on constraints.

	Returns the most cost-effective model that meets quality and budget constraints.
	"""
	try:
		optimization = await ai_service_manager.optimize_model_selection(
			model_type=request.model_type,
			prompt=request.prompt,
			context=request.context,
			budget_constraint=request.budget_constraint,
			quality_threshold=request.quality_threshold,
		)
		return optimization
	except Exception as e:
		logger.error(f"Model optimization failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-models")
async def get_available_models() -> Dict[str, List[str]]:
	"""
	Get list of available models by type.
	"""
	try:
		models = ai_service_manager.get_available_models()
		return models
	except Exception as e:
		logger.error(f"Available models retrieval failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/service-health")
async def get_service_health() -> Dict[str, Any]:
	"""
	Get health status of AI services and circuit breakers.
	"""
	try:
		health = ai_service_manager.get_service_health()
		return health
	except Exception as e:
		logger.error(f"Service health check failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def clear_cache() -> Dict[str, str]:
	"""
	Clear AI response cache.
	"""
	try:
		ai_service_manager.clear_cache()
		return {"message": "Cache cleared successfully"}
	except Exception as e:
		logger.error(f"Cache clearing failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/complexity-levels")
async def get_complexity_levels() -> Dict[str, Any]:
	"""
	Get information about task complexity levels and their characteristics.
	"""
	return {
		"complexity_levels": {
			TaskComplexity.SIMPLE.value: {
				"description": "Simple tasks suitable for cost-effective models",
				"recommended_providers": complexity_analyzer.get_recommended_providers(TaskComplexity.SIMPLE),
				"cost_multiplier": complexity_analyzer.estimate_cost_multiplier(TaskComplexity.SIMPLE),
			},
			TaskComplexity.MEDIUM.value: {
				"description": "Medium complexity tasks requiring balanced models",
				"recommended_providers": complexity_analyzer.get_recommended_providers(TaskComplexity.MEDIUM),
				"cost_multiplier": complexity_analyzer.estimate_cost_multiplier(TaskComplexity.MEDIUM),
			},
			TaskComplexity.COMPLEX.value: {
				"description": "Complex tasks requiring high-capability models",
				"recommended_providers": complexity_analyzer.get_recommended_providers(TaskComplexity.COMPLEX),
				"cost_multiplier": complexity_analyzer.estimate_cost_multiplier(TaskComplexity.COMPLEX),
			},
		},
		"cost_categories": [category.value for category in CostCategory],
		"budget_periods": [period.value for period in BudgetPeriod],
		"model_types": [model_type.value for model_type in ModelType],
	}
