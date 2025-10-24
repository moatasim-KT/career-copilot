"""
Consolidated Performance Monitoring and Metrics API Endpoints
Comprehensive performance monitoring, metrics collection, and system optimization.

This module consolidates functionality from:
- performance.py (performance monitoring and optimization)
- performance_metrics.py (performance metrics and streaming management)
- monitoring.py (comprehensive monitoring endpoints)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ...core.logging import get_logger, get_logging_metrics
from ...utils.error_handler import get_error_handler

logger = get_logger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])


# Response Models
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


class StreamingRequest(BaseModel):
    """Request model for streaming analysis."""
    model_type: str
    prompt: str
    context: Optional[str] = None
    streaming_mode: str = "buffered"
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TokenOptimizationRequest(BaseModel):
    """Request model for token optimization."""
    text: str
    max_tokens: int
    strategy: str = "balanced"
    preserve_quality: bool = True


class PerformanceQuery(BaseModel):
    """Query parameters for performance metrics."""
    provider: Optional[str] = None
    model: Optional[str] = None
    operation: Optional[str] = None
    time_window: str = "hour"


# Core Performance Monitoring Endpoints

@router.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get comprehensive performance metrics."""
    try:
        # Try to get metrics from all components with fallbacks
        cache_metrics = {}
        database_metrics = {}
        load_balancer_metrics = {}
        resource_metrics = {}
        
        # Cache metrics
        try:
            from ...core.caching import get_cache_manager
            cache_manager = get_cache_manager()
            cache_metrics = cache_manager.get_stats()
        except ImportError:
            cache_metrics = {"status": "not_available", "enabled": False}
        except Exception as e:
            logger.warning(f"Failed to get cache metrics: {e}")
            cache_metrics = {"status": "error", "error": str(e)}
        
        # Database metrics
        try:
            from ...core.database import get_database_manager
            db_manager = await get_database_manager()
            database_metrics = await db_manager.get_performance_metrics()
        except ImportError:
            database_metrics = {"status": "not_available"}
        except Exception as e:
            logger.warning(f"Failed to get database metrics: {e}")
            database_metrics = {"status": "error", "error": str(e)}
        
        # Load balancer metrics
        try:
            from ...core.load_balancer import get_load_balancer
            load_balancer = await get_load_balancer()
            load_balancer_metrics = load_balancer.get_stats()
        except ImportError:
            load_balancer_metrics = {"status": "not_available"}
        except Exception as e:
            logger.warning(f"Failed to get load balancer metrics: {e}")
            load_balancer_metrics = {"status": "error", "error": str(e)}
        
        # Resource metrics
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            resource_metrics = resource_manager.get_resource_status()
        except ImportError:
            resource_metrics = {"status": "not_available"}
        except Exception as e:
            logger.warning(f"Failed to get resource metrics: {e}")
            resource_metrics = {"status": "error", "error": str(e)}
        
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


