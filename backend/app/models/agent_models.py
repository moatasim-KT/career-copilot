"""
Agent State Machine Models

This module provides models for tracking agent execution state and workflow progress
for real-time updates and monitoring.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, String, Text, Integer, DECIMAL, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database_models import Base, UUID, JSONB_COMPAT


class AgentState(str, Enum):
    """Agent execution state enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class WorkflowState(str, Enum):
    """Workflow execution state enumeration."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEGRADED = "degraded"
    CANCELLED = "cancelled"


class AgentPriority(str, Enum):
    """Agent execution priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentProgressMetrics:
    """Metrics for tracking agent execution progress."""
    
    agent_name: str
    state: AgentState = AgentState.PENDING
    progress_percentage: float = 0.0
    current_operation: str = ""
    estimated_completion_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def update_progress(self, percentage: float, operation: str = None):
        """Update progress percentage and current operation."""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if operation:
            self.current_operation = operation
    
    def start_execution(self):
        """Mark agent execution as started."""
        self.state = AgentState.RUNNING
        self.start_time = datetime.utcnow()
        self.progress_percentage = 0.0
    
    def complete_execution(self):
        """Mark agent execution as completed."""
        self.state = AgentState.COMPLETED
        self.end_time = datetime.utcnow()
        self.progress_percentage = 100.0
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
    
    def fail_execution(self, error_message: str):
        """Mark agent execution as failed."""
        self.state = AgentState.FAILED
        self.end_time = datetime.utcnow()
        self.error_message = error_message
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
    
    def timeout_execution(self):
        """Mark agent execution as timed out."""
        self.state = AgentState.TIMEOUT
        self.end_time = datetime.utcnow()
        self.error_message = "Agent execution timed out"
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()


