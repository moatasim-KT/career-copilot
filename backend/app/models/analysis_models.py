"""
Pydantic models for analysis history and agent execution tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class AgentExecutionBase(BaseModel):
    """Base model for agent execution."""
    
    agent_name: str = Field(..., description="Name of the agent")
    agent_type: Optional[str] = Field(None, description="Type/category of the agent")
    status: str = Field(..., description="Execution status")
    
    # Performance metrics
    execution_time: Optional[Decimal] = Field(None, description="Execution time in seconds")
    token_usage: Optional[int] = Field(None, description="Total tokens used")
    cost: Optional[Decimal] = Field(None, description="Cost in USD")
    
    # LLM provider information
    llm_provider: Optional[str] = Field(None, description="LLM provider used")
    model_name: Optional[str] = Field(None, description="Model name used")
    prompt_tokens: Optional[int] = Field(None, description="Prompt tokens used")
    completion_tokens: Optional[int] = Field(None, description="Completion tokens used")
    
    # Error handling
    retry_count: int = Field(0, description="Number of retries attempted")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Type of error")
    fallback_used: bool = Field(False, description="Whether fallback was used")
    fallback_provider: Optional[str] = Field(None, description="Fallback provider used")
    
    # Circuit breaker information
    circuit_breaker_triggered: bool = Field(False, description="Whether circuit breaker was triggered")
    circuit_breaker_state: Optional[str] = Field(None, description="Circuit breaker state")
    
    # Request correlation
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracking")
    request_id: Optional[str] = Field(None, description="Request ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Result information
    result_size_bytes: Optional[int] = Field(None, description="Size of result in bytes")
    result_quality_score: Optional[Decimal] = Field(None, description="Quality score of result")
    
    # Additional metadata
    execution_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AgentExecutionCreate(AgentExecutionBase):
    """Model for creating agent execution records."""
    
    analysis_id: UUID = Field(..., description="Analysis ID this execution belongs to")


class AgentExecutionUpdate(BaseModel):
    """Model for updating agent execution records."""
    
    status: Optional[str] = Field(None, description="Execution status")
    execution_time: Optional[Decimal] = Field(None, description="Execution time in seconds")
    token_usage: Optional[int] = Field(None, description="Total tokens used")
    cost: Optional[Decimal] = Field(None, description="Cost in USD")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Type of error")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result_size_bytes: Optional[int] = Field(None, description="Size of result in bytes")
    result_quality_score: Optional[Decimal] = Field(None, description="Quality score of result")
    execution_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AgentExecutionResponse(AgentExecutionBase):
    """Model for agent execution responses."""
    
    id: UUID = Field(..., description="Unique identifier")
    analysis_id: UUID = Field(..., description="Analysis ID this execution belongs to")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AnalysisHistoryBase(BaseModel):
    """Base model for analysis history."""
    
    analysis_type: str = Field(..., description="Type of analysis performed")
    status: str = Field(..., description="Analysis status")
    risk_score: Optional[Decimal] = Field(None, description="Overall risk score")
    processing_time: Optional[Decimal] = Field(None, description="Processing time in seconds")
    
    # Results and metadata
    risk_level: Optional[str] = Field(None, description="Risk level classification")
    risky_clauses_count: Optional[int] = Field(0, description="Number of risky clauses found")
    recommendations_count: Optional[int] = Field(0, description="Number of recommendations")
    model_used: Optional[str] = Field(None, description="AI model used for analysis")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    total_cost: Optional[Decimal] = Field(None, description="Total cost in USD")
    
    # Agent tracking
    completed_agents: Optional[List[str]] = Field([], description="List of completed agents")
    failed_agents: Optional[List[str]] = Field([], description="List of failed agents")
    agent_count: Optional[int] = Field(0, description="Total number of agents")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    retry_count: int = Field(0, description="Number of retries attempted")
    fallback_used: bool = Field(False, description="Whether fallback was used")
    
    # Additional metadata
    analysis_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AnalysisHistoryCreate(AnalysisHistoryBase):
    """Model for creating analysis history records."""
    
    contract_id: UUID = Field(..., description="Contract ID this analysis belongs to")


class AnalysisHistoryUpdate(BaseModel):
    """Model for updating analysis history records."""
    
    status: Optional[str] = Field(None, description="Analysis status")
    risk_score: Optional[Decimal] = Field(None, description="Overall risk score")
    processing_time: Optional[Decimal] = Field(None, description="Processing time in seconds")
    risk_level: Optional[str] = Field(None, description="Risk level classification")
    risky_clauses_count: Optional[int] = Field(None, description="Number of risky clauses found")
    recommendations_count: Optional[int] = Field(None, description="Number of recommendations")
    model_used: Optional[str] = Field(None, description="AI model used for analysis")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    total_cost: Optional[Decimal] = Field(None, description="Total cost in USD")
    completed_agents: Optional[List[str]] = Field(None, description="List of completed agents")
    failed_agents: Optional[List[str]] = Field(None, description="List of failed agents")
    agent_count: Optional[int] = Field(None, description="Total number of agents")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    analysis_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AnalysisHistoryResponse(AnalysisHistoryBase):
    """Model for analysis history responses."""
    
    id: UUID = Field(..., description="Unique identifier")
    contract_id: UUID = Field(..., description="Contract ID this analysis belongs to")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    # Related data
    agent_executions: Optional[List[AgentExecutionResponse]] = Field([], description="Agent executions for this analysis")
    
    class Config:
        from_attributes = True


class AnalysisHistoryWithExecutions(AnalysisHistoryResponse):
    """Analysis history with detailed agent execution information."""
    
    agent_executions: List[AgentExecutionResponse] = Field(..., description="Detailed agent executions")


class AnalysisPerformanceMetrics(BaseModel):
    """Performance metrics for analysis."""
    
    total_analyses: int = Field(..., description="Total number of analyses")
    avg_processing_time: Optional[Decimal] = Field(None, description="Average processing time")
    avg_cost: Optional[Decimal] = Field(None, description="Average cost")
    avg_tokens: Optional[int] = Field(None, description="Average tokens used")
    success_rate: Decimal = Field(..., description="Success rate percentage")
    
    # Agent performance
    agent_performance: Dict[str, Dict[str, Any]] = Field({}, description="Performance by agent")
    
    # Provider performance
    provider_performance: Dict[str, Dict[str, Any]] = Field({}, description="Performance by LLM provider")
    
    # Time-based metrics
    analyses_by_day: Dict[str, int] = Field({}, description="Analyses count by day")
    cost_by_day: Dict[str, Decimal] = Field({}, description="Cost by day")


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for individual agents."""
    
    agent_name: str = Field(..., description="Agent name")
    total_executions: int = Field(..., description="Total executions")
    success_count: int = Field(..., description="Successful executions")
    failure_count: int = Field(..., description="Failed executions")
    success_rate: Decimal = Field(..., description="Success rate percentage")
    
    avg_execution_time: Optional[Decimal] = Field(None, description="Average execution time")
    avg_cost: Optional[Decimal] = Field(None, description="Average cost")
    avg_tokens: Optional[int] = Field(None, description="Average tokens used")
    
    # Error analysis
    error_types: Dict[str, int] = Field({}, description="Error types and counts")
    retry_statistics: Dict[str, int] = Field({}, description="Retry statistics")
    
    # Provider usage
    provider_usage: Dict[str, int] = Field({}, description="Usage by provider")
    fallback_usage: int = Field(0, description="Number of fallback usages")


