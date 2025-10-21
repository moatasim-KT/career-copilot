"""
GROQ API endpoints for service management, monitoring, and optimization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.groq_service import get_groq_service, GROQModel, GROQTaskType
from ...services.groq_optimizer import get_groq_optimizer, OptimizationStrategy
from ...services.groq_router import get_groq_router, RoutingStrategy
from ...services.groq_monitor import get_groq_monitor
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/groq", tags=["GROQ"])


# Request/Response Models
class GROQCompletionRequest(BaseModel):
    """Request model for GROQ completion."""
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    model: Optional[GROQModel] = Field(None, description="Specific model to use")
    task_type: GROQTaskType = Field(GROQTaskType.CONVERSATION, description="Task type for optimization")
    priority: str = Field("balanced", description="Priority: speed, quality, cost, balanced")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, ge=1, le=32768, description="Maximum tokens to generate")
    use_optimization: bool = Field(True, description="Whether to use GROQ optimizations")


class GROQCompletionResponse(BaseModel):
    """Response model for GROQ completion."""
    content: str
    model: str
    usage: Dict[str, int]
    cost: float
    processing_time: float
    confidence_score: float
    request_id: str
    timestamp: str
    metadata: Dict[str, Any]


class GROQHealthResponse(BaseModel):
    """Response model for GROQ health check."""
    service: str
    status: str
    timestamp: str
    api_key_configured: bool
    circuit_breaker_state: str
    models: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    errors: List[str]


class GROQMetricsResponse(BaseModel):
    """Response model for GROQ metrics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    uptime_percentage: float
    total_tokens_used: int
    total_cost: float
    avg_response_time: float
    avg_tokens_per_request: float
    avg_cost_per_request: float
    rate_limit_hits: int
    model_usage: Dict[str, int]
    task_performance: Dict[str, float]
    last_request_time: Optional[str]


class GROQOptimizationReport(BaseModel):
    """Response model for GROQ optimization report."""
    config: Dict[str, Any]
    metrics: Dict[str, Any]
    performance: Dict[str, Dict[str, Any]]
    groq_service_metrics: Dict[str, Any]


class GROQRoutingStats(BaseModel):
    """Response model for GROQ routing statistics."""
    total_models: int
    active_models: int
    routing_rules: int
    load_balancer_state: Dict[str, int]
    circuit_breaker_states: Dict[str, str]
    performance_metrics: Dict[str, Dict[str, Any]]


