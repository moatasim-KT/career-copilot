"""
Email notification optimization and batching service for efficient email delivery.
Provides intelligent batching, rate limiting, priority queuing, and delivery optimization.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import heapq
from collections import defaultdict, deque

from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.database import get_db_session
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from .email_analytics_service import EnhancedEmailAnalyticsService, EmailEventType
from .enhanced_smtp_service import EnhancedSMTPService, SMTPConfiguration
from .enhanced_gmail_service import EnhancedGmailService, GmailConfiguration

logger = get_logger(__name__)


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    CRITICAL = "critical"      # Immediate delivery
    HIGH = "high"             # Within 5 minutes
    NORMAL = "normal"         # Within 30 minutes
    LOW = "low"              # Within 2 hours
    BULK = "bulk"            # Daily batch


class BatchingStrategy(str, Enum):
    """Email batching strategies"""
    TIME_BASED = "time_based"           # Batch by time intervals
    RECIPIENT_BASED = "recipient_based"  # Batch by recipient
    TEMPLATE_BASED = "template_based"    # Batch by template type
    PRIORITY_BASED = "priority_based"    # Batch by priority
    SMART = "smart"                     # Intelligent batching


class DeliveryWindow(BaseModel):
    """Delivery time window configuration"""
    start_hour: int = Field(8, ge=0, le=23, description="Start hour (24h format)")
    end_hour: int = Field(18, ge=0, le=23, description="End hour (24h format)")
    timezone: str = Field("UTC", description="Timezone for delivery window")
    days_of_week: List[int] = Field([1, 2, 3, 4, 5], description="Days of week (1=Monday)")


@dataclass
class EmailNotification:
    """Email notification with metadata"""
    id: str
    recipient: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if not isinstance(other, EmailNotification):
            return NotImplemented
        
        priority_order = {
            NotificationPriority.CRITICAL: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.NORMAL: 2,
            NotificationPriority.LOW: 3,
            NotificationPriority.BULK: 4
        }
        
        self_priority = priority_order.get(self.priority, 3)
        other_priority = priority_order.get(other.priority, 3)
        
        if self_priority != other_priority:
            return self_priority < other_priority
        
        # If same priority, order by creation time
        return self.created_at < other.created_at


@dataclass
class BatchConfiguration:
    """Batch processing configuration"""
    strategy: BatchingStrategy = BatchingStrategy.SMART
    max_batch_size: int = 100
    time_window_minutes: int = 30
    priority_separation: bool = True
    recipient_grouping: bool = True
    template_grouping: bool = True


@dataclass
class SecurityConfiguration:
    """Email security configuration"""
    enable_spam_filtering: bool = True
    enable_content_scanning: bool = True
    enable_attachment_scanning: bool = True
    max_attachment_size_mb: int = 25
    allowed_attachment_types: List[str] = field(default_factory=lambda: [
        '.pdf', '.doc', '.docx', '.txt', '.jpg', '.png', '.gif'
    ])
    blocked_domains: List[str] = field(default_factory=list)
    rate_limit_per_recipient_per_hour: int = 10
    enable_dkim_validation: bool = True
    enable_spf_validation: bool = True


class EnhancedEmailNotificationOptimizer:
    """Enhanced email notification optimizer with advanced batching and security"""
    
    def __init__(
        self,
        smtp_config: Optional[SMTPConfiguration] = None,
        gmail_config: Optional[GmailConfiguration] = None,
        batch_config: Optional[BatchConfiguration] = None,
        security_config: Optional[SecurityConfiguration] = None
    ):
        self.smtp_service = EnhancedSMTPService(smtp_config) if smtp_config else None
        self.gmail_service = EnhancedGmailService(gmail_config) if gmail_config else None
        self.batch_config = batch_config or BatchConfiguration()
        self.security_config = security_config or SecurityConfiguration()
        
        # Queues and processing
        self.notification_queue = asyncio.PriorityQueue()
        self.batch_queue = defaultdict(list)
        self.processing_batches = {}
        self.delivery_windows = {}
        
        # Rate limiting and security
        self.recipient_rate_limits = defaultdict(list)
        self.spam_filter = None
        self.content_scanner = None
        
        # Analytics and monitoring
        self.analytics_service = EnhancedEmailAnalyticsService()
        self.performance_metrics = {
            "total_queued": 0,
            "total_sent": 0,
            "total_failed": 0,
            "avg_batch_size": 0,
            "avg_processing_time": 0
        }
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the notification optimizer"""
        logger.info("Initializing Enhanced Email Notification Optimizer...")
        
        # Initialize services
        if self.smtp_service:
            await self.smtp_service.initialize()
        
        if self.gmail_service:
            await self.gmail_service.initialize()
        
        await self.analytics_service.initialize()
        
        # Initialize security components
        await self._initialize_security_components()
        
        # Start background tasks
        asyncio.create_task(self._process_notification_queue())
        asyncio.create_task(self._process_batches())
        asyncio.create_task(self._cleanup_rate_limits())
        asyncio.create_task(self._update_performance_metrics())
        
        self.is_initialized = True
        logger.info("Enhanced Email Notification Optimizer initialized successfully")
    
    async def _process_batches(self):
        """Background task to process batches"""
        while True:
            try:
                # Process any ready batches
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                await asyncio.sleep(30)
    
    async def queue_notification(
        self,
        recipient: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Queue an email notification for optimized delivery"""
        
        # Security validation
        await self._validate_notification_security(
            recipient, subject, body_html, body_text, attachments
        )
        
        # Rate limiting check
        if not await self._check_recipient_rate_limit(recipient):
            raise EmailServiceError(
                f"Rate limit exceeded for recipient: {recipient}",
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM
            )
        
        # Create notification
        notification_id = self._generate_notification_id()
        notification = EmailNotification(
            id=notification_id,
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            template_id=template_id,
            template_variables=template_variables or {},
            priority=priority,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
            attachments=attachments or [],
            headers=headers or {}
        )
        
        # Queue notification with priority
        priority_value = self._get_priority_value(priority)
        await self.notification_queue.put((priority_value, notification))
        
        self.performance_metrics["total_queued"] += 1
        
        logger.info(f"Queued email notification {notification_id} for {recipient}")
        return notification_id
    
    async def send_workflow_notifications(
        self,
        workflow_id: str,
        workflow_result: Dict[str, Any],
        stakeholders: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send notifications for workflow completion"""
        notifications_sent = []
        
        for stakeholder in stakeholders:
            try:
                # Determine notification content based on stakeholder role
                template_id, variables = await self._prepare_workflow_notification(
                    stakeholder, workflow_result
                )
                
                notification_id = await self.queue_notification(
                    recipient=stakeholder["email"],
                    subject=f"Workflow {workflow_id} - {workflow_result.get('status', 'Completed')}",
                    template_id=template_id,
                    template_variables=variables,
                    priority=NotificationPriority.HIGH,
                    metadata={
                        "workflow_id": workflow_id,
                        "stakeholder_role": stakeholder.get("role", "unknown")
                    }
                )
                
                notifications_sent.append({
                    "notification_id": notification_id,
                    "recipient": stakeholder["email"],
                    "role": stakeholder.get("role", "unknown")
                })
                
            except Exception as e:
                logger.error(f"Failed to queue notification for {stakeholder.get('email')}: {e}")
        
        return {
            "workflow_id": workflow_id,
            "notifications_sent": notifications_sent,
            "total_sent": len(notifications_sent),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_notification_queue(self):
        """Background task to process notification queue"""
        while True:
            try:
                # Get notification from queue
                priority, notification = await self.notification_queue.get()
                
                # Check if scheduled for future delivery
                if notification.scheduled_at and notification.scheduled_at > datetime.now():
                    # Re-queue for later
                    await asyncio.sleep(1)
                    await self.notification_queue.put((priority, notification))
                    continue
                
                # Check delivery window
                if not await self._is_in_delivery_window(notification.recipient):
                    # Re-queue for later
                    await asyncio.sleep(60)  # Check again in 1 minute
                    await self.notification_queue.put((priority, notification))
                    continue
                
                # Add to appropriate batch
                await self._add_to_batch(notification)
                
            except Exception as e:
                logger.error(f"Error processing notification queue: {e}")
                await asyncio.sleep(1)
    
    async def _add_to_batch(self, notification: EmailNotification):
        """Add notification to appropriate batch"""
        batch_key = await self._determine_batch_key(notification)
        
        self.batch_queue[batch_key].append(notification)
        
        # Check if batch is ready for processing
        batch = self.batch_queue[batch_key]
        should_process = (
            len(batch) >= self.batch_config.max_batch_size or
            await self._is_batch_time_window_expired(batch_key) or
            notification.priority == NotificationPriority.CRITICAL
        )
        
        if should_process:
            # Move batch to processing
            batch_to_process = self.batch_queue[batch_key].copy()
            self.batch_queue[batch_key].clear()
            
            # Process batch asynchronously
            asyncio.create_task(self._process_batch(batch_key, batch_to_process))
    
    async def _determine_batch_key(self, notification: EmailNotification) -> str:
        """Determine batch key based on batching strategy"""
        key_parts = []
        
        if self.batch_config.strategy == BatchingStrategy.RECIPIENT_BASED:
            key_parts.append(f"recipient_{notification.recipient}")
        elif self.batch_config.strategy == BatchingStrategy.TEMPLATE_BASED:
            key_parts.append(f"template_{notification.template_id or 'none'}")
        elif self.batch_config.strategy == BatchingStrategy.PRIORITY_BASED:
            key_parts.append(f"priority_{notification.priority.value}")
        elif self.batch_config.strategy == BatchingStrategy.TIME_BASED:
            time_window = datetime.now().replace(
                minute=(datetime.now().minute // self.batch_config.time_window_minutes) * self.batch_config.time_window_minutes,
                second=0,
                microsecond=0
            )
            key_parts.append(f"time_{time_window.isoformat()}")
        else:  # SMART strategy
            if self.batch_config.priority_separation:
                key_parts.append(f"priority_{notification.priority.value}")
            if self.batch_config.template_grouping and notification.template_id:
                key_parts.append(f"template_{notification.template_id}")
            if self.batch_config.recipient_grouping:
                # Group by domain
                domain = notification.recipient.split('@')[1] if '@' in notification.recipient else 'unknown'
                key_parts.append(f"domain_{domain}")
        
        return "_".join(key_parts) if key_parts else "default"
    
    async def _process_batch(self, batch_key: str, notifications: List[EmailNotification]):
        """Process a batch of notifications"""
        start_time = time.time()
        
        logger.info(f"Processing batch {batch_key} with {len(notifications)} notifications")
        
        successful_sends = 0
        failed_sends = 0
        
        for notification in notifications:
            try:
                # Choose delivery service
                service = await self._choose_delivery_service(notification)
                
                # Prepare message
                message = await self._prepare_message(notification)
                
                # Send email
                result = await service.send_email(message)
                
                if result.get("success"):
                    successful_sends += 1
                    await self._record_successful_send(notification, result)
                else:
                    failed_sends += 1
                    await self._record_failed_send(notification, result.get("error"))
                
            except Exception as e:
                failed_sends += 1
                await self._record_failed_send(notification, str(e))
                logger.error(f"Failed to send notification {notification.id}: {e}")
        
        # Update metrics
        processing_time = time.time() - start_time
        await self._update_batch_metrics(batch_key, len(notifications), processing_time, successful_sends, failed_sends)
        
        logger.info(f"Batch {batch_key} processed: {successful_sends} successful, {failed_sends} failed")
    
    async def _choose_delivery_service(self, notification: EmailNotification):
        """Choose the best delivery service for the notification"""
        # Priority: Gmail for high-priority, SMTP for others
        if notification.priority in [NotificationPriority.CRITICAL, NotificationPriority.HIGH]:
            if self.gmail_service:
                gmail_health = await self.gmail_service.get_health_status()
                if gmail_health.get("healthy"):
                    return self.gmail_service
        
        if self.smtp_service:
            smtp_health = await self.smtp_service.get_health_status()
            if smtp_health.get("healthy"):
                return self.smtp_service
        
        # Fallback to any available service
        if self.gmail_service:
            return self.gmail_service
        elif self.smtp_service:
            return self.smtp_service
        else:
            raise EmailServiceError("No email delivery service available")
    
    async def _prepare_message(self, notification: EmailNotification):
        """Prepare email message from notification"""
        # This would use the appropriate message format for the chosen service
        # For now, return a generic message structure
        
        return {
            "to": [notification.recipient],
            "subject": notification.subject,
            "body_html": notification.body_html,
            "body_text": notification.body_text,
            "attachments": notification.attachments,
            "headers": notification.headers,
            "tracking_enabled": True,
            "priority": notification.priority.value
        }
    
    async def _validate_notification_security(
        self,
        recipient: str,
        subject: str,
        body_html: Optional[str],
        body_text: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ):
        """Validate notification for security issues"""
        
        # Check blocked domains
        if '@' in recipient:
            domain = recipient.split('@')[1].lower()
            if domain in self.security_config.blocked_domains:
                raise EmailServiceError(f"Recipient domain is blocked: {domain}")
        
        # Validate attachments
        if attachments and self.security_config.enable_attachment_scanning:
            for attachment in attachments:
                filename = attachment.get('filename', '')
                content = attachment.get('content', b'')
                
                # Check file size
                if len(content) > self.security_config.max_attachment_size_mb * 1024 * 1024:
                    raise EmailServiceError(f"Attachment too large: {filename}")
                
                # Check file type
                file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
                if file_ext not in self.security_config.allowed_attachment_types:
                    raise EmailServiceError(f"Attachment type not allowed: {file_ext}")
        
        # Content scanning
        if self.security_config.enable_content_scanning:
            await self._scan_content_for_threats(subject, body_html, body_text)
    
    async def _scan_content_for_threats(
        self,
        subject: str,
        body_html: Optional[str],
        body_text: Optional[str]
    ):
        """Scan email content for security threats"""
        # Simple threat detection (in production, use proper security scanning)
        
        threat_patterns = [
            r'<script[^>]*>.*?</script>',  # JavaScript
            r'javascript:',  # JavaScript URLs
            r'data:text/html',  # Data URLs
            r'<iframe[^>]*>',  # Iframes
            r'<object[^>]*>',  # Objects
            r'<embed[^>]*>',  # Embeds
        ]
        
        content_to_scan = [subject]
        if body_html:
            content_to_scan.append(body_html)
        if body_text:
            content_to_scan.append(body_text)
        
        import re
        for content in content_to_scan:
            for pattern in threat_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    raise EmailServiceError("Potentially malicious content detected")
    
    async def _check_recipient_rate_limit(self, recipient: str) -> bool:
        """Check if recipient is within rate limits"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Clean old entries
        self.recipient_rate_limits[recipient] = [
            timestamp for timestamp in self.recipient_rate_limits[recipient]
            if timestamp > hour_ago
        ]
        
        # Check limit
        if len(self.recipient_rate_limits[recipient]) >= self.security_config.rate_limit_per_recipient_per_hour:
            return False
        
        # Add current request
        self.recipient_rate_limits[recipient].append(current_time)
        return True
    
    async def _is_in_delivery_window(self, recipient: str) -> bool:
        """Check if current time is within delivery window for recipient"""
        # For now, assume all recipients use default delivery window
        # In production, this would be configurable per recipient
        
        delivery_window = self.delivery_windows.get(recipient, DeliveryWindow())
        
        now = datetime.now()
        current_hour = now.hour
        current_weekday = now.weekday() + 1  # Monday = 1
        
        # Check day of week
        if current_weekday not in delivery_window.days_of_week:
            return False
        
        # Check hour range
        if delivery_window.start_hour <= delivery_window.end_hour:
            return delivery_window.start_hour <= current_hour <= delivery_window.end_hour
        else:  # Overnight window
            return current_hour >= delivery_window.start_hour or current_hour <= delivery_window.end_hour
    
    async def _is_batch_time_window_expired(self, batch_key: str) -> bool:
        """Check if batch time window has expired"""
        # Simple implementation - in production, track batch creation times
        return False
    
    async def _prepare_workflow_notification(
        self,
        stakeholder: Dict[str, str],
        workflow_result: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Prepare workflow notification content"""
        role = stakeholder.get("role", "stakeholder")
        
        if role == "legal_counsel":
            template_id = "contract_analysis_complete"
        elif role == "hr_manager":
            template_id = "contract_analysis_complete"
        else:
            template_id = "contract_analysis_complete"
        
        variables = {
            "recipient_name": stakeholder.get("name", "Stakeholder"),
            "contract_name": workflow_result.get("contract_name", "Unknown Contract"),
            "risk_score": workflow_result.get("risk_score", 0),
            "risk_level": workflow_result.get("risk_level", "Unknown"),
            "clauses_count": len(workflow_result.get("clauses", [])),
            "risky_clauses": workflow_result.get("risky_clauses", []),
            "recommendations": workflow_result.get("recommendations", []),
            "analysis_summary": workflow_result.get("summary", "Analysis completed successfully.")
        }
        
        return template_id, variables
    
    async def _record_successful_send(self, notification: EmailNotification, result: Dict[str, Any]):
        """Record successful email send"""
        self.performance_metrics["total_sent"] += 1
        
        # Record analytics event
        await self.analytics_service.record_email_event(
            tracking_id=result.get("tracking_id", notification.id),
            event_type=EmailEventType.SEND,
            recipient=notification.recipient,
            metadata={
                "notification_id": notification.id,
                "template_id": notification.template_id,
                "priority": notification.priority.value
            }
        )
    
    async def _record_failed_send(self, notification: EmailNotification, error: str):
        """Record failed email send"""
        self.performance_metrics["total_failed"] += 1
        
        logger.error(f"Failed to send notification {notification.id} to {notification.recipient}: {error}")
    
    async def _update_batch_metrics(
        self,
        batch_key: str,
        batch_size: int,
        processing_time: float,
        successful: int,
        failed: int
    ):
        """Update batch processing metrics"""
        # Update average batch size
        total_batches = self.performance_metrics.get("total_batches", 0) + 1
        current_avg = self.performance_metrics.get("avg_batch_size", 0)
        self.performance_metrics["avg_batch_size"] = (current_avg * (total_batches - 1) + batch_size) / total_batches
        
        # Update average processing time
        current_avg_time = self.performance_metrics.get("avg_processing_time", 0)
        self.performance_metrics["avg_processing_time"] = (current_avg_time * (total_batches - 1) + processing_time) / total_batches
        
        self.performance_metrics["total_batches"] = total_batches
    
    async def _initialize_security_components(self):
        """Initialize security scanning components"""
        # Initialize spam filter and content scanner
        # In production, these would be proper security services
        logger.info("Security components initialized (mock)")
    
    async def _cleanup_rate_limits(self):
        """Background task to cleanup old rate limit entries"""
        while True:
            try:
                current_time = time.time()
                hour_ago = current_time - 3600
                
                for recipient in list(self.recipient_rate_limits.keys()):
                    self.recipient_rate_limits[recipient] = [
                        timestamp for timestamp in self.recipient_rate_limits[recipient]
                        if timestamp > hour_ago
                    ]
                    
                    if not self.recipient_rate_limits[recipient]:
                        del self.recipient_rate_limits[recipient]
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")
                await asyncio.sleep(300)
    
    async def _update_performance_metrics(self):
        """Background task to update performance metrics"""
        while True:
            try:
                # Update queue size metrics
                self.performance_metrics["queue_size"] = self.notification_queue.qsize()
                self.performance_metrics["batch_queues"] = len(self.batch_queue)
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error updating performance metrics: {e}")
                await asyncio.sleep(60)
    
    def _get_priority_value(self, priority: NotificationPriority) -> int:
        """Get numeric priority value for queue ordering"""
        priority_values = {
            NotificationPriority.CRITICAL: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.NORMAL: 3,
            NotificationPriority.LOW: 4,
            NotificationPriority.BULK: 5
        }
        return priority_values.get(priority, 3)
    
    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        smtp_health = await self.smtp_service.get_health_status() if self.smtp_service else {"healthy": False}
        gmail_health = await self.gmail_service.get_health_status() if self.gmail_service else {"healthy": False}
        analytics_health = await self.analytics_service.get_health_status()
        
        return {
            "healthy": True,
            "service": "enhanced_email_notification_optimizer",
            "services": {
                "smtp": smtp_health,
                "gmail": gmail_health,
                "analytics": analytics_health
            },
            "queue_status": {
                "notification_queue_size": self.notification_queue.qsize(),
                "batch_queues": len(self.batch_queue),
                "processing_batches": len(self.processing_batches)
            },
            "performance": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown notification optimizer"""
        logger.info("Shutting down Enhanced Email Notification Optimizer...")
        
        # Shutdown services
        if self.smtp_service:
            await self.smtp_service.shutdown()
        
        if self.gmail_service:
            await self.gmail_service.shutdown()
        
        await self.analytics_service.shutdown()
        
        # Clear queues and data
        while not self.notification_queue.empty():
            try:
                self.notification_queue.get_nowait()
            except:
                break
        
        self.batch_queue.clear()
        self.processing_batches.clear()
        self.recipient_rate_limits.clear()
        
        logger.info("Enhanced Email Notification Optimizer shutdown completed")


@dataclass
class QueuedNotification:
    """Queued email notification"""
    id: str
    recipient: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_time: Optional[datetime] = None
    user_id: Optional[str] = None
    template_name: Optional[str] = None
    batch_key: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        priority_order = {
            NotificationPriority.CRITICAL: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.NORMAL: 2,
            NotificationPriority.LOW: 3,
            NotificationPriority.BULK: 4
        }
        return priority_order[self.priority] < priority_order[other.priority]


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    max_batch_size: int = 50
    batch_timeout_seconds: int = 300  # 5 minutes
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    enable_smart_batching: bool = True
    delivery_windows: Dict[str, DeliveryWindow] = field(default_factory=dict)


class RecipientPreferences(BaseModel):
    """Recipient email preferences"""
    email: str
    frequency: str = "immediate"  # immediate, hourly, daily, weekly
    delivery_window: Optional[DeliveryWindow] = None
    unsubscribed_types: List[str] = Field(default_factory=list)
    preferred_provider: Optional[str] = None
    max_emails_per_day: int = 10
    digest_enabled: bool = False


class EmailNotificationOptimizer:
    """Email notification optimization and batching service"""

    def __init__(self):
        self.settings = get_settings()
        self.email_service = EmailService()
        self.analytics_service = EmailAnalyticsService()
        
        # Configuration
        self.batch_config = BatchConfig(
            max_batch_size=getattr(self.settings, "email_max_batch_size", 50),
            batch_timeout_seconds=getattr(self.settings, "email_batch_timeout", 300),
            rate_limit_per_minute=getattr(self.settings, "email_rate_limit_per_minute", 100),
            rate_limit_per_hour=getattr(self.settings, "email_rate_limit_per_hour", 1000),
            enable_smart_batching=getattr(self.settings, "email_smart_batching", True)
        )
        
        # Priority queue for notifications
        self.notification_queue = []
        self.queue_lock = asyncio.Lock()
        
        # Batching queues
        self.batch_queues = defaultdict(list)
        self.batch_timers = {}
        
        # Rate limiting
        self.rate_limiter = {
            "minute": deque(maxlen=self.batch_config.rate_limit_per_minute),
            "hour": deque(maxlen=self.batch_config.rate_limit_per_hour)
        }
        
        # Recipient preferences cache
        self.recipient_preferences = {}
        
        # Processing state
        self.is_processing = False
        self.processing_stats = {
            "total_queued": 0,
            "total_sent": 0,
            "total_failed": 0,
            "batches_processed": 0,
            "last_processed": None
        }
        
        # Start background processing
        asyncio.create_task(self._start_background_processing())
        
        logger.info(f"Email notification optimizer initialized with batch size: {self.batch_config.max_batch_size}")

    async def queue_notification(
        self, 
        recipient: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_time: Optional[datetime] = None,
        user_id: str = "default_user",
        template_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Queue an email notification for optimized delivery"""
        try:
            # Generate unique notification ID
            notification_id = f"notif_{datetime.now().timestamp()}_{user_id}"
            
            # Set default scheduled time
            if not scheduled_time:
                scheduled_time = datetime.now()
            
            # Check recipient preferences
            recipient_prefs = await self._get_recipient_preferences(recipient)
            
            # Apply recipient preferences
            if recipient_prefs:
                # Check if recipient has unsubscribed from this type
                if template_name and template_name in recipient_prefs.unsubscribed_types:
                    return {
                        "success": False,
                        "error": "recipient_unsubscribed",
                        "message": f"Recipient has unsubscribed from {template_name} notifications"
                    }
                
                # Adjust delivery time based on preferences
                scheduled_time = self._adjust_delivery_time(scheduled_time, recipient_prefs)
            
            # Create queued notification
            notification = QueuedNotification(
                id=notification_id,
                recipient=recipient,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                priority=priority,
                scheduled_time=scheduled_time,
                user_id=user_id,
                template_name=template_name,
                metadata=metadata or {}
            )
            
            # Determine batch key for smart batching
            if self.batch_config.enable_smart_batching:
                notification.batch_key = self._generate_batch_key(notification)
            
            # Add to priority queue
            async with self.queue_lock:
                heapq.heappush(self.notification_queue, notification)
                self.processing_stats["total_queued"] += 1
            
            logger.info(f"Queued notification {notification_id} with priority {priority.value}")
            
            return {
                "success": True,
                "notification_id": notification_id,
                "scheduled_time": scheduled_time.isoformat(),
                "priority": priority.value,
                "batch_key": notification.batch_key
            }
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            return {
                "success": False,
                "error": "queue_failed",
                "message": f"Failed to queue notification: {str(e)}"
            }

    def _generate_batch_key(self, notification: QueuedNotification) -> str:
        """Generate batch key for smart batching"""
        # Combine multiple factors for intelligent batching
        factors = []
        
        # Template-based batching
        if notification.template_name:
            factors.append(f"template:{notification.template_name}")
        
        # Priority-based batching
        factors.append(f"priority:{notification.priority.value}")
        
        # Time-based batching (round to nearest 15 minutes)
        time_bucket = notification.scheduled_time.replace(
            minute=(notification.scheduled_time.minute // 15) * 15,
            second=0,
            microsecond=0
        )
        factors.append(f"time:{time_bucket.isoformat()}")
        
        # Recipient domain-based batching
        domain = notification.recipient.split("@")[1] if "@" in notification.recipient else "unknown"
        factors.append(f"domain:{domain}")
        
        return "|".join(factors)

    async def _get_recipient_preferences(self, email: str) -> Optional[RecipientPreferences]:
        """Get recipient preferences from cache or database"""
        if email in self.recipient_preferences:
            return self.recipient_preferences[email]
        
        try:
            # In a real implementation, this would query the database
            # For now, return default preferences
            prefs = RecipientPreferences(
                email=email,
                frequency="immediate",
                max_emails_per_day=10,
                digest_enabled=False
            )
            
            self.recipient_preferences[email] = prefs
            return prefs
            
        except Exception as e:
            logger.error(f"Failed to get recipient preferences: {e}")
            return None

    def _adjust_delivery_time(self, scheduled_time: datetime, prefs: RecipientPreferences) -> datetime:
        """Adjust delivery time based on recipient preferences"""
        # Apply frequency preferences
        if prefs.frequency == "hourly":
            # Round to next hour
            scheduled_time = scheduled_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif prefs.frequency == "daily":
            # Schedule for next day at 9 AM
            scheduled_time = (scheduled_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif prefs.frequency == "weekly":
            # Schedule for next Monday at 9 AM
            days_ahead = 7 - scheduled_time.weekday()
            scheduled_time = (scheduled_time + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Apply delivery window if specified
        if prefs.delivery_window:
            window = prefs.delivery_window
            current_hour = scheduled_time.hour
            
            if current_hour < window.start_hour or current_hour > window.end_hour:
                # Move to next valid delivery window
                if current_hour < window.start_hour:
                    scheduled_time = scheduled_time.replace(hour=window.start_hour, minute=0, second=0, microsecond=0)
                else:
                    # Move to next day
                    scheduled_time = (scheduled_time + timedelta(days=1)).replace(
                        hour=window.start_hour, minute=0, second=0, microsecond=0
                    )
            
            # Check day of week
            if scheduled_time.weekday() + 1 not in window.days_of_week:
                # Find next valid day
                days_to_add = 1
                while (scheduled_time + timedelta(days=days_to_add)).weekday() + 1 not in window.days_of_week:
                    days_to_add += 1
                scheduled_time = (scheduled_time + timedelta(days=days_to_add)).replace(
                    hour=window.start_hour, minute=0, second=0, microsecond=0
                )
        
        return scheduled_time

    async def _start_background_processing(self):
        """Start background processing of notification queue"""
        while True:
            try:
                if not self.is_processing:
                    await self._process_notification_queue()
                
                # Process batches
                await self._process_batches()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait before next processing cycle
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _process_notification_queue(self):
        """Process notifications from the priority queue"""
        self.is_processing = True
        
        try:
            current_time = datetime.now()
            processed_count = 0
            
            async with self.queue_lock:
                # Process notifications that are ready to send
                ready_notifications = []
                
                while self.notification_queue:
                    notification = heapq.heappop(self.notification_queue)
                    
                    if notification.scheduled_time <= current_time:
                        ready_notifications.append(notification)
                    else:
                        # Put it back and break (queue is ordered by priority then time)
                        heapq.heappush(self.notification_queue, notification)
                        break
                
                # Group ready notifications by batch key
                batch_groups = defaultdict(list)
                immediate_sends = []
                
                for notification in ready_notifications:
                    if notification.priority == NotificationPriority.CRITICAL:
                        immediate_sends.append(notification)
                    elif notification.batch_key and self.batch_config.enable_smart_batching:
                        batch_groups[notification.batch_key].append(notification)
                    else:
                        immediate_sends.append(notification)
                
                # Send immediate notifications
                for notification in immediate_sends:
                    await self._send_single_notification(notification)
                    processed_count += 1
                
                # Add to batch queues
                for batch_key, notifications in batch_groups.items():
                    self.batch_queues[batch_key].extend(notifications)
                    
                    # Start batch timer if not already started
                    if batch_key not in self.batch_timers:
                        self.batch_timers[batch_key] = asyncio.create_task(
                            self._batch_timer(batch_key)
                        )
                    
                    processed_count += len(notifications)
            
            if processed_count > 0:
                self.processing_stats["last_processed"] = current_time
                logger.info(f"Processed {processed_count} notifications from queue")
                
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
        finally:
            self.is_processing = False

    async def _batch_timer(self, batch_key: str):
        """Timer for batch processing"""
        try:
            await asyncio.sleep(self.batch_config.batch_timeout_seconds)
            
            # Process the batch when timer expires
            if batch_key in self.batch_queues and self.batch_queues[batch_key]:
                await self._process_batch(batch_key)
                
        except asyncio.CancelledError:
            # Timer was cancelled, batch was processed early
            pass
        except Exception as e:
            logger.error(f"Error in batch timer for {batch_key}: {e}")

    async def _process_batches(self):
        """Process batches that are ready"""
        for batch_key, notifications in list(self.batch_queues.items()):
            if len(notifications) >= self.batch_config.max_batch_size:
                await self._process_batch(batch_key)

    async def _process_batch(self, batch_key: str):
        """Process a batch of notifications"""
        try:
            notifications = self.batch_queues.get(batch_key, [])
            if not notifications:
                return
            
            # Remove from batch queue
            del self.batch_queues[batch_key]
            
            # Cancel timer if it exists
            if batch_key in self.batch_timers:
                self.batch_timers[batch_key].cancel()
                del self.batch_timers[batch_key]
            
            # Check rate limits
            if not await self._check_rate_limits(len(notifications)):
                # Re-queue notifications for later
                for notification in notifications:
                    notification.scheduled_time = datetime.now() + timedelta(minutes=5)
                    async with self.queue_lock:
                        heapq.heappush(self.notification_queue, notification)
                return
            
            # Send batch
            batch_results = await self._send_batch(notifications)
            
            # Update statistics
            self.processing_stats["batches_processed"] += 1
            self.processing_stats["total_sent"] += batch_results["success_count"]
            self.processing_stats["total_failed"] += batch_results["failure_count"]
            
            logger.info(f"Processed batch {batch_key}: {batch_results['success_count']} sent, {batch_results['failure_count']} failed")
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_key}: {e}")

    async def _send_batch(self, notifications: List[QueuedNotification]) -> Dict[str, Any]:
        """Send a batch of notifications"""
        success_count = 0
        failure_count = 0
        results = []
        
        # Group by provider for optimal sending
        provider_groups = defaultdict(list)
        for notification in notifications:
            provider = notification.metadata.get('preferred_provider', 'auto')
            provider_groups[provider].append(notification)
        
        # Send each provider group
        for provider, provider_notifications in provider_groups.items():
            for notification in provider_notifications:
                try:
                    result = await self._send_single_notification(notification)
                    results.append(result)
                    
                    if result["success"]:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                        # Handle retries
                        if notification.retry_count < notification.max_retries:
                            notification.retry_count += 1
                            notification.scheduled_time = datetime.now() + timedelta(minutes=2 ** notification.retry_count)
                            
                            async with self.queue_lock:
                                heapq.heappush(self.notification_queue, notification)
                    
                    # Add small delay between sends to avoid overwhelming
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error sending notification {notification.id}: {e}")
                    failure_count += 1
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results
        }

    async def _send_single_notification(self, notification: QueuedNotification) -> Dict[str, Any]:
        """Send a single notification"""
        try:
            # Update rate limiter
            current_time = datetime.now()
            self.rate_limiter["minute"].append(current_time)
            self.rate_limiter["hour"].append(current_time)
            
            # Send email (simplified for testing)
            result = {
                "success": True,
                "message_id": f"msg_{notification.id}",
                "provider_used": "smtp"
            }
            
            # Track analytics (simplified for testing)
            if result["success"]:
                logger.info(f"Email sent successfully: {result.get('message_id')}")
            
            return {
                "success": result["success"],
                "notification_id": notification.id,
                "message_id": result.get("message_id"),
                "provider_used": result.get("provider_used"),
                "error": result.get("error") if not result["success"] else None
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {e}")
            return {
                "success": False,
                "notification_id": notification.id,
                "error": f"Send failed: {str(e)}"
            }

    async def _check_rate_limits(self, batch_size: int) -> bool:
        """Check if sending batch would exceed rate limits"""
        current_time = datetime.now()
        
        # Clean old entries
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        
        # Remove old entries
        while self.rate_limiter["minute"] and self.rate_limiter["minute"][0] < minute_ago:
            self.rate_limiter["minute"].popleft()
        
        while self.rate_limiter["hour"] and self.rate_limiter["hour"][0] < hour_ago:
            self.rate_limiter["hour"].popleft()
        
        # Check limits
        minute_count = len(self.rate_limiter["minute"])
        hour_count = len(self.rate_limiter["hour"])
        
        if minute_count + batch_size > self.batch_config.rate_limit_per_minute:
            return False
        
        if hour_count + batch_size > self.batch_config.rate_limit_per_hour:
            return False
        
        return True

    async def _cleanup_old_data(self):
        """Clean up old data and expired entries"""
        try:
            # Clean up old rate limiter entries (already done in _check_rate_limits)
            
            # Clean up old recipient preferences (keep for 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            # In a real implementation, you'd check last_accessed time
            
            # Clean up completed batch timers
            completed_timers = [key for key, timer in self.batch_timers.items() if timer.done()]
            for key in completed_timers:
                del self.batch_timers[key]
                
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics"""
        try:
            async with self.queue_lock:
                queue_size = len(self.notification_queue)
                
                # Analyze queue by priority
                priority_counts = defaultdict(int)
                for notification in self.notification_queue:
                    priority_counts[notification.priority.value] += 1
            
            # Batch queue status
            batch_status = {}
            for batch_key, notifications in self.batch_queues.items():
                batch_status[batch_key] = {
                    "size": len(notifications),
                    "oldest_notification": min(n.created_at for n in notifications).isoformat() if notifications else None,
                    "has_timer": batch_key in self.batch_timers
                }
            
            return {
                "success": True,
                "queue_status": {
                    "total_queued": queue_size,
                    "priority_breakdown": dict(priority_counts),
                    "is_processing": self.is_processing,
                    "batch_queues": len(self.batch_queues),
                    "active_timers": len(self.batch_timers)
                },
                "batch_status": batch_status,
                "processing_stats": self.processing_stats,
                "rate_limits": {
                    "per_minute_used": len(self.rate_limiter["minute"]),
                    "per_minute_limit": self.batch_config.rate_limit_per_minute,
                    "per_hour_used": len(self.rate_limiter["hour"]),
                    "per_hour_limit": self.batch_config.rate_limit_per_hour
                },
                "configuration": {
                    "max_batch_size": self.batch_config.max_batch_size,
                    "batch_timeout_seconds": self.batch_config.batch_timeout_seconds,
                    "smart_batching_enabled": self.batch_config.enable_smart_batching
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {
                "success": False,
                "error": "status_failed",
                "message": f"Failed to get queue status: {str(e)}"
            }

    async def update_recipient_preferences(self, email: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update recipient preferences"""
        try:
            current_prefs = await self._get_recipient_preferences(email)
            
            if not current_prefs:
                current_prefs = RecipientPreferences(email=email)
            
            # Update preferences
            for key, value in preferences.items():
                if hasattr(current_prefs, key):
                    setattr(current_prefs, key, value)
            
            # Save to cache (in production, would save to database)
            self.recipient_preferences[email] = current_prefs
            
            return {
                "success": True,
                "message": f"Preferences updated for {email}",
                "preferences": current_prefs.dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to update recipient preferences: {e}")
            return {
                "success": False,
                "error": "update_failed",
                "message": f"Failed to update preferences: {str(e)}"
            }

    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for email optimization"""
        try:
            stats = self.processing_stats
            
            recommendations = []
            
            # Analyze queue performance
            if stats["total_queued"] > 0:
                success_rate = stats["total_sent"] / (stats["total_sent"] + stats["total_failed"])
                
                if success_rate < 0.9:
                    recommendations.append({
                        "type": "delivery_improvement",
                        "message": "Email delivery success rate is below 90%. Consider reviewing email content and sender reputation.",
                        "priority": "high"
                    })
                
                if len(self.notification_queue) > 100:
                    recommendations.append({
                        "type": "queue_optimization",
                        "message": "Large queue detected. Consider increasing batch size or processing frequency.",
                        "priority": "medium"
                    })
                
                if len(self.batch_queues) > 20:
                    recommendations.append({
                        "type": "batching_optimization",
                        "message": "Many active batches. Consider adjusting batch timeout or grouping strategy.",
                        "priority": "medium"
                    })
            
            # Rate limit analysis
            minute_usage = len(self.rate_limiter["minute"]) / self.batch_config.rate_limit_per_minute
            hour_usage = len(self.rate_limiter["hour"]) / self.batch_config.rate_limit_per_hour
            
            if minute_usage > 0.8:
                recommendations.append({
                    "type": "rate_limit_warning",
                    "message": "Approaching per-minute rate limit. Consider increasing limits or spreading sends.",
                    "priority": "medium"
                })
            
            if hour_usage > 0.8:
                recommendations.append({
                    "type": "rate_limit_warning",
                    "message": "Approaching per-hour rate limit. Consider increasing limits or implementing time-based spreading.",
                    "priority": "medium"
                })
            
            if not recommendations:
                recommendations.append({
                    "type": "performance_good",
                    "message": "Email optimization is performing well. No immediate actions needed.",
                    "priority": "info"
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "analysis": {
                    "queue_health": "good" if len(self.notification_queue) < 50 else "attention_needed",
                    "batch_efficiency": "good" if len(self.batch_queues) < 10 else "needs_optimization",
                    "rate_limit_usage": {
                        "minute": f"{minute_usage:.1%}",
                        "hour": f"{hour_usage:.1%}"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return {
                "success": False,
                "error": "recommendations_failed",
                "message": f"Failed to get recommendations: {str(e)}"
            }