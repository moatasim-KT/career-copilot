"""
Clean, minimal Email Template Manager.

This file replaces a previously corrupted module with a compact, import-safe
implementation that preserves the public API used by routes and tests. It uses
in-memory storage and simple string formatting for rendering. Extend as needed.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from ..core.exceptions import EmailServiceError
from ..core.logging import get_logger
from .email_service import EmailProvider, EmailStatus

logger = get_logger(__name__)


class TemplateType(str, Enum):
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
	HTML = "html"
	TEXT = "text"
	MIXED = "mixed"


class NotificationPriority(str, Enum):
	CRITICAL = "critical"
	HIGH = "high"
	NORMAL = "normal"
	LOW = "low"


class EmailTemplate(BaseModel):
	template_id: str
	name: str
	template_type: TemplateType
	subject_template: str
	html_template: Optional[str] = None
	text_template: Optional[str] = None
	variables: List[str] = Field(default_factory=list)
	default_values: Dict[str, Any] = Field(default_factory=dict)
	created_at: datetime = Field(default_factory=datetime.now)
	updated_at: datetime = Field(default_factory=datetime.now)
	version: str = Field(default="1.0")


class EmailTemplateCreate(BaseModel):
	template_id: str
	name: str
	template_type: TemplateType
	subject_template: str
	html_template: Optional[str] = None
	text_template: Optional[str] = None
	variables: List[str] = Field(default_factory=list)
	default_values: Dict[str, Any] = Field(default_factory=dict)


class Attachment(BaseModel):
	filename: str
	size: int
	content_type: str
	attachment_type: str = "document"
	description: Optional[str] = None


class EmailMessage(BaseModel):
	to: List[EmailStr] = Field(default_factory=list)
	subject: str
	html_body: Optional[str] = None
	text_body: Optional[str] = None
	tracking_id: Optional[str] = None
	attachments: List[Attachment] = Field(default_factory=list)


class EmailDeliveryRecord(BaseModel):
	tracking_id: str
	status: EmailStatus
	provider: EmailProvider
	message_id: Optional[str] = None
	error_message: Optional[str] = None
	metadata: Dict[str, Any] = Field(default_factory=dict)
	created_at: datetime = Field(default_factory=datetime.now)


class DeliveryStatistics(BaseModel):
	total_sent: int = 0
	delivered: int = 0
	opened: int = 0
	clicked: int = 0
	bounced: int = 0
	failed: int = 0
	period_start: Optional[datetime] = None
	period_end: Optional[datetime] = None


class TemplateRenderRequest(BaseModel):
	template_id: str
	variables: Dict[str, Any]
	recipient: EmailStr
	tracking_id: Optional[str] = None


class TemplateRenderResponse(BaseModel):
	message: EmailMessage
	tracking_id: Optional[str]
	variables_used: Dict[str, Any]
	render_time: float


class TemplateListResponse(BaseModel):
	templates: List[EmailTemplate]
	total_count: int
	template_types: List[str]


class AttachmentUploadResponse(BaseModel):
	attachment_id: str
	filename: str
	size: int
	content_hash: str


class EmailHealthStatus(BaseModel):
	status: str
	templates_loaded: int
	queue_size: int
	last_processed: Optional[datetime] = None


class TemplateValidationResult(BaseModel):
	valid: bool
	errors: List[str] = Field(default_factory=list)
	variables_found: List[str] = Field(default_factory=list)
	missing_variables: List[str] = Field(default_factory=list)


class BulkEmailRequest(BaseModel):
	template_id: str
	recipients: List[Dict[str, Any]]
	common_variables: Optional[Dict[str, Any]] = None
	batch_size: int = 100


class BulkEmailResponse(BaseModel):
	job_id: str
	total_recipients: int
	batches_created: int
	estimated_completion: datetime
	tracking_ids: List[str]


class BulkEmailStatus(BaseModel):
	job_id: str
	status: str
	total_recipients: int
	processed: int
	successful: int
	failed: int
	progress_percentage: float
	started_at: datetime


class EmailTemplateManager:
	"""Minimal, import-safe email template manager with in-memory storage."""

	def __init__(self):
		self.templates_dir = Path("backend/app/templates/email")
		self.templates: Dict[str, EmailTemplate] = {}
		self.delivery_records: Dict[str, EmailDeliveryRecord] = {}
		self.notification_queue: List[Dict[str, Any]] = []
		self.max_attachment_size: int = 25 * 1024 * 1024  # 25MB
		self._last_processed: Optional[datetime] = None

	async def initialize(self) -> None:
		self.templates_dir.mkdir(parents=True, exist_ok=True)
		logger.info("EmailTemplateManager initialized")

	async def create_template(
		self,
		template_id: str,
		name: str,
		template_type: TemplateType,
		subject_template: str,
		html_template: Optional[str] = None,
		text_template: Optional[str] = None,
		variables: Optional[List[str]] = None,
		default_values: Optional[Dict[str, Any]] = None,
	) -> EmailTemplate:
		if template_id in self.templates:
			raise EmailServiceError(f"Template already exists: {template_id}")
		tpl = EmailTemplate(
			template_id=template_id,
			name=name,
			template_type=template_type,
			subject_template=subject_template,
			html_template=html_template,
			text_template=text_template,
			variables=variables or [],
			default_values=default_values or {},
		)
		self.templates[template_id] = tpl
		return tpl

	async def list_templates(self, template_type: Optional[TemplateType] = None) -> List[EmailTemplate]:
		values = list(self.templates.values())
		if template_type is not None:
			values = [t for t in values if t.template_type == template_type]
		return values

	async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
		return self.templates.get(template_id)

	def _format(self, template: Optional[str], variables: Dict[str, Any]) -> Optional[str]:
		if template is None:
			return None
		try:
			return template.format(**variables)
		except KeyError as e:
			missing = str(e).strip("'")
			raise EmailServiceError(f"Missing template variable: {missing}")

	async def render_template(
		self, *, template_id: str, variables: Dict[str, Any], recipient: EmailStr, tracking_id: Optional[str] = None
	) -> EmailMessage:
		tpl = await self.get_template(template_id)
		if not tpl:
			raise EmailServiceError(f"Template not found: {template_id}")
		merged: Dict[str, Any] = {**tpl.default_values, **variables}
		subject = self._format(tpl.subject_template, merged) or ""
		html_body = self._format(tpl.html_template, merged)
		text_body = self._format(tpl.text_template, merged)
		if not html_body and not text_body:
			text_body = ""
		return EmailMessage(to=[recipient], subject=subject, html_body=html_body, text_body=text_body, tracking_id=tracking_id)

	async def add_attachment_from_file(
		self,
		*,
		message: EmailMessage,
		file_path: str,
		attachment_type: str = "document",
		filename: Optional[str] = None,
		description: Optional[str] = None,
	) -> EmailMessage:
		p = Path(file_path)
		if not p.exists() or not p.is_file():
			raise EmailServiceError(f"Attachment file not found: {file_path}")
		data = p.read_bytes()
		if len(data) > self.max_attachment_size:
			raise EmailServiceError("Attachment too large")
		import mimetypes

		content_type, _ = mimetypes.guess_type(p.name)
		content_type = content_type or "application/octet-stream"
		att = Attachment(
			filename=filename or p.name,
			size=len(data),
			content_type=content_type,
			attachment_type=attachment_type,
			description=description,
		)
		message.attachments.append(att)
		return message

	async def create_pdf_report_attachment(self, *, report_data: Dict[str, Any], filename: str = "report.pdf") -> Attachment:
		content = ("PDF REPORT\n" + str(report_data)).encode("utf-8")
		return Attachment(filename=filename, size=len(content), content_type="application/pdf", attachment_type="report")

	async def create_docx_redline_attachment(self, *, original_content: str, redlined_content: str, filename: str = "redlines.docx") -> Attachment:
		content = (f"ORIGINAL\n{original_content}\nREDLINED\n{redlined_content}").encode("utf-8")
		return Attachment(
			filename=filename,
			size=len(content),
			content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			attachment_type="document",
		)

	async def track_delivery_status(
		self,
		*,
		tracking_id: str,
		status: EmailStatus,
		provider: EmailProvider,
		message_id: Optional[str] = None,
		error_message: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
	) -> EmailDeliveryRecord:
		record = EmailDeliveryRecord(
			tracking_id=tracking_id,
			status=status,
			provider=provider,
			message_id=message_id,
			error_message=error_message,
			metadata=metadata or {},
		)
		self.delivery_records[tracking_id] = record
		return record

	async def get_delivery_status(self, tracking_id: str) -> Optional[EmailDeliveryRecord]:
		return self.delivery_records.get(tracking_id)

	async def get_delivery_statistics(
		self, *, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, template_id: Optional[str] = None
	) -> Dict[str, int]:
		sent = delivered = opened = clicked = bounced = failed = 0
		for rec in self.delivery_records.values():
			ts = rec.created_at
			if start_date and ts < start_date:
				continue
			if end_date and ts > end_date:
				continue
			sent += 1
			if rec.status in {EmailStatus.DELIVERED, EmailStatus.SENT}:
				delivered += 1
			if rec.status == EmailStatus.OPENED:
				opened += 1
			if rec.status == EmailStatus.CLICKED:
				clicked += 1
			if rec.status == EmailStatus.BOUNCED:
				bounced += 1
			if rec.status == EmailStatus.FAILED:
				failed += 1
		return {
			"total_sent": sent,
			"delivered": delivered,
			"opened": opened,
			"clicked": clicked,
			"bounced": bounced,
			"failed": failed,
		}

	async def get_health_status(self) -> EmailHealthStatus:
		return EmailHealthStatus(
			status="ok",
			templates_loaded=len(self.templates),
			queue_size=len(self.notification_queue),
			last_processed=self._last_processed,
		)

	async def queue_notification(self, notification: Dict[str, Any]) -> None:
		self.notification_queue.append(notification)

	async def _process_single_notification(self, notification: Dict[str, Any]) -> None:
		await asyncio.sleep(0)

	async def _process_notification_queue(self) -> None:
		now = datetime.now()
		remaining: List[Dict[str, Any]] = []
		for item in self.notification_queue:
			scheduled: Optional[datetime] = item.get("scheduled_time")
			if scheduled and scheduled > now:
				remaining.append(item)
				continue
			await self._process_single_notification(item)
			self._last_processed = datetime.now()
		self.notification_queue = remaining

	async def schedule_morning_briefing(self, *, user_id: str, email: str, briefing_data: Dict[str, Any], scheduled_time: datetime) -> None:
		await self.queue_notification(
			{
				"type": "morning_briefing",
				"user_id": user_id,
				"email": email,
				"content": briefing_data,
				"scheduled_time": scheduled_time,
			}
		)

	async def schedule_deadline_reminder(
		self,
		*,
		application_id: str,
		user_id: str,
		email: str,
		deadline_data: Dict[str, Any],
		scheduled_time: datetime,
	) -> None:
		await self.queue_notification(
			{
				"type": "deadline_reminder",
				"application_id": application_id,
				"user_id": user_id,
				"email": email,
				"content": deadline_data,
				"scheduled_time": scheduled_time,
			}
		)


__all__ = [
	"AttachmentUploadResponse",
	"BulkEmailRequest",
	"BulkEmailResponse",
	"BulkEmailStatus",
	"DeliveryStatistics",
	"EmailDeliveryRecord",
	"EmailHealthStatus",
	"EmailMessage",
	"EmailTemplate",
	"EmailTemplateCreate",
	"EmailTemplateManager",
	"NotificationPriority",
	"TemplateFormat",
	"TemplateListResponse",
	"TemplateRenderRequest",
	"TemplateRenderResponse",
	"TemplateType",
	"TemplateValidationResult",
]