class GROQDashboardData(BaseModel):
    """Response model for GROQ dashboard data."""
    summary: Dict[str, Any]
    model_usage: Dict[str, int]
    task_usage: Dict[str, int]
    cost_breakdown: Dict[str, Dict[str, Any]]
    performance_analysis: Dict[str, Dict[str, Any]]
    quality_metrics: Dict[str, Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    time_range: str
    last_updated: str


# API Endpoints
@router.post("/completion", response_model=GROQCompletionResponse)
async def generate_completion(
    request: GROQCompletionRequest,
    groq_service = Depends(get_groq_service),
    groq_optimizer = Depends(get_groq_optimizer)
):
    """Generate completion using GROQ service with optimizations."""
    try:
        if request.use_optimization:
            # Use optimized completion
            result = await groq_optimizer.optimized_completion(
                messages=request.messages,
                task_type=request.task_type,
                priority=request.priority,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        else:
            # Use direct service
            result = await groq_service.generate_completion(
                messages=request.messages,
                model=request.model,
                task_type=request.task_type,
                priority=request.priority,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        return GROQCompletionResponse(**result)
        
    except Exception as e:
        logger.error(f"GROQ completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=GROQHealthResponse)
async def health_check(groq_service = Depends(get_groq_service)):
    """Get GROQ service health status."""
    try:
        health_status = await groq_service.health_check()
        return GROQHealthResponse(**health_status)
    except Exception as e:
        logger.error(f"GROQ health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=GROQMetricsResponse)
async def get_metrics(groq_service = Depends(get_groq_service)):
    """Get GROQ service metrics."""
    try:
        metrics = groq_service.get_metrics_summary()
        return GROQMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Failed to get GROQ metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(groq_service = Depends(get_groq_service)):
    """List available GROQ models with configurations."""
    try:
        models = {}
        for model, config in groq_service.model_configs.items():
            models[model.value] = {
                "model": model.value,
                "max_tokens": config.max_tokens,
                "context_window": config.context_window,
                "cost_per_token": config.cost_per_token,
                "tokens_per_minute_limit": config.tokens_per_minute_limit,
                "requests_per_minute_limit": config.requests_per_minute_limit,
                "optimal_tasks": [task.value for task in config.optimal_tasks],
                "quality_score": config.quality_score,
                "speed_score": config.speed_score,
                "enabled": config.enabled,
                "metadata": config.metadata
            }
        
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to list GROQ models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimal-model")
async def get_optimal_model(
    task_type: GROQTaskType = Query(..., description="Task type"),
    priority: str = Query("balanced", description="Priority: speed, quality, cost, balanced"),
    groq_service = Depends(get_groq_service)
):
    """Get optimal model for a specific task type and priority."""
    try:
        optimal_model = await groq_service.get_optimal_model(task_type, priority)
        model_config = groq_service.model_configs[optimal_model]
        
        return {
            "optimal_model": optimal_model.value,
            "task_type": task_type.value,
            "priority": priority,
            "model_config": {
                "max_tokens": model_config.max_tokens,
                "cost_per_token": model_config.cost_per_token,
                "quality_score": model_config.quality_score,
                "speed_score": model_config.speed_score,
                "optimal_tasks": [task.value for task in model_config.optimal_tasks]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get optimal model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-analysis")
async def get_cost_analysis(groq_service = Depends(get_groq_service)):
    """Get detailed cost analysis."""
    try:
        cost_analysis = groq_service.get_cost_analysis()
        return cost_analysis
    except Exception as e:
        logger.error(f"Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-analysis")
async def get_performance_analysis(groq_service = Depends(get_groq_service)):
    """Get detailed performance analysis."""
    try:
        performance_analysis = groq_service.get_performance_analysis()
        return performance_analysis
    except Exception as e:
        logger.error(f"Failed to get performance analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-metrics")
async def reset_metrics(groq_service = Depends(get_groq_service)):
    """Reset GROQ service metrics."""
    try:
        await groq_service.reset_metrics()
        return {"message": "GROQ metrics reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset GROQ metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Optimization Endpoints
@router.get("/optimization/report", response_model=GROQOptimizationReport)
async def get_optimization_report(groq_optimizer = Depends(get_groq_optimizer)):
    """Get comprehensive optimization report."""
    try:
        report = await groq_optimizer.get_optimization_report()
        return GROQOptimizationReport(**report)
    except Exception as e:
        logger.error(f"Failed to get optimization report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/reset")
async def reset_optimization_metrics(groq_optimizer = Depends(get_groq_optimizer)):
    """Reset optimization metrics."""
    try:
        await groq_optimizer.reset_optimization_metrics()
        return {"message": "GROQ optimization metrics reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset optimization metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Routing Endpoints
@router.post("/routing/select-model")
async def select_model(
    task_type: GROQTaskType = Query(..., description="Task type"),
    strategy: RoutingStrategy = Query(RoutingStrategy.ADAPTIVE, description="Routing strategy"),
    context: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    groq_router = Depends(get_groq_router)
):
    """Select optimal model using routing logic."""
    try:
        decision = await groq_router.select_model(
            task_type=task_type,
            strategy=strategy,
            context=context or {},
            constraints=constraints or {}
        )
        
        return {
            "selected_model": decision.selected_model.value,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "alternatives": [model.value for model in decision.alternatives],
            "estimated_cost": decision.estimated_cost,
            "estimated_time": decision.estimated_time,
            "routing_strategy": decision.routing_strategy.value,
            "metadata": decision.metadata
        }
    except Exception as e:
        logger.error(f"Failed to select model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/statistics", response_model=GROQRoutingStats)
async def get_routing_statistics(groq_router = Depends(get_groq_router)):
    """Get routing statistics."""
    try:
        stats = groq_router.get_routing_statistics()
        return GROQRoutingStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get routing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/reset-metrics")
async def reset_routing_metrics(groq_router = Depends(get_groq_router)):
    """Reset routing metrics."""
    try:
        await groq_router.reset_routing_metrics()
        return {"message": "GROQ routing metrics reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset routing metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring Endpoints
@router.get("/monitoring/dashboard", response_model=GROQDashboardData)
async def get_dashboard_data(
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    groq_monitor = Depends(get_groq_monitor)
):
    """Get dashboard data for monitoring."""
    try:
        dashboard_data = groq_monitor.get_dashboard_data(time_range)
        return GROQDashboardData(**dashboard_data)
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/cost-report")
async def get_cost_report(
    period: str = Query("daily", description="Period: hourly, daily, weekly"),
    groq_monitor = Depends(get_groq_monitor)
):
    """Get cost report."""
    try:
        cost_report = groq_monitor.get_cost_report(period)
        return cost_report
    except Exception as e:
        logger.error(f"Failed to get cost report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts")
async def get_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    groq_monitor = Depends(get_groq_monitor)
):
    """Get monitoring alerts."""
    try:
        alerts = groq_monitor.alerts
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "metric_type": alert.metric_type.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "model": alert.model,
                    "task_type": alert.task_type,
                    "threshold_value": alert.threshold_value,
                    "actual_value": alert.actual_value,
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    groq_monitor = Depends(get_groq_monitor)
):
    """Resolve a monitoring alert."""
    try:
        success = groq_monitor.resolve_alert(alert_id)
        if success:
            return {"message": f"Alert {alert_id} resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_monitoring(groq_monitor = Depends(get_groq_monitor)):
    """Start continuous monitoring."""
    try:
        await groq_monitor.start_monitoring()
        return {"message": "GROQ monitoring started successfully"}
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_monitoring(groq_monitor = Depends(get_groq_monitor)):
    """Stop continuous monitoring."""
    try:
        await groq_monitor.stop_monitoring()
        return {"message": "GROQ monitoring stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/export")
async def export_metrics(
    format: str = Query("json", description="Export format: json"),
    groq_monitor = Depends(get_groq_monitor)
):
    """Export monitoring metrics."""
    try:
        exported_data = await groq_monitor.export_metrics(format)
        
        return {
            "format": format,
            "data": exported_data,
            "exported_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))