"""
Consolidated Email Template Manager - Unified template management with analytics and optimization.
Combines template management, analytics, and notification optimization functionality.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import uuid

from pydantic import BaseModel, Field, EmailStr, validator
from jinja2 import Environment, FileSystemLoader, Template, TemplateError, select_autoescape
import aiofiles

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class TemplateStatus(str, Enum):
    """Template status types"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemplateCategory(str, Enum):
    """Template categories"""
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    LEGAL = "legal"


class TemplateType(str, Enum):
    """Email template types"""
    CONTRACT_ANALYSIS = "contract_analysis"
    RISK_ALERT = "risk_alert"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    REMINDER = "reminder"
    REPORT = "report"
    MORNING_BRIEFING = "morning_briefing"
    EVENING_SUMMARY = "evening_summary"
    JOB_ALERT = "job_alert"
    APPLICATION_CONFIRMATION = "application_confirmation"
    SKILL_GAP_REPORT = "skill_gap_report"
    MARKETING = "marketing"
    SYSTEM = "system"
    CUSTOM = "custom"


class TemplateFormat(str, Enum):
    """Template format types"""
    HTML = "html"
    TEXT = "text"
    MIXED = "mixed"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BULK = "bulk"


class BatchingStrategy(str, Enum):
    """Email batching strategies"""
    TIME_BASED = "time_based"
    RECIPIENT_BASED = "recipient_based"
    TEMPLATE_BASED = "template_based"
    PRIORITY_BASED = "priority_based"
    SMART = "smart"


@dataclass
class TemplateVariable:
    """Template variable definition"""
    name: str
    type: str  # string, number, boolean, array, object
    required: bool = True
    default_value: Optional[Any] = None
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class TemplateVersion:
    """Template version information"""
    version: str
    created_at: datetime
    created_by: str
    changelog: str
    is_active: bool = False


@dataclass
class TemplateMetrics:
    """Template usage metrics"""
    sent_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    last_used: Optional[datetime] = None


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


