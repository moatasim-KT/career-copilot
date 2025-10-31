"""
Production Optimization API endpoints.

Provides endpoints for performance optimization, security validation,
and production monitoring capabilities.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.monitoring import get_performance_optimizer
from ...core.security_validator import get_security_validator
from ...core.monitoring import get_production_monitor
from ...core.logging import get_logger
from ...core.monitoring import log_audit_event

logger = get_logger(__name__)
router = APIRouter(tags=["Production Optimization"])


# Request/Response Models
class OptimizationRequest(BaseModel):
	"""Request model for optimization operations."""

	optimization_types: List[str] = Field(
		default=["database", "caching", "memory", "queries", "connections"], description="Types of optimizations to perform"
	)
	auto_apply: bool = Field(default=False, description="Automatically apply optimizations")
	force_optimization: bool = Field(default=False, description="Force optimization even if not needed")


class SecurityScanRequest(BaseModel):
	"""Request model for security scanning."""

	scan_types: List[str] = Field(
		default=["input_validation", "authentication", "headers", "file_upload"], description="Types of security scans to perform"
	)
	input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data to validate")
	auth_data: Optional[Dict[str, Any]] = Field(default=None, description="Authentication data to validate")
	headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers to validate")
	file_data: Optional[Dict[str, Any]] = Field(default=None, description="File upload data to validate")


class MonitoringConfigRequest(BaseModel):
	"""Request model for monitoring configuration."""

	monitoring_enabled: bool = Field(default=True, description="Enable/disable monitoring")
	auto_optimization_enabled: bool = Field(default=True, description="Enable/disable auto-optimization")
	metrics_interval: int = Field(default=30, description="Metrics collection interval in seconds")
	health_check_interval: int = Field(default=60, description="Health check interval in seconds")


# Performance Optimization Endpoints
@router.get("/performance/metrics")
async def get_performance_metrics():
	"""Get current performance metrics."""
	try:
		optimizer = await get_performance_optimizer()
		metrics = await optimizer.collect_performance_metrics()

		return {
			"status": "success",
			"metrics": {
				"response_time": metrics.response_time,
				"memory_usage": metrics.memory_usage,
				"cpu_usage": metrics.cpu_usage,
				"cache_hit_rate": metrics.cache_hit_rate,
				"database_query_time": metrics.database_query_time,
				"active_connections": metrics.active_connections,
				"timestamp": metrics.timestamp.isoformat(),
			},
		}
	except Exception as e:
		logger.error(f"Failed to get performance metrics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {e!s}")


@router.get("/performance/analysis")
async def analyze_performance_bottlenecks():
	"""Analyze system performance and identify bottlenecks."""
	try:
		optimizer = await get_performance_optimizer()
		analysis = await optimizer.analyze_performance_bottlenecks()

		log_audit_event("performance_analysis_requested", details={"bottlenecks_found": len(analysis.get("bottlenecks", []))})

		return {"status": "success", "analysis": analysis}
	except Exception as e:
		logger.error(f"Failed to analyze performance: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {e!s}")


@router.post("/performance/optimize")
async def optimize_system_performance(request: OptimizationRequest, background_tasks: BackgroundTasks):
	"""Optimize system performance."""
	try:
		optimizer = await get_performance_optimizer()

		if request.auto_apply:
			# Run optimization in background
			background_tasks.add_task(_run_optimization_background, optimizer, request.optimization_types, request.force_optimization)

			return {"status": "accepted", "message": "Optimization started in background", "optimization_types": request.optimization_types}
		else:
			# Run optimization synchronously
			result = await optimizer.optimize_system_performance()

			log_audit_event(
				"system_optimization_completed",
				details={"optimization_types": request.optimization_types, "improvement": result.get("overall_improvement", 0)},
			)

			return {"status": "success", "result": result}
	except Exception as e:
		logger.error(f"Failed to optimize system performance: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to optimize system performance: {e!s}")


@router.get("/performance/report")
async def get_performance_report():
	"""Get comprehensive performance report."""
	try:
		optimizer = await get_performance_optimizer()
		report = optimizer.get_performance_report()

		return {"status": "success", "report": report}
	except Exception as e:
		logger.error(f"Failed to get performance report: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get performance report: {e!s}")


# Security Validation Endpoints
@router.post("/security/scan")
async def perform_security_scan(request: SecurityScanRequest):
	"""Perform comprehensive security scan."""
	try:
		validator = get_security_validator()

		# Prepare scan data
		scan_data = {}
		if request.input_data:
			scan_data["input_data"] = request.input_data
		if request.auth_data:
			scan_data["auth_data"] = request.auth_data
		if request.headers:
			scan_data["headers"] = request.headers
		if request.file_data:
			scan_data["file_data"] = request.file_data

		# Perform comprehensive scan
		result = await validator.comprehensive_security_scan(scan_data)

		log_audit_event(
			"security_scan_completed",
			details={"scan_types": request.scan_types, "vulnerabilities_found": len(result.vulnerabilities), "security_score": result.score},
		)

		return {
			"status": "success",
			"scan_result": {
				"passed": result.passed,
				"score": result.score,
				"vulnerabilities": [
					{
						"type": vuln.vulnerability_type.value,
						"severity": vuln.severity.value,
						"description": vuln.description,
						"location": vuln.location,
						"recommendation": vuln.recommendation,
						"cve_references": vuln.cve_references,
						"timestamp": vuln.timestamp.isoformat(),
					}
					for vuln in result.vulnerabilities
				],
				"recommendations": result.recommendations,
				"compliance_status": result.compliance_status,
				"timestamp": result.timestamp.isoformat(),
			},
		}
	except Exception as e:
		logger.error(f"Failed to perform security scan: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to perform security scan: {e!s}")


@router.post("/security/validate-input")
async def validate_input_security(input_data: Dict[str, Any]):
	"""Validate input data for security vulnerabilities."""
	try:
		validator = get_security_validator()
		result = await validator.validate_input_security(input_data)

		return {
			"status": "success",
			"validation_result": {
				"passed": result.passed,
				"score": result.score,
				"vulnerabilities": len(result.vulnerabilities),
				"recommendations": result.recommendations,
			},
		}
	except Exception as e:
		logger.error(f"Failed to validate input security: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to validate input security: {e!s}")


@router.post("/security/validate-headers")
async def validate_security_headers(headers: Dict[str, str]):
	"""Validate HTTP security headers."""
	try:
		validator = get_security_validator()
		result = await validator.validate_security_headers(headers)

		return {
			"status": "success",
			"validation_result": {
				"passed": result.passed,
				"score": result.score,
				"vulnerabilities": len(result.vulnerabilities),
				"recommendations": result.recommendations,
			},
		}
	except Exception as e:
		logger.error(f"Failed to validate security headers: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to validate security headers: {e!s}")


# Production Monitoring Endpoints
@router.get("/monitoring/status")
async def get_monitoring_status():
	"""Get comprehensive monitoring status."""
	try:
		monitor = await get_production_monitor()
		status = monitor.get_monitoring_status()

		return {"status": "success", "monitoring_status": status}
	except Exception as e:
		logger.error(f"Failed to get monitoring status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {e!s}")


@router.get("/monitoring/health")
async def get_health_checks():
	"""Get comprehensive health check results."""
	try:
		monitor = await get_production_monitor()
		health_checks = await monitor.perform_comprehensive_health_check()

		return {
			"status": "success",
			"health_checks": {
				component: {
					"status": check.status.value,
					"message": check.message,
					"response_time": check.response_time,
					"timestamp": check.timestamp.isoformat(),
					"metadata": check.metadata,
				}
				for component, check in health_checks.items()
			},
		}
	except Exception as e:
		logger.error(f"Failed to get health checks: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get health checks: {e!s}")


@router.get("/monitoring/alerts")
async def get_alerts(
	include_resolved: bool = Query(False, description="Include resolved alerts"),
	limit: int = Query(50, description="Maximum number of alerts to return"),
):
	"""Get system alerts."""
	try:
		monitor = await get_production_monitor()
		alerts = monitor.get_alerts(include_resolved=include_resolved)

		# Limit results
		if limit > 0:
			alerts = alerts[:limit]

		return {"status": "success", "alerts": alerts, "total_count": len(alerts)}
	except Exception as e:
		logger.error(f"Failed to get alerts: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get alerts: {e!s}")


@router.get("/monitoring/metrics")
async def get_system_metrics():
	"""Get system metrics summary."""
	try:
		monitor = await get_production_monitor()
		metrics = monitor.get_metrics_summary()

		return {"status": "success", "metrics": metrics}
	except Exception as e:
		logger.error(f"Failed to get system metrics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {e!s}")


@router.post("/monitoring/configure")
async def configure_monitoring(request: MonitoringConfigRequest):
	"""Configure monitoring settings."""
	try:
		monitor = await get_production_monitor()
		optimizer = await get_performance_optimizer()

		# Update monitoring configuration
		monitor.monitoring_enabled = request.monitoring_enabled
		monitor.metrics_interval = request.metrics_interval
		monitor.health_check_interval = request.health_check_interval

		# Update optimizer configuration
		optimizer.enable_monitoring(request.monitoring_enabled)
		optimizer.enable_auto_optimization(request.auto_optimization_enabled)

		log_audit_event(
			"monitoring_configuration_updated",
			details={
				"monitoring_enabled": request.monitoring_enabled,
				"auto_optimization_enabled": request.auto_optimization_enabled,
				"metrics_interval": request.metrics_interval,
			},
		)

		return {
			"status": "success",
			"message": "Monitoring configuration updated",
			"configuration": {
				"monitoring_enabled": request.monitoring_enabled,
				"auto_optimization_enabled": request.auto_optimization_enabled,
				"metrics_interval": request.metrics_interval,
				"health_check_interval": request.health_check_interval,
			},
		}
	except Exception as e:
		logger.error(f"Failed to configure monitoring: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to configure monitoring: {e!s}")


@router.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
	"""Start production monitoring."""
	try:
		monitor = await get_production_monitor()

		# Start monitoring in background
		background_tasks.add_task(monitor.start_monitoring)

		log_audit_event("production_monitoring_started", details={})

		return {"status": "success", "message": "Production monitoring started"}
	except Exception as e:
		logger.error(f"Failed to start monitoring: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {e!s}")


@router.post("/monitoring/stop")
async def stop_monitoring():
	"""Stop production monitoring."""
	try:
		monitor = await get_production_monitor()
		await monitor.stop_monitoring()

		log_audit_event("production_monitoring_stopped", details={})

		return {"status": "success", "message": "Production monitoring stopped"}
	except Exception as e:
		logger.error(f"Failed to stop monitoring: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {e!s}")


# Comprehensive Production Readiness Endpoint
@router.get("/readiness/check")
async def check_production_readiness():
	"""Perform comprehensive production readiness check."""
	try:
		# Get all components
		optimizer = await get_performance_optimizer()
		validator = get_security_validator()
		monitor = await get_production_monitor()

		# Performance analysis
		performance_analysis = await optimizer.analyze_performance_bottlenecks()
		performance_report = optimizer.get_performance_report()

		# Security validation
		security_scan_data = {"headers": {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "X-XSS-Protection": "1; mode=block"}}
		security_result = await validator.comprehensive_security_scan(security_scan_data)

		# Monitoring status
		monitoring_status = monitor.get_monitoring_status()
		health_checks = await monitor.perform_comprehensive_health_check()

		# Calculate overall readiness score
		performance_score = 100 - len(performance_analysis.get("bottlenecks", [])) * 10
		security_score = security_result.score
		monitoring_score = 100 if monitoring_status["overall_status"] == "healthy" else 50

		overall_score = (performance_score + security_score + monitoring_score) / 3

		# Determine readiness level
		if overall_score >= 90:
			readiness_level = "PRODUCTION_READY"
		elif overall_score >= 75:
			readiness_level = "MOSTLY_READY"
		elif overall_score >= 60:
			readiness_level = "NEEDS_IMPROVEMENT"
		else:
			readiness_level = "NOT_READY"

		# Compile recommendations
		all_recommendations = []
		all_recommendations.extend(performance_analysis.get("recommendations", []))
		all_recommendations.extend(security_result.recommendations)

		log_audit_event(
			"production_readiness_check",
			details={
				"overall_score": overall_score,
				"readiness_level": readiness_level,
				"performance_score": performance_score,
				"security_score": security_score,
				"monitoring_score": monitoring_score,
			},
		)

		return {
			"status": "success",
			"production_readiness": {
				"overall_score": overall_score,
				"readiness_level": readiness_level,
				"component_scores": {"performance": performance_score, "security": security_score, "monitoring": monitoring_score},
				"performance_analysis": performance_analysis,
				"security_validation": {
					"score": security_result.score,
					"vulnerabilities": len(security_result.vulnerabilities),
					"compliance_status": security_result.compliance_status,
				},
				"monitoring_status": monitoring_status,
				"health_checks": {component: check.status.value for component, check in health_checks.items()},
				"recommendations": list(set(all_recommendations)),  # Remove duplicates
				"check_timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	except Exception as e:
		logger.error(f"Failed to check production readiness: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to check production readiness: {e!s}")


# Background task functions
async def _run_optimization_background(optimizer, optimization_types: List[str], force_optimization: bool):
	"""Run optimization in background."""
	try:
		result = await optimizer.optimize_system_performance()
		logger.info(f"Background optimization completed with {result.get('overall_improvement', 0):.1f}% improvement")
	except Exception as e:
		logger.error(f"Background optimization failed: {e}")