class WorkflowProgress(BaseModel):
    """Model for tracking overall workflow progress."""
    
    workflow_id: str = Field(description="Unique workflow identifier")
    contract_id: Optional[str] = Field(None, description="Associated contract ID")
    workflow_state: WorkflowState = Field(WorkflowState.INITIALIZED, description="Current workflow state")
    
    # Agent tracking
    total_agents: int = Field(description="Total number of agents in workflow")
    completed_agents: int = Field(0, description="Number of completed agents")
    failed_agents: int = Field(0, description="Number of failed agents")
    running_agents: int = Field(0, description="Number of currently running agents")
    
    # Progress calculation
    overall_progress_percentage: float = Field(0.0, description="Overall workflow progress percentage")
    current_stage: str = Field("initialization", description="Current workflow stage")
    current_agent: Optional[str] = Field(None, description="Currently executing agent")
    
    # Timing
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Workflow start time")
    estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")
    end_time: Optional[datetime] = Field(None, description="Workflow end time")
    total_execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    
    # Agent details
    agent_progress: Dict[str, AgentProgressMetrics] = Field(
        default_factory=dict, 
        description="Individual agent progress metrics"
    )
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")
    
    def add_agent(self, agent_name: str, priority: AgentPriority = AgentPriority.NORMAL):
        """Add an agent to the workflow tracking."""
        if agent_name not in self.agent_progress:
            self.agent_progress[agent_name] = AgentProgressMetrics(agent_name=agent_name)
            # Don't increment total_agents here as it should be set during initialization
    
    def start_agent(self, agent_name: str):
        """Mark an agent as started."""
        if agent_name in self.agent_progress:
            self.agent_progress[agent_name].start_execution()
            self.current_agent = agent_name
            self.running_agents += 1
            self._update_overall_progress()
    
    def complete_agent(self, agent_name: str):
        """Mark an agent as completed."""
        if agent_name in self.agent_progress:
            self.agent_progress[agent_name].complete_execution()
            self.completed_agents += 1
            self.running_agents = max(0, self.running_agents - 1)
            self._update_overall_progress()
            self._update_current_agent()
    
    def fail_agent(self, agent_name: str, error_message: str):
        """Mark an agent as failed."""
        if agent_name in self.agent_progress:
            self.agent_progress[agent_name].fail_execution(error_message)
            self.failed_agents += 1
            self.running_agents = max(0, self.running_agents - 1)
            self._update_overall_progress()
            self._update_current_agent()
    
    def update_agent_progress(self, agent_name: str, percentage: float, operation: str = None):
        """Update progress for a specific agent."""
        if agent_name in self.agent_progress:
            self.agent_progress[agent_name].update_progress(percentage, operation)
            self._update_overall_progress()
    
    def _update_overall_progress(self):
        """Calculate and update overall workflow progress."""
        if len(self.agent_progress) == 0:
            self.overall_progress_percentage = 0.0
            return
        
        total_progress = 0.0
        for agent_metrics in self.agent_progress.values():
            total_progress += agent_metrics.progress_percentage
        
        self.overall_progress_percentage = total_progress / len(self.agent_progress)
        
        # Update workflow state based on progress
        total_finished_agents = self.completed_agents + self.failed_agents
        total_tracked_agents = len(self.agent_progress)
        
        if self.failed_agents > 0 and total_finished_agents == total_tracked_agents:
            if self.completed_agents > 0:
                self.workflow_state = WorkflowState.DEGRADED
            else:
                self.workflow_state = WorkflowState.FAILED
        elif self.completed_agents == total_tracked_agents and total_tracked_agents > 0:
            self.workflow_state = WorkflowState.COMPLETED
            self.end_time = datetime.utcnow()
            self.total_execution_time = (self.end_time - self.start_time).total_seconds()
        elif self.running_agents > 0 or self.completed_agents > 0:
            self.workflow_state = WorkflowState.RUNNING
    
    def _update_current_agent(self):
        """Update the current agent based on running agents."""
        running_agents = [
            name for name, metrics in self.agent_progress.items()
            if metrics.state == AgentState.RUNNING
        ]
        self.current_agent = running_agents[0] if running_agents else None
    
    def estimate_completion_time(self) -> Optional[datetime]:
        """Estimate workflow completion time based on current progress."""
        if self.overall_progress_percentage <= 0:
            return None
        
        elapsed_time = (datetime.utcnow() - self.start_time).total_seconds()
        if elapsed_time <= 0:
            return None
        
        # Calculate estimated total time based on current progress
        estimated_total_time = elapsed_time / (self.overall_progress_percentage / 100.0)
        remaining_time = estimated_total_time - elapsed_time
        
        if remaining_time > 0:
            self.estimated_completion_time = datetime.utcnow() + \
                datetime.timedelta(seconds=remaining_time)
            return self.estimated_completion_time
        
        return None
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of workflow progress for frontend display."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_state": self.workflow_state.value,
            "overall_progress_percentage": round(self.overall_progress_percentage, 2),
            "current_stage": self.current_stage,
            "current_agent": self.current_agent,
            "total_agents": self.total_agents,
            "completed_agents": self.completed_agents,
            "failed_agents": self.failed_agents,
            "running_agents": self.running_agents,
            "start_time": self.start_time.isoformat(),
            "estimated_completion_time": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_execution_time": self.total_execution_time,
            "error_message": self.error_message,
            "agent_details": {
                name: {
                    "state": metrics.state.value,
                    "progress_percentage": round(metrics.progress_percentage, 2),
                    "current_operation": metrics.current_operation,
                    "execution_time": metrics.execution_time,
                    "error_message": metrics.error_message,
                    "retry_count": metrics.retry_count
                }
                for name, metrics in self.agent_progress.items()
            }
        }
    
    def cancel_workflow(self):
        """Cancel the workflow and all running agents."""
        self.workflow_state = WorkflowState.CANCELLED
        self.end_time = datetime.utcnow()
        self.total_execution_time = (self.end_time - self.start_time).total_seconds()
        
        # Cancel all running agents
        for agent_metrics in self.agent_progress.values():
            if agent_metrics.state == AgentState.RUNNING:
                agent_metrics.state = AgentState.CANCELLED
                agent_metrics.end_time = datetime.utcnow()
                if agent_metrics.start_time:
                    agent_metrics.execution_time = (agent_metrics.end_time - agent_metrics.start_time).total_seconds()


class WorkflowExecution(Base):
    """Database model for storing workflow execution history."""
    
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(255), nullable=False, unique=True, index=True)
    contract_analysis_id = Column(UUID(), ForeignKey("contract_analyses.id", ondelete="CASCADE"), nullable=True)
    
    # Workflow metadata
    workflow_type = Column(String(100), nullable=False, default="contract_analysis")
    workflow_state = Column(String(50), nullable=False, default=WorkflowState.INITIALIZED.value)
    execution_mode = Column(String(50), nullable=False, default="sequential")
    
    # Progress tracking
    total_agents = Column(Integer, nullable=False, default=0)
    completed_agents = Column(Integer, nullable=False, default=0)
    failed_agents = Column(Integer, nullable=False, default=0)
    running_agents = Column(Integer, nullable=False, default=0)
    overall_progress_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.0)
    
    # Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    estimated_completion_time = Column(DateTime(timezone=True), nullable=True)
    total_execution_time = Column(DECIMAL(10, 3), nullable=True)
    
    # Status and error handling
    current_stage = Column(String(100), nullable=False, default="initialization")
    current_agent = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    recovery_actions = Column(JSONB_COMPAT(), nullable=True)
    
    # Detailed progress data
    agent_progress_data = Column(JSONB_COMPAT(), nullable=True)
    workflow_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    contract_analysis = relationship("ContractAnalysis")
    agent_executions = relationship("WorkflowAgentExecution", back_populates="workflow_execution", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_executions_workflow_id", "workflow_id"),
        Index("idx_workflow_executions_state", "workflow_state"),
        Index("idx_workflow_executions_start_time", "start_time"),
        Index("idx_workflow_executions_contract_analysis_id", "contract_analysis_id"),
        Index("idx_workflow_executions_current_stage", "current_stage"),
    )
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id='{self.workflow_id}', state='{self.workflow_state}')>"


