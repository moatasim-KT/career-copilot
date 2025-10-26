"""
Repository for analysis history and agent execution data access.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from ..models.database_models import AnalysisHistory, AgentExecution, ContractAnalysis
from ..models.analysis_models import (
    AnalysisHistoryCreate,
    AnalysisHistoryUpdate,
    AnalysisHistoryFilter,
    AgentExecutionCreate,
    AgentExecutionUpdate,
    AgentExecutionFilter,
    AnalysisPerformanceMetrics,
    AgentPerformanceMetrics,
    ProviderPerformanceMetrics,
    RetryStatistics
)


class AnalysisRepository:
    """Repository for analysis history and agent execution operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Analysis History Methods
    
    def create_analysis_history(self, analysis_data: AnalysisHistoryCreate) -> AnalysisHistory:
        """Create a new analysis history record."""
        db_analysis = AnalysisHistory(**analysis_data.dict())
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        return db_analysis
    
    def get_analysis_history(self, analysis_id: UUID) -> Optional[AnalysisHistory]:
        """Get analysis history by ID."""
        return self.db.query(AnalysisHistory).filter(
            AnalysisHistory.id == analysis_id,
            AnalysisHistory.deleted_at.is_(None)
        ).first()
    
    def get_analysis_history_with_executions(self, analysis_id: UUID) -> Optional[AnalysisHistory]:
        """Get analysis history with agent executions."""
        return self.db.query(AnalysisHistory).options(
            joinedload(AnalysisHistory.agent_executions)
        ).filter(
            AnalysisHistory.id == analysis_id,
            AnalysisHistory.deleted_at.is_(None)
        ).first()
    
    def update_analysis_history(self, analysis_id: UUID, update_data: AnalysisHistoryUpdate) -> Optional[AnalysisHistory]:
        """Update analysis history record."""
        db_analysis = self.get_analysis_history(analysis_id)
        if not db_analysis:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_analysis, field, value)
        
        db_analysis.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_analysis)
        return db_analysis
    
    def soft_delete_analysis_history(self, analysis_id: UUID) -> bool:
        """Soft delete analysis history record."""
        db_analysis = self.get_analysis_history(analysis_id)
        if not db_analysis:
            return False
        
        db_analysis.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
        
    async def calculate_agent_performance(
        self,
        agent_id: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> AgentPerformanceMetrics:
        """
        Calculate performance metrics for an agent or all agents.
        
        Args:
            agent_id: Optional ID of specific agent to analyze
            time_window: Optional time window for analysis (e.g., last 24 hours)
            
        Returns:
            AgentPerformanceMetrics with calculated performance data
        """
        query = self.db.query(AgentExecution)
        
        if agent_id:
            query = query.filter(AgentExecution.agent_id == agent_id)
        
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - time_window
            query = query.filter(AgentExecution.created_at >= cutoff_time)
        
        executions = query.all()
        
        if not executions:
            return AgentPerformanceMetrics(
                total_executions=0,
                success_rate=0.0,
                average_duration=0.0,
                error_rate=0.0,
                retry_stats=RetryStatistics(
                    total_retries=0,
                    average_retries=0.0,
                    max_retries=0
                )
            )
        
        total = len(executions)
        successful = sum(1 for e in executions if e.status == 'completed')
        errors = sum(1 for e in executions if e.status == 'failed')
        durations = [e.duration for e in executions if e.duration is not None]
        retries = [e.retry_count for e in executions if e.retry_count is not None]
        
        return AgentPerformanceMetrics(
            total_executions=total,
            success_rate=float(successful / total) if total > 0 else 0.0,
            average_duration=float(sum(durations) / len(durations)) if durations else 0.0,
            error_rate=float(errors / total) if total > 0 else 0.0,
            retry_stats=RetryStatistics(
                total_retries=sum(retries),
                average_retries=float(sum(retries) / len(retries)) if retries else 0.0,
                max_retries=max(retries) if retries else 0
            )
        )
    
    async def calculate_provider_performance(
        self,
        provider: str,
        time_window: Optional[timedelta] = None
    ) -> ProviderPerformanceMetrics:
        """
        Calculate performance metrics for an AI provider.
        
        Args:
            provider: Name of the AI provider (e.g., 'openai', 'anthropic')
            time_window: Optional time window for analysis
            
        Returns:
            ProviderPerformanceMetrics with calculated metrics
        """
        query = self.db.query(
            AgentExecution
        ).filter(
            AgentExecution.provider == provider
        )
        
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - time_window
            query = query.filter(AgentExecution.created_at >= cutoff_time)
            
        executions = query.all()
        
        if not executions:
            return ProviderPerformanceMetrics(
                total_requests=0,
                success_rate=0.0,
                average_latency=0.0,
                error_rate=0.0,
                cost_metrics={
                    'total_cost': Decimal('0.0'),
                    'average_cost': Decimal('0.0')
                }
            )
            
        total = len(executions)
        successful = sum(1 for e in executions if e.status == 'completed')
        errors = sum(1 for e in executions if e.status == 'failed')
        latencies = [e.duration for e in executions if e.duration is not None]
        costs = [e.cost for e in executions if e.cost is not None]
        
        return ProviderPerformanceMetrics(
            total_requests=total,
            success_rate=float(successful / total) if total > 0 else 0.0,
            average_latency=float(sum(latencies) / len(latencies)) if latencies else 0.0,
            error_rate=float(errors / total) if total > 0 else 0.0,
            cost_metrics={
                'total_cost': sum(costs, Decimal('0.0')),
                'average_cost': sum(costs, Decimal('0.0')) / len(costs) if costs else Decimal('0.0')
            }
        )
    
    async def calculate_retry_statistics(
        self,
        time_window: Optional[timedelta] = None
    ) -> RetryStatistics:
        """
        Calculate retry statistics across all executions.
        
        Args:
            time_window: Optional time window for analysis
            
        Returns:
            RetryStatistics with retry metrics
        """
        query = self.db.query(AgentExecution)
        
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - time_window
            query = query.filter(AgentExecution.created_at >= cutoff_time)
            
        executions = query.all()
        retries = [e.retry_count for e in executions if e.retry_count is not None]
        
        if not retries:
            return RetryStatistics(
                total_retries=0,
                average_retries=0.0,
                max_retries=0
            )
            
        return RetryStatistics(
            total_retries=sum(retries),
            average_retries=float(sum(retries) / len(retries)),
            max_retries=max(retries)
        )
    
    def list_analysis_history(
        self,
        filters: Optional[AnalysisHistoryFilter] = None,
        skip: int = 0,
        limit: int = 100,
        include_executions: bool = False
    ) -> Tuple[List[AnalysisHistory], int]:
        """List analysis history with optional filters."""
        query = self.db.query(AnalysisHistory)
        
        if include_executions:
            query = query.options(joinedload(AnalysisHistory.agent_executions))
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.contract_id:
                conditions.append(AnalysisHistory.contract_id == filters.contract_id)
            
            if filters.analysis_type:
                conditions.append(AnalysisHistory.analysis_type == filters.analysis_type)
            
            if filters.status:
                conditions.append(AnalysisHistory.status == filters.status)
            
            if filters.risk_level:
                conditions.append(AnalysisHistory.risk_level == filters.risk_level)
            
            if filters.model_used:
                conditions.append(AnalysisHistory.model_used == filters.model_used)
            
            # Date filters
            if filters.created_after:
                conditions.append(AnalysisHistory.created_at >= filters.created_after)
            
            if filters.created_before:
                conditions.append(AnalysisHistory.created_at <= filters.created_before)
            
            if filters.completed_after:
                conditions.append(AnalysisHistory.completed_at >= filters.completed_after)
            
            if filters.completed_before:
                conditions.append(AnalysisHistory.completed_at <= filters.completed_before)
            
            # Performance filters
            if filters.min_processing_time:
                conditions.append(AnalysisHistory.processing_time >= filters.min_processing_time)
            
            if filters.max_processing_time:
                conditions.append(AnalysisHistory.processing_time <= filters.max_processing_time)
            
            if filters.min_cost:
                conditions.append(AnalysisHistory.total_cost >= filters.min_cost)
            
            if filters.max_cost:
                conditions.append(AnalysisHistory.total_cost <= filters.max_cost)
            
            # Soft delete filter
            if not filters.include_deleted:
                conditions.append(AnalysisHistory.deleted_at.is_(None))
            
            if conditions:
                query = query.filter(and_(*conditions))
        else:
            # Default: exclude soft deleted
            query = query.filter(AnalysisHistory.deleted_at.is_(None))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(desc(AnalysisHistory.created_at)).offset(skip).limit(limit).all()
        
        return items, total
    
    def get_analysis_history_by_contract(self, contract_id: UUID) -> List[AnalysisHistory]:
        """Get all analysis history for a contract."""
        return self.db.query(AnalysisHistory).filter(
            AnalysisHistory.contract_id == contract_id,
            AnalysisHistory.deleted_at.is_(None)
        ).order_by(desc(AnalysisHistory.created_at)).all()
    
    # Agent Execution Methods
    
    def create_agent_execution(self, execution_data: AgentExecutionCreate) -> AgentExecution:
        """Create a new agent execution record."""
        db_execution = AgentExecution(**execution_data.dict())
        self.db.add(db_execution)
        self.db.commit()
        self.db.refresh(db_execution)
        return db_execution
    
    def get_agent_execution(self, execution_id: UUID) -> Optional[AgentExecution]:
        """Get agent execution by ID."""
        return self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()
    
    def update_agent_execution(self, execution_id: UUID, update_data: AgentExecutionUpdate) -> Optional[AgentExecution]:
        """Update agent execution record."""
        db_execution = self.get_agent_execution(execution_id)
        if not db_execution:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_execution, field, value)
        
        db_execution.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_execution)
        return db_execution
    
    def list_agent_executions(
        self,
        filters: Optional[AgentExecutionFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AgentExecution], int]:
        """List agent executions with optional filters."""
        query = self.db.query(AgentExecution)
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.analysis_id:
                conditions.append(AgentExecution.analysis_id == filters.analysis_id)
            
            if filters.agent_name:
                conditions.append(AgentExecution.agent_name == filters.agent_name)
            
            if filters.agent_type:
                conditions.append(AgentExecution.agent_type == filters.agent_type)
            
            if filters.status:
                conditions.append(AgentExecution.status == filters.status)
            
            if filters.llm_provider:
                conditions.append(AgentExecution.llm_provider == filters.llm_provider)
            
            if filters.model_name:
                conditions.append(AgentExecution.model_name == filters.model_name)
            
            if filters.error_type:
                conditions.append(AgentExecution.error_type == filters.error_type)
            
            # Date filters
            if filters.started_after:
                conditions.append(AgentExecution.started_at >= filters.started_after)
            
            if filters.started_before:
                conditions.append(AgentExecution.started_at <= filters.started_before)
            
            if filters.completed_after:
                conditions.append(AgentExecution.completed_at >= filters.completed_after)
            
            if filters.completed_before:
                conditions.append(AgentExecution.completed_at <= filters.completed_before)
            
            # Performance filters
            if filters.min_execution_time:
                conditions.append(AgentExecution.execution_time >= filters.min_execution_time)
            
            if filters.max_execution_time:
                conditions.append(AgentExecution.execution_time <= filters.max_execution_time)
            
            if filters.min_cost:
                conditions.append(AgentExecution.cost >= filters.min_cost)
            
            if filters.max_cost:
                conditions.append(AgentExecution.cost <= filters.max_cost)
            
            # Boolean filters
            if filters.has_errors is not None:
                if filters.has_errors:
                    conditions.append(AgentExecution.error_message.isnot(None))
                else:
                    conditions.append(AgentExecution.error_message.is_(None))
            
            if filters.fallback_used is not None:
                conditions.append(AgentExecution.fallback_used == filters.fallback_used)
            
            if filters.circuit_breaker_triggered is not None:
                conditions.append(AgentExecution.circuit_breaker_triggered == filters.circuit_breaker_triggered)
            
            if conditions:
                query = query.filter(and_(*conditions))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(desc(AgentExecution.started_at)).offset(skip).limit(limit).all()
        
        return items, total
    
    def get_executions_by_analysis(self, analysis_id: UUID) -> List[AgentExecution]:
        """Get all agent executions for an analysis."""
        return self.db.query(AgentExecution).filter(
            AgentExecution.analysis_id == analysis_id
        ).order_by(AgentExecution.started_at).all()
    
    # Analytics and Metrics Methods
    
    def get_analysis_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalysisPerformanceMetrics:
        """Get performance metrics for analyses."""
        query = self.db.query(AnalysisHistory).filter(
            AnalysisHistory.deleted_at.is_(None)
        )
        
        if start_date:
            query = query.filter(AnalysisHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(AnalysisHistory.created_at <= end_date)
        
        analyses = query.all()
        
        if not analyses:
            return AnalysisPerformanceMetrics(
                total_analyses=0,
                success_rate=Decimal('0'),
                agent_performance={},
                provider_performance={},
                analyses_by_day={},
                cost_by_day={}
            )
        
        total_analyses = len(analyses)
        successful_analyses = len([a for a in analyses if a.status == 'completed'])
        success_rate = Decimal(successful_analyses) / Decimal(total_analyses) * 100
        
        # Calculate averages
        processing_times = [a.processing_time for a in analyses if a.processing_time]
        costs = [a.total_cost for a in analyses if a.total_cost]
        tokens = [a.total_tokens for a in analyses if a.total_tokens]
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None
        avg_cost = sum(costs) / len(costs) if costs else None
        avg_tokens = sum(tokens) // len(tokens) if tokens else None
        
        # Group by day
        analyses_by_day = {}
        cost_by_day = {}
        
        for analysis in analyses:
            day_key = analysis.created_at.date().isoformat()
            analyses_by_day[day_key] = analyses_by_day.get(day_key, 0) + 1
            
            if analysis.total_cost:
                cost_by_day[day_key] = cost_by_day.get(day_key, Decimal('0')) + analysis.total_cost
        
        # Calculate agent performance
        agent_performance = self._calculate_agent_performance_for_analyses(analyses)
        
        # Calculate provider performance
        provider_performance = self._calculate_provider_performance_for_analyses(analyses)
        
        # Error analysis
        error_analysis = {}
        for analysis in analyses:
            if analysis.status == 'failed':
                # Get error details from associated agent executions
                executions = self.db.query(AgentExecution).filter(
                    AgentExecution.analysis_id == analysis.id
                ).all()
                
                for execution in executions:
                    if execution.error_type:
                        error_analysis[execution.error_type] = error_analysis.get(execution.error_type, 0) + 1
        
        return AnalysisPerformanceMetrics(
            total_analyses=total_analyses,
            avg_processing_time=avg_processing_time,
            avg_cost=avg_cost,
            avg_tokens=avg_tokens,
            success_rate=success_rate,
            agent_performance=agent_performance,
            provider_performance=provider_performance,
            analyses_by_day=analyses_by_day,
            cost_by_day=cost_by_day,
            error_analysis=error_analysis
        )
    
    def get_agent_performance_metrics(
        self,
        agent_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AgentPerformanceMetrics]:
        """Get performance metrics for agents."""
        query = self.db.query(AgentExecution)
        
        if agent_name:
            query = query.filter(AgentExecution.agent_name == agent_name)
        
        if start_date:
            query = query.filter(AgentExecution.started_at >= start_date)
        
        if end_date:
            query = query.filter(AgentExecution.started_at <= end_date)
        
        executions = query.all()
        
        # Group by agent name
        agent_groups = {}
        for execution in executions:
            if execution.agent_name not in agent_groups:
                agent_groups[execution.agent_name] = []
            agent_groups[execution.agent_name].append(execution)
        
        metrics = []
        for agent_name, agent_executions in agent_groups.items():
            total_executions = len(agent_executions)
            success_count = len([e for e in agent_executions if e.status == 'completed'])
            failure_count = total_executions - success_count
            success_rate = Decimal(success_count) / Decimal(total_executions) * 100 if total_executions > 0 else Decimal('0')
            
            # Calculate averages
            execution_times = [e.execution_time for e in agent_executions if e.execution_time]
            costs = [e.cost for e in agent_executions if e.cost]
            tokens = [e.token_usage for e in agent_executions if e.token_usage]
            
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
            avg_cost = sum(costs) / len(costs) if costs else None
            avg_tokens = sum(tokens) // len(tokens) if tokens else None
            
            # Error analysis
            error_types = {}
            for execution in agent_executions:
                if execution.error_type:
                    error_types[execution.error_type] = error_types.get(execution.error_type, 0) + 1
            
            # Provider usage
            provider_usage = {}
            for execution in agent_executions:
                if execution.llm_provider:
                    provider_usage[execution.llm_provider] = provider_usage.get(execution.llm_provider, 0) + 1
            
            fallback_usage = len([e for e in agent_executions if e.fallback_used])
            
            # Calculate retry statistics
            retry_statistics = self._calculate_retry_statistics_for_executions(agent_executions)
            
            metrics.append(AgentPerformanceMetrics(
                agent_name=agent_name,
                total_executions=total_executions,
                success_count=success_count,
                failure_count=failure_count,
                success_rate=success_rate,
                avg_execution_time=avg_execution_time,
                avg_cost=avg_cost,
                avg_tokens=avg_tokens,
                error_types=error_types,
                retry_statistics=retry_statistics,
                provider_usage=provider_usage,
                fallback_usage=fallback_usage
            ))
        
        return metrics
    
    def get_cost_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = 'day'  # 'day', 'week', 'month', 'provider', 'model'
    ) -> Dict[str, Decimal]:
        """Get cost analysis grouped by specified dimension."""
        query = self.db.query(AgentExecution).filter(
            AgentExecution.cost.isnot(None)
        )
        
        if start_date:
            query = query.filter(AgentExecution.started_at >= start_date)
        
        if end_date:
            query = query.filter(AgentExecution.started_at <= end_date)
        
        executions = query.all()
        
        cost_data = {}
        
        for execution in executions:
            if group_by == 'day':
                key = execution.started_at.date().isoformat()
            elif group_by == 'week':
                # Get Monday of the week
                monday = execution.started_at.date() - timedelta(days=execution.started_at.weekday())
                key = monday.isoformat()
            elif group_by == 'month':
                key = execution.started_at.strftime('%Y-%m')
            elif group_by == 'provider':
                key = execution.llm_provider or execution.provider or 'unknown'
            elif group_by == 'model':
                key = execution.model_name or 'unknown'
            else:
                key = 'total'
            
            cost_data[key] = cost_data.get(key, Decimal('0')) + (execution.cost or Decimal('0'))
        
        return cost_data
    
    def get_performance_trends(
        self,
        metric: str = 'execution_time',  # 'execution_time', 'cost', 'token_usage'
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_name: Optional[str] = None
    ) -> Dict[str, List[Decimal]]:
        """Get performance trends over time."""
        query = self.db.query(AgentExecution)
        
        if start_date:
            query = query.filter(AgentExecution.started_at >= start_date)
        
        if end_date:
            query = query.filter(AgentExecution.started_at <= end_date)
        
        if agent_name:
            query = query.filter(AgentExecution.agent_name == agent_name)
        
        executions = query.order_by(AgentExecution.started_at).all()
        
        trends = {}
        
        for execution in executions:
            day_key = execution.started_at.date().isoformat()
            
            if day_key not in trends:
                trends[day_key] = []
            
            if metric == 'execution_time' and execution.execution_time:
                trends[day_key].append(execution.execution_time)
            elif metric == 'cost' and execution.cost:
                trends[day_key].append(execution.cost)
            elif metric == 'token_usage' and execution.token_usage:
                trends[day_key].append(Decimal(execution.token_usage))
        
        # Calculate averages for each day
        avg_trends = {}
        for day, values in trends.items():
            if values:
                avg_trends[day] = sum(values) / len(values)
        
        return avg_trends
    
    # Helper methods for TODO implementations
    
    def _calculate_agent_performance_for_analyses(self, analyses: List[AnalysisHistory]) -> Dict[str, AgentPerformanceMetrics]:
        """Calculate agent performance metrics for a list of analyses."""
        agent_performance = {}
        
        # Get all agent executions for these analyses
        analysis_ids = [analysis.id for analysis in analyses]
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.analysis_id.in_(analysis_ids)
        ).all()
        
        # Group executions by agent name
        agent_groups = {}
        for execution in executions:
            agent_name = execution.agent_name
            if agent_name not in agent_groups:
                agent_groups[agent_name] = []
            agent_groups[agent_name].append(execution)
        
        # Calculate metrics for each agent
        for agent_name, agent_executions in agent_groups.items():
            total_executions = len(agent_executions)
            successful = sum(1 for e in agent_executions if e.status == 'completed')
            failed = sum(1 for e in agent_executions if e.status == 'failed')
            
            success_rate = float(successful / total_executions) if total_executions > 0 else 0.0
            error_rate = float(failed / total_executions) if total_executions > 0 else 0.0
            
            # Calculate average duration
            durations = [e.execution_time or e.duration for e in agent_executions if (e.execution_time or e.duration)]
            avg_duration = float(sum(durations) / len(durations)) if durations else 0.0
            
            # Calculate retry statistics
            retry_stats = self._calculate_retry_statistics_for_executions(agent_executions)
            
            agent_performance[agent_name] = AgentPerformanceMetrics(
                agent_name=agent_name,
                total_executions=total_executions,
                success_count=successful,
                failure_count=failed,
                success_rate=success_rate,
                error_rate=error_rate,
                average_duration=avg_duration,
                retry_stats=retry_stats
            )
        
        return agent_performance
    
    def _calculate_provider_performance_for_analyses(self, analyses: List[AnalysisHistory]) -> Dict[str, ProviderPerformanceMetrics]:
        """Calculate provider performance metrics for a list of analyses."""
        provider_performance = {}
        
        # Get all agent executions for these analyses
        analysis_ids = [analysis.id for analysis in analyses]
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.analysis_id.in_(analysis_ids)
        ).all()
        
        # Group executions by provider
        provider_groups = {}
        for execution in executions:
            provider = execution.llm_provider or execution.provider or 'unknown'
            if provider not in provider_groups:
                provider_groups[provider] = []
            provider_groups[provider].append(execution)
        
        # Calculate metrics for each provider
        for provider, provider_executions in provider_groups.items():
            total_requests = len(provider_executions)
            successful = sum(1 for e in provider_executions if e.status == 'completed')
            failed = sum(1 for e in provider_executions if e.status == 'failed')
            
            success_rate = float(successful / total_requests) if total_requests > 0 else 0.0
            error_rate = float(failed / total_requests) if total_requests > 0 else 0.0
            
            # Calculate average latency
            latencies = [e.execution_time or e.duration for e in provider_executions if (e.execution_time or e.duration)]
            avg_latency = float(sum(latencies) / len(latencies)) if latencies else 0.0
            
            # Calculate cost metrics
            costs = [e.cost for e in provider_executions if e.cost]
            total_cost = sum(costs, Decimal('0.0'))
            avg_cost = total_cost / len(costs) if costs else Decimal('0.0')
            
            # Model usage breakdown
            model_usage = {}
            for execution in provider_executions:
                model = execution.model_name or 'unknown'
                model_usage[model] = model_usage.get(model, 0) + 1
            
            # Error breakdown
            error_breakdown = {}
            for execution in provider_executions:
                if execution.error_type:
                    error_breakdown[execution.error_type] = error_breakdown.get(execution.error_type, 0) + 1
            
            provider_performance[provider] = ProviderPerformanceMetrics(
                provider=provider,
                total_requests=total_requests,
                success_rate=success_rate,
                average_latency=avg_latency,
                error_rate=error_rate,
                cost_metrics={
                    'total_cost': total_cost,
                    'average_cost': avg_cost
                },
                model_usage=model_usage,
                error_breakdown=error_breakdown
            )
        
        return provider_performance
    
    def _calculate_retry_statistics_for_executions(self, executions: List[AgentExecution]) -> Dict[str, Any]:
        """Calculate retry statistics for a list of executions."""
        if not executions:
            return {
                'total_retries': 0,
                'average_retries': 0.0,
                'max_retries': 0,
                'retry_success_rate': 0.0,
                'common_retry_reasons': {}
            }
        
        retry_counts = [e.retry_count for e in executions if e.retry_count is not None]
        total_retries = sum(retry_counts)
        avg_retries = float(total_retries / len(retry_counts)) if retry_counts else 0.0
        max_retries = max(retry_counts) if retry_counts else 0
        
        # Calculate retry success rate (executions that succeeded after retries)
        retried_executions = [e for e in executions if e.retry_count and e.retry_count > 0]
        successful_after_retry = sum(1 for e in retried_executions if e.status == 'completed')
        retry_success_rate = float(successful_after_retry / len(retried_executions)) if retried_executions else 0.0
        
        # Common retry reasons (based on error types of failed executions that were retried)
        retry_reasons = {}
        for execution in executions:
            if execution.retry_count and execution.retry_count > 0 and execution.error_type:
                retry_reasons[execution.error_type] = retry_reasons.get(execution.error_type, 0) + 1
        
        return {
            'total_retries': total_retries,
            'average_retries': avg_retries,
            'max_retries': max_retries,
            'retry_success_rate': retry_success_rate,
            'common_retry_reasons': retry_reasons
        }