@router.get("/metrics/summary")
async def get_performance_summary(
    time_window: str = Query("hour", description="Time window: minute, hour, day, week"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    model: Optional[str] = Query(None, description="Filter by model")
) -> Dict[str, Any]:
    """Get comprehensive performance metrics summary."""
    try:
        # Try to use performance metrics collector if available
        try:
            from ...core.performance_metrics import get_performance_metrics_collector, TimeWindow
            
            performance_collector = get_performance_metrics_collector()
            
            # Parse time window
            window_map = {
                "minute": TimeWindow.MINUTE,
                "hour": TimeWindow.HOUR,
                "day": TimeWindow.DAY,
                "week": TimeWindow.WEEK
            }
            
            window = window_map.get(time_window.lower(), TimeWindow.HOUR)
            
            # Get overall summary
            summary = performance_collector.get_performance_summary(window)
            
            # Filter by provider/model if specified
            if provider or model:
                filtered_summary = {"time_window": summary["time_window"], "providers": {}}
                
                for prov_name, prov_data in summary.get("providers", {}).items():
                    if provider and prov_name != provider:
                        continue
                    
                    filtered_models = {}
                    for model_name, model_data in prov_data.get("models", {}).items():
                        if model and model_name != model:
                            continue
                        filtered_models[model_name] = model_data
                    
                    if filtered_models:
                        filtered_summary["providers"][prov_name] = {"models": filtered_models}
                
                summary = filtered_summary
            
            return {
                "status": "success",
                "data": summary,
                "metadata": {
                    "filters_applied": {
                        "provider": provider,
                        "model": model,
                        "time_window": time_window
                    }
                }
            }
            
        except ImportError:
            # Fallback to basic performance summary
            return {
                "status": "success",
                "data": {
                    "time_window": time_window,
                    "summary": {
                        "total_requests": 0,
                        "average_response_time": 0.0,
                        "success_rate": 100.0
                    },
                    "note": "Performance metrics collector not available - showing placeholder data"
                },
                "metadata": {
                    "filters_applied": {
                        "provider": provider,
                        "model": model,
                        "time_window": time_window
                    }
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Optimization Endpoints

@router.get("/cache/optimize", response_model=OptimizationResponse)
async def optimize_cache():
    """Optimize cache performance."""
    try:
        try:
            from ...core.caching import get_cache_manager
            cache_manager = get_cache_manager()
            results = cache_manager.optimize_cache()
            
            return OptimizationResponse(
                success=True,
                message="Cache optimization completed",
                results=results
            )
        except ImportError:
            return OptimizationResponse(
                success=False,
                message="Cache manager not available"
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
        try:
            from ...core.database import get_database_manager
            db_manager = await get_database_manager()
            results = await db_manager.optimize_queries()
            
            return OptimizationResponse(
                success=True,
                message="Database optimization completed",
                results=results
            )
        except ImportError:
            return OptimizationResponse(
                success=False,
                message="Database manager not available"
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
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            results = await resource_manager.optimize_memory()
            
            return OptimizationResponse(
                success=True,
                message="Memory optimization completed",
                results=results
            )
        except ImportError:
            # Fallback to basic garbage collection
            import gc
            collected = gc.collect()
            
            return OptimizationResponse(
                success=True,
                message="Basic memory optimization completed",
                results={"objects_collected": collected, "method": "gc"}
            )
        
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")
        return OptimizationResponse(
            success=False,
            message=f"Memory optimization failed: {str(e)}"
        )


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


# System Health and Status Endpoints

@router.get("/health")
async def get_system_health():
    """Get system health status."""
    try:
        # Get basic health metrics with fallbacks
        cache_health = {}
        db_health = {}
        resource_health = {}
        
        try:
            from ...core.caching import get_cache_manager
            cache_manager = get_cache_manager()
            cache_health = cache_manager.get_stats()
        except ImportError:
            cache_health = {"redis_connected": False}
        except Exception:
            cache_health = {"redis_connected": False}
        
        try:
            from ...core.database import get_database_manager
            db_manager = await get_database_manager()
            db_health = await db_manager.health_check()
        except ImportError:
            db_health = {"database": False}
        except Exception:
            db_health = {"database": False}
        
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            resource_health = resource_manager.get_resource_status()
        except ImportError:
            resource_health = {"resource_level": "unknown"}
        except Exception:
            resource_health = {"resource_level": "unknown"}
        
        # Calculate health score
        health_score = _calculate_health_score(cache_health, db_health, resource_health)
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy",
            "score": health_score,
            "components": {
                "cache": "healthy" if cache_health.get("redis_connected", False) else "degraded",
                "database": "healthy" if db_health.get("database", False) else "degraded",
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
        alerts = []
        
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            
            # Get recent alerts from resource manager
            for alert in resource_manager.resource_alerts[-10:]:  # Last 10 alerts
                alerts.append({
                    "timestamp": alert["timestamp"],
                    "level": alert["level"],
                    "message": alert["message"]
                })
        except ImportError:
            # No alerts available
            pass
        except Exception as e:
            logger.warning(f"Failed to get alerts: {e}")
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "recent_alerts": len([a for a in alerts 
                                if a.get("timestamp", datetime.min) > datetime.utcnow() - timedelta(hours=1)])
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


# Detailed Component Statistics

@router.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics."""
    try:
        try:
            from ...core.caching import get_cache_manager
            cache_manager = get_cache_manager()
            stats = cache_manager.get_stats()
            
            return {
                "cache": stats,
                "timestamp": datetime.utcnow()
            }
        except ImportError:
            return {
                "cache": {"status": "not_available", "message": "Cache manager not available"},
                "timestamp": datetime.utcnow()
            }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache stats")


@router.get("/database/stats")
async def get_database_stats():
    """Get detailed database statistics."""
    try:
        try:
            from ...core.database import get_database_manager
            db_manager = await get_database_manager()
            stats = await db_manager.get_performance_metrics()
            
            return {
                "database": stats,
                "timestamp": datetime.utcnow()
            }
        except ImportError:
            return {
                "database": {"status": "not_available", "message": "Database manager not available"},
                "timestamp": datetime.utcnow()
            }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database stats")


@router.get("/resources/stats")
async def get_resource_stats():
    """Get detailed resource statistics."""
    try:
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            stats = resource_manager.get_performance_metrics()
            
            return {
                "resources": stats,
                "timestamp": datetime.utcnow()
            }
        except ImportError:
            # Fallback to basic system stats
            try:
                import psutil
                
                stats = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                }
                
                return {
                    "resources": stats,
                    "timestamp": datetime.utcnow(),
                    "note": "Using basic system stats (psutil)"
                }
            except ImportError:
                return {
                    "resources": {"status": "not_available", "message": "Resource manager and psutil not available"},
                    "timestamp": datetime.utcnow()
                }
        
    except Exception as e:
        logger.error(f"Failed to get resource stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resource stats")


# Monitoring Dashboard Endpoints (consolidated from monitoring.py)

@router.get("/monitoring/dashboard", tags=["Monitoring"])
async def get_monitoring_dashboard() -> JSONResponse:
    """Get comprehensive monitoring dashboard data."""
    try:
        # Try to get comprehensive monitoring data
        try:
            from ...core.comprehensive_monitoring import get_comprehensive_monitoring
            monitoring_system = get_comprehensive_monitoring()
            dashboard_data = monitoring_system.get_monitoring_dashboard()
            
            return JSONResponse(content=dashboard_data)
        except ImportError:
            # Fallback dashboard data
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "healthy",
                "components": {
                    "performance": "healthy",
                    "monitoring": "basic"
                },
                "metrics": {
                    "uptime_seconds": time.time(),
                    "requests_per_minute": 0,
                    "error_rate": 0.0
                },
                "note": "Comprehensive monitoring not available - showing basic dashboard"
            }
            
            return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Monitoring dashboard failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/health", tags=["Monitoring"])
async def get_system_health_monitoring() -> JSONResponse:
    """Get overall system health status for monitoring."""
    try:
        # Try to get comprehensive health status
        try:
            from ...core.comprehensive_monitoring import get_comprehensive_monitoring
            monitoring_system = get_comprehensive_monitoring()
            health_status = monitoring_system.get_health_status()
            
            # Determine HTTP status code based on health
            status_code = 200
            if health_status["status"] == "critical":
                status_code = 503
            elif health_status["status"] == "degraded":
                status_code = 200  # Still functional but degraded
            
            return JSONResponse(content=health_status, status_code=status_code)
        except ImportError:
            # Fallback health status
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "api": "healthy",
                    "monitoring": "basic"
                },
                "note": "Comprehensive monitoring not available - showing basic health"
            }
            
            return JSONResponse(content=health_status, status_code=200)
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/alerts", tags=["Monitoring"])
async def get_system_alerts_monitoring(
    active_only: bool = Query(True, description="Return only active alerts"),
    limit: int = Query(50, description="Maximum number of alerts to return")
) -> JSONResponse:
    """Get system alerts for monitoring."""
    try:
        alerts = []
        
        # Try to get comprehensive monitoring alerts
        try:
            from ...core.comprehensive_monitoring import get_comprehensive_monitoring
            monitoring_system = get_comprehensive_monitoring()
            dashboard_data = monitoring_system.get_monitoring_dashboard()
            
            alerts = dashboard_data.get("alerts", [])
            
            if active_only:
                alerts = [alert for alert in alerts if not alert.get("resolved", False)]
            
            # Limit results
            alerts = alerts[-limit:] if len(alerts) > limit else alerts
        except ImportError:
            # No alerts available
            alerts = []
        
        return JSONResponse(content={
            "alerts": alerts,
            "total_count": len(alerts),
            "active_count": len([a for a in alerts if not a.get("resolved", False)]),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get alerts failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/metrics", tags=["Monitoring"])
async def get_performance_metrics_monitoring() -> JSONResponse:
    """Get detailed performance metrics for monitoring."""
    try:
        # Get additional metrics
        logging_metrics = get_logging_metrics()
        error_handler = get_error_handler()
        error_stats = error_handler.get_error_stats()
        
        # Get basic performance metrics
        try:
            performance_metrics = await get_performance_metrics()
            system_metrics = {
                "cache": performance_metrics.cache_metrics,
                "database": performance_metrics.database_metrics,
                "resources": performance_metrics.resource_metrics,
                "system_health": performance_metrics.system_health
            }
        except Exception:
            system_metrics = {"status": "error", "message": "Failed to get performance metrics"}
        
        metrics = {
            "system_metrics": system_metrics,
            "logging_metrics": logging_metrics,
            "error_statistics": error_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Get performance metrics failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


# Streaming and Token Optimization Endpoints (from performance_metrics.py)

@router.get("/streaming/status")
async def get_streaming_status() -> Dict[str, Any]:
    """Get current streaming status and performance."""
    try:
        try:
            from ...core.streaming_manager import get_streaming_manager
            streaming_manager = get_streaming_manager()
            streaming_summary = streaming_manager.get_streaming_performance_summary()
            
            return {
                "status": "success",
                "data": streaming_summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        except ImportError:
            return {
                "status": "success",
                "data": {
                    "active_sessions": 0,
                    "total_streams": 0,
                    "average_latency": 0.0
                },
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Streaming manager not available"
            }
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token-optimization/analyze")
async def analyze_token_optimization(request: TokenOptimizationRequest) -> Dict[str, Any]:
    """Analyze token optimization for given text."""
    try:
        try:
            from ...core.token_optimizer import get_token_optimizer, OptimizationStrategy, TokenBudget
            
            token_optimizer = get_token_optimizer()
            
            # Parse optimization strategy
            strategy_map = {
                "aggressive": OptimizationStrategy.AGGRESSIVE,
                "balanced": OptimizationStrategy.BALANCED,
                "conservative": OptimizationStrategy.CONSERVATIVE,
                "adaptive": OptimizationStrategy.ADAPTIVE
            }
            
            strategy = strategy_map.get(request.strategy.lower(), OptimizationStrategy.BALANCED)
            
            # Create token budget
            budget = TokenBudget(
                max_prompt_tokens=request.max_tokens // 2,
                max_completion_tokens=request.max_tokens // 2,
                max_total_tokens=request.max_tokens
            )
            
            # Create dummy messages for optimization
            from langchain.schema import HumanMessage
            messages = [HumanMessage(content=request.text)]
            
            # Perform optimization
            optimized_messages, result = token_optimizer.optimize_messages(
                messages=messages,
                budget=budget,
                strategy=strategy,
                preserve_quality=request.preserve_quality
            )
            
            return {
                "status": "success",
                "data": {
                    "original_text": request.text,
                    "optimized_text": optimized_messages[0].content,
                    "original_tokens": result.original_tokens,
                    "optimized_tokens": result.optimized_tokens,
                    "reduction_percentage": result.reduction_percentage,
                    "techniques_used": [t.value for t in result.techniques_used],
                    "quality_score": result.quality_score,
                    "optimization_time": result.optimization_time
                },
                "metadata": {
                    "strategy": strategy.value,
                    "preserve_quality": request.preserve_quality,
                    "max_tokens": request.max_tokens
                }
            }
        except ImportError:
            # Basic token optimization fallback
            original_length = len(request.text)
            optimized_text = request.text[:request.max_tokens] if len(request.text) > request.max_tokens else request.text
            optimized_length = len(optimized_text)
            
            return {
                "status": "success",
                "data": {
                    "original_text": request.text,
                    "optimized_text": optimized_text,
                    "original_tokens": original_length,
                    "optimized_tokens": optimized_length,
                    "reduction_percentage": ((original_length - optimized_length) / original_length * 100) if original_length > 0 else 0,
                    "techniques_used": ["truncation"],
                    "quality_score": 0.8,
                    "optimization_time": 0.001
                },
                "metadata": {
                    "strategy": request.strategy,
                    "preserve_quality": request.preserve_quality,
                    "max_tokens": request.max_tokens
                },
                "note": "Token optimizer not available - using basic truncation"
            }
        
    except Exception as e:
        logger.error(f"Error analyzing token optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Functions

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
    if db_health.get("database", False):
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
        try:
            from ...core.caching import get_cache_manager
            cache_manager = get_cache_manager()
            cache_results = cache_manager.optimize_cache()
            logger.info(f"Cache optimization completed: {cache_results}")
        except ImportError:
            logger.info("Cache optimization skipped - cache manager not available")
        
        # Optimize database
        try:
            from ...core.database import get_database_manager
            db_manager = await get_database_manager()
            db_results = await db_manager.optimize_queries()
            logger.info(f"Database optimization completed: {db_results}")
        except ImportError:
            logger.info("Database optimization skipped - database manager not available")
        
        # Optimize memory
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            memory_results = await resource_manager.optimize_memory()
            logger.info(f"Memory optimization completed: {memory_results}")
        except ImportError:
            # Fallback to basic garbage collection
            import gc
            collected = gc.collect()
            logger.info(f"Basic memory optimization completed: {collected} objects collected")
        
        logger.info("Comprehensive optimization completed successfully")
        
    except Exception as e:
        logger.error(f"Background optimization failed: {e}")