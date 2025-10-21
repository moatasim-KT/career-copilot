"""
Enhanced LLM Manager API endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.enhanced_llm_manager import (
    get_enhanced_llm_manager,
    EnhancedLLMManager,
    TaskType,
    RoutingCriteria,
    LLMProvider
)
from ...core.auth import get_current_user
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/enhanced-llm", tags=["Enhanced LLM"])


class CompletionRequest(BaseModel):
    """Request model for LLM completion."""
    prompt: str = Field(..., description="Input prompt for completion")
    task_type: TaskType = Field(default=TaskType.GENERAL, description="Type of task")
    routing_criteria: RoutingCriteria = Field(default=RoutingCriteria.COST, description="Provider selection criteria")
    preferred_provider: Optional[str] = Field(default=None, description="Preferred provider ID")
    fallback_enabled: bool = Field(default=True, description="Enable fallback to other providers")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Temperature override")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8000, description="Max tokens override")


class CompletionResponse(BaseModel):
    """Response model for LLM completion."""
    content: str
    provider: str
    model: str
    confidence_score: float
    processing_time: float
    token_usage: Dict[str, int]
    cost: float
    request_id: str
    metadata: Dict[str, Any]


class ProviderHealthResponse(BaseModel):
    """Response model for provider health check."""
    provider_id: str
    healthy: bool
    last_checked: str


class ProviderMetricsResponse(BaseModel):
    """Response model for provider metrics."""
    provider_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    avg_cost_per_request: float
    total_tokens_used: int
    total_cost: float
    error_rate: float
    availability: float
    health_score: float


class ProviderInfoResponse(BaseModel):
    """Response model for provider information."""
    provider_id: str
    provider_type: str
    model_name: str
    enabled: bool
    capabilities: List[str]
    cost_per_token: float
    priority: int
    circuit_breaker_state: str
    metadata: Dict[str, Any]


@router.post("/completion", response_model=CompletionResponse)
async def generate_completion(
    request: CompletionRequest,
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """
    Generate completion using enhanced LLM manager with intelligent routing.
    
    This endpoint provides:
    - Intelligent provider selection based on task type and criteria
    - Automatic fallback to alternative providers
    - Cost optimization and performance monitoring
    - Circuit breaker protection
    """
    try:
        logger.info(
            f"Generating completion for user {current_user.get('user_id')} "
            f"with task type {request.task_type} and criteria {request.routing_criteria}"
        )
        
        # Prepare kwargs for completion
        kwargs = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        
        # Generate completion
        response = await llm_manager.get_completion(
            prompt=request.prompt,
            task_type=request.task_type,
            routing_criteria=request.routing_criteria,
            preferred_provider=request.preferred_provider,
            fallback_enabled=request.fallback_enabled,
            max_retries=request.max_retries,
            **kwargs
        )
        
        logger.info(
            f"Completion generated successfully: {response.provider.value} "
            f"({response.processing_time:.2f}s, confidence: {response.confidence_score:.2f})"
        )
        
        return CompletionResponse(
            content=response.content,
            provider=response.provider.value,
            model=response.model,
            confidence_score=response.confidence_score,
            processing_time=response.processing_time,
            token_usage=response.token_usage,
            cost=response.cost,
            request_id=response.request_id,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to generate completion: {e}")
        raise HTTPException(status_code=500, detail=f"Completion generation failed: {str(e)}")


@router.get("/providers", response_model=List[str])
async def get_available_providers(
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Get list of available LLM providers."""
    try:
        providers = llm_manager.get_available_providers()
        logger.info(f"Retrieved {len(providers)} available providers")
        return providers
        
    except Exception as e:
        logger.error(f"Failed to get available providers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")


