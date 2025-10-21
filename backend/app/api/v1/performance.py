"""
Performance Monitoring API Endpoints
Provides comprehensive performance metrics and optimization tools.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ...core.caching import get_cache_manager
from ...core.database import get_database_manager
from ...core.load_balancer import get_load_balancer
from ...core.resource_manager import get_resource_manager
from ...core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


class PerformanceMetrics(BaseModel):
    """Performance metrics response model."""
    timestamp: datetime
    cache_metrics: Dict[str, Any]
    database_metrics: Dict[str, Any]
    load_balancer_metrics: Dict[str, Any]
    resource_metrics: Dict[str, Any]
    system_health: str


class OptimizationRequest(BaseModel):
    """Request model for optimization operations."""
    operation: str
    parameters: Optional[Dict[str, Any]] = None


class OptimizationResponse(BaseModel):
    """Response model for optimization operations."""
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None


@router.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get comprehensive performance metrics."""
    try:
        # Get metrics from all components
        cache_manager = get_cache_manager()
        db_manager = await get_database_manager()
        load_balancer = await get_load_balancer()
        resource_manager = await get_resource_manager()
        
        # Collect all metrics
        cache_metrics = cache_manager.get_stats()
        database_metrics = await db_manager.get_performance_metrics()
        load_balancer_metrics = load_balancer.get_stats()
        resource_metrics = resource_manager.get_resource_status()
        
        # Determine overall system health
        system_health = _determine_system_health(
            cache_metrics, database_metrics, load_balancer_metrics, resource_metrics
        )
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cache_metrics=cache_metrics,
            database_metrics=database_metrics,
            load_balancer_metrics=load_balancer_metrics,
            resource_metrics=resource_metrics,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/cache/optimize", response_model=OptimizationResponse)
async def optimize_cache():
    """Optimize cache performance."""
    try:
        cache_manager = get_cache_manager()
        results = cache_manager.optimize_cache()
        
        return OptimizationResponse(
            success=True,
            message="Cache optimization completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Cache optimization failed: {e}")
        return OptimizationResponse(
            success=False,
            message=f"Cache optimization failed: {str(e)}"
        )


@router.get("/database/optimize", response_model=OptimizationResponse)
async def optimize_database():
    """Optimize database performance."""
    try:
        db_manager = await get_database_manager()
        results = await db_manager.optimize_queries()
        
        return OptimizationResponse(
            success=True,
            message="Database optimization completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return OptimizationResponse(
            success=False,
            message=f"Database optimization failed: {str(e)}"
        )


@router.post("/memory/optimize", response_model=OptimizationResponse)
async def optimize_memory():
    """Optimize memory usage."""
    try:
        resource_manager = await get_resource_manager()
        results = await resource_manager.optimize_memory()
        
        return OptimizationResponse(
            success=True,
            message="Memory optimization completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")
        return OptimizationResponse(
            success=False,
            message=f"Memory optimization failed: {str(e)}"
        )