class WorkflowAgentExecution(Base):
    """Database model for storing individual agent execution details in workflows."""
    
    __tablename__ = "workflow_agent_executions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    workflow_execution_id = Column(UUID(), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    
    # Agent identification
    agent_name = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False)
    agent_version = Column(String(50), nullable=True)
    
    # Execution state
    execution_state = Column(String(50), nullable=False, default=AgentState.PENDING.value)
    priority = Column(String(20), nullable=False, default=AgentPriority.NORMAL.value)
    
    # Progress tracking
    progress_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.0)
    current_operation = Column(String(255), nullable=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(DECIMAL(10, 3), nullable=True)
    estimated_completion_time = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling and retries
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Performance metrics
    token_usage = Column(Integer, nullable=True)
    cost = Column(DECIMAL(10, 4), nullable=True)
    model_used = Column(String(100), nullable=True)
    provider_used = Column(String(100), nullable=True)
    fallback_used = Column(Boolean, nullable=False, default=False)
    
    # Input and output data
    input_data = Column(JSONB_COMPAT(), nullable=True)
    output_data = Column(JSONB_COMPAT(), nullable=True)
    execution_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="agent_executions")
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_agent_executions_workflow_id", "workflow_execution_id"),
        Index("idx_workflow_agent_executions_agent_name", "agent_name"),
        Index("idx_workflow_agent_executions_state", "execution_state"),
        Index("idx_workflow_agent_executions_start_time", "start_time"),
        Index("idx_workflow_agent_executions_priority", "priority"),
    )
    
    def __repr__(self):
        return f"<WorkflowAgentExecution(id={self.id}, agent_name='{self.agent_name}', state='{self.execution_state}')>"


class WorkflowProgressManager:
    """Manager class for handling workflow progress tracking and updates."""
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowProgress] = {}
    
    def create_workflow(
        self, 
        workflow_id: str, 
        agent_names: List[str], 
        contract_id: Optional[str] = None
    ) -> WorkflowProgress:
        """Create a new workflow progress tracker."""
        workflow_progress = WorkflowProgress(
            workflow_id=workflow_id,
            contract_id=contract_id,
            total_agents=len(agent_names)
        )
        
        # Add all agents to the workflow
        for agent_name in agent_names:
            workflow_progress.add_agent(agent_name)
        
        self.active_workflows[workflow_id] = workflow_progress
        return workflow_progress
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get workflow progress by ID."""
        return self.active_workflows.get(workflow_id)
    
    def update_agent_progress(
        self, 
        workflow_id: str, 
        agent_name: str, 
        percentage: float, 
        operation: str = None
    ) -> bool:
        """Update progress for a specific agent in a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.update_agent_progress(agent_name, percentage, operation)
            return True
        return False
    
    def start_agent(self, workflow_id: str, agent_name: str) -> bool:
        """Mark an agent as started in a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.start_agent(agent_name)
            return True
        return False
    
    def complete_agent(self, workflow_id: str, agent_name: str) -> bool:
        """Mark an agent as completed in a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.complete_agent(agent_name)
            return True
        return False
    
    def fail_agent(self, workflow_id: str, agent_name: str, error_message: str) -> bool:
        """Mark an agent as failed in a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.fail_agent(agent_name, error_message)
            return True
        return False
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow and all its agents."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.cancel_workflow()
            return True
        return False
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up completed workflows older than specified hours."""
        current_time = datetime.utcnow()
        workflows_to_remove = []
        
        for workflow_id, workflow in self.active_workflows.items():
            if workflow.workflow_state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                # Use end_time if available, otherwise use start_time for age calculation
                reference_time = workflow.end_time if workflow.end_time else workflow.start_time
                if reference_time:
                    age_hours = (current_time - reference_time).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]
        
        return len(workflows_to_remove)
    
    def get_all_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all active workflows."""
        return {
            workflow_id: workflow.get_progress_summary()
            for workflow_id, workflow in self.active_workflows.items()
        }


# Global workflow progress manager instance
workflow_progress_manager = WorkflowProgressManager()


def get_workflow_progress_manager() -> WorkflowProgressManager:
    """Get the global workflow progress manager instance."""
    return workflow_progress_manager