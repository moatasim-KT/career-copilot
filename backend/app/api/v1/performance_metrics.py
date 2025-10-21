"""
API endpoints for performance metrics and streaming management.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio

from ...core.performance_metrics import get_performance_metrics_collector, TimeWindow
from ...core.streaming_manager import get_streaming_manager, StreamingMode
from ...core.token_optimizer import get_token_optimizer, OptimizationStrategy, TokenBudget
from ...services.ai_service_manager import get_ai_service_manager, ModelType
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])

performance_collector = get_performance_metrics_collector()
streaming_manager = get_streaming_manager()
token_optimizer = get_token_optimizer()
ai_service_manager = get_ai_service_manager()


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


@router.get("/metrics/summary")
async def get_performance_summary(
    time_window: str = Query("hour", description="Time window: minute, hour, day, week"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    model: Optional[str] = Query(None, description="Filter by model")
) -> Dict[str, Any]:
    """Get comprehensive performance metrics summary."""
    try:
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
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/latency")
async def get_latency_metrics(
    provider: str = Query(..., description="Provider name"),
    model: str = Query(..., description="Model name"),
    operation: str = Query(..., description="Operation type"),
    time_window: str = Query("hour", description="Time window")
) -> Dict[str, Any]:
    """Get detailed latency metrics for a specific provider/model/operation."""
    try:
        window_map = {
            "minute": TimeWindow.MINUTE,
            "hour": TimeWindow.HOUR,
            "day": TimeWindow.DAY,
            "week": TimeWindow.WEEK
        }
        
        window = window_map.get(time_window.lower(), TimeWindow.HOUR)
        
        latency_metrics = performance_collector.get_latency_metrics(
            provider=provider,
            model=model,
            operation=operation,
            time_window=window
        )
        
        if not latency_metrics:
            return {
                "status": "success",
                "data": None,
                "message": "No latency data available for the specified parameters"
            }
        
        return {
            "status": "success",
            "data": {
                "mean_latency": latency_metrics.mean,
                "median_latency": latency_metrics.median,
                "p95_latency": latency_metrics.p95,
                "p99_latency": latency_metrics.p99,
                "min_latency": latency_metrics.min_latency,
                "max_latency": latency_metrics.max_latency,
                "sample_count": latency_metrics.sample_count
            },
            "metadata": {
                "provider": provider,
                "model": model,
                "operation": operation,
                "time_window": time_window
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting latency metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/success-rate")
async def get_success_rate_metrics(
    provider: str = Query(..., description="Provider name"),
    model: str = Query(..., description="Model name"),
    operation: str = Query(..., description="Operation type"),
    time_window: str = Query("hour", description="Time window")
) -> Dict[str, Any]:
    """Get success rate metrics for a specific provider/model/operation."""
    try:
        window_map = {
            "minute": TimeWindow.MINUTE,
            "hour": TimeWindow.HOUR,
            "day": TimeWindow.DAY,
            "week": TimeWindow.WEEK
        }
        
        window = window_map.get(time_window.lower(), TimeWindow.HOUR)
        
        success_metrics = performance_collector.get_success_rate_metrics(
            provider=provider,
            model=model,
            operation=operation,
            time_window=window
        )
        
        if not success_metrics:
            return {
                "status": "success",
                "data": None,
                "message": "No success rate data available for the specified parameters"
            }
        
        return {
            "status": "success",
            "data": {
                "success_rate": success_metrics.success_rate,
                "total_requests": success_metrics.total_requests,
                "successful_requests": success_metrics.successful_requests,
                "failed_requests": success_metrics.failed_requests,
                "error_breakdown": success_metrics.error_breakdown
            },
            "metadata": {
                "provider": provider,
                "model": model,
                "operation": operation,
                "time_window": time_window
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting success rate metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/token-usage")
async def get_token_usage_metrics(
    provider: str = Query(..., description="Provider name"),
    model: str = Query(..., description="Model name"),
    operation: str = Query(..., description="Operation type"),
    time_window: str = Query("hour", description="Time window")
) -> Dict[str, Any]:
    """Get token usage metrics for a specific provider/model/operation."""
    try:
        window_map = {
            "minute": TimeWindow.MINUTE,
            "hour": TimeWindow.HOUR,
            "day": TimeWindow.DAY,
            "week": TimeWindow.WEEK
        }
        
        window = window_map.get(time_window.lower(), TimeWindow.HOUR)
        
        token_metrics = performance_collector.get_token_usage_metrics(
            provider=provider,
            model=model,
            operation=operation,
            time_window=window
        )
        
        if not token_metrics:
            return {
                "status": "success",
                "data": None,
                "message": "No token usage data available for the specified parameters"
            }
        
        return {
            "status": "success",
            "data": {
                "total_tokens": token_metrics.total_tokens,
                "prompt_tokens": token_metrics.prompt_tokens,
                "completion_tokens": token_metrics.completion_tokens,
                "tokens_per_second": token_metrics.tokens_per_second,
                "cost_per_token": token_metrics.cost_per_token,
                "total_cost": token_metrics.total_cost
            },
            "metadata": {
                "provider": provider,
                "model": model,
                "operation": operation,
                "time_window": time_window
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting token usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaming/status")
async def get_streaming_status() -> Dict[str, Any]:
    """Get current streaming status and performance."""
    try:
        streaming_summary = streaming_manager.get_streaming_performance_summary()
        
        return {
            "status": "success",
            "data": streaming_summary,
            "timestamp": performance_collector.get_performance_summary()["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error getting streaming status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaming/metrics")
async def get_streaming_metrics(
    provider: str = Query(..., description="Provider name"),
    model: str = Query(..., description="Model name"),
    operation: str = Query(..., description="Operation type"),
    time_window: str = Query("hour", description="Time window")
) -> Dict[str, Any]:
    """Get streaming performance metrics."""
    try:
        window_map = {
            "minute": TimeWindow.MINUTE,
            "hour": TimeWindow.HOUR,
            "day": TimeWindow.DAY,
            "week": TimeWindow.WEEK
        }
        
        window = window_map.get(time_window.lower(), TimeWindow.HOUR)
        
        streaming_metrics = performance_collector.get_streaming_metrics(
            provider=provider,
            model=model,
            operation=operation,
            time_window=window
        )
        
        if not streaming_metrics:
            return {
                "status": "success",
                "data": None,
                "message": "No streaming data available for the specified parameters"
            }
        
        return {
            "status": "success",
            "data": {
                "first_token_latency": streaming_metrics.first_token_latency,
                "tokens_per_second": streaming_metrics.tokens_per_second,
                "total_streaming_time": streaming_metrics.total_streaming_time,
                "chunk_count": streaming_metrics.chunk_count,
                "average_chunk_size": streaming_metrics.average_chunk_size,
                "streaming_efficiency": streaming_metrics.streaming_efficiency
            },
            "metadata": {
                "provider": provider,
                "model": model,
                "operation": operation,
                "time_window": time_window
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting streaming metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/streaming/analyze")
async def stream_analysis(request: StreamingRequest) -> StreamingResponse:
    """Start streaming analysis with real-time response."""
    try:
        # Validate model type
        try:
            model_type = ModelType(request.model_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid model type: {request.model_type}")
        
        # Validate streaming mode
        try:
            streaming_mode = StreamingMode(request.streaming_mode.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid streaming mode: {request.streaming_mode}")
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                async for chunk in await ai_service_manager.analyze_with_fallback(
                    model_type=model_type,
                    prompt=request.prompt,
                    context=request.context,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    enable_streaming=True,
                    streaming_mode=streaming_mode
                ):
                    # Format chunk as JSON for streaming
                    chunk_data = {
                        "content": chunk.content,
                        "chunk_id": chunk.chunk_id,
                        "sequence_number": chunk.sequence_number,
                        "timestamp": chunk.timestamp,
                        "token_count": chunk.token_count,
                        "is_final": chunk.is_final,
                        "metadata": chunk.metadata
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    if chunk.is_final:
                        yield "data: [DONE]\n\n"
                        break
                        
            except Exception as e:
                error_data = {
                    "error": str(e),
                    "type": type(e).__name__,
                    "is_final": True
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting streaming analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token-optimization/analyze")
async def analyze_token_optimization(request: TokenOptimizationRequest) -> Dict[str, Any]:
    """Analyze token optimization for given text."""
    try:
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
        
    except Exception as e:
        logger.error(f"Error analyzing token optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token-optimization/stats")
async def get_token_optimization_stats() -> Dict[str, Any]:
    """Get token optimization statistics."""
    try:
        stats = token_optimizer.get_optimization_stats()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting token optimization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_performance_cache() -> Dict[str, Any]:
    """Clear performance metrics cache."""
    try:
        # Clear various caches
        performance_collector.clear_old_metrics(max_age_hours=0)  # Clear all
        token_optimizer.clear_cache()
        ai_service_manager.clear_cache()
        
        return {
            "status": "success",
            "message": "Performance caches cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing performance cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_performance_health() -> Dict[str, Any]:
    """Get performance system health status."""
    try:
        # Get AI service health
        ai_health = ai_service_manager.get_service_health()
        
        # Get streaming status
        streaming_status = streaming_manager.get_active_sessions()
        
        # Get optimization stats
        optimization_stats = token_optimizer.get_optimization_stats()
        
        return {
            "status": "success",
            "data": {
                "ai_services": ai_health,
                "streaming": {
                    "active_sessions": len(streaming_status),
                    "session_details": streaming_status
                },
                "token_optimization": {
                    "cache_size": optimization_stats.get("cache_size", 0),
                    "total_optimizations": optimization_stats.get("total_optimizations", 0)
                },
                "performance_metrics": {
                    "collectors_active": True,
                    "metrics_available": True
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance health: {e}")
        raise HTTPException(status_code=500, detail=str(e))