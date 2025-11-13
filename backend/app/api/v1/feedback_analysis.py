"""
from ...services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

Feedback analysis and model improvement API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.dependencies import get_current_user, get_admin_user
from app.models.user import User
from app.services.feedback_analysis_service import FeedbackAnalysisService
from app.services.job_recommendation_service import JobRecommendationService

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


class WeightAdjustmentRequest(BaseModel):
	"""Schema for algorithm weight adjustment requests"""

	skill_matching: float = Field(..., ge=0, le=100)
	location_matching: float = Field(..., ge=0, le=100)
	experience_matching: float = Field(..., ge=0, le=100)

	def __init__(self, **data):
		super().__init__(**data)
		# Validate weights sum to 100
		total = self.skill_matching + self.location_matching + self.experience_matching
		if abs(total - 100) > 0.1:
			raise ValueError(f"Weights must sum to 100, got {total}")


class ABTestRequest(BaseModel):
	"""Schema for A/B test creation requests"""

	test_name: str = Field(..., min_length=1, max_length=100)
	variant_a_weights: WeightAdjustmentRequest
	variant_b_weights: WeightAdjustmentRequest
	traffic_split: float = Field(0.5, ge=0.1, le=0.9)
	description: Optional[str] = Field(None, max_length=500)


@router.get("/feedback-analysis")
async def get_feedback_analysis(
	days_back: int = Query(30, ge=1, le=365),
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Get comprehensive feedback analysis for pattern recognition
	Admin endpoint for analyzing user feedback patterns
	"""
	analysis_service = FeedbackAnalysisService(db)
	analysis = analysis_service.analyze_feedback_patterns(days_back)

	return {"status": "success", "data": analysis}


@router.get("/algorithm-suggestions")
async def get_algorithm_suggestions(
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Get algorithm weight adjustment suggestions based on feedback analysis
	"""
	analysis_service = FeedbackAnalysisService(db)
	suggestions = analysis_service.get_algorithm_adjustment_suggestions()

	return {"status": "success", "data": suggestions}


@router.post("/apply-algorithm-adjustments")
async def apply_algorithm_adjustments(
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Apply algorithm adjustments based on feedback analysis
	This will either update weights directly (high confidence) or start an A/B test (low confidence)
	"""
	engine = JobRecommendationService(db)
	result = engine.apply_feedback_insights()

	return {"status": "success", "data": result}


@router.post("/algorithm-weights")
async def update_algorithm_weights(
	weights: WeightAdjustmentRequest,
	test_name: Optional[str] = Query(None),
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Manually update algorithm weights
	"""
	engine = JobRecommendationService(db)

	weight_dict = {
		"skill_matching": weights.skill_matching,
		"location_matching": weights.location_matching,
		"experience_matching": weights.experience_matching,
	}

	try:
		engine.update_algorithm_weights(weight_dict, test_name)
		return {
			"status": "success",
			"message": f"Algorithm weights updated {'for test ' + test_name if test_name else 'globally'}",
			"weights": weight_dict,
		}
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/ab-tests")
async def create_ab_test(
	test_request: ABTestRequest,
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Create a new A/B test for algorithm improvements
	"""
	engine = JobRecommendationService(db)

	variant_a_dict = {
		"skill_matching": test_request.variant_a_weights.skill_matching,
		"location_matching": test_request.variant_a_weights.location_matching,
		"experience_matching": test_request.variant_a_weights.experience_matching,
	}

	variant_b_dict = {
		"skill_matching": test_request.variant_b_weights.skill_matching,
		"location_matching": test_request.variant_b_weights.location_matching,
		"experience_matching": test_request.variant_b_weights.experience_matching,
	}

	try:
		engine.start_ab_test(test_request.test_name, variant_a_dict, variant_b_dict, test_request.traffic_split)

		return {
			"status": "success",
			"message": f"A/B test '{test_request.test_name}' started",
			"test_config": {
				"test_name": test_request.test_name,
				"variant_a": variant_a_dict,
				"variant_b": variant_b_dict,
				"traffic_split": test_request.traffic_split,
				"description": test_request.description,
			},
		}
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ab-tests")
async def list_ab_tests(
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	List all A/B tests and their configurations
	"""
	engine = JobRecommendationService(db)

	return {"status": "success", "data": {"ab_tests": engine.ab_test_configs, "default_weights": engine.default_weights}}


@router.get("/ab-tests/{test_name}/results")
async def get_ab_test_results(
	test_name: str,
	days_back: int = Query(30, ge=1, le=365),
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Get A/B test results and statistical analysis
	"""
	engine = JobRecommendationService(db)

	try:
		results = engine.get_ab_test_results(test_name, days_back)
		return {"status": "success", "data": results}
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/ab-tests/{test_name}/stop")
async def stop_ab_test(
	test_name: str,
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Stop an active A/B test
	"""
	engine = JobRecommendationService(db)
	engine.stop_ab_test(test_name)

	return {"status": "success", "message": f"A/B test '{test_name}' stopped"}


@router.get("/user-algorithm-info")
async def get_user_algorithm_info(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get algorithm information for the current user (for transparency)
	Shows which weights/variant the user is currently receiving
	"""
	engine = JobRecommendationService(db)
	weights = engine.get_algorithm_weights(current_user.id)
	active_variant = engine._get_active_test_variant(current_user.id)

	return {
		"status": "success",
		"data": {
			"user_id": current_user.id,
			"algorithm_weights": weights,
			"active_test_variant": active_variant,
			"explanation": {
				"skill_matching": f"{weights['skill_matching']}% - How much your skills match job requirements",
				"location_matching": f"{weights['location_matching']}% - How well job location matches your preferences",
				"experience_matching": f"{weights['experience_matching']}% - How well job experience level matches yours",
			},
		},
	}


@router.get("/feedback-impact")
async def get_feedback_impact(
	days_back: int = Query(30, ge=1, le=365),
	current_user: User = Depends(get_admin_user),  # Admin only
	db: AsyncSession = Depends(get_db),
):
	"""
	Get feedback impact tracking and reporting
	Shows how user feedback has influenced algorithm improvements
	"""
	analysis_service = FeedbackAnalysisService(db)
	engine = JobRecommendationService(db)

	# Get feedback analysis
	analysis = analysis_service.analyze_feedback_patterns(days_back)

	# Get algorithm suggestions
	suggestions = analysis_service.get_algorithm_adjustment_suggestions()

	# Get current A/B tests
	active_tests = {name: config for name, config in engine.ab_test_configs.items() if config.get("active", False)}

	return {
		"status": "success",
		"data": {
			"feedback_summary": {
				"total_feedback": analysis["total_feedback"],
				"analysis_period_days": days_back,
				"patterns_identified": len(analysis["patterns"]),
				"recommendations_generated": len(analysis["recommendations"]),
			},
			"algorithm_impact": {
				"current_weights": engine.default_weights,
				"suggested_adjustments": suggestions["adjustments"],
				"confidence_score": suggestions["confidence_score"],
				"sample_size": suggestions["sample_size"],
			},
			"active_experiments": {"ab_tests_running": len(active_tests), "tests": active_tests},
			"improvement_recommendations": analysis["recommendations"],
		},
	}