@router.get("/providers/{provider_id}", response_model=ProviderInfoResponse)
async def get_provider_info(
    provider_id: str,
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Get detailed information about a specific provider."""
    try:
        info = llm_manager.get_provider_info(provider_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        return ProviderInfoResponse(
            provider_id=info["provider_id"],
            provider_type=info["provider_type"],
            model_name=info["model_name"],
            enabled=info["enabled"],
            capabilities=info["capabilities"],
            cost_per_token=info["cost_per_token"],
            priority=info["priority"],
            circuit_breaker_state=info["circuit_breaker_state"],
            metadata=info["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider info for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


@router.get("/providers/{provider_id}/metrics", response_model=ProviderMetricsResponse)
async def get_provider_metrics(
    provider_id: str,
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Get performance metrics for a specific provider."""
    try:
        all_metrics = llm_manager.get_provider_metrics()
        if provider_id not in all_metrics:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        metrics = all_metrics[provider_id]
        
        return ProviderMetricsResponse(
            provider_id=provider_id,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            avg_response_time=metrics.avg_response_time,
            avg_cost_per_request=metrics.avg_cost_per_request,
            total_tokens_used=metrics.total_tokens_used,
            total_cost=metrics.total_cost,
            error_rate=metrics.error_rate,
            availability=metrics.availability,
            health_score=metrics.health_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/health", response_model=List[ProviderHealthResponse])
async def check_provider_health(
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Check health status of all providers."""
    try:
        health_results = await llm_manager.health_check_all_providers()
        
        responses = []
        for provider_id, healthy in health_results.items():
            responses.append(ProviderHealthResponse(
                provider_id=provider_id,
                healthy=healthy,
                last_checked=str(datetime.now())
            ))
        
        logger.info(f"Health check completed for {len(responses)} providers")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to check provider health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/best-provider")
async def get_best_provider(
    task_type: TaskType = Query(default=TaskType.GENERAL, description="Task type"),
    criteria: RoutingCriteria = Query(default=RoutingCriteria.COST, description="Selection criteria"),
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Get the best provider for a specific task type and criteria."""
    try:
        best_provider = await llm_manager.get_best_provider(task_type, criteria)
        
        if not best_provider:
            raise HTTPException(
                status_code=404, 
                detail=f"No suitable provider found for task type {task_type} with criteria {criteria}"
            )
        
        return {
            "best_provider": best_provider,
            "task_type": task_type.value,
            "criteria": criteria.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best provider: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get best provider: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Clear LLM response cache."""
    try:
        await llm_manager.clear_cache()
        logger.info(f"Cache cleared by user {current_user.get('user_id')}")
        
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/metrics/reset")
async def reset_metrics(
    provider_id: Optional[str] = Query(default=None, description="Provider ID to reset (all if not specified)"),
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Reset provider metrics."""
    try:
        llm_manager.reset_provider_metrics(provider_id)
        
        message = f"Metrics reset for {provider_id}" if provider_id else "All provider metrics reset"
        logger.info(f"{message} by user {current_user.get('user_id')}")
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.get("/task-types")
async def get_task_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available task types for routing."""
    return {
        "task_types": [task_type.value for task_type in TaskType],
        "descriptions": {
            TaskType.CONTRACT_ANALYSIS.value: "Complex job application tracking requiring high accuracy",
            TaskType.RISK_ASSESSMENT.value: "Risk evaluation and scoring tasks",
            TaskType.LEGAL_PRECEDENT.value: "Legal precedent research and analysis",
            TaskType.NEGOTIATION.value: "Contract negotiation strategy and communication",
            TaskType.COMMUNICATION.value: "General communication and correspondence",
            TaskType.GENERAL.value: "General purpose tasks"
        }
    }


@router.get("/routing-criteria")
async def get_routing_criteria(
    current_user: dict = Depends(get_current_user)
):
    """Get available routing criteria for provider selection."""
    return {
        "criteria": [criteria.value for criteria in RoutingCriteria],
        "descriptions": {
            RoutingCriteria.COST.value: "Optimize for lowest cost per token",
            RoutingCriteria.PERFORMANCE.value: "Optimize for fastest response time",
            RoutingCriteria.QUALITY.value: "Optimize for highest quality results",
            RoutingCriteria.SPEED.value: "Optimize for fastest processing",
            RoutingCriteria.AVAILABILITY.value: "Optimize for highest availability"
        }
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    current_user: dict = Depends(get_current_user),
    llm_manager: EnhancedLLMManager = Depends(get_enhanced_llm_manager)
):
    """Get summary of all provider metrics."""
    try:
        all_metrics = llm_manager.get_provider_metrics()
        
        summary = {
            "total_providers": len(all_metrics),
            "total_requests": sum(m.total_requests for m in all_metrics.values()),
            "total_successful": sum(m.successful_requests for m in all_metrics.values()),
            "total_failed": sum(m.failed_requests for m in all_metrics.values()),
            "total_cost": sum(m.total_cost for m in all_metrics.values()),
            "total_tokens": sum(m.total_tokens_used for m in all_metrics.values()),
            "avg_response_time": sum(m.avg_response_time for m in all_metrics.values()) / len(all_metrics) if all_metrics else 0,
            "overall_success_rate": 0
        }
        
        if summary["total_requests"] > 0:
            summary["overall_success_rate"] = summary["total_successful"] / summary["total_requests"]
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")


# Import datetime for health check response
from datetime import datetime