@router.get("/health")
async def get_system_health():
    """Get system health status."""
    try:
        cache_manager = get_cache_manager()
        db_manager = await get_database_manager()
        resource_manager = await get_resource_manager()
        
        # Get basic health metrics
        cache_health = cache_manager.get_stats()
        db_health = await db_manager.health_check()
        resource_health = resource_manager.get_resource_status()
        
        # Determine overall health
        health_score = _calculate_health_score(cache_health, db_health, resource_health)
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy",
            "score": health_score,
            "components": {
                "cache": "healthy" if cache_health.get("redis_connected", False) else "degraded",
                "database": "healthy" if all(db_health.values()) else "degraded",
                "resources": resource_health.get("resource_level", "unknown")
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "score": 0.0,
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@router.get("/alerts")
async def get_performance_alerts():
    """Get performance alerts and warnings."""
    try:
        resource_manager = await get_resource_manager()
        
        # Get recent alerts from resource manager
        alerts = []
        for alert in resource_manager.resource_alerts[-10:]:  # Last 10 alerts
            alerts.append({
                "timestamp": alert["timestamp"],
                "level": alert["level"],
                "message": alert["message"]
            })
        
        return {
            "alerts": alerts,
            "total_alerts": len(resource_manager.resource_alerts),
            "recent_alerts": len([a for a in resource_manager.resource_alerts 
                                if a["timestamp"] > datetime.utcnow() - timedelta(hours=1)])
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/optimize", response_model=OptimizationResponse)
async def run_comprehensive_optimization(background_tasks: BackgroundTasks):
    """Run comprehensive system optimization."""
    try:
        # Run optimizations in background
        background_tasks.add_task(_run_background_optimization)
        
        return OptimizationResponse(
            success=True,
            message="Comprehensive optimization started in background"
        )
        
    except Exception as e:
        logger.error(f"Comprehensive optimization failed: {e}")
        return OptimizationResponse(
            success=False,
            message=f"Comprehensive optimization failed: {str(e)}"
        )


@router.get("/load-balancer/stats")
async def get_load_balancer_stats():
    """Get detailed load balancer statistics."""
    try:
        load_balancer = await get_load_balancer()
        stats = load_balancer.get_stats()
        
        return {
            "load_balancer": stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get load balancer stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve load balancer stats")


@router.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics."""
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        
        return {
            "cache": stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache stats")


@router.get("/database/stats")
async def get_database_stats():
    """Get detailed database statistics."""
    try:
        db_manager = await get_database_manager()
        stats = await db_manager.get_performance_metrics()
        
        return {
            "database": stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database stats")


@router.get("/resources/stats")
async def get_resource_stats():
    """Get detailed resource statistics."""
    try:
        resource_manager = await get_resource_manager()
        stats = resource_manager.get_performance_metrics()
        
        return {
            "resources": stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resource stats")


def _determine_system_health(cache_metrics: Dict, database_metrics: Dict, 
                           load_balancer_metrics: Dict, resource_metrics: Dict) -> str:
    """Determine overall system health based on component metrics."""
    health_indicators = []
    
    # Cache health
    if cache_metrics.get("redis_connected", False):
        hit_rate = cache_metrics.get("hit_rate", 0)
        if hit_rate > 80:
            health_indicators.append(1.0)
        elif hit_rate > 60:
            health_indicators.append(0.7)
        else:
            health_indicators.append(0.4)
    else:
        health_indicators.append(0.2)
    
    # Database health
    if database_metrics.get("status") != "no_queries":
        query_perf = database_metrics.get("query_performance", {})
        avg_time = query_perf.get("avg_execution_time", 0)
        if avg_time < 0.1:
            health_indicators.append(1.0)
        elif avg_time < 0.5:
            health_indicators.append(0.8)
        else:
            health_indicators.append(0.5)
    else:
        health_indicators.append(0.5)
    
    # Resource health
    resource_level = resource_metrics.get("resource_level", "unknown")
    if resource_level == "low":
        health_indicators.append(1.0)
    elif resource_level == "normal":
        health_indicators.append(0.8)
    elif resource_level == "high":
        health_indicators.append(0.5)
    else:
        health_indicators.append(0.2)
    
    # Calculate overall health
    if not health_indicators:
        return "unknown"
    
    avg_health = sum(health_indicators) / len(health_indicators)
    
    if avg_health > 0.8:
        return "excellent"
    elif avg_health > 0.6:
        return "good"
    elif avg_health > 0.4:
        return "fair"
    else:
        return "poor"


def _calculate_health_score(cache_health: Dict, db_health: Dict, resource_health: Dict) -> float:
    """Calculate a numerical health score (0.0 to 1.0)."""
    scores = []
    
    # Cache score
    if cache_health.get("redis_connected", False):
        scores.append(0.9)
    else:
        scores.append(0.3)
    
    # Database score
    if all(db_health.values()):
        scores.append(0.9)
    else:
        scores.append(0.5)
    
    # Resource score
    resource_level = resource_health.get("resource_level", "unknown")
    if resource_level == "low":
        scores.append(0.9)
    elif resource_level == "normal":
        scores.append(0.8)
    elif resource_level == "high":
        scores.append(0.6)
    else:
        scores.append(0.3)
    
    return sum(scores) / len(scores) if scores else 0.0


async def _run_background_optimization():
    """Run comprehensive optimization in background."""
    try:
        logger.info("Starting comprehensive optimization...")
        
        # Optimize cache
        cache_manager = get_cache_manager()
        cache_results = cache_manager.optimize_cache()
        logger.info(f"Cache optimization completed: {cache_results}")
        
        # Optimize database
        db_manager = await get_database_manager()
        db_results = await db_manager.optimize_queries()
        logger.info(f"Database optimization completed: {db_results}")
        
        # Optimize memory
        resource_manager = await get_resource_manager()
        memory_results = await resource_manager.optimize_memory()
        logger.info(f"Memory optimization completed: {memory_results}")
        
        logger.info("Comprehensive optimization completed successfully")
        
    except Exception as e:
        logger.error(f"Background optimization failed: {e}")