class EmailTemplate(BaseModel):
    """Enhanced email template model"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    type: TemplateType = Field(..., description="Template type")
    category: TemplateCategory = Field(..., description="Template category")
    status: TemplateStatus = Field(TemplateStatus.DRAFT, description="Template status")
    
    # Content
    subject_template: str = Field(..., description="Subject template")
    html_template: Optional[str] = Field(None, description="HTML template")
    text_template: Optional[str] = Field(None, description="Text template")
    
    # Metadata
    variables: List[TemplateVariable] = Field(default_factory=list, description="Template variables")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    language: str = Field("en", description="Template language")
    
    # Versioning
    version: str = Field("1.0.0", description="Template version")
    versions: List[TemplateVersion] = Field(default_factory=list, description="Version history")
    
    # Settings
    tracking_enabled: bool = Field(True, description="Enable tracking")
    unsubscribe_enabled: bool = Field(True, description="Enable unsubscribe")
    
    # Metrics
    metrics: TemplateMetrics = Field(default_factory=TemplateMetrics, description="Usage metrics")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field("system", description="Creator")
    updated_by: str = Field("system", description="Last updater")

    @validator('subject_template', 'html_template', 'text_template')
    def validate_templates(cls, v):
        if v and len(v) > 100000:  # 100KB limit
            raise ValueError('Template too large (max 100KB)')
        return v


class DeliveryWindow(BaseModel):
    """Delivery time window configuration"""
    start_hour: int = Field(8, ge=0, le=23, description="Start hour (24h format)")
    end_hour: int = Field(18, ge=0, le=23, description="End hour (24h format)")
    timezone: str = Field("UTC", description="Timezone for delivery window")
    days_of_week: List[int] = Field([1, 2, 3, 4, 5], description="Days of week (1=Monday)")


class RecipientPreferences(BaseModel):
    """Recipient email preferences"""
    email: str
    frequency: str = "immediate"  # immediate, hourly, daily, weekly
    delivery_window: Optional[DeliveryWindow] = None
    unsubscribed_types: List[str] = Field(default_factory=list)
    preferred_provider: Optional[str] = None
    max_emails_per_day: int = 10
    digest_enabled: bool = False


class EmailTemplateManager:
    """Consolidated email template manager with analytics and optimization"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Template management
        self.templates: Dict[str, EmailTemplate] = {}
        self.templates_dir = Path("backend/app/email_templates")
        self.custom_templates_dir = Path("backend/app/email_templates/custom")
        
        # Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader([str(self.templates_dir), str(self.custom_templates_dir)]),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Caching
        self.template_cache = {}
        self.rendered_cache = {}
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour
        
        # Notification optimization
        self.notification_queue = asyncio.PriorityQueue()
        self.batch_queue = defaultdict(list)
        self.batch_config = BatchConfiguration(
            max_batch_size=getattr(self.settings, "email_max_batch_size", 50),
            time_window_minutes=getattr(self.settings, "email_batch_timeout", 5),
            strategy=BatchingStrategy.SMART
        )
        
        # Rate limiting
        self.rate_limiter = {
            "minute": deque(maxlen=100),
            "hour": deque(maxlen=1000)
        }
        
        # Recipient preferences
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
        
        # Analytics
        self.template_analytics = defaultdict(lambda: {
            "renders": 0,
            "sends": 0,
            "opens": 0,
            "clicks": 0,
            "last_used": None
        })
        
        self.is_initialized = False

    async def initialize(self):
        """Initialize the template manager"""
        logger.info("Initializing consolidated email template manager...")
        
        # Create directories
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 filters and functions
        self._setup_jinja_filters()
        
        # Load built-in templates
        await self._load_builtin_templates()
        
        # Start background processing
        asyncio.create_task(self._start_background_processing())
        
        self.is_initialized = True
        logger.info("Consolidated email template manager initialized successfully")

    def _setup_jinja_filters(self):
        """Setup custom Jinja2 filters and functions"""
        def format_currency(value, currency='USD'):
            """Format currency values"""
            return f"${value:,.2f}" if currency == "USD" else f"{value:,.2f} {currency}"
        
        def format_date(value, format='%Y-%m-%d'):
            """Format date values"""
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            return value.strftime(format)
        
        def truncate_text(value, length=100, suffix='...'):
            """Truncate text to specified length"""
            if len(value) <= length:
                return value
            return value[:length] + suffix
        
        def format_risk_level(risk_score: float) -> str:
            """Format risk level from score"""
            if risk_score >= 8:
                return "Critical"
            elif risk_score >= 6:
                return "High"
            elif risk_score >= 4:
                return "Medium"
            else:
                return "Low"
        
        def risk_color(risk_level: str) -> str:
            """Get color for risk level"""
            colors = {
                "Critical": "#dc3545",
                "High": "#fd7e14",
                "Medium": "#ffc107",
                "Low": "#28a745"
            }
            return colors.get(risk_level, "#6c757d")
        
        # Add filters
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['date'] = format_date
        self.jinja_env.filters['truncate'] = truncate_text
        self.jinja_env.filters['risk_level'] = format_risk_level
        self.jinja_env.filters['risk_color'] = risk_color
        
        # Add global functions
        self.jinja_env.globals['now'] = datetime.now
        self.jinja_env.globals['today'] = datetime.now().date

    async def _load_builtin_templates(self):
        """Load built-in email templates"""
        builtin_templates = [
            {
                "id": "contract_analysis_complete",
                "name": "Contract Analysis Complete",
                "description": "Notification when contract analysis is completed",
                "type": TemplateType.CONTRACT_ANALYSIS,
                "category": TemplateCategory.TRANSACTIONAL,
                "status": TemplateStatus.ACTIVE,
                "subject_template": "🔍 Contract Analysis Complete - {{ contract_name }}",
                "html_template": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Contract Analysis Complete</h2>
                    <p>Hello {{ recipient_name }},</p>
                    <p>The analysis for contract "{{ contract_name }}" has been completed.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Analysis Summary</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Risk Score:</strong> {{ risk_score }}/10</li>
                            <li><strong>Risk Level:</strong> <span style="color: {{ risk_score | risk_level | risk_color }}; font-weight: bold;">{{ risk_score | risk_level }}</span></li>
                            <li><strong>Clauses Analyzed:</strong> {{ clauses_count }}</li>
                        </ul>
                    </div>
                    
                    {% if risky_clauses %}
                    <h3>Risky Clauses Identified</h3>
                    <ul>
                    {% for clause in risky_clauses %}
                        <li style="margin-bottom: 10px;">
                            <strong>{{ clause.type }}:</strong> {{ clause.description }}
                            {% if clause.risk_level %}
                            <span style="color: {{ clause.risk_level | risk_color }}; font-size: 0.9em;">({{ clause.risk_level }})</span>
                            {% endif %}
                        </li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if recommendations %}
                    <h3>Recommendations</h3>
                    <ul>
                    {% for recommendation in recommendations %}
                        <li style="margin-bottom: 10px;">{{ recommendation }}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    
                    <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Summary:</strong> {{ analysis_summary }}</p>
                    </div>
                    
                    <p style="margin-top: 30px;">
                        Best regards,<br>
                        <strong>Career Copilot Team</strong>
                    </p>
                    
                    <div style="font-size: 0.8em; color: #666; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                        <p>Analysis completed on {{ analysis_date }} at {{ analysis_time }}</p>
                        <p>Analysis ID: {{ analysis_id }}</p>
                    </div>
                </div>
                """,
                "text_template": """
                Contract Analysis Complete
                
                Hello {{ recipient_name }},
                
                The analysis for contract "{{ contract_name }}" has been completed.
                
                Analysis Summary:
                - Risk Score: {{ risk_score }}/10
                - Risk Level: {{ risk_score | risk_level }}
                - Clauses Analyzed: {{ clauses_count }}
                
                {% if risky_clauses %}
                Risky Clauses Identified:
                {% for clause in risky_clauses %}
                - {{ clause.type }}: {{ clause.description }}
                {% endfor %}
                {% endif %}
                
                {% if recommendations %}
                Recommendations:
                {% for recommendation in recommendations %}
                - {{ recommendation }}
                {% endfor %}
                {% endif %}
                
                Summary: {{ analysis_summary }}
                
                Best regards,
                Career Copilot Team
                
                Analysis completed on {{ analysis_date }} at {{ analysis_time }}
                Analysis ID: {{ analysis_id }}
                """,
                "variables": [
                    TemplateVariable("recipient_name", "string", False, description="Recipient name"),
                    TemplateVariable("contract_name", "string", True, description="Name of the contract"),
                    TemplateVariable("risk_score", "number", True, description="Overall risk score (0-10)"),
                    TemplateVariable("clauses_count", "number", True, description="Number of clauses analyzed"),
                    TemplateVariable("risky_clauses", "array", True, description="List of risky clauses"),
                    TemplateVariable("recommendations", "array", True, description="List of recommendations"),
                    TemplateVariable("analysis_summary", "string", True, description="Analysis summary text"),
                    TemplateVariable("analysis_date", "string", True, description="Analysis completion date"),
                    TemplateVariable("analysis_time", "string", True, description="Analysis completion time"),
                    TemplateVariable("analysis_id", "string", True, description="Unique analysis identifier")
                ]
            },
            {
                "id": "risk_alert",
                "name": "High Risk Alert",
                "description": "Alert for high-risk contracts requiring immediate attention",
                "type": TemplateType.RISK_ALERT,
                "category": TemplateCategory.NOTIFICATION,
                "status": TemplateStatus.ACTIVE,
                "subject_template": "🚨 HIGH RISK ALERT: {{ contract_name }}",
                "html_template": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <h2 style="color: #721c24; margin-top: 0;">⚠️ High Risk Contract Detected</h2>
                        <p><strong>Contract:</strong> {{ contract_name }}</p>
                        <p><strong>Risk Score:</strong> <span style="color: #dc3545; font-weight: bold; font-size: 1.2em;">{{ risk_score }}/10</span></p>
                        <p><strong>Risk Level:</strong> <span style="color: {{ risk_level | risk_color }}; font-weight: bold;">{{ risk_level }}</span></p>
                        <p><strong>Alert Time:</strong> {{ alert_timestamp }}</p>
                    </div>
                    
                    <h3 style="color: #dc3545;">Urgent Clauses Requiring Immediate Attention</h3>
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px;">
                        <ul style="margin: 0; padding-left: 20px;">
                        {% for clause in urgent_clauses %}
                            <li style="margin-bottom: 15px; color: #856404;">
                                <strong style="color: #dc3545;">{{ clause.type }}:</strong> {{ clause.description }}
                                {% if clause.severity %}
                                <br><small style="color: #666;">Severity: {{ clause.severity }}</small>
                                {% endif %}
                            </li>
                        {% endfor %}
                        </ul>
                    </div>
                    
                    <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #0c5460;">
                            <strong>⚡ Immediate Action Required:</strong> 
                            Please review this contract carefully before proceeding. Consider consulting with legal counsel.
                        </p>
                    </div>
                    
                    <p style="margin-top: 30px;">
                        Best regards,<br>
                        <strong>Career Copilot Risk Management Team</strong>
                    </p>
                </div>
                """,
                "variables": [
                    TemplateVariable("recipient_name", "string", False, description="Recipient name"),
                    TemplateVariable("contract_name", "string", True, description="Name of the contract"),
                    TemplateVariable("risk_score", "number", True, description="Risk score (0-10)"),
                    TemplateVariable("risk_level", "string", True, description="Risk level text"),
                    TemplateVariable("urgent_clauses", "array", True, description="List of urgent clauses"),
                    TemplateVariable("alert_timestamp", "string", True, description="Alert timestamp")
                ]
            }
        ]
        
        for template_data in builtin_templates:
            try:
                template = EmailTemplate(**template_data)
                template.versions.append(TemplateVersion(
                    version=template.version,
                    created_at=datetime.now(),
                    created_by="system",
                    changelog="Built-in template",
                    is_active=True
                ))
                self.templates[template.id] = template
                logger.info(f"Loaded built-in template: {template.id}")
            except Exception as e:
                logger.error(f"Failed to load built-in template {template_data.get('id')}: {e}")

    async def create_template(
        self,
        template_data: Dict[str, Any],
        created_by: str = "system"
    ) -> EmailTemplate:
        """Create a new email template"""
        # Validate template data
        await self._validate_template_data(template_data)
        
        # Create template
        template = EmailTemplate(
            **template_data,
            created_by=created_by,
            updated_by=created_by
        )
        
        # Add initial version
        template.versions.append(TemplateVersion(
            version=template.version,
            created_at=datetime.now(),
            created_by=created_by,
            changelog="Initial version",
            is_active=True
        ))
        
        # Store template
        self.templates[template.id] = template
        
        # Save to file
        await self._save_template_to_file(template)
        
        logger.info(f"Created email template: {template.id}")
        return template

    async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    async def list_templates(
        self,
        type_filter: Optional[TemplateType] = None,
        category_filter: Optional[TemplateCategory] = None,
        status_filter: Optional[TemplateStatus] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[EmailTemplate]:
        """List templates with optional filters"""
        templates = list(self.templates.values())
        
        if type_filter:
            templates = [t for t in templates if t.type == type_filter]
        
        if category_filter:
            templates = [t for t in templates if t.category == category_filter]
        
        if status_filter:
            templates = [t for t in templates if t.status == status_filter]
        
        if tags_filter:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags_filter)
            ]
        
        return sorted(templates, key=lambda t: t.updated_at, reverse=True)

    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        format_type: TemplateFormat = TemplateFormat.HTML,
        recipient: Optional[str] = None
    ) -> str:
        """Render template with variables"""
        template = await self.get_template(template_id)
        if not template:
            raise EmailServiceError(f"Template not found: {template_id}")
        
        # Validate variables
        await self._validate_template_variables(template, variables)
        
        # Add system variables
        render_vars = {**variables}
        render_vars.update({
            'recipient_email': recipient or "unknown",
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_datetime': datetime.now().isoformat(),
            'template_id': template_id,
            'template_name': template.name
        })
        
        # Get template content
        if format_type == TemplateFormat.HTML and template.html_template:
            template_content = template.html_template
        elif format_type == TemplateFormat.TEXT and template.text_template:
            template_content = template.text_template
        else:
            raise EmailServiceError(f"Template format not available: {format_type}")
        
        # Check cache
        cache_key = f"{template_id}_{format_type}_{hash(str(variables))}"
        if self.cache_enabled and cache_key in self.rendered_cache:
            return self.rendered_cache[cache_key]
        
        try:
            # Render template
            jinja_template = self.jinja_env.from_string(template_content)
            rendered = jinja_template.render(**render_vars)
            
            # Cache result
            if self.cache_enabled:
                self.rendered_cache[cache_key] = rendered
            
            # Update metrics
            await self._update_template_metrics(template_id, 'render')
            
            return rendered
            
        except TemplateError as e:
            logger.error(f"Template rendering error for {template_id}: {e}")
            raise EmailServiceError(f"Template rendering failed: {e}")

    async def render_subject(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render template subject"""
        template = await self.get_template(template_id)
        if not template:
            raise EmailServiceError(f"Template not found: {template_id}")
        
        # Add system variables
        render_vars = {**variables}
        render_vars.update({
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_datetime': datetime.now().isoformat(),
            'template_id': template_id,
            'template_name': template.name
        })
        
        try:
            jinja_template = self.jinja_env.from_string(template.subject_template)
            return jinja_template.render(**render_vars)
        except TemplateError as e:
            logger.error(f"Subject rendering error for {template_id}: {e}")
            raise EmailServiceError(f"Subject rendering failed: {e}")

    async def queue_notification(
        self, 
        recipient: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_time: Optional[datetime] = None,
        user_id: str = "default_user",
        template_id: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None,
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
                if template_id and template_id in recipient_prefs.unsubscribed_types:
                    return {
                        "success": False,
                        "error": "recipient_unsubscribed",
                        "message": f"Recipient has unsubscribed from {template_id} notifications"
                    }
                
                # Adjust delivery time based on preferences
                scheduled_time = self._adjust_delivery_time(scheduled_time, recipient_prefs)
            
            # Create queued notification
            notification = EmailNotification(
                id=notification_id,
                recipient=recipient,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                priority=priority,
                scheduled_at=scheduled_time,
                template_id=template_id,
                template_variables=template_variables or {},
                metadata=metadata or {}
            )
            
            # Add to priority queue
            priority_value = self._get_priority_value(priority)
            await self.notification_queue.put((priority_value, notification))
            
            self.processing_stats["total_queued"] += 1
            
            logger.info(f"Queued notification {notification_id} with priority {priority.value}")
            
            return {
                "success": True,
                "notification_id": notification_id,
                "scheduled_time": scheduled_time.isoformat(),
                "priority": priority.value
            }
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            return {
                "success": False,
                "error": "queue_failed",
                "message": f"Failed to queue notification: {str(e)}"
            }

    async def _get_recipient_preferences(self, email: str) -> Optional[RecipientPreferences]:
        """Get recipient preferences from cache"""
        if email in self.recipient_preferences:
            return self.recipient_preferences[email]
        
        try:
            # In a real implementation, this would query the database
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

    async def _start_background_processing(self):
        """Start background processing of notification queue"""
        while True:
            try:
                if not self.is_processing:
                    await self._process_notification_queue()
                
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
            
            # Process up to 10 notifications per cycle
            for _ in range(10):
                try:
                    # Get notification from queue (non-blocking)
                    priority, notification = self.notification_queue.get_nowait()
                    
                    if notification.scheduled_at and notification.scheduled_at <= current_time:
                        # Process notification (simplified - would integrate with email service)
                        await self._process_single_notification(notification)
                        processed_count += 1
                    else:
                        # Put it back for later
                        await self.notification_queue.put((priority, notification))
                        break
                        
                except asyncio.QueueEmpty:
                    break
            
            if processed_count > 0:
                self.processing_stats["last_processed"] = current_time
                self.processing_stats["total_sent"] += processed_count
                logger.info(f"Processed {processed_count} notifications from queue")
                
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
        finally:
            self.is_processing = False

    async def _process_single_notification(self, notification: EmailNotification):
        """Process a single notification"""
        try:
            # If template_id is specified, render the template
            if notification.template_id:
                # Render subject
                subject = await self.render_subject(
                    notification.template_id, 
                    notification.template_variables or {}
                )
                
                # Render HTML body
                if not notification.body_html:
                    notification.body_html = await self.render_template(
                        notification.template_id,
                        notification.template_variables or {},
                        TemplateFormat.HTML,
                        notification.recipient
                    )
                
                # Render text body if template has it
                template = await self.get_template(notification.template_id)
                if template and template.text_template and not notification.body_text:
                    notification.body_text = await self.render_template(
                        notification.template_id,
                        notification.template_variables or {},
                        TemplateFormat.TEXT,
                        notification.recipient
                    )
                
                notification.subject = subject
            
            # Update template analytics
            if notification.template_id:
                await self._update_template_metrics(notification.template_id, 'send')
            
            logger.info(f"Processed notification {notification.id} for {notification.recipient}")
            
        except Exception as e:
            logger.error(f"Failed to process notification {notification.id}: {e}")
            self.processing_stats["total_failed"] += 1

    async def _validate_template_data(self, template_data: Dict[str, Any]):
        """Validate template data"""
        required_fields = ['id', 'name', 'type', 'subject_template']
        for field in required_fields:
            if field not in template_data:
                raise EmailServiceError(f"Missing required field: {field}")
        
        # Check for duplicate ID
        if template_data['id'] in self.templates:
            raise EmailServiceError(f"Template ID already exists: {template_data['id']}")
        
        # Validate template syntax
        if 'subject_template' in template_data:
            try:
                self.jinja_env.from_string(template_data['subject_template'])
            except TemplateError as e:
                raise EmailServiceError(f"Invalid subject template syntax: {e}")
        
        if 'html_template' in template_data and template_data['html_template']:
            try:
                self.jinja_env.from_string(template_data['html_template'])
            except TemplateError as e:
                raise EmailServiceError(f"Invalid HTML template syntax: {e}")
        
        if 'text_template' in template_data and template_data['text_template']:
            try:
                self.jinja_env.from_string(template_data['text_template'])
            except TemplateError as e:
                raise EmailServiceError(f"Invalid text template syntax: {e}")

    async def _validate_template_variables(
        self,
        template: EmailTemplate,
        variables: Dict[str, Any]
    ):
        """Validate template variables"""
        errors = []
        
        for var in template.variables:
            if var.required and var.name not in variables:
                errors.append(f"Missing required variable: {var.name}")
                continue
            
            if var.name in variables:
                value = variables[var.name]
                
                # Type validation
                if var.type == "string" and not isinstance(value, str):
                    errors.append(f"Variable '{var.name}' must be a string")
                elif var.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Variable '{var.name}' must be a number")
                elif var.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Variable '{var.name}' must be a boolean")
                elif var.type == "array" and not isinstance(value, list):
                    errors.append(f"Variable '{var.name}' must be an array")
                elif var.type == "object" and not isinstance(value, dict):
                    errors.append(f"Variable '{var.name}' must be an object")
        
        if errors:
            raise EmailServiceError(f"Template variable validation failed: {'; '.join(errors)}")

    async def _save_template_to_file(self, template: EmailTemplate):
        """Save template to JSON file"""
        template_file = self.custom_templates_dir / f"{template.id}.json"
        
        template_data = template.dict()
        template_data['created_at'] = template_data['created_at'].isoformat()
        template_data['updated_at'] = template_data['updated_at'].isoformat()
        
        # Convert TemplateVariable objects to dicts
        template_data['variables'] = [
            {
                "name": var.name,
                "type": var.type,
                "required": var.required,
                "default_value": var.default_value,
                "description": var.description,
                "validation_rules": var.validation_rules
            }
            for var in template.variables
        ]
        
        async with aiofiles.open(template_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(template_data, indent=2, default=str))

    async def _update_template_metrics(self, template_id: str, event_type: str):
        """Update template usage metrics"""
        analytics = self.template_analytics[template_id]
        
        if event_type == 'render':
            analytics["renders"] += 1
        elif event_type == 'send':
            analytics["sends"] += 1
        elif event_type == 'open':
            analytics["opens"] += 1
        elif event_type == 'click':
            analytics["clicks"] += 1
        
        analytics["last_used"] = datetime.now()
        
        # Update template metrics if it exists
        template = self.templates.get(template_id)
        if template:
            if event_type == 'send':
                template.metrics.sent_count += 1
            template.metrics.last_used = datetime.now()

    async def get_template_analytics(self, template_id: str) -> Dict[str, Any]:
        """Get template analytics and metrics"""
        template = await self.get_template(template_id)
        if not template:
            raise EmailServiceError(f"Template not found: {template_id}")
        
        analytics = self.template_analytics[template_id]
        
        return {
            "template_id": template_id,
            "name": template.name,
            "type": template.type,
            "category": template.category,
            "status": template.status,
            "metrics": {
                "sent_count": template.metrics.sent_count,
                "open_rate": template.metrics.open_rate,
                "click_rate": template.metrics.click_rate,
                "bounce_rate": template.metrics.bounce_rate,
                "unsubscribe_rate": template.metrics.unsubscribe_rate,
                "last_used": template.metrics.last_used.isoformat() if template.metrics.last_used else None
            },
            "analytics": {
                "renders": analytics["renders"],
                "sends": analytics["sends"],
                "opens": analytics["opens"],
                "clicks": analytics["clicks"],
                "last_used": analytics["last_used"].isoformat() if analytics["last_used"] else None
            },
            "versions": [
                {
                    "version": v.version,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "is_active": v.is_active
                }
                for v in template.versions
            ],
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics"""
        try:
            queue_size = self.notification_queue.qsize()
            
            return {
                "success": True,
                "queue_status": {
                    "total_queued": queue_size,
                    "is_processing": self.is_processing,
                    "batch_queues": len(self.batch_queue)
                },
                "processing_stats": self.processing_stats,
                "configuration": {
                    "max_batch_size": self.batch_config.max_batch_size,
                    "time_window_minutes": self.batch_config.time_window_minutes,
                    "smart_batching_enabled": self.batch_config.strategy == BatchingStrategy.SMART
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {
                "success": False,
                "error": "status_failed",
                "message": f"Failed to get queue status: {str(e)}"
            }

    async def track_delivery_status(
        self,
        tracking_id: str,
        status: str,
        provider: str,
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track email delivery status (compatibility method)"""
        try:
            # This is a compatibility method for the API
            # In a full implementation, this would integrate with the email service analytics
            logger.info(f"Tracking delivery status: {tracking_id} -> {status} via {provider}")
            
            return {
                "success": True,
                "tracking_id": tracking_id,
                "status": status,
                "provider": provider,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to track delivery status: {e}")
            return {
                "success": False,
                "error": str(e),
                "tracking_id": tracking_id
            }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "healthy": True,
            "service": "consolidated_email_template_manager",
            "templates_loaded": len(self.templates),
            "cache_size": len(self.template_cache),
            "rendered_cache_size": len(self.rendered_cache),
            "queue_size": self.notification_queue.qsize(),
            "processing_active": self.is_processing,
            "jinja_env_ready": self.jinja_env is not None,
            "timestamp": datetime.now().isoformat()
        }

    async def shutdown(self):
        """Shutdown template manager"""
        logger.info("Shutting down consolidated email template manager...")
        
        # Clear caches
        self.template_cache.clear()
        self.rendered_cache.clear()
        self.templates.clear()
        self.template_analytics.clear()
        
        # Clear queues
        while not self.notification_queue.empty():
            try:
                self.notification_queue.get_nowait()
            except:
                break
        
        self.batch_queue.clear()
        self.recipient_preferences.clear()
        
        logger.info("Consolidated email template manager shutdown completed")