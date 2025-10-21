"""
Task models for background task processing system.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    """Types of background tasks."""
    CONTRACT_ANALYSIS = "contract_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    RISK_ASSESSMENT = "risk_assessment"
    PRECEDENT_SEARCH = "precedent_search"
    REPORT_GENERATION = "report_generation"
    EMAIL_NOTIFICATION = "email_notification"
    BATCH_PROCESSING = "batch_processing"


class TaskRetryInfo(BaseModel):
    """Task retry information."""
    attempt_number: int
    delay_seconds: float
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class TaskResult(BaseModel):
    """Task execution result."""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_history: List[TaskRetryInfo] = Field(default_factory=list)
    next_retry_at: Optional[datetime] = None
    cancellation_requested: bool = False
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None


class TaskRetryConfig(BaseModel):
    """Task retry configuration."""
    max_retries: int = 3
    base_delay_seconds: int = 60
    max_delay_seconds: int = 3600  # 1 hour
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_max_seconds: float = 30.0
    
    # Retryable error patterns
    retryable_error_patterns: List[str] = Field(default_factory=lambda: [
        "timeout", "connection", "network", "rate_limit", "service_unavailable"
    ])
    
    # Non-retryable error patterns
    non_retryable_error_patterns: List[str] = Field(default_factory=lambda: [
        "validation", "authentication", "authorization", "not_found"
    ])


class TaskDefinition(BaseModel):
    """Background task definition."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any]
    
    # Scheduling options
    scheduled_at: Optional[datetime] = None
    delay_seconds: Optional[int] = None
    
    # Execution options
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 60
    retry_config: Optional[TaskRetryConfig] = None
    
    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    callback_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_execution_time(self) -> datetime:
        """Get the time when task should be executed."""
        if self.scheduled_at:
            return self.scheduled_at
        elif self.delay_seconds:
            return self.created_at + timedelta(seconds=self.delay_seconds)
        else:
            return self.created_at
    
    def get_retry_config(self) -> TaskRetryConfig:
        """Get retry configuration with defaults."""
        if self.retry_config:
            return self.retry_config
        return TaskRetryConfig(
            max_retries=self.max_retries,
            base_delay_seconds=self.retry_delay_seconds
        )


class TaskProgress(BaseModel):
    """Task progress information."""
    task_id: str
    current_step: str
    progress_percentage: float = 0.0
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskScheduleRequest(BaseModel):
    """Request to schedule a background task."""
    task_type: TaskType
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    delay_seconds: Optional[int] = None
    timeout_seconds: int = 300
    max_retries: int = 3
    callback_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    progress: Optional[TaskProgress] = None
    result: Optional[TaskResult] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    can_cancel: bool = False


class TaskListResponse(BaseModel):
    """Response for task list queries."""
    tasks: List[TaskStatusResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class TaskQueueStats(BaseModel):
    """Task queue statistics."""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    
    # Queue sizes by priority
    urgent_queue_size: int = 0
    high_queue_size: int = 0
    normal_queue_size: int = 0
    low_queue_size: int = 0
    
    # Performance metrics
    average_execution_time: Optional[float] = None
    success_rate: Optional[float] = None
    
    # System metrics
    active_workers: int = 0
    max_workers: int = 0
    system_load: Optional[float] = None


class ContractAnalysisTaskPayload(BaseModel):
    """Payload for job application tracking tasks."""
    contract_id: str
    contract_text: str
    contract_filename: str
    analysis_options: Dict[str, Any] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Analysis configuration
    enable_risk_assessment: bool = True
    enable_precedent_search: bool = True
    enable_redline_generation: bool = True
    enable_negotiation_suggestions: bool = True
    
    # Output options
    generate_report: bool = True
    send_email_notification: bool = False
    email_recipients: List[str] = Field(default_factory=list)


class DocumentProcessingTaskPayload(BaseModel):
    """Payload for document processing tasks."""
    document_id: str
    document_path: str
    processing_type: str  # ocr, table_extraction, structure_analysis
    options: Dict[str, Any] = Field(default_factory=dict)


class BatchProcessingTaskPayload(BaseModel):
    """Payload for batch processing tasks."""
    batch_id: str
    item_ids: List[str]
    processing_type: str
    batch_options: Dict[str, Any] = Field(default_factory=dict)
    
    # Batch configuration
    max_concurrent_items: int = 5
    continue_on_error: bool = True
    notify_on_completion: bool = True


class TaskNotificationConfig(BaseModel):
    """Task notification configuration."""
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notify_on_retry: bool = False
    notify_on_cancellation: bool = True
    
    # Notification channels
    email_notifications: bool = False
    email_recipients: List[str] = Field(default_factory=list)
    webhook_notifications: bool = False
    webhook_urls: List[str] = Field(default_factory=list)
    slack_notifications: bool = False
    slack_channels: List[str] = Field(default_factory=list)


class TaskCancellationRequest(BaseModel):
    """Task cancellation request."""
    task_id: str
    reason: Optional[str] = None
    force: bool = False  # Force cancellation even if task is running
    notify_user: bool = True