class AnalysisHistoryFilter(BaseModel):
    """Filter model for analysis history queries."""
    
    contract_id: Optional[UUID] = Field(None, description="Filter by contract ID")
    analysis_type: Optional[str] = Field(None, description="Filter by analysis type")
    status: Optional[str] = Field(None, description="Filter by status")
    risk_level: Optional[str] = Field(None, description="Filter by risk level")
    model_used: Optional[str] = Field(None, description="Filter by model used")
    
    # Date range filters
    created_after: Optional[datetime] = Field(None, description="Filter by creation date after")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date before")
    completed_after: Optional[datetime] = Field(None, description="Filter by completion date after")
    completed_before: Optional[datetime] = Field(None, description="Filter by completion date before")
    
    # Performance filters
    min_processing_time: Optional[Decimal] = Field(None, description="Minimum processing time")
    max_processing_time: Optional[Decimal] = Field(None, description="Maximum processing time")
    min_cost: Optional[Decimal] = Field(None, description="Minimum cost")
    max_cost: Optional[Decimal] = Field(None, description="Maximum cost")
    
    # Include soft deleted records
    include_deleted: bool = Field(False, description="Include soft deleted records")


class AgentExecutionFilter(BaseModel):
    """Filter model for agent execution queries."""
    
    analysis_id: Optional[UUID] = Field(None, description="Filter by analysis ID")
    agent_name: Optional[str] = Field(None, description="Filter by agent name")
    agent_type: Optional[str] = Field(None, description="Filter by agent type")
    status: Optional[str] = Field(None, description="Filter by status")
    llm_provider: Optional[str] = Field(None, description="Filter by LLM provider")
    model_name: Optional[str] = Field(None, description="Filter by model name")
    error_type: Optional[str] = Field(None, description="Filter by error type")
    
    # Date range filters
    started_after: Optional[datetime] = Field(None, description="Filter by start date after")
    started_before: Optional[datetime] = Field(None, description="Filter by start date before")
    completed_after: Optional[datetime] = Field(None, description="Filter by completion date after")
    completed_before: Optional[datetime] = Field(None, description="Filter by completion date before")
    
    # Performance filters
    min_execution_time: Optional[Decimal] = Field(None, description="Minimum execution time")
    max_execution_time: Optional[Decimal] = Field(None, description="Maximum execution time")
    min_cost: Optional[Decimal] = Field(None, description="Minimum cost")
    max_cost: Optional[Decimal] = Field(None, description="Maximum cost")
    
    # Error filters
    has_errors: Optional[bool] = Field(None, description="Filter by presence of errors")
    fallback_used: Optional[bool] = Field(None, description="Filter by fallback usage")
    circuit_breaker_triggered: Optional[bool] = Field(None, description="Filter by circuit breaker triggers")


# Validation functions are handled by Pydantic v2 field validators in the model classes