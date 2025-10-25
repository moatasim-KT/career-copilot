"""
Enhanced Email Template Service with Jinja2, HTML support, and attachment handling.
Provides comprehensive email template management with delivery tracking.
"""

import asyncio
import os
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, BinaryIO
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json
import mimetypes

from jinja2 import Environment, FileSystemLoader, Template, TemplateError, select_autoescape
from pydantic import BaseModel, Field, EmailStr, validator
import aiofiles
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from .email_analytics_service import EnhancedEmailAnalyticsService, EmailEventType, DeliveryProvider

logger = get_logger(__name__)


class TemplateType(str, Enum):
    """Email template types"""
    ANALYSIS_REPORT = "analysis_report"
    RISK_ALERT = "risk_alert"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    CONTRACT_ANALYSIS_DETAILED = "contract_analysis_detailed"
    INTEGRATION_TEST = "integration_test"
    CUSTOM = "custom"


class AttachmentType(str, Enum):
    """Email attachment types"""
    PDF_REPORT = "pdf_report"
    DOCX_REDLINE = "docx_redline"
    JSON_DATA = "json_data"
    CSV_EXPORT = "csv_export"
    IMAGE = "image"
    DOCUMENT = "document"


class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailAttachment(BaseModel):
    """Email attachment model"""
    filename: str = Field(..., description="Attachment filename")
    content: bytes = Field(..., description="Attachment content")
    content_type: str = Field(..., description="MIME content type")
    attachment_type: AttachmentType = Field(AttachmentType.DOCUMENT, description="Attachment type")
    size: int = Field(..., description="Attachment size in bytes")
    description: Optional[str] = Field(None, description="Attachment description")
    
    @validator('size')
    def validate_size(cls, v):
        # 25MB limit for most email providers
        max_size = 25 * 1024 * 1024
        if v > max_size:
            raise ValueError(f"Attachment too large: {v} bytes (max: {max_size})")
        return v
    
    class Config:
        arbitrary_types_allowed = True


class EmailTemplate(BaseModel):
    """Email template model"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    template_type: TemplateType = Field(..., description="Template type")
    subject_template: str = Field(..., description="Subject line template")
    html_template: str = Field(..., description="HTML template content")
    text_template: Optional[str] = Field(None, description="Plain text template")
    variables: List[str] = Field(default_factory=list, description="Required template variables")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default variable values")
    css_inline: bool = Field(True, description="Whether to inline CSS")
    tracking_enabled: bool = Field(True, description="Enable email tracking")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    version: str = Field("1.0", description="Template version")
    tags: List[str] = Field(default_factory=list, description="Template tags")


class EmailMessage(BaseModel):
    """Complete email message model"""
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    cc: List[EmailStr] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailStr] = Field(default_factory=list, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    html_body: Optional[str] = Field(None, description="HTML body content")
    text_body: Optional[str] = Field(None, description="Plain text body content")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    attachments: List[EmailAttachment] = Field(default_factory=list, description="Email attachments")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    priority: EmailPriority = Field(EmailPriority.NORMAL, description="Email priority")
    template_id: Optional[str] = Field(None, description="Template used")
    tracking_id: Optional[str] = Field(None, description="Tracking identifier")
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")


class DeliveryStatus(str, Enum):
    """Email delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    SPAM = "spam"
    UNSUBSCRIBED = "unsubscribed"


