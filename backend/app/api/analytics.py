"""
Analytics API endpoints for advanced job application tracking features.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..core.langsmith_integration import LangSmithMetrics, get_langsmith_metrics_summary
from ..core.logging import get_logger
from ..core.monitoring import log_audit_event
from ..core.pagination import PaginationParams, create_paginated_response
from ..models.api_models import ErrorResponse
from ..services.analytics_service import AnalysisType, get_analytics_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/analytics/risk-trends", tags=["Analytics"])
async def get_risk_trends(
	request: Request,
	time_period: str = Query(default="30d", description="Time period for analysis (e.g., 7d, 30d, 90d)"),
	contract_types: Optional[List[str]] = Query(default=None, description="Filter by contract types"),
	user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
	"""
	Get risk trend analysis over time.

	Args:
	    time_period: Time period for analysis
	    contract_types: Optional list of contract types to filter
	    user_id: Optional user ID to filter by

	Returns:
	    Risk trend analysis data
	"""
	try:
		analytics_service = get_analytics_service()

		# Log analytics request
		log_audit_event(
			"analysis_request",
			user_id=user_id or "anonymous",
			details={"action": "risk_trend_analysis", "result": "started", "time_period": time_period, "contract_types": contract_types},
		)

		# Get risk trends
		trend_data = await analytics_service.analyze_risk_trends(time_period=time_period, contract_types=contract_types, user_id=user_id)

		# Log successful analysis
		log_audit_event(
			"analysis_complete",
			user_id=user_id or "anonymous",
			details={"action": "risk_trend_analysis", "result": "success", "trend": trend_data.trend.value, "confidence": trend_data.confidence},
		)

		return {
			"period": trend_data.period,
			"average_risk_score": trend_data.average_risk_score,
			"risk_count": trend_data.risk_count,
			"high_risk_percentage": trend_data.high_risk_percentage,
			"trend": trend_data.trend.value,
			"confidence": trend_data.confidence,
			"metadata": trend_data.metadata,
		}

	except Exception as e:
		logger.error(f"Risk trends analysis failed: {e}", exc_info=True)
		log_audit_event(
			"ANALYSIS_ERROR", user_id=user_id or "anonymous", details={"action": "risk_trend_analysis", "result": "failed", **{"error": str(e)}}
		)
		raise HTTPException(status_code=500, detail="Risk trends analysis failed")


@router.get("/analytics/contract-comparison", tags=["Analytics"])
async def compare_contracts(
	request: Request,
	contract_1_id: str = Query(description="First contract ID"),
	contract_2_id: str = Query(description="Second contract ID"),
	comparison_type: str = Query(default="comprehensive", description="Type of comparison"),
):
	"""
	Compare two contracts for similarities and differences.

	Args:
	    contract_1_id: ID of first contract
	    contract_2_id: ID of second contract
	    comparison_type: Type of comparison to perform

	Returns:
	    Contract comparison analysis
	"""
	try:
		analytics_service = get_analytics_service()

		# Log comparison request
		log_audit_event(
			"analysis_request",
			user_id="anonymous",
			details={
				"action": "contract_comparison",
				"result": "started",
				"contract_1_id": contract_1_id,
				"contract_2_id": contract_2_id,
				"comparison_type": comparison_type,
			},
		)

		# Compare contracts
		comparison = await analytics_service.compare_contracts(
			contract_1_id=contract_1_id, contract_2_id=contract_2_id, comparison_type=comparison_type
		)

		# Log successful comparison
		log_audit_event(
			"analysis_complete",
			user_id="anonymous",
			details={
				"action": "contract_comparison",
				"result": "success",
				"similarity_score": comparison.similarity_score,
				"risk_differences_count": len(comparison.risk_differences),
			},
		)

		return {
			"contract_1_id": comparison.contract_1_id,
			"contract_2_id": comparison.contract_2_id,
			"similarity_score": comparison.similarity_score,
			"risk_differences": comparison.risk_differences,
			"clause_differences": comparison.clause_differences,
			"recommendations": comparison.recommendations,
		}

	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		logger.error(f"Contract comparison failed: {e}", exc_info=True)
		log_audit_event("ANALYSIS_ERROR", user_id="anonymous", details={"action": "contract_comparison", "result": "failed", **{"error": str(e)}})
		raise HTTPException(status_code=500, detail="Contract comparison failed")


@router.get("/analytics/compliance-check", tags=["Analytics"])
async def check_compliance(
	request: Request,
	contract_id: str = Query(description="Contract ID to check"),
	regulatory_framework: str = Query(default="general", description="Regulatory framework to check against"),
):
	"""
	Check contract compliance with regulatory framework.

	Args:
	    contract_id: ID of contract to check
	    regulatory_framework: Regulatory framework to check against

	Returns:
	    Compliance analysis report
	"""
	try:
		analytics_service = get_analytics_service()

		# Log compliance check request
		log_audit_event(
			"ANALYSIS_REQUEST",
			user_id="anonymous",
			action="compliance_check",
			result="started",
			details={"contract_id": contract_id, "regulatory_framework": regulatory_framework},
			request=request,
		)

		# Check compliance
		compliance_report = await analytics_service.check_compliance(contract_id=contract_id, regulatory_framework=regulatory_framework)

		# Log successful compliance check
		log_audit_event(
			"ANALYSIS_COMPLETE",
			user_id="anonymous",
			action="compliance_check",
			result="success",
			details={"compliance_score": compliance_report.compliance_score, "violations_count": len(compliance_report.violations)},
			request=request,
		)

		return {
			"contract_id": compliance_report.contract_id,
			"compliance_score": compliance_report.compliance_score,
			"violations": compliance_report.violations,
			"recommendations": compliance_report.recommendations,
			"regulatory_framework": compliance_report.regulatory_framework,
		}

	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		logger.error(f"Compliance check failed: {e}", exc_info=True)
		log_audit_event("ANALYSIS_ERROR", user_id="anonymous", details={"action": "compliance_check", "result": "failed", **{"error": str(e)}})
		raise HTTPException(status_code=500, detail="Compliance check failed")


@router.get("/analytics/cost-analysis", tags=["Analytics"])
async def analyze_costs(
	request: Request,
	time_period: str = Query(default="30d", description="Time period for cost analysis"),
	breakdown_by: str = Query(default="model", description="Breakdown by model, user, or analysis_type"),
):
	"""
	Analyze AI operation costs over time.

	Args:
	    time_period: Time period for analysis
	    breakdown_by: How to breakdown costs (model, user, analysis_type)

	Returns:
	    Cost analysis data
	"""
	try:
		analytics_service = get_analytics_service()

		# Log cost analysis request
		log_audit_event(
			"ANALYSIS_REQUEST",
			user_id="anonymous",
			action="cost_analysis",
			result="started",
			details={"time_period": time_period, "breakdown_by": breakdown_by},
			request=request,
		)

		# Analyze costs
		cost_analysis = await analytics_service.analyze_costs(time_period=time_period, breakdown_by=breakdown_by)

		# Log successful cost analysis
		log_audit_event(
			"ANALYSIS_COMPLETE",
			user_id="anonymous",
			action="cost_analysis",
			result="success",
			details={"total_cost": cost_analysis.get("total_cost", 0)},
			request=request,
		)

		return cost_analysis

	except Exception as e:
		logger.error(f"Cost analysis failed: {e}", exc_info=True)
		log_audit_event("ANALYSIS_ERROR", user_id="anonymous", details={"action": "cost_analysis", "result": "failed", **{"error": str(e)}})
		raise HTTPException(status_code=500, detail="Cost analysis failed")


@router.get("/analytics/performance-metrics", tags=["Analytics"])
async def get_performance_metrics(request: Request, time_period: str = Query(default="7d", description="Time period for performance analysis")):
	"""
	Get system performance metrics.

	Args:
	    time_period: Time period for analysis

	Returns:
	    Performance metrics data
	"""
	try:
		analytics_service = get_analytics_service()

		# Log performance metrics request
		log_audit_event(
			"ANALYSIS_REQUEST", user_id="anonymous", details={"action": "performance_metrics", "result": "started", **{"time_period": time_period}}
		)

		# Get performance metrics
		metrics = await analytics_service.get_performance_metrics(time_period=time_period)

		# Log successful metrics retrieval
		log_audit_event("ANALYSIS_COMPLETE", user_id="anonymous", details={"action": "performance_metrics", "result": "success"})

		return metrics

	except Exception as e:
		logger.error(f"Performance metrics retrieval failed: {e}", exc_info=True)
		log_audit_event("ANALYSIS_ERROR", user_id="anonymous", details={"action": "performance_metrics", "result": "failed", **{"error": str(e)}})
		raise HTTPException(status_code=500, detail="Performance metrics retrieval failed")


@router.get("/analytics/dashboard", tags=["Analytics"])
async def get_analytics_dashboard(request: Request, time_period: str = Query(default="30d", description="Time period for dashboard data")):
	"""
	Get comprehensive analytics dashboard data.

	Args:
	    time_period: Time period for dashboard data

	Returns:
	    Complete dashboard data
	"""
	try:
		analytics_service = get_analytics_service()

		# Log dashboard request
		log_audit_event(
			"ANALYSIS_REQUEST", user_id="anonymous", details={"action": "analytics_dashboard", "result": "started", **{"time_period": time_period}}
		)

		# Get all dashboard data in parallel
		import asyncio

		risk_trends_task = analytics_service.analyze_risk_trends(time_period)
		cost_analysis_task = analytics_service.analyze_costs(time_period)
		performance_task = analytics_service.get_performance_metrics(time_period)

		risk_trends, cost_analysis, performance = await asyncio.gather(risk_trends_task, cost_analysis_task, performance_task)

		# Compile dashboard data
		dashboard_data = {
			"risk_trends": {
				"period": risk_trends.period,
				"average_risk_score": risk_trends.average_risk_score,
				"risk_count": risk_trends.risk_count,
				"high_risk_percentage": risk_trends.high_risk_percentage,
				"trend": risk_trends.trend.value,
				"confidence": risk_trends.confidence,
			},
			"cost_analysis": cost_analysis,
			"performance_metrics": performance,
			"metadata": {"generated_at": datetime.utcnow().isoformat(), "time_period": time_period},
		}

		# Log successful dashboard generation
		log_audit_event("ANALYSIS_COMPLETE", user_id="anonymous", details={"action": "analytics_dashboard", "result": "success"})

		return dashboard_data

	except Exception as e:
		logger.error(f"Analytics dashboard generation failed: {e}", exc_info=True)
		log_audit_event("ANALYSIS_ERROR", user_id="anonymous", details={"action": "analytics_dashboard", "result": "failed", **{"error": str(e)}})
		raise HTTPException(status_code=500, detail="Analytics dashboard generation failed")


@router.get("/analytics/langsmith-metrics", tags=["Analytics"])
async def get_langsmith_metrics(
	request: Request,
	hours: int = Query(default=24, description="Time period in hours"),
	user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
	"""
	Get LangSmith AI operation metrics.

	Args:
	    hours: Time period in hours for analysis
	    user_id: Optional user ID to filter by

	Returns:
	    LangSmith metrics data
	"""
	try:
		# Log analytics request
		log_audit_event(
			"ANALYSIS_REQUEST",
			user_id=user_id or "anonymous",
			details={"action": "langsmith_metrics", "result": "started", "hours": hours},
		)

		# Get LangSmith metrics
		metrics = LangSmithMetrics()
		performance = await metrics.get_performance_metrics(hours)
		errors = await metrics.get_error_analysis(hours)
		costs = await metrics.get_cost_analysis(hours)

		# Log successful completion
		log_audit_event(
			"ANALYSIS_COMPLETE",
			user_id=user_id or "anonymous",
			details={"action": "langsmith_metrics", "result": "completed", "hours": hours},
		)

		return {
			"timestamp": datetime.utcnow().isoformat(),
			"period_hours": hours,
			"performance": performance,
			"errors": errors,
			"costs": costs,
		}

	except Exception as e:
		logger.error(f"LangSmith metrics retrieval failed: {e}", exc_info=True)
		log_audit_event(
			"ANALYSIS_ERROR", user_id=user_id or "anonymous", details={"action": "langsmith_metrics", "result": "failed", **{"error": str(e)}}
		)
		raise HTTPException(status_code=500, detail="LangSmith metrics retrieval failed")


@router.get("/analytics/langsmith-summary", tags=["Analytics"])
async def get_langsmith_summary(
	request: Request,
	user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
	"""
	Get comprehensive LangSmith metrics summary.

	Args:
	    user_id: Optional user ID to filter by

	Returns:
	    LangSmith summary data
	"""
	try:
		# Log analytics request
		log_audit_event(
			"ANALYSIS_REQUEST",
			user_id=user_id or "anonymous",
			details={"action": "langsmith_summary", "result": "started"},
		)

		# Get LangSmith summary
		summary = await get_langsmith_metrics_summary()

		# Log successful completion
		log_audit_event(
			"ANALYSIS_COMPLETE",
			user_id=user_id or "anonymous",
			details={"action": "langsmith_summary", "result": "completed"},
		)

		return {
			"timestamp": datetime.utcnow().isoformat(),
			"langsmith": summary,
		}

	except Exception as e:
		logger.error(f"LangSmith summary retrieval failed: {e}", exc_info=True)
		log_audit_event(
			"ANALYSIS_ERROR", user_id=user_id or "anonymous", details={"action": "langsmith_summary", "result": "failed", **{"error": str(e)}}
		)
		raise HTTPException(status_code=500, detail="LangSmith summary retrieval failed")
