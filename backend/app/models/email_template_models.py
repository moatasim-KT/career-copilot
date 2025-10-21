"""
Email template models for comprehensive email template management.
Provides data models for templates, messages, attachments, and delivery tracking.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid

from pydantic import BaseModel, Field, EmailStr, validator
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from ..core.database import Base


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


class DeliveryProvider(str, Enum):
    """Email delivery providers"""
    SMTP = "smtp"
    GMAIL = "gmail"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"


# Database Models

class EmailTemplateDB(Base):
    """Database model for email templates"""
    __tablename__ = "email_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)
    subject_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=False)
    text_template = Column(Text, nullable=True)
    variables = Column(JSON, default=list)
    default_values = Column(JSON, default=dict)
    css_inline = Column(Boolean, default=True)
    tracking_enabled = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    email_messages = relationship("EmailMessageDB", back_populates="template")
    delivery_records = relationship("EmailDeliveryRecordDB", back_populates="template")


class EmailMessageDB(Base):
    """Database model for email messages"""
    __tablename__ = "email_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String(50), unique=True, nullable=False, index=True)
    template_id = Column(String(100), ForeignKey("email_templates.template_id"), nullable=True)
    to_emails = Column(JSON, nullable=False)  # List of recipient emails
    cc_emails = Column(JSON, default=list)
    bcc_emails = Column(JSON, default=list)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=True)
    text_body = Column(Text, nullable=True)
    from_email = Column(String(200), nullable=True)
    from_name = Column(String(200), nullable=True)
    reply_to = Column(String(200), nullable=True)
    headers = Column(JSON, default=dict)
    priority = Column(String(20), default="normal")
    send_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    template = relationship("EmailTemplateDB", back_populates="email_messages")
    attachments = relationship("EmailAttachmentDB", back_populates="message")
    delivery_record = relationship("EmailDeliveryRecordDB", back_populates="message", uselist=False)


class EmailAttachmentDB(Base):
    """Database model for email attachments"""
    __tablename__ = "email_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("email_messages.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    content_type = Column(String(200), nullable=False)
    attachment_type = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=True)  # Path to stored file
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("EmailMessageDB", back_populates="attachments")


class EmailDeliveryRecordDB(Base):
    """Database model for email delivery tracking"""
    __tablename__ = "email_delivery_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String(50), unique=True, nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("email_messages.id"), nullable=False)
    template_id = Column(String(100), ForeignKey("email_templates.template_id"), nullable=True)
    provider_message_id = Column(String(200), nullable=True)
    to_email = Column(String(200), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", index=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    last_opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    email_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    message = relationship("EmailMessageDB", back_populates="delivery_record")
    template = relationship("EmailTemplateDB", back_populates="delivery_records")
    events = relationship("EmailEventDB", back_populates="delivery_record")


class EmailEventDB(Base):
    """Database model for email events"""
    __tablename__ = "email_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String(50), ForeignKey("email_delivery_records.tracking_id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    recipient = Column(String(200), nullable=False)
    provider = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    location_data = Column(JSON, nullable=True)
    link_url = Column(Text, nullable=True)
    bounce_reason = Column(Text, nullable=True)
    spam_reason = Column(Text, nullable=True)
    event_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    delivery_record = relationship("EmailDeliveryRecordDB", back_populates="events")


# Pydantic Models for API

class EmailAttachmentCreate(BaseModel):
    """Model for creating email attachments"""
    filename: str = Field(..., description="Attachment filename")
    content_type: str = Field(..., description="MIME content type")
    attachment_type: AttachmentType = Field(AttachmentType.DOCUMENT, description="Attachment type")
    description: Optional[str] = Field(None, description="Attachment description")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        return v.strip()


class EmailAttachment(EmailAttachmentCreate):
    """Complete email attachment model"""
    id: Optional[str] = Field(None, description="Attachment ID")
    content: bytes = Field(..., description="Attachment content")
    size: int = Field(..., description="Attachment size in bytes")
    content_hash: Optional[str] = Field(None, description="Content hash")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    @validator('size')
    def validate_size(cls, v):
        max_size = 25 * 1024 * 1024  # 25MB
        if v > max_size:
            raise ValueError(f"Attachment too large: {v} bytes (max: {max_size})")
        return v
    
    class Config:
        arbitrary_types_allowed = True


class EmailTemplateCreate(BaseModel):
    """Model for creating email templates"""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    template_type: TemplateType = Field(..., description="Template type")
    subject_template: str = Field(..., description="Subject line template")
    html_template: str = Field(..., description="HTML template content")
    text_template: Optional[str] = Field(None, description="Plain text template")
    variables: Optional[List[str]] = Field(None, description="Required template variables")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default variable values")
    css_inline: bool = Field(True, description="Whether to inline CSS")
    tracking_enabled: bool = Field(True, description="Enable email tracking")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    
    @validator('template_id')
    def validate_template_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Template ID cannot be empty")
        # Only allow alphanumeric, underscore, and hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Template ID can only contain letters, numbers, underscores, and hyphens")
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Template name cannot be empty")
        return v.strip()


class EmailTemplate(EmailTemplateCreate):
    """Complete email template model"""
    id: Optional[str] = Field(None, description="Database ID")
    version: str = Field("1.0", description="Template version")
    is_active: bool = Field(True, description="Whether template is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")


class EmailMessageCreate(BaseModel):
    """Model for creating email messages"""
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    html_body: Optional[str] = Field(None, description="HTML body content")
    text_body: Optional[str] = Field(None, description="Plain text body content")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    priority: EmailPriority = Field(EmailPriority.NORMAL, description="Email priority")
    template_id: Optional[str] = Field(None, description="Template used")
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")
    
    @validator('to')
    def validate_recipients(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one recipient is required")
        return v
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Subject cannot be empty")
        return v.strip()


class EmailMessage(EmailMessageCreate):
    """Complete email message model"""
    id: Optional[str] = Field(None, description="Message ID")
    tracking_id: str = Field(..., description="Tracking identifier")
    attachments: List[EmailAttachment] = Field(default_factory=list, description="Email attachments")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    sent_at: Optional[datetime] = Field(None, description="Send timestamp")


class EmailDeliveryRecordCreate(BaseModel):
    """Model for creating delivery records"""
    tracking_id: str = Field(..., description="Unique tracking identifier")
    to_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    template_id: Optional[str] = Field(None, description="Template used")
    provider: DeliveryProvider = Field(..., description="Email provider")


class EmailDeliveryRecord(EmailDeliveryRecordCreate):
    """Complete email delivery tracking record"""
    id: Optional[str] = Field(None, description="Record ID")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID")
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
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class EmailEventCreate(BaseModel):
    """Model for creating email events"""
    tracking_id: str = Field(..., description="Email tracking ID")
    event_type: str = Field(..., description="Event type")
    recipient: str = Field(..., description="Recipient email")
    provider: DeliveryProvider = Field(..., description="Delivery provider")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    location_data: Optional[Dict[str, str]] = Field(None, description="Geographic location")
    link_url: Optional[str] = Field(None, description="Clicked link URL")
    bounce_reason: Optional[str] = Field(None, description="Bounce reason")
    spam_reason: Optional[str] = Field(None, description="Spam report reason")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EmailEvent(EmailEventCreate):
    """Complete email event model"""
    id: str = Field(..., description="Event ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")


class TemplateRenderRequest(BaseModel):
    """Request model for template rendering"""
    template_id: str = Field(..., description="Template to render")
    variables: Dict[str, Any] = Field(..., description="Template variables")
    recipient: EmailStr = Field(..., description="Recipient email")
    tracking_id: Optional[str] = Field(None, description="Custom tracking ID")


class TemplateRenderResponse(BaseModel):
    """Response model for template rendering"""
    message: EmailMessage = Field(..., description="Rendered email message")
    tracking_id: str = Field(..., description="Tracking ID")
    variables_used: Dict[str, Any] = Field(..., description="Variables used in rendering")
    render_time: float = Field(..., description="Rendering time in seconds")


class DeliveryStatistics(BaseModel):
    """Email delivery statistics model"""
    total_sent: int = Field(0, description="Total emails sent")
    delivered: int = Field(0, description="Successfully delivered")
    opened: int = Field(0, description="Emails opened")
    clicked: int = Field(0, description="Emails clicked")
    bounced: int = Field(0, description="Bounced emails")
    failed: int = Field(0, description="Failed deliveries")
    delivery_rate: float = Field(0.0, description="Delivery rate percentage")
    open_rate: float = Field(0.0, description="Open rate percentage")
    click_rate: float = Field(0.0, description="Click rate percentage")
    bounce_rate: float = Field(0.0, description="Bounce rate percentage")
    failure_rate: float = Field(0.0, description="Failure rate percentage")
    period_start: Optional[datetime] = Field(None, description="Statistics period start")
    period_end: Optional[datetime] = Field(None, description="Statistics period end")


class TemplateListResponse(BaseModel):
    """Response model for template listing"""
    templates: List[EmailTemplate] = Field(..., description="List of templates")
    total_count: int = Field(..., description="Total number of templates")
    template_types: List[str] = Field(..., description="Available template types")


class AttachmentUploadRequest(BaseModel):
    """Request model for attachment upload"""
    filename: str = Field(..., description="Attachment filename")
    content_type: str = Field(..., description="MIME content type")
    attachment_type: AttachmentType = Field(AttachmentType.DOCUMENT, description="Attachment type")
    description: Optional[str] = Field(None, description="Attachment description")


class AttachmentUploadResponse(BaseModel):
    """Response model for attachment upload"""
    attachment_id: str = Field(..., description="Attachment ID")
    filename: str = Field(..., description="Attachment filename")
    size: int = Field(..., description="Attachment size")
    content_hash: str = Field(..., description="Content hash")
    upload_url: Optional[str] = Field(None, description="Upload URL if using external storage")


class EmailHealthStatus(BaseModel):
    """Email service health status"""
    healthy: bool = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    templates_loaded: int = Field(..., description="Number of templates loaded")
    delivery_records: int = Field(..., description="Number of delivery records")
    templates_dir: str = Field(..., description="Templates directory path")
    cache_enabled: bool = Field(..., description="Whether caching is enabled")
    inline_css_enabled: bool = Field(..., description="Whether CSS inlining is enabled")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    timestamp: datetime = Field(..., description="Status check timestamp")


# Template validation schemas

class TemplateValidationResult(BaseModel):
    """Template validation result"""
    valid: bool = Field(..., description="Whether template is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    variables_found: List[str] = Field(default_factory=list, description="Variables found in template")
    missing_variables: List[str] = Field(default_factory=list, description="Missing required variables")


class BulkEmailRequest(BaseModel):
    """Request model for bulk email sending"""
    template_id: str = Field(..., description="Template to use")
    recipients: List[Dict[str, Any]] = Field(..., description="Recipients with their variables")
    common_variables: Optional[Dict[str, Any]] = Field(None, description="Variables common to all recipients")
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")
    batch_size: int = Field(100, description="Batch size for sending")
    
    @validator('recipients')
    def validate_recipients(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one recipient is required")
        
        for i, recipient in enumerate(v):
            if 'email' not in recipient:
                raise ValueError(f"Recipient {i} missing email field")
        
        return v


class BulkEmailResponse(BaseModel):
    """Response model for bulk email sending"""
    job_id: str = Field(..., description="Bulk email job ID")
    total_recipients: int = Field(..., description="Total number of recipients")
    batches_created: int = Field(..., description="Number of batches created")
    estimated_completion: datetime = Field(..., description="Estimated completion time")
    tracking_ids: List[str] = Field(..., description="List of tracking IDs")


class BulkEmailStatus(BaseModel):
    """Bulk email job status"""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    total_recipients: int = Field(..., description="Total recipients")
    processed: int = Field(..., description="Processed recipients")
    successful: int = Field(..., description="Successful sends")
    failed: int = Field(..., description="Failed sends")
    progress_percentage: float = Field(..., description="Progress percentage")
    started_at: datetime = Field(..., description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")