class EmailDeliveryRecord(BaseModel):
    """Email delivery tracking record"""
    tracking_id: str = Field(..., description="Unique tracking identifier")
    message_id: Optional[str] = Field(None, description="Provider message ID")
    to_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    template_id: Optional[str] = Field(None, description="Template used")
    provider: DeliveryProvider = Field(..., description="Email provider")
    status: DeliveryStatus = Field(DeliveryStatus.PENDING, description="Current status")
    sent_at: Optional[datetime] = Field(None, description="Send timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    opened_at: Optional[datetime] = Field(None, description="First open timestamp")
    last_opened_at: Optional[datetime] = Field(None, description="Last open timestamp")
    clicked_at: Optional[datetime] = Field(None, description="First click timestamp")
    bounced_at: Optional[datetime] = Field(None, description="Bounce timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    open_count: int = Field(0, description="Number of opens")
    click_count: int = Field(0, description="Number of clicks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation time")


@dataclass
class TemplateRenderContext:
    """Template rendering context"""
    variables: Dict[str, Any]
    template: EmailTemplate
    recipient: str
    tracking_id: str
    render_timestamp: datetime


class EnhancedEmailTemplateService:
    """Enhanced email template service with Jinja2 and comprehensive features"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.settings = get_settings()
        self.templates_dir = Path(templates_dir or "backend/app/templates/email")
        self.custom_templates_dir = Path("backend/app/templates/email/custom")
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader([str(self.templates_dir), str(self.custom_templates_dir)]),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters and functions
        self._setup_jinja_filters()
        
        # Template cache
        self.template_cache: Dict[str, EmailTemplate] = {}
        self.rendered_cache: Dict[str, str] = {}
        
        # Delivery tracking
        self.delivery_records: Dict[str, EmailDeliveryRecord] = {}
        self.analytics_service = EnhancedEmailAnalyticsService()
        
        # Configuration
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour
        self.max_attachment_size = 25 * 1024 * 1024  # 25MB
        self.inline_css_enabled = True
        
        logger.info(f"Enhanced Email Template Service initialized with templates dir: {self.templates_dir}")
    
    async def initialize(self):
        """Initialize the template service"""
        logger.info("Initializing Enhanced Email Template Service...")
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load built-in templates
        await self._load_builtin_templates()
        
        # Initialize analytics service
        await self.analytics_service.initialize()
        
        # Start background tasks
        asyncio.create_task(self._cleanup_old_records())
        
        logger.info("Enhanced Email Template Service initialized successfully")
    
    async def create_template(
        self,
        template_id: str,
        name: str,
        template_type: TemplateType,
        subject_template: str,
        html_template: str,
        text_template: Optional[str] = None,
        variables: Optional[List[str]] = None,
        default_values: Optional[Dict[str, Any]] = None
    ) -> EmailTemplate:
        """Create a new email template"""
        # Validate template syntax
        try:
            self.jinja_env.from_string(subject_template)
            self.jinja_env.from_string(html_template)
            if text_template:
                self.jinja_env.from_string(text_template)
        except TemplateError as e:
            raise EmailServiceError(
                f"Invalid template syntax: {e}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH
            )
        
        # Extract variables from templates
        extracted_vars = self._extract_template_variables(subject_template, html_template, text_template)
        
        template = EmailTemplate(
            template_id=template_id,
            name=name,
            template_type=template_type,
            subject_template=subject_template,
            html_template=html_template,
            text_template=text_template,
            variables=variables or extracted_vars,
            default_values=default_values or {}
        )
        
        # Save template to file
        await self._save_template_to_file(template)
        
        # Cache template
        self.template_cache[template_id] = template
        
        logger.info(f"Created email template: {template_id}")
        return template
    
    async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID"""
        # Check cache first
        if template_id in self.template_cache:
            return self.template_cache[template_id]
        
        # Load from file
        template = await self._load_template_from_file(template_id)
        if template:
            self.template_cache[template_id] = template
        
        return template
    
    async def list_templates(self, template_type: Optional[TemplateType] = None) -> List[EmailTemplate]:
        """List all available templates"""
        templates = []
        
        # Load all templates from directory
        for template_file in self.templates_dir.glob("*.json"):
            template_id = template_file.stem
            template = await self.get_template(template_id)
            if template and (not template_type or template.template_type == template_type):
                templates.append(template)
        
        # Load custom templates
        for template_file in self.custom_templates_dir.glob("*.json"):
            template_id = f"custom_{template_file.stem}"
            template = await self.get_template(template_id)
            if template and (not template_type or template.template_type == template_type):
                templates.append(template)
        
        return templates
    
    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        recipient: str,
        tracking_id: Optional[str] = None
    ) -> EmailMessage:
        """Render email template with variables"""
        template = await self.get_template(template_id)
        if not template:
            raise EmailServiceError(
                f"Template not found: {template_id}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH
            )
        
        # Generate tracking ID if not provided
        if not tracking_id:
            tracking_id = self._generate_tracking_id(template_id, recipient)
        
        # Merge with default values
        render_vars = {**template.default_values, **variables}
        
        # Add system variables
        render_vars.update({
            'recipient_email': recipient,
            'tracking_id': tracking_id,
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_datetime': datetime.now().isoformat(),
            'template_id': template_id,
            'template_name': template.name
        })
        
        # Create render context
        context = TemplateRenderContext(
            variables=render_vars,
            template=template,
            recipient=recipient,
            tracking_id=tracking_id,
            render_timestamp=datetime.now()
        )
        
        try:
            # Render subject
            subject_tmpl = self.jinja_env.from_string(template.subject_template)
            subject = subject_tmpl.render(**render_vars)
            
            # Render HTML body
            html_tmpl = self.jinja_env.from_string(template.html_template)
            html_body = html_tmpl.render(**render_vars)
            
            # Add tracking pixel if enabled
            if template.tracking_enabled:
                html_body = self._add_tracking_pixel(html_body, tracking_id)
            
            # Inline CSS if enabled
            if template.css_inline and self.inline_css_enabled:
                html_body = await self._inline_css(html_body)
            
            # Render text body if available
            text_body = None
            if template.text_template:
                text_tmpl = self.jinja_env.from_string(template.text_template)
                text_body = text_tmpl.render(**render_vars)
            
            # Create email message
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                template_id=template_id,
                tracking_id=tracking_id
            )
            
            logger.debug(f"Rendered template {template_id} for {recipient}")
            return message
            
        except TemplateError as e:
            raise EmailServiceError(
                f"Template rendering failed: {e}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH
            )
    
    async def add_attachment_from_file(
        self,
        message: EmailMessage,
        file_path: str,
        attachment_type: AttachmentType = AttachmentType.DOCUMENT,
        filename: Optional[str] = None,
        description: Optional[str] = None
    ) -> EmailMessage:
        """Add attachment from file path"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise EmailServiceError(
                f"Attachment file not found: {file_path}",
                category=ErrorCategory.FILE_PROCESSING,
                severity=ErrorSeverity.HIGH
            )
        
        # Read file content
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create attachment
        attachment = EmailAttachment(
            filename=filename or file_path.name,
            content=content,
            content_type=content_type,
            attachment_type=attachment_type,
            size=len(content),
            description=description
        )
        
        message.attachments.append(attachment)
        logger.debug(f"Added attachment: {attachment.filename} ({attachment.size} bytes)")
        
        return message
    
    async def add_attachment_from_data(
        self,
        message: EmailMessage,
        filename: str,
        content: bytes,
        content_type: str,
        attachment_type: AttachmentType = AttachmentType.DOCUMENT,
        description: Optional[str] = None
    ) -> EmailMessage:
        """Add attachment from raw data"""
        attachment = EmailAttachment(
            filename=filename,
            content=content,
            content_type=content_type,
            attachment_type=attachment_type,
            size=len(content),
            description=description
        )
        
        message.attachments.append(attachment)
        logger.debug(f"Added data attachment: {filename} ({len(content)} bytes)")
        
        return message
    
    async def create_pdf_report_attachment(
        self,
        report_data: Dict[str, Any],
        filename: str = "contract_analysis_report.pdf"
    ) -> EmailAttachment:
        """Create PDF report attachment from analysis data"""
        # This would integrate with a PDF generation service
        # For now, we'll create a placeholder
        pdf_content = await self._generate_pdf_report(report_data)
        
        return EmailAttachment(
            filename=filename,
            content=pdf_content,
            content_type="application/pdf",
            attachment_type=AttachmentType.PDF_REPORT,
            size=len(pdf_content),
            description="Contract Analysis Report"
        )
    
    async def create_docx_redline_attachment(
        self,
        original_content: str,
        redlined_content: str,
        filename: str = "contract_redlines.docx"
    ) -> EmailAttachment:
        """Create DOCX redline attachment"""
        # This would integrate with a DOCX generation service
        docx_content = await self._generate_docx_redline(original_content, redlined_content)
        
        return EmailAttachment(
            filename=filename,
            content=docx_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            attachment_type=AttachmentType.DOCX_REDLINE,
            size=len(docx_content),
            description="Contract Redlines"
        )
    
    async def track_delivery_status(
        self,
        tracking_id: str,
        status: DeliveryStatus,
        provider: DeliveryProvider,
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailDeliveryRecord:
        """Track email delivery status"""
        # Get or create delivery record
        if tracking_id not in self.delivery_records:
            # This should normally come from the original send request
            logger.warning(f"Creating delivery record for unknown tracking ID: {tracking_id}")
            record = EmailDeliveryRecord(
                tracking_id=tracking_id,
                to_email="unknown",
                subject="Unknown",
                provider=provider,
                status=status
            )
        else:
            record = self.delivery_records[tracking_id]
        
        # Update status and timestamps
        record.status = status
        if message_id:
            record.message_id = message_id
        if error_message:
            record.error_message = error_message
        if metadata:
            record.metadata.update(metadata)
        
        current_time = datetime.now()
        
        if status == DeliveryStatus.SENT:
            record.sent_at = current_time
        elif status == DeliveryStatus.DELIVERED:
            record.delivered_at = current_time
        elif status == DeliveryStatus.OPENED:
            if not record.opened_at:
                record.opened_at = current_time
            record.last_opened_at = current_time
            record.open_count += 1
        elif status == DeliveryStatus.CLICKED:
            if not record.clicked_at:
                record.clicked_at = current_time
            record.click_count += 1
        elif status == DeliveryStatus.BOUNCED:
            record.bounced_at = current_time
        
        # Store updated record
        self.delivery_records[tracking_id] = record
        
        # Record analytics event
        event_type_mapping = {
            DeliveryStatus.SENT: EmailEventType.SEND,
            DeliveryStatus.DELIVERED: EmailEventType.DELIVERY,
            DeliveryStatus.OPENED: EmailEventType.OPEN,
            DeliveryStatus.CLICKED: EmailEventType.CLICK,
            DeliveryStatus.BOUNCED: EmailEventType.BOUNCE,
            DeliveryStatus.SPAM: EmailEventType.SPAM_REPORT,
            DeliveryStatus.UNSUBSCRIBED: EmailEventType.UNSUBSCRIBE
        }
        
        if status in event_type_mapping:
            await self.analytics_service.record_email_event(
                tracking_id=tracking_id,
                event_type=event_type_mapping[status],
                recipient=record.to_email,
                provider=provider,
                metadata=metadata or {}
            )
        
        logger.debug(f"Updated delivery status for {tracking_id}: {status}")
        return record
    
    async def get_delivery_status(self, tracking_id: str) -> Optional[EmailDeliveryRecord]:
        """Get delivery status for tracking ID"""
        return self.delivery_records.get(tracking_id)
    
    async def get_delivery_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        # Filter records by criteria
        filtered_records = []
        for record in self.delivery_records.values():
            if start_date and record.created_at < start_date:
                continue
            if end_date and record.created_at > end_date:
                continue
            if template_id and record.template_id != template_id:
                continue
            filtered_records.append(record)
        
        # Calculate statistics
        total_sent = len(filtered_records)
        delivered = len([r for r in filtered_records if r.status in [DeliveryStatus.DELIVERED, DeliveryStatus.OPENED, DeliveryStatus.CLICKED]])
        opened = len([r for r in filtered_records if r.open_count > 0])
        clicked = len([r for r in filtered_records if r.click_count > 0])
        bounced = len([r for r in filtered_records if r.status == DeliveryStatus.BOUNCED])
        failed = len([r for r in filtered_records if r.status == DeliveryStatus.FAILED])
        
        return {
            "total_sent": total_sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "failed": failed,
            "delivery_rate": (delivered / total_sent) if total_sent > 0 else 0,
            "open_rate": (opened / delivered) if delivered > 0 else 0,
            "click_rate": (clicked / delivered) if delivered > 0 else 0,
            "bounce_rate": (bounced / total_sent) if total_sent > 0 else 0,
            "failure_rate": (failed / total_sent) if total_sent > 0 else 0
        }
    
    def _setup_jinja_filters(self):
        """Setup custom Jinja2 filters and functions"""
        
        def format_currency(value: float, currency: str = "USD") -> str:
            """Format currency value"""
            return f"${value:,.2f}" if currency == "USD" else f"{value:,.2f} {currency}"
        
        def format_date(value: datetime, format_str: str = "%Y-%m-%d") -> str:
            """Format datetime value"""
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            return value.strftime(format_str)
        
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
        
        def truncate_text(text: str, length: int = 100) -> str:
            """Truncate text to specified length"""
            return text[:length] + "..." if len(text) > length else text
        
        def format_filesize(value: Union[int, float, str]) -> str:
            """Format file size in bytes to human readable format"""
            if isinstance(value, str):
                return value  # Already formatted
            
            try:
                bytes_val = float(value)
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.1f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.1f} PB"
            except (ValueError, TypeError):
                return str(value)
        
        # Register filters
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['date'] = format_date
        self.jinja_env.filters['risk_level'] = format_risk_level
        self.jinja_env.filters['risk_color'] = risk_color
        self.jinja_env.filters['truncate'] = truncate_text
        self.jinja_env.filters['filesizeformat'] = format_filesize
        
        # Add global functions
        self.jinja_env.globals['now'] = datetime.now
        self.jinja_env.globals['today'] = datetime.now().date
    
    def _extract_template_variables(self, *templates: str) -> List[str]:
        """Extract variables from template strings"""
        variables = set()
        
        for template_str in templates:
            if not template_str:
                continue
            
            try:
                # Parse template to extract variables
                from jinja2 import meta
                ast = self.jinja_env.parse(template_str)
                variables.update(meta.find_undeclared_variables(ast))
            except Exception as e:
                logger.warning(f"Could not extract variables from template: {e}")
        
        # Remove system variables
        system_vars = {
            'recipient_email', 'tracking_id', 'current_date', 
            'current_datetime', 'template_id', 'template_name', 'now', 'today'
        }
        variables -= system_vars
        
        return sorted(list(variables))
    
    async def _load_builtin_templates(self):
        """Load built-in email templates"""
        builtin_templates = {
            TemplateType.ANALYSIS_REPORT: {
                "name": "Contract Analysis Report",
                "subject": "Contract Analysis Complete: {{ contract_name }}",
                "html_file": "analysis_report.html"
            },
            TemplateType.RISK_ALERT: {
                "name": "Risk Alert Notification",
                "subject": "⚠️ High Risk Contract Detected: {{ contract_name }}",
                "html_file": "risk_alert.html"
            },
            TemplateType.NOTIFICATION: {
                "name": "General Notification",
                "subject": "{{ notification_title }}",
                "html_file": "notification.html"
            },
            TemplateType.WELCOME: {
                "name": "Welcome Email",
                "subject": "Welcome to Career Copilot",
                "html_file": "welcome.html"
            }
        }
        
        for template_type, config in builtin_templates.items():
            template_id = template_type.value
            
            # Check if template file exists
            html_file = self.templates_dir / config["html_file"]
            if html_file.exists():
                async with aiofiles.open(html_file, 'r', encoding='utf-8') as f:
                    html_content = await f.read()
                
                # Create template object
                template = EmailTemplate(
                    template_id=template_id,
                    name=config["name"],
                    template_type=template_type,
                    subject_template=config["subject"],
                    html_template=html_content,
                    variables=self._extract_template_variables(config["subject"], html_content)
                )
                
                self.template_cache[template_id] = template
                logger.debug(f"Loaded built-in template: {template_id}")
    
    async def _save_template_to_file(self, template: EmailTemplate):
        """Save template to JSON file"""
        template_file = self.custom_templates_dir / f"{template.template_id}.json"
        
        template_data = template.dict()
        template_data['created_at'] = template_data['created_at'].isoformat()
        template_data['updated_at'] = template_data['updated_at'].isoformat()
        
        async with aiofiles.open(template_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(template_data, indent=2))
    
    async def _load_template_from_file(self, template_id: str) -> Optional[EmailTemplate]:
        """Load template from JSON file"""
        # Try custom templates first
        template_file = self.custom_templates_dir / f"{template_id}.json"
        if not template_file.exists():
            # Try removing custom_ prefix
            if template_id.startswith("custom_"):
                template_file = self.custom_templates_dir / f"{template_id[7:]}.json"
        
        if template_file.exists():
            try:
                async with aiofiles.open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.loads(await f.read())
                
                # Convert datetime strings back to datetime objects
                template_data['created_at'] = datetime.fromisoformat(template_data['created_at'])
                template_data['updated_at'] = datetime.fromisoformat(template_data['updated_at'])
                
                return EmailTemplate(**template_data)
            except Exception as e:
                logger.error(f"Failed to load template {template_id}: {e}")
        
        return None
    
    def _add_tracking_pixel(self, html_content: str, tracking_id: str) -> str:
        """Add tracking pixel to HTML content"""
        tracking_url = f"https://track.contractanalyzer.com/email/open/{tracking_id}"
        tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="">'
        
        # Insert before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
        else:
            html_content += tracking_pixel
        
        return html_content
    
    async def _inline_css(self, html_content: str) -> str:
        """Inline CSS styles for better email client compatibility"""
        # This is a simplified implementation
        # In production, you might want to use a library like premailer
        return html_content
    
    async def _generate_pdf_report(self, report_data: Dict[str, Any]) -> bytes:
        """Generate PDF report from data"""
        # Placeholder implementation
        # In production, this would use a PDF generation library
        
        # Convert datetime objects to strings for JSON serialization
        serializable_data = {}
        for key, value in report_data.items():
            if isinstance(value, datetime):
                serializable_data[key] = value.isoformat()
            else:
                serializable_data[key] = value
        
        pdf_content = f"PDF Report: {json.dumps(serializable_data, indent=2, default=str)}"
        return pdf_content.encode('utf-8')
    
    async def _generate_docx_redline(self, original: str, redlined: str) -> bytes:
        """Generate DOCX redline document"""
        # Placeholder implementation
        # In production, this would use python-docx or similar
        docx_content = f"DOCX Redline:\nOriginal: {original}\nRedlined: {redlined}"
        return docx_content.encode('utf-8')
    
    def _generate_tracking_id(self, template_id: str, recipient: str) -> str:
        """Generate unique tracking ID"""
        import hashlib
        data = f"{template_id}_{recipient}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def _cleanup_old_records(self):
        """Background task to cleanup old delivery records"""
        while True:
            try:
                cutoff_date = datetime.now() - timedelta(days=90)  # Keep 90 days
                
                old_tracking_ids = [
                    tracking_id for tracking_id, record in self.delivery_records.items()
                    if record.created_at < cutoff_date
                ]
                
                for tracking_id in old_tracking_ids:
                    del self.delivery_records[tracking_id]
                
                if old_tracking_ids:
                    logger.info(f"Cleaned up {len(old_tracking_ids)} old delivery records")
                
                await asyncio.sleep(86400)  # Run daily
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            template_count = len(self.template_cache)
            delivery_record_count = len(self.delivery_records)
            
            return {
                "healthy": True,
                "service": "enhanced_email_template",
                "templates_loaded": template_count,
                "delivery_records": delivery_record_count,
                "templates_dir": str(self.templates_dir),
                "custom_templates_dir": str(self.custom_templates_dir),
                "cache_enabled": self.cache_enabled,
                "inline_css_enabled": self.inline_css_enabled,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "enhanced_email_template",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def shutdown(self):
        """Shutdown template service"""
        logger.info("Shutting down Enhanced Email Template Service...")
        
        # Clear caches
        self.template_cache.clear()
        self.rendered_cache.clear()
        
        # Shutdown analytics service
        await self.analytics_service.shutdown()
        
        logger.info("Enhanced Email Template Service shutdown completed")


# Backward compatibility alias
EmailTemplateService = EnhancedEmailTemplateService