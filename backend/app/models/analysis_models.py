"""
Pydantic models for analysis history and agent execution data.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisHistoryCreate(BaseModel):
    """Model for creating analysis history."""
    contract_id: UUID
    analysis_type: str
    status: str = "pending"
    risk_level: Optional[str] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    total_cost: Optional[Decimal] = None
    total_tokens: Optional[int] = None
    analysis_results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisHistoryUpdate(BaseModel):
    """Model for updating analysis history."""
    status: Optional[str] = None
    risk_level: Optional[str] = None
    processing_time: Optional[float] = None
    total_cost: Optional[Decimal] = None
    total_tokens: Optional[int] = None
    analysis_results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class AnalysisHistoryFilter(BaseModel):
    """Model for filtering analysis history."""
    contract_id: Optional[UUID] = None
    analysis_type: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    model_used: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    min_processing_time: Optional[float] = None
    max_processing_time: Optional[float] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
    include_deleted: bool = False


class AgentExecutionCreate(BaseModel):
    """Model for creating agent execution."""
    analysis_id: UUID
    agent_name: str
    agent_type: str
    agent_id: Optional[str] = None
    status: str = "running"
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentExecutionUpdate(BaseModel):
    """Model for updating agent execution."""
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    cost: Optional[Decimal] = None
    token_usage: Optional[int] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: Optional[int] = None
    fallback_used: Optional[bool] = None
    circuit_breaker_triggered: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentExecutionFilter(BaseModel):
    """Model for filtering agent executions."""
    analysis_id: Optional[UUID] = None
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    status: Optional[str] = None
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    error_type: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
    has_errors: Optional[bool] = None
    fallback_used: Optional[bool] = None
    circuit_breaker_triggered: Optional[bool] = None


class RetryStatistics(BaseModel):
    """Model for retry statistics."""
    total_retries: int
    average_retries: float
    max_retries: int
    retry_success_rate: Optional[float] = None
    common_retry_reasons: Optional[Dict[str, int]] = None


class AgentPerformanceMetrics(BaseModel):
    """Model for agent performance metrics."""
    agent_name: Optional[str] = None
    total_executions: int
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    success_rate: float
    average_duration: Optional[float] = None
    avg_execution_time: Optional[float] = None
    avg_cost: Optional[Decimal] = None
    avg_tokens: Optional[int] = None
    error_rate: float
    error_types: Optional[Dict[str, int]] = None
    retry_stats: Optional[RetryStatistics] = None
    retry_statistics: Optional[Dict[str, Any]] = None
    provider_usage: Optional[Dict[str, int]] = None
    fallback_usage: Optional[int] = None


class ProviderPerformanceMetrics(BaseModel):
    """Model for provider performance metrics."""
    provider: Optional[str] = None
    total_requests: int
    success_rate: float
    average_latency: float
    error_rate: float
    cost_metrics: Dict[str, Decimal]
    model_usage: Optional[Dict[str, int]] = None
    error_breakdown: Optional[Dict[str, int]] = None


class AnalysisPerformanceMetrics(BaseModel):
    """Model for analysis performance metrics."""
    total_analyses: int
    avg_processing_time: Optional[float] = None
    avg_cost: Optional[Decimal] = None
    avg_tokens: Optional[int] = None
    success_rate: Decimal
    agent_performance: Dict[str, AgentPerformanceMetrics]
    provider_performance: Dict[str, ProviderPerformanceMetrics]
    analyses_by_day: Dict[str, int]
    cost_by_day: Dict[str, Decimal]
    error_analysis: Optional[Dict[str, int]] = None
    trend_analysis: Optional[Dict[str, Any]] = None