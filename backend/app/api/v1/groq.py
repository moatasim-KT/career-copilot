"""
GROQ API endpoints for Phase 2 services (Optimizer, Router, Monitor)
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ...services.groq_service import GROQTaskType, GROQModel
from ...services.groq_optimizer import get_groq_optimizer, OptimizationStrategy
from ...services.groq_router import get_groq_router, RoutingStrategy
from ...services.groq_monitor import get_groq_monitor
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/groq", tags=["groq"])


# Request/Response Models
class OptimizedCompletionRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="List of messages")
    task_type: str = Field(default="conversation", description="Task type")
    priority: str = Field(default="balanced", description="Priority: speed, quality, cost, balanced")
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192)


class RouteModelRequest(BaseModel):
    task_type: str = Field(..., description="Task type")
    strategy: str = Field(default="adaptive", description="Routing strategy")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context for routing")


# Optimizer Endpoints
@router.post("/optimize/completion")
async def optimized_completion(request: OptimizedCompletionRequest):
    """Generate optimized completion using GROQ optimizer"""
    try:
        optimizer = get_groq_optimizer()
        task_type = GROQTaskType(request.task_type)
        
        result = await optimizer.optimized_completion(
            messages=request.messages,
            task_type=task_type,
            priority=request.priority,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimize/report")
async def optimization_report():
    """Get optimization performance report"""
    try:
        optimizer = get_groq_optimizer()
        report = await optimizer.get_optimization_report()
        return {"success": True, "data": report}
    except Exception as e:
        logger.error(f"Report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/reset")
async def reset_optimization_metrics():
    """Reset optimization metrics"""
    try:
        optimizer = get_groq_optimizer()
        await optimizer.reset_optimization_metrics()
        return {"success": True, "message": "Metrics reset"}
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Router Endpoints
@router.post("/route/select")
async def select_model(request: RouteModelRequest):
    """Select optimal model using router"""
    try:
        router_service = get_groq_router()
        task_type = GROQTaskType(request.task_type)
        strategy = RoutingStrategy(request.strategy)
        
        decision = await router_service.select_model(
            task_type=task_type,
            strategy=strategy,
            context=request.context
        )
        
        return {
            "success": True,
            "data": {
                "selected_model": decision.selected_model.value,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "alternatives": [m.value for m in decision.alternatives],
                "estimated_cost": decision.estimated_cost,
                "estimated_time": decision.estimated_time,
                "strategy": decision.routing_strategy.value
            }
        }
    except Exception as e:
        logger.error(f"Routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/route/statistics")
async def routing_statistics():
    """Get routing statistics"""
    try:
        router_service = get_groq_router()
        stats = router_service.get_routing_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route/reset")
async def reset_routing_metrics():
    """Reset routing metrics"""
    try:
        router_service = get_groq_router()
        await router_service.reset_routing_metrics()
        return {"success": True, "message": "Routing metrics reset"}
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Monitor Endpoints
@router.get("/monitor/dashboard")
async def monitor_dashboard(time_range: str = Query(default="24h", pattern="^(1h|24h|7d|30d)$")):
    """Get monitoring dashboard data"""
    try:
        monitor = get_groq_monitor()
        dashboard = monitor.get_dashboard_data(time_range)
        return {"success": True, "data": dashboard}
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/cost-report")
async def cost_report(period: str = Query(default="daily", pattern="^(hourly|daily|weekly)$")):
    """Get cost report"""
    try:
        monitor = get_groq_monitor()
        report = monitor.get_cost_report(period)
        return {"success": True, "data": report}
    except Exception as e:
        logger.error(f"Cost report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/start")
async def start_monitoring():
    """Start continuous monitoring"""
    try:
        monitor = get_groq_monitor()
        await monitor.start_monitoring()
        return {"success": True, "message": "Monitoring started"}
    except Exception as e:
        logger.error(f"Start monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_monitoring():
    """Stop continuous monitoring"""
    try:
        monitor = get_groq_monitor()
        await monitor.stop_monitoring()
        return {"success": True, "message": "Monitoring stopped"}
    except Exception as e:
        logger.error(f"Stop monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/export")
async def export_metrics(format: str = Query(default="json")):
    """Export monitoring metrics"""
    try:
        monitor = get_groq_monitor()
        data = await monitor.export_metrics(format)
        return {"success": True, "data": data, "format": format}
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check
@router.get("/health")
async def health_check():
    """Health check for GROQ services"""
    try:
        from ...services.groq_service import get_groq_service
        
        groq_service = get_groq_service()
        health = await groq_service.health_check()
        
        return {
            "success": True,
            "status": health["status"],
            "services": {
                "optimizer": "operational",
                "router": "operational",
                "monitor": "operational"
            },
            "details": health
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
