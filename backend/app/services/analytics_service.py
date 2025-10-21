"""
Analytics Service for Career Copilot
Provides comprehensive analytics and dashboard data
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TimeRange(str, Enum):
	"""Time range options for analytics"""

	LAST_7_DAYS = "last_7_days"
	LAST_30_DAYS = "last_30_days"
	LAST_90_DAYS = "last_90_days"
	LAST_YEAR = "last_year"
	ALL_TIME = "all_time"


class AnalysisType(str, Enum):
	"""Analysis type options"""

	COMPREHENSIVE = "comprehensive"
	BASIC = "basic"
	RISK_ASSESSMENT = "risk_assessment"
	COMPLIANCE_CHECK = "compliance_check"


@dataclass
class RiskDistribution:
	"""Risk distribution data"""

	high_risk: int
	medium_risk: int
	low_risk: int
	total: int


@dataclass
class ContractMetrics:
	"""Contract analysis metrics"""

	total_contracts: int
	risk_distribution: RiskDistribution
	average_risk_score: float
	high_risk_percentage: float
	analysis_success_rate: float
	processing_time_avg: float


@dataclass
class TrendData:
	"""Trend analysis data"""

	date: str
	contracts_analyzed: int
	average_risk_score: float
	high_risk_count: int


@dataclass
class ComplianceMetrics:
	"""Compliance analysis metrics"""

	gdpr_compliant: int
	sox_compliant: int
	hipaa_compliant: int
	non_compliant: int
	total_checked: int


class AnalyticsService:
	"""Advanced analytics service for job application tracking"""

	def __init__(self):
		self.settings = get_settings()
		self.db = None

	async def _get_database(self):
		"""Get database connection"""
		# Mock database for now
		return None

	async def get_dashboard_overview(self, time_range: TimeRange = TimeRange.LAST_30_DAYS) -> Dict[str, Any]:
		"""Get comprehensive dashboard overview"""
		try:
			db = await self._get_database()

			# Calculate date range
			end_date = datetime.now()
			start_date = self._calculate_start_date(end_date, time_range)

			# Get basic metrics
			metrics = await self._get_contract_metrics(db, start_date, end_date)

			# Get trend data
			trend_data = await self._get_trend_data(db, start_date, end_date)

			# Get compliance metrics
			compliance_metrics = await self._get_compliance_metrics(db, start_date, end_date)

			# Get top risky contracts
			risky_contracts = await self._get_top_risky_contracts(db, start_date, end_date, limit=5)

			# Get analysis performance
			performance_metrics = await self._get_performance_metrics(db, start_date, end_date)

			return {
				"overview": {
					"total_contracts": metrics.total_contracts,
					"average_risk_score": round(metrics.average_risk_score, 2),
					"high_risk_percentage": round(metrics.high_risk_percentage, 2),
					"analysis_success_rate": round(metrics.analysis_success_rate, 2),
					"time_range": time_range.value,
				},
				"risk_distribution": {
					"high_risk": metrics.risk_distribution.high_risk,
					"medium_risk": metrics.risk_distribution.medium_risk,
					"low_risk": metrics.risk_distribution.low_risk,
					"total": metrics.risk_distribution.total,
				},
				"trend_data": trend_data,
				"compliance_metrics": {
					"gdpr_compliant": compliance_metrics.gdpr_compliant,
					"sox_compliant": compliance_metrics.sox_compliant,
					"hipaa_compliant": compliance_metrics.hipaa_compliant,
					"non_compliant": compliance_metrics.non_compliant,
					"total_checked": compliance_metrics.total_checked,
				},
				"top_risky_contracts": risky_contracts,
				"performance_metrics": performance_metrics,
				"generated_at": datetime.now().isoformat(),
			}

		except Exception as e:
			logger.error(f"Failed to get dashboard overview: {e}")
			return self._get_empty_dashboard()

	async def _get_contract_metrics(self, db, start_date: datetime, end_date: datetime) -> ContractMetrics:
		"""Get job application tracking metrics"""
		try:
			# This would query your actual database
			# For now, returning mock data
			return ContractMetrics(
				total_contracts=150,
				risk_distribution=RiskDistribution(high_risk=25, medium_risk=60, low_risk=65, total=150),
				average_risk_score=5.2,
				high_risk_percentage=16.7,
				analysis_success_rate=94.5,
				processing_time_avg=12.3,
			)
		except Exception as e:
			logger.error(f"Failed to get contract metrics: {e}")
			return ContractMetrics(0, RiskDistribution(0, 0, 0, 0), 0.0, 0.0, 0.0, 0.0)

	async def _get_trend_data(self, db, start_date: datetime, end_date: datetime) -> List[TrendData]:
		"""Get trend analysis data"""
		try:
			# Generate mock trend data
			trend_data = []
			current_date = start_date

			while current_date <= end_date:
				# Mock data - in real implementation, query database
				contracts_analyzed = 5 + (current_date.day % 10)
				average_risk_score = 4.0 + (current_date.day % 3)
				high_risk_count = 1 + (current_date.day % 3)

				trend_data.append(
					TrendData(
						date=current_date.strftime("%Y-%m-%d"),
						contracts_analyzed=contracts_analyzed,
						average_risk_score=round(average_risk_score, 2),
						high_risk_count=high_risk_count,
					)
				)

				current_date += timedelta(days=1)

			return trend_data

		except Exception as e:
			logger.error(f"Failed to get trend data: {e}")
			return []

	async def _get_compliance_metrics(self, db, start_date: datetime, end_date: datetime) -> ComplianceMetrics:
		"""Get compliance analysis metrics"""
		try:
			# Mock compliance data
			return ComplianceMetrics(gdpr_compliant=120, sox_compliant=135, hipaa_compliant=110, non_compliant=15, total_checked=150)
		except Exception as e:
			logger.error(f"Failed to get compliance metrics: {e}")
			return ComplianceMetrics(0, 0, 0, 0, 0)

	async def _get_top_risky_contracts(self, db, start_date: datetime, end_date: datetime, limit: int = 5) -> List[Dict[str, Any]]:
		"""Get top risky contracts"""
		try:
			# Mock risky contracts data
			return [
				{
					"contract_id": "contract_001",
					"contract_name": "High-Risk Service Agreement",
					"risk_score": 8.5,
					"risk_level": "High",
					"analysis_date": "2024-09-20T10:30:00Z",
					"key_risks": ["Liability limitations", "Force majeure clauses"],
				},
				{
					"contract_id": "contract_002",
					"contract_name": "Software License Agreement",
					"risk_score": 7.8,
					"risk_level": "High",
					"analysis_date": "2024-09-19T14:15:00Z",
					"key_risks": ["Data privacy concerns", "Termination clauses"],
				},
				{
					"contract_id": "contract_003",
					"contract_name": "Employment Contract",
					"risk_score": 7.2,
					"risk_level": "High",
					"analysis_date": "2024-09-18T09:45:00Z",
					"key_risks": ["Non-compete clauses", "Intellectual property"],
				},
			]
		except Exception as e:
			logger.error(f"Failed to get top risky contracts: {e}")
			return []

	async def _get_performance_metrics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
		"""Get analysis performance metrics"""
		try:
			return {
				"average_processing_time": 12.3,
				"success_rate": 94.5,
				"error_rate": 5.5,
				"total_analyses": 150,
				"failed_analyses": 8,
				"average_risk_score": 5.2,
				"peak_analysis_time": "14:30",
				"most_common_risk_type": "Liability limitations",
			}
		except Exception as e:
			logger.error(f"Failed to get performance metrics: {e}")
			return {}

	def _calculate_start_date(self, end_date: datetime, time_range: TimeRange) -> datetime:
		"""Calculate start date based on time range"""
		if time_range == TimeRange.LAST_7_DAYS:
			return end_date - timedelta(days=7)
		elif time_range == TimeRange.LAST_30_DAYS:
			return end_date - timedelta(days=30)
		elif time_range == TimeRange.LAST_90_DAYS:
			return end_date - timedelta(days=90)
		elif time_range == TimeRange.LAST_YEAR:
			return end_date - timedelta(days=365)
		else:
			return datetime(2020, 1, 1)  # All time

	def _get_empty_dashboard(self) -> Dict[str, Any]:
		"""Get empty dashboard data"""
		return {
			"overview": {
				"total_contracts": 0,
				"average_risk_score": 0.0,
				"high_risk_percentage": 0.0,
				"analysis_success_rate": 0.0,
				"time_range": "last_30_days",
			},
			"risk_distribution": {"high_risk": 0, "medium_risk": 0, "low_risk": 0, "total": 0},
			"trend_data": [],
			"compliance_metrics": {"gdpr_compliant": 0, "sox_compliant": 0, "hipaa_compliant": 0, "non_compliant": 0, "total_checked": 0},
			"top_risky_contracts": [],
			"performance_metrics": {},
			"generated_at": datetime.now().isoformat(),
		}

	async def get_risk_heatmap_data(self, time_range: TimeRange = TimeRange.LAST_30_DAYS) -> Dict[str, Any]:
		"""Get risk heatmap data for visualization"""
		try:
			# Mock heatmap data
			return {
				"data": [
					{"x": "Monday", "y": "Week 1", "value": 6.2, "contracts": 8},
					{"x": "Tuesday", "y": "Week 1", "value": 5.8, "contracts": 12},
					{"x": "Wednesday", "y": "Week 1", "value": 7.1, "contracts": 6},
					{"x": "Thursday", "y": "Week 1", "value": 4.9, "contracts": 15},
					{"x": "Friday", "y": "Week 1", "value": 6.5, "contracts": 10},
					{"x": "Monday", "y": "Week 2", "value": 5.3, "contracts": 9},
					{"x": "Tuesday", "y": "Week 2", "value": 7.8, "contracts": 4},
					{"x": "Wednesday", "y": "Week 2", "value": 6.0, "contracts": 11},
					{"x": "Thursday", "y": "Week 2", "value": 5.7, "contracts": 13},
					{"x": "Friday", "y": "Week 2", "value": 6.9, "contracts": 7},
				],
				"max_value": 10.0,
				"min_value": 0.0,
				"time_range": time_range.value,
			}
		except Exception as e:
			logger.error(f"Failed to get risk heatmap data: {e}")
			return {"data": [], "max_value": 10.0, "min_value": 0.0, "time_range": time_range.value}


# Global analytics service instance
_analytics_service = None


def get_analytics_service() -> AnalyticsService:
	"""Get the global analytics service instance."""
	global _analytics_service
	if _analytics_service is None:
		_analytics_service = AnalyticsService()
	return _analytics_service
