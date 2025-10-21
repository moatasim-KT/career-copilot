"""
Advanced Workflow Management System

This module provides advanced workflow management capabilities including:
- Workflow templates for common job application tracking scenarios
- Workflow branching and conditional execution
- Workflow parallelization and optimization
- Workflow scheduling and batch processing
- Workflow audit logging and compliance tracking
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

import redis.asyncio as redis
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, DECIMAL, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

from ..core.config import get_settings
from ..core.database import get_db_session
from ..core.exceptions import WorkflowExecutionError, ErrorCategory, ErrorSeverity
from ..core.monitoring import log_audit_event
from ..models.database_models import Base
# Import will be done dynamically to avoid circular imports
from .state import ContractAnalysisState, WorkflowStatus

logger = logging.getLogger(__name__)


class WorkflowTemplateType(str, Enum):
    """Types of workflow templates."""
    STANDARD_CONTRACT_ANALYSIS = "standard_contract_analysis"
    HIGH_RISK_CONTRACT_ANALYSIS = "high_risk_contract_analysis"
    BULK_CONTRACT_ANALYSIS = "bulk_contract_analysis"
    COMPLIANCE_FOCUSED_ANALYSIS = "compliance_focused_analysis"
    NEGOTIATION_FOCUSED_ANALYSIS = "negotiation_focused_analysis"
    QUICK_RISK_ASSESSMENT = "quick_risk_assessment"
    DETAILED_LEGAL_REVIEW = "detailed_legal_review"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class WorkflowExecutionMode(str, Enum):
    """Workflow execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    BATCH = "batch"


class ScheduleType(str, Enum):
    """Workflow schedule types."""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    RECURRING = "recurring"
    CRON = "cron"


class BranchConditionType(str, Enum):
    """Types of branching conditions."""
    RISK_SCORE_THRESHOLD = "risk_score_threshold"
    CONTRACT_TYPE = "contract_type"
    CONTRACT_SIZE = "contract_size"
    COMPLIANCE_REQUIREMENTS = "compliance_requirements"
    USER_PREFERENCES = "user_preferences"
    CUSTOM_LOGIC = "custom_logic"


@dataclass
class WorkflowTemplate:
    """Workflow template definition."""
    template_id: str
    name: str
    description: str
    template_type: WorkflowTemplateType
    execution_mode: WorkflowExecutionMode
    steps: List[Dict[str, Any]]
    branching_rules: List[Dict[str, Any]] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    timeout_seconds: int = 3600
    retry_config: Dict[str, Any] = field(default_factory=dict)
    compliance_requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "execution_mode": self.execution_mode.value,
            "steps": self.steps,
            "branching_rules": self.branching_rules,
            "parallel_groups": self.parallel_groups,
            "timeout_seconds": self.timeout_seconds,
            "retry_config": self.retry_config,
            "compliance_requirements": self.compliance_requirements,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class WorkflowSchedule:
    """Workflow schedule definition."""
    schedule_id: str
    workflow_template_id: str
    schedule_type: ScheduleType
    schedule_expression: str  # Cron expression or delay specification
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    enabled: bool = True
    next_execution: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    max_executions: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schedule_id": self.schedule_id,
            "workflow_template_id": self.workflow_template_id,
            "schedule_type": self.schedule_type.value,
            "schedule_expression": self.schedule_expression,
            "input_data": self.input_data,
            "context": self.context,
            "enabled": self.enabled,
            "next_execution": self.next_execution.isoformat() if self.next_execution else None,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
            "max_executions": self.max_executions,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BatchWorkflowExecution:
    """Batch workflow execution definition."""
    batch_id: str
    template_id: str
    input_items: List[Dict[str, Any]]
    batch_config: Dict[str, Any]
    status: str = "pending"
    progress: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "batch_id": self.batch_id,
            "template_id": self.template_id,
            "input_items": self.input_items,
            "batch_config": self.batch_config,
            "status": self.status,
            "progress": self.progress,
            "results": self.results,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class WorkflowAuditLog(Base):
    """Database model for workflow audit logging."""
    
    __tablename__ = "workflow_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(255), nullable=False, index=True)
    execution_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    compliance_tags = Column(ARRAY(String), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_audit_logs_workflow_id", "workflow_id"),
        Index("idx_workflow_audit_logs_execution_id", "execution_id"),
        Index("idx_workflow_audit_logs_event_type", "event_type"),
        Index("idx_workflow_audit_logs_timestamp", "timestamp"),
        Index("idx_workflow_audit_logs_user_id", "user_id"),
    )


class WorkflowTemplateRegistry(Base):
    """Database model for workflow template registry."""
    
    __tablename__ = "workflow_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(100), nullable=False, index=True)
    execution_mode = Column(String(50), nullable=False)
    template_data = Column(JSONB, nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_templates_template_id", "template_id"),
        Index("idx_workflow_templates_template_type", "template_type"),
        Index("idx_workflow_templates_is_active", "is_active"),
    )


class WorkflowScheduleRegistry(Base):
    """Database model for workflow schedule registry."""
    
    __tablename__ = "workflow_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(String(255), nullable=False, unique=True, index=True)
    workflow_template_id = Column(String(255), nullable=False, index=True)
    schedule_type = Column(String(50), nullable=False)
    schedule_expression = Column(String(255), nullable=False)
    schedule_data = Column(JSONB, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    next_execution = Column(DateTime(timezone=True), nullable=True, index=True)
    last_execution = Column(DateTime(timezone=True), nullable=True)
    execution_count = Column(Integer, default=0, nullable=False)
    max_executions = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_workflow_schedules_schedule_id", "schedule_id"),
        Index("idx_workflow_schedules_template_id", "workflow_template_id"),
        Index("idx_workflow_schedules_next_execution", "next_execution"),
        Index("idx_workflow_schedules_enabled", "enabled"),
    )


