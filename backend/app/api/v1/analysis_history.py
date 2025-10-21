"""
API endpoints for analysis history and agent execution management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db_session
from ...models.analysis_models import (
    AnalysisHistoryCreate,
    AnalysisHistoryUpdate,
    AnalysisHistoryResponse,
    AnalysisHistoryWithExecutions,
    AnalysisHistoryFilter,
    AgentExecutionCreate,
    AgentExecutionUpdate,
    AgentExecutionResponse,
    AgentExecutionFilter,
    AnalysisPerformanceMetrics,
    AgentPerformanceMetrics
)
from ...repositories.analysis_repository import AnalysisRepository

router = APIRouter(prefix="/analysis-history", tags=["analysis-history"])


@router.post("/", response_model=AnalysisHistoryResponse)
def create_analysis_history(
    analysis_data: AnalysisHistoryCreate,
    db = Depends(get_db_session)
):
    """Create a new analysis history record."""
    repository = AnalysisRepository(db)
    
    try:
        analysis = repository.create_analysis_history(analysis_data)
        return AnalysisHistoryResponse.from_orm(analysis)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create analysis history: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisHistoryResponse)
def get_analysis_history(
    analysis_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get analysis history by ID."""
    repository = AnalysisRepository(db)
    
    analysis = repository.get_analysis_history(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    
    return AnalysisHistoryResponse.from_orm(analysis)


@router.get("/{analysis_id}/with-executions", response_model=AnalysisHistoryWithExecutions)
def get_analysis_history_with_executions(
    analysis_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get analysis history with agent executions."""
    repository = AnalysisRepository(db)
    
    analysis = repository.get_analysis_history_with_executions(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    
    return AnalysisHistoryWithExecutions.from_orm(analysis)


@router.put("/{analysis_id}", response_model=AnalysisHistoryResponse)
def update_analysis_history(
    analysis_id: UUID,
    update_data: AnalysisHistoryUpdate,
    db: Session = Depends(get_db_session)
):
    """Update analysis history record."""
    repository = AnalysisRepository(db)
    
    analysis = repository.update_analysis_history(analysis_id, update_data)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    
    return AnalysisHistoryResponse.from_orm(analysis)


@router.delete("/{analysis_id}")
def delete_analysis_history(
    analysis_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Soft delete analysis history record."""
    repository = AnalysisRepository(db)
    
    success = repository.soft_delete_analysis_history(analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    
    return {"message": "Analysis history deleted successfully"}


@router.get("/", response_model=List[AnalysisHistoryResponse])
def list_analysis_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    include_executions: bool = Query(False, description="Include agent executions"),
    
    # Filter parameters
    contract_id: Optional[UUID] = Query(None, description="Filter by contract ID"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    model_used: Optional[str] = Query(None, description="Filter by model used"),
    
    # Date filters
    created_after: Optional[datetime] = Query(None, description="Filter by creation date after"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date before"),
    completed_after: Optional[datetime] = Query(None, description="Filter by completion date after"),
    completed_before: Optional[datetime] = Query(None, description="Filter by completion date before"),
    
    include_deleted: bool = Query(False, description="Include soft deleted records"),
    
    db: Session = Depends(get_db_session)
):
    """List analysis history with optional filters."""
    repository = AnalysisRepository(db)
    
    # Build filters
    filters = AnalysisHistoryFilter(
        contract_id=contract_id,
        analysis_type=analysis_type,
        status=status,
        risk_level=risk_level,
        model_used=model_used,
        created_after=created_after,
        created_before=created_before,
        completed_after=completed_after,
        completed_before=completed_before,
        include_deleted=include_deleted
    )
    
    analyses, total = repository.list_analysis_history(
        filters=filters,
        skip=skip,
        limit=limit,
        include_executions=include_executions
    )
    
    # Add total count to response headers
    from fastapi import Response
    response = Response()
    response.headers["X-Total-Count"] = str(total)
    
    return [AnalysisHistoryResponse.from_orm(analysis) for analysis in analyses]


@router.get("/contract/{contract_id}", response_model=List[AnalysisHistoryResponse])
def get_analysis_history_by_contract(
    contract_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get all analysis history for a specific contract."""
    repository = AnalysisRepository(db)
    
    analyses = repository.get_analysis_history_by_contract(contract_id)
    return [AnalysisHistoryResponse.from_orm(analysis) for analysis in analyses]


# Agent Execution Endpoints

@router.post("/executions/", response_model=AgentExecutionResponse)
def create_agent_execution(
    execution_data: AgentExecutionCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new agent execution record."""
    repository = AnalysisRepository(db)
    
    try:
        execution = repository.create_agent_execution(execution_data)
        return AgentExecutionResponse.from_orm(execution)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create agent execution: {str(e)}")


@router.get("/executions/{execution_id}", response_model=AgentExecutionResponse)
def get_agent_execution(
    execution_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get agent execution by ID."""
    repository = AnalysisRepository(db)
    
    execution = repository.get_agent_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Agent execution not found")
    
    return AgentExecutionResponse.from_orm(execution)


@router.put("/executions/{execution_id}", response_model=AgentExecutionResponse)
def update_agent_execution(
    execution_id: UUID,
    update_data: AgentExecutionUpdate,
    db: Session = Depends(get_db_session)
):
    """Update agent execution record."""
    repository = AnalysisRepository(db)
    
    execution = repository.update_agent_execution(execution_id, update_data)
    if not execution:
        raise HTTPException(status_code=404, detail="Agent execution not found")
    
    return AgentExecutionResponse.from_orm(execution)


@router.get("/executions/", response_model=List[AgentExecutionResponse])
def list_agent_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    
    # Filter parameters
    analysis_id: Optional[UUID] = Query(None, description="Filter by analysis ID"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    llm_provider: Optional[str] = Query(None, description="Filter by LLM provider"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    
    # Date filters
    started_after: Optional[datetime] = Query(None, description="Filter by start date after"),
    started_before: Optional[datetime] = Query(None, description="Filter by start date before"),
    completed_after: Optional[datetime] = Query(None, description="Filter by completion date after"),
    completed_before: Optional[datetime] = Query(None, description="Filter by completion date before"),
    
    # Boolean filters
    has_errors: Optional[bool] = Query(None, description="Filter by presence of errors"),
    fallback_used: Optional[bool] = Query(None, description="Filter by fallback usage"),
    circuit_breaker_triggered: Optional[bool] = Query(None, description="Filter by circuit breaker triggers"),
    
    db: Session = Depends(get_db_session)
):
    """List agent executions with optional filters."""
    repository = AnalysisRepository(db)
    
    # Build filters
    filters = AgentExecutionFilter(
        analysis_id=analysis_id,
        agent_name=agent_name,
        agent_type=agent_type,
        status=status,
        llm_provider=llm_provider,
        model_name=model_name,
        error_type=error_type,
        started_after=started_after,
        started_before=started_before,
        completed_after=completed_after,
        completed_before=completed_before,
        has_errors=has_errors,
        fallback_used=fallback_used,
        circuit_breaker_triggered=circuit_breaker_triggered
    )
    
    executions, total = repository.list_agent_executions(
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    # Add total count to response headers
    from fastapi import Response
    response = Response()
    response.headers["X-Total-Count"] = str(total)
    
    return [AgentExecutionResponse.from_orm(execution) for execution in executions]


@router.get("/{analysis_id}/executions", response_model=List[AgentExecutionResponse])
def get_executions_by_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get all agent executions for a specific analysis."""
    repository = AnalysisRepository(db)
    
    executions = repository.get_executions_by_analysis(analysis_id)
    return [AgentExecutionResponse.from_orm(execution) for execution in executions]


# Analytics and Metrics Endpoints

@router.get("/metrics/performance", response_model=AnalysisPerformanceMetrics)
def get_analysis_performance_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    db: Session = Depends(get_db_session)
):
    """Get performance metrics for analyses."""
    repository = AnalysisRepository(db)
    
    metrics = repository.get_analysis_performance_metrics(start_date, end_date)
    return metrics


@router.get("/metrics/agents", response_model=List[AgentPerformanceMetrics])
def get_agent_performance_metrics(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    db: Session = Depends(get_db_session)
):
    """Get performance metrics for agents."""
    repository = AnalysisRepository(db)
    
    metrics = repository.get_agent_performance_metrics(agent_name, start_date, end_date)
    return metrics


@router.get("/metrics/costs")
def get_cost_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    group_by: str = Query("day", description="Group by: day, week, month, provider, model"),
    db: Session = Depends(get_db_session)
):
    """Get cost analysis grouped by specified dimension."""
    repository = AnalysisRepository(db)
    
    if group_by not in ['day', 'week', 'month', 'provider', 'model']:
        raise HTTPException(status_code=400, detail="Invalid group_by parameter")
    
    cost_data = repository.get_cost_analysis(start_date, end_date, group_by)
    return {"cost_data": cost_data, "group_by": group_by}


@router.get("/metrics/trends")
def get_performance_trends(
    metric: str = Query("execution_time", description="Metric: execution_time, cost, token_usage"),
    start_date: Optional[datetime] = Query(None, description="Start date for trends"),
    end_date: Optional[datetime] = Query(None, description="End date for trends"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    db: Session = Depends(get_db_session)
):
    """Get performance trends over time."""
    repository = AnalysisRepository(db)
    
    if metric not in ['execution_time', 'cost', 'token_usage']:
        raise HTTPException(status_code=400, detail="Invalid metric parameter")
    
    trends = repository.get_performance_trends(metric, start_date, end_date, agent_name)
    return {"trends": trends, "metric": metric}