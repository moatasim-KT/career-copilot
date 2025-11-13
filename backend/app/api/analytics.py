"""
Analytics API endpoints for advanced job application tracking features.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from ..core.langsmith_integration import LangSmithMetrics, get_langsmith_metrics_summary
from ..core.logging import get_logger
from ..core.monitoring import log_audit_event
from ..services.analytics_service import get_analytics_service

logger = get_logger(__name__)
router = APIRouter()


# Mark legacy analytics endpoints as removed. Return 410 Gone to force clients
# to use consolidated /api/v1/analytics endpoints.
def _deprecated_analytics_response():
	raise HTTPException(status_code=410, detail="Deprecated. Use /api/v1/analytics/* for analytics endpoints")


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
	# Legacy endpoint removed
	_deprecated_analytics_response()


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
	# Legacy endpoint removed
	_deprecated_analytics_response()


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
	# Legacy endpoint removed
	_deprecated_analytics_response()


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
	# Legacy endpoint removed
	_deprecated_analytics_response()


@router.get("/analytics/performance-metrics", tags=["Analytics"])
async def get_performance_metrics(request: Request, time_period: str = Query(default="7d", description="Time period for performance analysis")):
	"""
	Get system performance metrics.

	Args:
	    time_period: Time period for analysis

	Returns:
	    Performance metrics data
	"""
	# Legacy endpoint removed
	_deprecated_analytics_response()


@router.get("/analytics/dashboard", tags=["Analytics"])
async def get_analytics_dashboard(request: Request, time_period: str = Query(default="30d", description="Time period for dashboard data")):
	"""
	Get comprehensive analytics dashboard data.

	Args:
	    time_period: Time period for dashboard data

	Returns:
	    Complete dashboard data
	"""
	# Legacy endpoint removed
	_deprecated_analytics_response()


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
	# Legacy endpoint removed
	_deprecated_analytics_response()


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
	# Legacy endpoint removed
	_deprecated_analytics_response()