class AdvancedWorkflowManager:
    """Advanced workflow management system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.active_batches: Dict[str, BatchWorkflowExecution] = {}
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Initialize built-in templates
        self.built_in_templates = self._create_built_in_templates()
        
        logger.info("Advanced workflow manager initialized")
    
    async def initialize(self):
        """Initialize async components."""
        try:
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                decode_responses=False
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            
            # Register built-in templates
            await self._register_built_in_templates()
            
            # Start scheduler
            await self.start_scheduler()
            
            logger.info("Advanced workflow manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced workflow manager: {e}")
            raise WorkflowExecutionError(
                f"Failed to initialize advanced workflow manager: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
    
    def _create_built_in_templates(self) -> Dict[str, WorkflowTemplate]:
        """Create built-in workflow templates."""
        templates = {}
        
        # Standard Contract Analysis Template
        templates["standard_contract_analysis"] = WorkflowTemplate(
            template_id="standard_contract_analysis",
            name="Standard Contract Analysis",
            description="Standard workflow for comprehensive job application tracking",
            template_type=WorkflowTemplateType.STANDARD_CONTRACT_ANALYSIS,
            execution_mode=WorkflowExecutionMode.SEQUENTIAL,
            steps=[
                {"step_id": "validation", "name": "Input Validation", "required": True},
                {"step_id": "analysis", "name": "Contract Analysis", "required": True},
                {"step_id": "risk_assessment", "name": "Risk Assessment", "required": True},
                {"step_id": "precedent_research", "name": "Legal Precedent Research", "required": False},
                {"step_id": "negotiation", "name": "Negotiation Strategy", "required": False},
                {"step_id": "communication", "name": "Communication Preparation", "required": False},
                {"step_id": "finalization", "name": "Result Compilation", "required": True}
            ],
            branching_rules=[
                {
                    "condition_type": BranchConditionType.RISK_SCORE_THRESHOLD.value,
                    "condition": {"threshold": 7.0, "operator": ">="},
                    "action": {"skip_steps": [], "add_steps": ["detailed_review"]},
                    "description": "Add detailed review for high-risk contracts"
                }
            ],
            timeout_seconds=1800,
            retry_config={"max_retries": 3, "retry_strategy": "exponential_backoff"},
            compliance_requirements=["audit_logging", "data_retention"]
        )
        
        # High Risk Contract Analysis Template
        templates["high_risk_contract_analysis"] = WorkflowTemplate(
            template_id="high_risk_contract_analysis",
            name="High Risk Contract Analysis",
            description="Enhanced workflow for high-risk job application tracking with additional scrutiny",
            template_type=WorkflowTemplateType.HIGH_RISK_CONTRACT_ANALYSIS,
            execution_mode=WorkflowExecutionMode.SEQUENTIAL,
            steps=[
                {"step_id": "validation", "name": "Enhanced Input Validation", "required": True},
                {"step_id": "preliminary_scan", "name": "Preliminary Risk Scan", "required": True},
                {"step_id": "detailed_analysis", "name": "Detailed Contract Analysis", "required": True},
                {"step_id": "multi_agent_review", "name": "Multi-Agent Risk Assessment", "required": True},
                {"step_id": "precedent_research", "name": "Comprehensive Legal Research", "required": True},
                {"step_id": "compliance_check", "name": "Compliance Verification", "required": True},
                {"step_id": "negotiation_strategy", "name": "Advanced Negotiation Strategy", "required": True},
                {"step_id": "executive_summary", "name": "Executive Summary Generation", "required": True},
                {"step_id": "approval_workflow", "name": "Approval Workflow", "required": True}
            ],
            parallel_groups=[
                ["detailed_analysis", "precedent_research"],
                ["compliance_check", "negotiation_strategy"]
            ],
            timeout_seconds=3600,
            retry_config={"max_retries": 5, "retry_strategy": "exponential_backoff"},
            compliance_requirements=["audit_logging", "data_retention", "executive_approval", "security_review"]
        )
        
        # Bulk Contract Analysis Template
        templates["bulk_contract_analysis"] = WorkflowTemplate(
            template_id="bulk_contract_analysis",
            name="Bulk Contract Analysis",
            description="Optimized workflow for processing multiple contracts in batch",
            template_type=WorkflowTemplateType.BULK_CONTRACT_ANALYSIS,
            execution_mode=WorkflowExecutionMode.BATCH,
            steps=[
                {"step_id": "batch_validation", "name": "Batch Input Validation", "required": True},
                {"step_id": "parallel_analysis", "name": "Parallel Contract Analysis", "required": True},
                {"step_id": "risk_aggregation", "name": "Risk Score Aggregation", "required": True},
                {"step_id": "comparative_analysis", "name": "Comparative Analysis", "required": False},
                {"step_id": "batch_reporting", "name": "Batch Report Generation", "required": True}
            ],
            parallel_groups=[
                ["parallel_analysis"]  # All contracts analyzed in parallel
            ],
            timeout_seconds=7200,
            retry_config={"max_retries": 2, "retry_strategy": "fixed_interval"},
            compliance_requirements=["audit_logging", "batch_tracking"]
        )
        
        # Quick Risk Assessment Template
        templates["quick_risk_assessment"] = WorkflowTemplate(
            template_id="quick_risk_assessment",
            name="Quick Risk Assessment",
            description="Fast workflow for initial risk assessment",
            template_type=WorkflowTemplateType.QUICK_RISK_ASSESSMENT,
            execution_mode=WorkflowExecutionMode.SEQUENTIAL,
            steps=[
                {"step_id": "validation", "name": "Basic Validation", "required": True},
                {"step_id": "quick_scan", "name": "Quick Risk Scan", "required": True},
                {"step_id": "risk_scoring", "name": "Risk Scoring", "required": True},
                {"step_id": "summary", "name": "Summary Generation", "required": True}
            ],
            timeout_seconds=300,
            retry_config={"max_retries": 2, "retry_strategy": "immediate"},
            compliance_requirements=["audit_logging"]
        )
        
        # Compliance Focused Analysis Template
        templates["compliance_focused_analysis"] = WorkflowTemplate(
            template_id="compliance_focused_analysis",
            name="Compliance Focused Analysis",
            description="Workflow focused on compliance and regulatory requirements",
            template_type=WorkflowTemplateType.COMPLIANCE_FOCUSED_ANALYSIS,
            execution_mode=WorkflowExecutionMode.SEQUENTIAL,
            steps=[
                {"step_id": "validation", "name": "Input Validation", "required": True},
                {"step_id": "regulatory_scan", "name": "Regulatory Compliance Scan", "required": True},
                {"step_id": "compliance_analysis", "name": "Detailed Compliance Analysis", "required": True},
                {"step_id": "gap_analysis", "name": "Compliance Gap Analysis", "required": True},
                {"step_id": "remediation_plan", "name": "Remediation Plan Generation", "required": True},
                {"step_id": "compliance_report", "name": "Compliance Report", "required": True}
            ],
            timeout_seconds=2400,
            retry_config={"max_retries": 3, "retry_strategy": "exponential_backoff"},
            compliance_requirements=["audit_logging", "data_retention", "compliance_tracking", "regulatory_reporting"]
        )
        
        return templates
    
    async def _register_built_in_templates(self):
        """Register built-in templates in the database."""
        try:
            async with get_db_session() as session:
                for template in self.built_in_templates.values():
                    # Check if template already exists
                    existing = await session.execute(
                        "SELECT id FROM workflow_templates WHERE template_id = :template_id",
                        {"template_id": template.template_id}
                    )
                    
                    if not existing.fetchone():
                        # Create new template record
                        template_record = WorkflowTemplateRegistry(
                            template_id=template.template_id,
                            name=template.name,
                            description=template.description,
                            template_type=template.template_type.value,
                            execution_mode=template.execution_mode.value,
                            template_data=template.to_dict(),
                            version="1.0.0",
                            is_active=True
                        )
                        session.add(template_record)
                
                await session.commit()
                logger.info(f"Registered {len(self.built_in_templates)} built-in workflow templates")
                
        except Exception as e:
            logger.error(f"Failed to register built-in templates: {e}")
    
    async def create_workflow_template(
        self,
        name: str,
        description: str,
        template_type: WorkflowTemplateType,
        execution_mode: WorkflowExecutionMode,
        steps: List[Dict[str, Any]],
        branching_rules: Optional[List[Dict[str, Any]]] = None,
        parallel_groups: Optional[List[List[str]]] = None,
        timeout_seconds: int = 3600,
        retry_config: Optional[Dict[str, Any]] = None,
        compliance_requirements: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> WorkflowTemplate:
        """Create a new workflow template."""
        
        template_id = str(uuid.uuid4())
        
        template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=description,
            template_type=template_type,
            execution_mode=execution_mode,
            steps=steps,
            branching_rules=branching_rules or [],
            parallel_groups=parallel_groups or [],
            timeout_seconds=timeout_seconds,
            retry_config=retry_config or {"max_retries": 3, "retry_strategy": "exponential_backoff"},
            compliance_requirements=compliance_requirements or [],
            metadata=metadata or {}
        )
        
        # Store in database
        async with get_db_session() as session:
            template_record = WorkflowTemplateRegistry(
                template_id=template_id,
                name=name,
                description=description,
                template_type=template_type.value,
                execution_mode=execution_mode.value,
                template_data=template.to_dict(),
                version="1.0.0",
                is_active=True,
                created_by=created_by
            )
            session.add(template_record)
            await session.commit()
        
        # Log audit event
        await self._log_audit_event(
            workflow_id=template_id,
            execution_id="template_creation",
            event_type="template_created",
            event_data={
                "template_id": template_id,
                "name": name,
                "template_type": template_type.value,
                "created_by": created_by
            },
            compliance_tags=["template_management"]
        )
        
        logger.info(f"Created workflow template: {template_id} - {name}")
        return template 
   
    async def get_workflow_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID."""
        try:
            # Check built-in templates first
            if template_id in self.built_in_templates:
                return self.built_in_templates[template_id]
            
            # Check database
            async with get_db_session() as session:
                result = await session.execute(
                    "SELECT template_data FROM workflow_templates WHERE template_id = :template_id AND is_active = true",
                    {"template_id": template_id}
                )
                row = result.fetchone()
                
                if row:
                    template_data = row[0]
                    return WorkflowTemplate(**template_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get workflow template {template_id}: {e}")
            return None
    
    async def list_workflow_templates(
        self,
        template_type: Optional[WorkflowTemplateType] = None,
        execution_mode: Optional[WorkflowExecutionMode] = None
    ) -> List[WorkflowTemplate]:
        """List available workflow templates."""
        try:
            templates = []
            
            # Add built-in templates
            for template in self.built_in_templates.values():
                if template_type and template.template_type != template_type:
                    continue
                if execution_mode and template.execution_mode != execution_mode:
                    continue
                templates.append(template)
            
            # Add custom templates from database
            async with get_db_session() as session:
                query = "SELECT template_data FROM workflow_templates WHERE is_active = true"
                params = {}
                
                if template_type:
                    query += " AND template_type = :template_type"
                    params["template_type"] = template_type.value
                
                if execution_mode:
                    query += " AND execution_mode = :execution_mode"
                    params["execution_mode"] = execution_mode.value
                
                result = await session.execute(query, params)
                
                for row in result.fetchall():
                    template_data = row[0]
                    template = WorkflowTemplate(**template_data)
                    templates.append(template)
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to list workflow templates: {e}")
            return []
    
    async def execute_workflow_with_template(
        self,
        template_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        execution_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute workflow using a template with advanced features."""
        
        # Get template
        template = await self.get_workflow_template(template_id)
        if not template:
            raise WorkflowExecutionError(f"Workflow template not found: {template_id}")
        
        execution_id = str(uuid.uuid4())
        
        # Log audit event for workflow start
        await self._log_audit_event(
            workflow_id=template_id,
            execution_id=execution_id,
            event_type="workflow_started",
            event_data={
                "template_id": template_id,
                "template_name": template.name,
                "input_data_keys": list(input_data.keys()),
                "execution_options": execution_options or {}
            },
            user_id=context.get("user_id"),
            compliance_tags=template.compliance_requirements
        )
        
        try:
            # Execute based on execution mode
            if template.execution_mode == WorkflowExecutionMode.SEQUENTIAL:
                result = await self._execute_sequential_workflow(template, input_data, context, execution_id)
            elif template.execution_mode == WorkflowExecutionMode.PARALLEL:
                result = await self._execute_parallel_workflow(template, input_data, context, execution_id)
            elif template.execution_mode == WorkflowExecutionMode.CONDITIONAL:
                result = await self._execute_conditional_workflow(template, input_data, context, execution_id)
            elif template.execution_mode == WorkflowExecutionMode.BATCH:
                result = await self._execute_batch_workflow(template, input_data, context, execution_id)
            else:
                raise WorkflowExecutionError(f"Unsupported execution mode: {template.execution_mode}")
            
            # Log successful completion
            await self._log_audit_event(
                workflow_id=template_id,
                execution_id=execution_id,
                event_type="workflow_completed",
                event_data={
                    "template_id": template_id,
                    "execution_duration": result.get("execution_duration"),
                    "result_summary": self._create_result_summary(result)
                },
                user_id=context.get("user_id"),
                compliance_tags=template.compliance_requirements
            )
            
            return result
            
        except Exception as e:
            # Log workflow failure
            await self._log_audit_event(
                workflow_id=template_id,
                execution_id=execution_id,
                event_type="workflow_failed",
                event_data={
                    "template_id": template_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                user_id=context.get("user_id"),
                compliance_tags=template.compliance_requirements
            )
            raise
    
    async def _execute_sequential_workflow(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute workflow sequentially with branching logic."""
        
        start_time = datetime.utcnow()
        
        # Create workflow instance (import dynamically to avoid circular imports)
        from ..workflows.core import create_workflow
        
        workflow_config = {
            "execution_id": execution_id,
            "template_id": template.template_id,
            "timeout_seconds": template.timeout_seconds,
            **template.retry_config
        }
        
        workflow = create_workflow(workflow_config)
        
        # Apply branching rules to determine execution path
        execution_steps = await self._apply_branching_rules(template, input_data, context)
        
        # Execute workflow
        contract_text = input_data.get("contract_text", "")
        contract_filename = input_data.get("contract_filename", "")
        
        result = await workflow.execute(contract_text, contract_filename, workflow_config)
        
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        
        # Add execution metadata
        result["execution_metadata"] = {
            "execution_id": execution_id,
            "template_id": template.template_id,
            "execution_mode": template.execution_mode.value,
            "execution_duration": execution_duration,
            "steps_executed": execution_steps,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        return result
    
    async def _execute_parallel_workflow(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute workflow with parallel step groups."""
        
        start_time = datetime.utcnow()
        
        # Create multiple workflow instances for parallel execution
        parallel_results = {}
        
        # Execute parallel groups
        for group_index, parallel_group in enumerate(template.parallel_groups):
            group_tasks = []
            
            for step_name in parallel_group:
                # Create separate workflow for each parallel step
                workflow_config = {
                    "execution_id": f"{execution_id}_parallel_{group_index}_{step_name}",
                    "template_id": template.template_id,
                    "timeout_seconds": template.timeout_seconds,
                    "focus_step": step_name,  # Focus on specific step
                    **template.retry_config
                }
                
                # Import dynamically to avoid circular imports
                from ..workflows.core import create_workflow
                workflow = create_workflow(workflow_config)
                
                # Create task for parallel execution
                task = asyncio.create_task(
                    self._execute_workflow_step(workflow, input_data, step_name)
                )
                group_tasks.append((step_name, task))
            
            # Wait for all tasks in the group to complete
            for step_name, task in group_tasks:
                try:
                    step_result = await task
                    parallel_results[step_name] = step_result
                except Exception as e:
                    logger.error(f"Parallel step {step_name} failed: {e}")
                    parallel_results[step_name] = {"error": str(e), "status": "failed"}
        
        # Merge parallel results
        merged_result = await self._merge_parallel_results(parallel_results, input_data)
        
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        
        # Add execution metadata
        merged_result["execution_metadata"] = {
            "execution_id": execution_id,
            "template_id": template.template_id,
            "execution_mode": template.execution_mode.value,
            "execution_duration": execution_duration,
            "parallel_groups": template.parallel_groups,
            "parallel_results": list(parallel_results.keys()),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        return merged_result
    
    async def _execute_conditional_workflow(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute workflow with conditional branching."""
        
        start_time = datetime.utcnow()
        
        # Evaluate branching conditions
        execution_path = await self._evaluate_branching_conditions(template, input_data, context)
        
        # Create workflow with conditional configuration
        workflow_config = {
            "execution_id": execution_id,
            "template_id": template.template_id,
            "timeout_seconds": template.timeout_seconds,
            "execution_path": execution_path,
            **template.retry_config
        }
        
        # Import dynamically to avoid circular imports
        from ..workflows.core import create_workflow
        workflow = create_workflow(workflow_config)
        
        # Execute workflow with conditional path
        contract_text = input_data.get("contract_text", "")
        contract_filename = input_data.get("contract_filename", "")
        
        result = await workflow.execute(contract_text, contract_filename, workflow_config)
        
        end_time = datetime.utcnow()
        execution_duration = (end_time - start_time).total_seconds()
        
        # Add execution metadata
        result["execution_metadata"] = {
            "execution_id": execution_id,
            "template_id": template.template_id,
            "execution_mode": template.execution_mode.value,
            "execution_duration": execution_duration,
            "execution_path": execution_path,
            "branching_conditions": template.branching_rules,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        return result
    
    async def _execute_batch_workflow(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute batch workflow for multiple items."""
        
        batch_id = str(uuid.uuid4())
        input_items = input_data.get("batch_items", [])
        batch_config = input_data.get("batch_config", {})
        
        if not input_items:
            raise WorkflowExecutionError("No batch items provided for batch workflow")
        
        # Create batch execution record
        batch_execution = BatchWorkflowExecution(
            batch_id=batch_id,
            template_id=template.template_id,
            input_items=input_items,
            batch_config=batch_config,
            status="running",
            started_at=datetime.utcnow()
        )
        
        self.active_batches[batch_id] = batch_execution
        
        try:
            # Execute batch processing
            batch_results = await self._process_batch_items(
                template, input_items, context, batch_id, batch_config
            )
            
            # Update batch execution
            batch_execution.status = "completed"
            batch_execution.completed_at = datetime.utcnow()
            batch_execution.results = batch_results
            
            # Calculate batch statistics
            successful_items = len([r for r in batch_results if r.get("status") == "completed"])
            failed_items = len([r for r in batch_results if r.get("status") == "failed"])
            
            batch_summary = {
                "batch_id": batch_id,
                "template_id": template.template_id,
                "total_items": len(input_items),
                "successful_items": successful_items,
                "failed_items": failed_items,
                "success_rate": successful_items / len(input_items) if input_items else 0,
                "execution_duration": (batch_execution.completed_at - batch_execution.started_at).total_seconds(),
                "results": batch_results
            }
            
            return batch_summary
            
        except Exception as e:
            batch_execution.status = "failed"
            batch_execution.completed_at = datetime.utcnow()
            batch_execution.errors.append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
        finally:
            # Clean up batch tracking
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
    
    async def _process_batch_items(
        self,
        template: WorkflowTemplate,
        input_items: List[Dict[str, Any]],
        context: Dict[str, Any],
        batch_id: str,
        batch_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process batch items with parallel execution."""
        
        max_concurrent = batch_config.get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item_index: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # Create workflow for this item
                    item_execution_id = f"{batch_id}_item_{item_index}"
                    
                    workflow_config = {
                        "execution_id": item_execution_id,
                        "template_id": template.template_id,
                        "timeout_seconds": template.timeout_seconds,
                        "batch_mode": True,
                        **template.retry_config
                    }
                    
                    # Import dynamically to avoid circular imports
                    from ..workflows.core import create_workflow
                    workflow = create_workflow(workflow_config)
                    
                    # Execute workflow for this item
                    contract_text = item_data.get("contract_text", "")
                    contract_filename = item_data.get("contract_filename", f"batch_item_{item_index}")
                    
                    result = await workflow.execute(contract_text, contract_filename, workflow_config)
                    
                    # Update batch progress
                    batch_execution = self.active_batches.get(batch_id)
                    if batch_execution:
                        batch_execution.progress[f"item_{item_index}"] = "completed"
                    
                    return {
                        "item_index": item_index,
                        "status": "completed",
                        "result": result,
                        "execution_id": item_execution_id
                    }
                    
                except Exception as e:
                    # Update batch progress with error
                    batch_execution = self.active_batches.get(batch_id)
                    if batch_execution:
                        batch_execution.progress[f"item_{item_index}"] = "failed"
                        batch_execution.errors.append({
                            "item_index": item_index,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    return {
                        "item_index": item_index,
                        "status": "failed",
                        "error": str(e),
                        "execution_id": f"{batch_id}_item_{item_index}"
                    }
        
        # Create tasks for all items
        tasks = [
            asyncio.create_task(process_item(i, item))
            for i, item in enumerate(input_items)
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "item_index": i,
                    "status": "failed",
                    "error": str(result),
                    "execution_id": f"{batch_id}_item_{i}"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _apply_branching_rules(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Apply branching rules to determine execution steps."""
        
        execution_steps = [step["step_id"] for step in template.steps if step.get("required", True)]
        
        for rule in template.branching_rules:
            condition_met = await self._evaluate_condition(rule, input_data, context)
            
            if condition_met:
                action = rule.get("action", {})
                
                # Skip steps
                skip_steps = action.get("skip_steps", [])
                execution_steps = [step for step in execution_steps if step not in skip_steps]
                
                # Add steps
                add_steps = action.get("add_steps", [])
                execution_steps.extend(add_steps)
                
                logger.info(f"Applied branching rule: {rule.get('description', 'Unknown rule')}")
        
        return execution_steps
    
    async def _evaluate_condition(
        self,
        rule: Dict[str, Any],
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a branching condition."""
        
        condition_type = rule.get("condition_type")
        condition = rule.get("condition", {})
        
        if condition_type == BranchConditionType.RISK_SCORE_THRESHOLD.value:
            # This would need to be evaluated after initial analysis
            # For now, return False as we don't have risk score yet
            return False
        
        elif condition_type == BranchConditionType.CONTRACT_TYPE.value:
            contract_type = input_data.get("contract_type", "").lower()
            expected_types = condition.get("types", [])
            return contract_type in [t.lower() for t in expected_types]
        
        elif condition_type == BranchConditionType.CONTRACT_SIZE.value:
            contract_text = input_data.get("contract_text", "")
            contract_size = len(contract_text)
            threshold = condition.get("threshold", 0)
            operator = condition.get("operator", ">=")
            
            if operator == ">=":
                return contract_size >= threshold
            elif operator == "<=":
                return contract_size <= threshold
            elif operator == ">":
                return contract_size > threshold
            elif operator == "<":
                return contract_size < threshold
            elif operator == "==":
                return contract_size == threshold
        
        elif condition_type == BranchConditionType.USER_PREFERENCES.value:
            user_prefs = context.get("user_preferences", {})
            required_prefs = condition.get("preferences", {})
            
            for key, value in required_prefs.items():
                if user_prefs.get(key) != value:
                    return False
            return True
        
        elif condition_type == BranchConditionType.CUSTOM_LOGIC.value:
            # Custom logic evaluation would be implemented here
            # For now, return the default value
            return condition.get("default", False)
        
        return False
    
    async def _evaluate_branching_conditions(
        self,
        template: WorkflowTemplate,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate all branching conditions to determine execution path."""
        
        execution_path = {
            "base_steps": [step["step_id"] for step in template.steps if step.get("required", True)],
            "conditional_steps": [],
            "skipped_steps": [],
            "applied_rules": []
        }
        
        for rule in template.branching_rules:
            condition_met = await self._evaluate_condition(rule, input_data, context)
            
            if condition_met:
                action = rule.get("action", {})
                
                # Track applied rules
                execution_path["applied_rules"].append({
                    "rule_description": rule.get("description", "Unknown rule"),
                    "condition_type": rule.get("condition_type"),
                    "action": action
                })
                
                # Add conditional steps
                add_steps = action.get("add_steps", [])
                execution_path["conditional_steps"].extend(add_steps)
                
                # Track skipped steps
                skip_steps = action.get("skip_steps", [])
                execution_path["skipped_steps"].extend(skip_steps)
        
        return execution_path
    
    async def _execute_workflow_step(
        self,
        workflow: Any,  # ContractAnalysisWorkflow - using Any to avoid circular import
        input_data: Dict[str, Any],
        step_name: str
    ) -> Dict[str, Any]:
        """Execute a specific workflow step."""
        
        contract_text = input_data.get("contract_text", "")
        contract_filename = input_data.get("contract_filename", "")
        
        # Execute the workflow and extract step-specific results
        result = await workflow.execute(contract_text, contract_filename, {"focus_step": step_name})
        
        # Return step-specific result
        return {
            "step_name": step_name,
            "status": result.get("status"),
            "result": result,
            "execution_time": result.get("processing_metadata", {}).get("processing_duration")
        }
    
    async def _merge_parallel_results(
        self,
        parallel_results: Dict[str, Dict[str, Any]],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge results from parallel workflow execution."""
        
        merged_result = {
            "status": "completed",
            "risky_clauses": [],
            "suggested_redlines": [],
            "email_draft": "",
            "overall_risk_score": 0.0,
            "precedent_context": [],
            "parallel_execution_results": parallel_results
        }
        
        # Merge risky clauses from all parallel results
        for step_name, step_result in parallel_results.items():
            if step_result.get("status") == "failed":
                merged_result["status"] = "partial_failure"
                continue
            
            result_data = step_result.get("result", {})
            
            # Merge risky clauses
            risky_clauses = result_data.get("risky_clauses", [])
            merged_result["risky_clauses"].extend(risky_clauses)
            
            # Merge suggested redlines
            suggested_redlines = result_data.get("suggested_redlines", [])
            merged_result["suggested_redlines"].extend(suggested_redlines)
            
            # Use the highest risk score
            risk_score = result_data.get("overall_risk_score", 0.0)
            merged_result["overall_risk_score"] = max(merged_result["overall_risk_score"], risk_score)
            
            # Merge precedent context
            precedent_context = result_data.get("precedent_context", [])
            merged_result["precedent_context"].extend(precedent_context)
            
            # Use email draft from communication step
            if step_name == "communicator" and result_data.get("email_draft"):
                merged_result["email_draft"] = result_data["email_draft"]
        
        # Remove duplicates from merged lists
        merged_result["risky_clauses"] = self._remove_duplicate_clauses(merged_result["risky_clauses"])
        merged_result["suggested_redlines"] = self._remove_duplicate_redlines(merged_result["suggested_redlines"])
        
        return merged_result
    
    def _remove_duplicate_clauses(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate risky clauses."""
        seen_clauses = set()
        unique_clauses = []
        
        for clause in clauses:
            clause_text = clause.get("clause_text", "")
            if clause_text not in seen_clauses:
                seen_clauses.add(clause_text)
                unique_clauses.append(clause)
        
        return unique_clauses
    
    def _remove_duplicate_redlines(self, redlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate redline suggestions."""
        seen_redlines = set()
        unique_redlines = []
        
        for redline in redlines:
            original_clause = redline.get("original_clause", "")
            if original_clause not in seen_redlines:
                seen_redlines.add(original_clause)
                unique_redlines.append(redline)
        
        return unique_redlines
    
    def _create_result_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of workflow results for audit logging."""
        return {
            "status": result.get("status"),
            "risky_clauses_count": len(result.get("risky_clauses", [])),
            "suggested_redlines_count": len(result.get("suggested_redlines", [])),
            "overall_risk_score": result.get("overall_risk_score"),
            "execution_duration": result.get("execution_metadata", {}).get("execution_duration"),
            "has_email_draft": bool(result.get("email_draft"))
        }
    
    async def _log_audit_event(
        self,
        workflow_id: str,
        execution_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        compliance_tags: Optional[List[str]] = None
    ):
        """Log workflow audit event."""
        try:
            async with get_db_session() as session:
                audit_log = WorkflowAuditLog(
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    event_type=event_type,
                    event_data=event_data,
                    user_id=user_id,
                    compliance_tags=compliance_tags or []
                )
                session.add(audit_log)
                await session.commit()
            
            logger.debug(f"Logged audit event: {event_type} for workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}") 
   
    # Workflow Scheduling Methods
    
    async def create_workflow_schedule(
        self,
        workflow_template_id: str,
        schedule_type: ScheduleType,
        schedule_expression: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        max_executions: Optional[int] = None,
        enabled: bool = True
    ) -> WorkflowSchedule:
        """Create a new workflow schedule."""
        
        schedule_id = str(uuid.uuid4())
        
        # Calculate next execution time
        next_execution = await self._calculate_next_execution(schedule_type, schedule_expression)
        
        schedule = WorkflowSchedule(
            schedule_id=schedule_id,
            workflow_template_id=workflow_template_id,
            schedule_type=schedule_type,
            schedule_expression=schedule_expression,
            input_data=input_data,
            context=context,
            enabled=enabled,
            next_execution=next_execution,
            max_executions=max_executions
        )
        
        # Store in database
        async with get_db_session() as session:
            schedule_record = WorkflowScheduleRegistry(
                schedule_id=schedule_id,
                workflow_template_id=workflow_template_id,
                schedule_type=schedule_type.value,
                schedule_expression=schedule_expression,
                schedule_data=schedule.to_dict(),
                enabled=enabled,
                next_execution=next_execution,
                max_executions=max_executions
            )
            session.add(schedule_record)
            await session.commit()
        
        # Log audit event
        await self._log_audit_event(
            workflow_id=workflow_template_id,
            execution_id=f"schedule_{schedule_id}",
            event_type="schedule_created",
            event_data={
                "schedule_id": schedule_id,
                "workflow_template_id": workflow_template_id,
                "schedule_type": schedule_type.value,
                "schedule_expression": schedule_expression,
                "enabled": enabled
            },
            user_id=context.get("user_id"),
            compliance_tags=["scheduling"]
        )
        
        logger.info(f"Created workflow schedule: {schedule_id} for template {workflow_template_id}")
        return schedule
    
    async def _calculate_next_execution(
        self,
        schedule_type: ScheduleType,
        schedule_expression: str
    ) -> Optional[datetime]:
        """Calculate the next execution time for a schedule."""
        
        now = datetime.utcnow()
        
        if schedule_type == ScheduleType.IMMEDIATE:
            return now
        
        elif schedule_type == ScheduleType.DELAYED:
            # Parse delay expression (e.g., "30m", "2h", "1d")
            try:
                if schedule_expression.endswith('m'):
                    minutes = int(schedule_expression[:-1])
                    return now + timedelta(minutes=minutes)
                elif schedule_expression.endswith('h'):
                    hours = int(schedule_expression[:-1])
                    return now + timedelta(hours=hours)
                elif schedule_expression.endswith('d'):
                    days = int(schedule_expression[:-1])
                    return now + timedelta(days=days)
                else:
                    # Assume seconds
                    seconds = int(schedule_expression)
                    return now + timedelta(seconds=seconds)
            except ValueError:
                logger.error(f"Invalid delay expression: {schedule_expression}")
                return None
        
        elif schedule_type == ScheduleType.RECURRING:
            # Parse recurring expression (e.g., "every 1h", "every 30m")
            try:
                parts = schedule_expression.split()
                if len(parts) == 2 and parts[0] == "every":
                    interval = parts[1]
                    if interval.endswith('m'):
                        minutes = int(interval[:-1])
                        return now + timedelta(minutes=minutes)
                    elif interval.endswith('h'):
                        hours = int(interval[:-1])
                        return now + timedelta(hours=hours)
                    elif interval.endswith('d'):
                        days = int(interval[:-1])
                        return now + timedelta(days=days)
            except ValueError:
                logger.error(f"Invalid recurring expression: {schedule_expression}")
                return None
        
        elif schedule_type == ScheduleType.CRON:
            # For cron expressions, we would use a cron parser library
            # For now, return a default next hour
            return now + timedelta(hours=1)
        
        return None
    
    async def start_scheduler(self):
        """Start the workflow scheduler."""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Workflow scheduler started")
    
    async def stop_scheduler(self):
        """Stop the workflow scheduler."""
        if not self.scheduler_running:
            return
        
        self.scheduler_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Workflow scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.scheduler_running:
            try:
                await self._process_scheduled_workflows()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _process_scheduled_workflows(self):
        """Process scheduled workflows that are due for execution."""
        try:
            now = datetime.utcnow()
            
            # Get due schedules from database
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT schedule_data FROM workflow_schedules 
                    WHERE enabled = true 
                    AND next_execution <= :now 
                    AND (max_executions IS NULL OR execution_count < max_executions)
                    """,
                    {"now": now}
                )
                
                due_schedules = []
                for row in result.fetchall():
                    schedule_data = row[0]
                    schedule = WorkflowSchedule(**schedule_data)
                    due_schedules.append(schedule)
            
            # Execute due schedules
            for schedule in due_schedules:
                try:
                    await self._execute_scheduled_workflow(schedule)
                except Exception as e:
                    logger.error(f"Failed to execute scheduled workflow {schedule.schedule_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to process scheduled workflows: {e}")
    
    async def _execute_scheduled_workflow(self, schedule: WorkflowSchedule):
        """Execute a scheduled workflow."""
        
        # Log scheduled execution
        await self._log_audit_event(
            workflow_id=schedule.workflow_template_id,
            execution_id=f"scheduled_{schedule.schedule_id}_{schedule.execution_count + 1}",
            event_type="scheduled_execution_started",
            event_data={
                "schedule_id": schedule.schedule_id,
                "execution_count": schedule.execution_count + 1,
                "scheduled_time": schedule.next_execution.isoformat() if schedule.next_execution else None
            },
            compliance_tags=["scheduling", "automated_execution"]
        )
        
        try:
            # Execute the workflow
            result = await self.execute_workflow_with_template(
                schedule.workflow_template_id,
                schedule.input_data,
                schedule.context
            )
            
            # Update schedule execution count and next execution time
            await self._update_schedule_after_execution(schedule, success=True)
            
            # Log successful execution
            await self._log_audit_event(
                workflow_id=schedule.workflow_template_id,
                execution_id=f"scheduled_{schedule.schedule_id}_{schedule.execution_count}",
                event_type="scheduled_execution_completed",
                event_data={
                    "schedule_id": schedule.schedule_id,
                    "execution_count": schedule.execution_count,
                    "result_summary": self._create_result_summary(result)
                },
                compliance_tags=["scheduling", "automated_execution"]
            )
            
        except Exception as e:
            # Update schedule and log failure
            await self._update_schedule_after_execution(schedule, success=False)
            
            await self._log_audit_event(
                workflow_id=schedule.workflow_template_id,
                execution_id=f"scheduled_{schedule.schedule_id}_{schedule.execution_count}",
                event_type="scheduled_execution_failed",
                event_data={
                    "schedule_id": schedule.schedule_id,
                    "execution_count": schedule.execution_count,
                    "error": str(e)
                },
                compliance_tags=["scheduling", "automated_execution"]
            )
            
            logger.error(f"Scheduled workflow execution failed for schedule {schedule.schedule_id}: {e}")
    
    async def _update_schedule_after_execution(self, schedule: WorkflowSchedule, success: bool):
        """Update schedule after execution."""
        try:
            # Calculate next execution time
            next_execution = None
            if schedule.schedule_type in [ScheduleType.RECURRING, ScheduleType.CRON]:
                next_execution = await self._calculate_next_execution(
                    schedule.schedule_type,
                    schedule.schedule_expression
                )
            
            # Update database
            async with get_db_session() as session:
                await session.execute(
                    """
                    UPDATE workflow_schedules 
                    SET execution_count = execution_count + 1,
                        last_execution = :now,
                        next_execution = :next_execution,
                        updated_at = :now
                    WHERE schedule_id = :schedule_id
                    """,
                    {
                        "schedule_id": schedule.schedule_id,
                        "now": datetime.utcnow(),
                        "next_execution": next_execution
                    }
                )
                await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update schedule after execution: {e}")
    
    # Batch Processing Methods
    
    async def create_batch_execution(
        self,
        template_id: str,
        input_items: List[Dict[str, Any]],
        batch_config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new batch execution."""
        
        batch_id = str(uuid.uuid4())
        
        batch_execution = BatchWorkflowExecution(
            batch_id=batch_id,
            template_id=template_id,
            input_items=input_items,
            batch_config=batch_config or {},
            status="pending"
        )
        
        self.active_batches[batch_id] = batch_execution
        
        # Log batch creation
        await self._log_audit_event(
            workflow_id=template_id,
            execution_id=f"batch_{batch_id}",
            event_type="batch_created",
            event_data={
                "batch_id": batch_id,
                "template_id": template_id,
                "item_count": len(input_items),
                "batch_config": batch_config or {}
            },
            user_id=context.get("user_id") if context else None,
            compliance_tags=["batch_processing"]
        )
        
        logger.info(f"Created batch execution: {batch_id} with {len(input_items)} items")
        return batch_id
    
    async def execute_batch(
        self,
        batch_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a batch workflow."""
        
        batch_execution = self.active_batches.get(batch_id)
        if not batch_execution:
            raise WorkflowExecutionError(f"Batch execution not found: {batch_id}")
        
        # Get template
        template = await self.get_workflow_template(batch_execution.template_id)
        if not template:
            raise WorkflowExecutionError(f"Template not found: {batch_execution.template_id}")
        
        # Execute batch using template's batch workflow
        input_data = {
            "batch_items": batch_execution.input_items,
            "batch_config": batch_execution.batch_config
        }
        
        result = await self._execute_batch_workflow(
            template,
            input_data,
            context or {},
            f"batch_{batch_id}"
        )
        
        return result
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch execution."""
        
        batch_execution = self.active_batches.get(batch_id)
        if not batch_execution:
            return None
        
        return {
            "batch_id": batch_id,
            "status": batch_execution.status,
            "progress": batch_execution.progress,
            "total_items": len(batch_execution.input_items),
            "completed_items": len([k for k, v in batch_execution.progress.items() if v == "completed"]),
            "failed_items": len([k for k, v in batch_execution.progress.items() if v == "failed"]),
            "errors": batch_execution.errors,
            "created_at": batch_execution.created_at.isoformat(),
            "started_at": batch_execution.started_at.isoformat() if batch_execution.started_at else None,
            "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None
        }
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch execution."""
        
        batch_execution = self.active_batches.get(batch_id)
        if not batch_execution:
            return False
        
        batch_execution.status = "cancelled"
        batch_execution.completed_at = datetime.utcnow()
        
        # Log batch cancellation
        await self._log_audit_event(
            workflow_id=batch_execution.template_id,
            execution_id=f"batch_{batch_id}",
            event_type="batch_cancelled",
            event_data={
                "batch_id": batch_id,
                "cancelled_at": datetime.utcnow().isoformat()
            },
            compliance_tags=["batch_processing"]
        )
        
        logger.info(f"Cancelled batch execution: {batch_id}")
        return True
    
    # Audit and Compliance Methods
    
    async def get_workflow_audit_logs(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        compliance_tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get workflow audit logs with filtering."""
        
        try:
            query = "SELECT * FROM workflow_audit_logs WHERE 1=1"
            params = {}
            
            if workflow_id:
                query += " AND workflow_id = :workflow_id"
                params["workflow_id"] = workflow_id
            
            if execution_id:
                query += " AND execution_id = :execution_id"
                params["execution_id"] = execution_id
            
            if event_type:
                query += " AND event_type = :event_type"
                params["event_type"] = event_type
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            if start_time:
                query += " AND timestamp >= :start_time"
                params["start_time"] = start_time
            
            if end_time:
                query += " AND timestamp <= :end_time"
                params["end_time"] = end_time
            
            if compliance_tags:
                query += " AND compliance_tags && :compliance_tags"
                params["compliance_tags"] = compliance_tags
            
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            async with get_db_session() as session:
                result = await session.execute(query, params)
                
                logs = []
                for row in result.fetchall():
                    log_dict = dict(row._mapping)
                    log_dict["timestamp"] = log_dict["timestamp"].isoformat()
                    logs.append(log_dict)
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    async def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        compliance_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a compliance report for workflow executions."""
        
        try:
            # Get audit logs for the time period
            audit_logs = await self.get_workflow_audit_logs(
                start_time=start_time,
                end_time=end_time,
                compliance_tags=compliance_tags,
                limit=10000
            )
            
            # Analyze logs for compliance metrics
            report = {
                "report_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                "total_events": len(audit_logs),
                "event_types": {},
                "workflow_executions": {},
                "compliance_tags": {},
                "user_activity": {},
                "error_summary": {},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Analyze events
            for log in audit_logs:
                event_type = log.get("event_type", "unknown")
                workflow_id = log.get("workflow_id", "unknown")
                user_id = log.get("user_id", "system")
                tags = log.get("compliance_tags", [])
                
                # Count event types
                report["event_types"][event_type] = report["event_types"].get(event_type, 0) + 1
                
                # Count workflow executions
                report["workflow_executions"][workflow_id] = report["workflow_executions"].get(workflow_id, 0) + 1
                
                # Count compliance tags
                for tag in tags:
                    report["compliance_tags"][tag] = report["compliance_tags"].get(tag, 0) + 1
                
                # Count user activity
                if user_id:
                    report["user_activity"][user_id] = report["user_activity"].get(user_id, 0) + 1
                
                # Count errors
                if "failed" in event_type or "error" in event_type:
                    report["error_summary"][event_type] = report["error_summary"].get(event_type, 0) + 1
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def cleanup_old_audit_logs(self, retention_days: int = 90) -> int:
        """Clean up old audit logs based on retention policy."""
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with get_db_session() as session:
                result = await session.execute(
                    "DELETE FROM workflow_audit_logs WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                deleted_count = result.rowcount
                await session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old audit log entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return 0
    
    async def shutdown(self):
        """Shutdown the advanced workflow manager."""
        await self.stop_scheduler()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.executor.shutdown(wait=True)
        
        logger.info("Advanced workflow manager shutdown complete")


# Factory function for creating advanced workflow manager
def create_advanced_workflow_manager() -> AdvancedWorkflowManager:
    """Factory function to create a new advanced workflow manager instance."""
    return AdvancedWorkflowManager()