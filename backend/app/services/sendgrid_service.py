"""
SendGrid Email Service Integration for Career Co-Pilot System
Provides reliable email delivery with template support, personalization, and tracking.
"""

import asyncio
import json
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import uuid

from pydantic import BaseModel, Field, EmailStr, validator
import httpx
from jinja2 import Environment, FileSystemLoader, Template, TemplateError

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class SendGridEmailType(str, Enum):
    """SendGrid email types for Career Co-Pilot"""
    MORNING_BRIEFING = "morning_briefing"
    EVENING_SUMMARY = "evening_summary"
    JOB_ALERT = "job_alert"
    APPLICATION_CONFIRMATION = "application_confirmation"
    SKILL_GAP_REPORT = "skill_gap_report"
    WEEKLY_PROGRESS = "weekly_progress"
    WELCOME = "welcome"
    NOTIFICATION = "notification"


class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SendGridAttachment(BaseModel):
    """SendGrid email attachment model"""
    content: str = Field(..., description="Base64 encoded attachment content")
    filename: str = Field(..., description="Attachment filename")
    type: str = Field(..., description="MIME type")
    disposition: str = Field("attachment", description="Content disposition")
    content_id: Optional[str] = Field(None, description="Content ID for inline attachments")


class SendGridPersonalization(BaseModel):
    """SendGrid personalization for dynamic content"""
    to: List[Dict[str, str]] = Field(..., description="Recipient list")
    cc: Optional[List[Dict[str, str]]] = Field(None, description="CC recipients")
    bcc: Optional[List[Dict[str, str]]] = Field(None, description="BCC recipients")
    subject: Optional[str] = Field(None, description="Personalized subject")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    substitutions: Optional[Dict[str, str]] = Field(None, description="Template substitutions")
    dynamic_template_data: Optional[Dict[str, Any]] = Field(None, description="Dynamic template data")
    send_at: Optional[int] = Field(None, description="Scheduled send timestamp")


class SendGridEmailMessage(BaseModel):
    """SendGrid email message model"""
    personalizations: List[SendGridPersonalization] = Field(..., description="Email personalizations")
    from_email: Dict[str, str] = Field(..., description="Sender information", alias="from")
    reply_to: Optional[Dict[str, str]] = Field(None, description="Reply-to address")
    subject: Optional[str] = Field(None, description="Email subject")
    content: Optional[List[Dict[str, str]]] = Field(None, description="Email content")
    attachments: Optional[List[SendGridAttachment]] = Field(None, description="Email attachments")
    template_id: Optional[str] = Field(None, description="SendGrid template ID")
    headers: Optional[Dict[str, str]] = Field(None, description="Global headers")
    categories: Optional[List[str]] = Field(None, description="Email categories for tracking")
    custom_args: Optional[Dict[str, str]] = Field(None, description="Custom arguments")
    send_at: Optional[int] = Field(None, description="Scheduled send timestamp")
    batch_id: Optional[str] = Field(None, description="Batch ID for bulk operations")
    asm: Optional[Dict[str, Any]] = Field(None, description="Advanced Suppression Manager")
    ip_pool_name: Optional[str] = Field(None, description="IP pool name")
    mail_settings: Optional[Dict[str, Any]] = Field(None, description="Mail settings")
    tracking_settings: Optional[Dict[str, Any]] = Field(None, description="Tracking settings")

    class Config:
        allow_population_by_field_name = True


class EmailDeliveryStatus(str, Enum):
    """Email delivery status tracking"""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    DROPPED = "dropped"
    SPAM_REPORT = "spam_report"
    UNSUBSCRIBE = "unsubscribe"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


@dataclass
class EmailTrackingRecord:
    """Email tracking record for delivery monitoring"""
    tracking_id: str
    message_id: str
    recipient: str
    subject: str
    email_type: SendGridEmailType
    status: EmailDeliveryStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SendGridConfiguration(BaseModel):
    """SendGrid service configuration"""
    api_key: str = Field(..., description="SendGrid API key")
    from_email: EmailStr = Field(..., description="Default sender email")
    from_name: str = Field("Career Co-Pilot", description="Default sender name")
    reply_to_email: Optional[EmailStr] = Field(None, description="Reply-to email")
    base_url: str = Field("https://api.sendgrid.com/v3", description="SendGrid API base URL")
    timeout: float = Field(30.0, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries")
    rate_limit_per_second: int = Field(10, description="Rate limit per second")
    enable_tracking: bool = Field(True, description="Enable email tracking")
    enable_click_tracking: bool = Field(True, description="Enable click tracking")
    enable_open_tracking: bool = Field(True, description="Enable open tracking")
    enable_subscription_tracking: bool = Field(True, description="Enable subscription tracking")
    template_cache_ttl: int = Field(3600, description="Template cache TTL in seconds")


class SendGridService:
    """SendGrid email service for Career Co-Pilot system"""
    
    def __init__(self, config: Optional[SendGridConfiguration] = None):
        self.settings = get_settings()
        
        # Initialize configuration
        if config:
            self.config = config
        else:
            self.config = SendGridConfiguration(
                api_key=getattr(self.settings, "sendgrid_api_key", ""),
                from_email=getattr(self.settings, "sendgrid_from_email", "noreply@career-copilot.com"),
                from_name=getattr(self.settings, "sendgrid_from_name", "Career Co-Pilot"),
                reply_to_email=getattr(self.settings, "sendgrid_reply_to_email", None),
                enable_tracking=getattr(self.settings, "sendgrid_enable_tracking", True),
                enable_click_tracking=getattr(self.settings, "sendgrid_enable_click_tracking", True),
                enable_open_tracking=getattr(self.settings, "sendgrid_enable_open_tracking", True)
            )
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Initialize template engine
        self.template_env = Environment(
            loader=FileSystemLoader("backend/app/templates/email"),
            autoescape=True
        )
        
        # Tracking and caching
        self.delivery_records: Dict[str, EmailTrackingRecord] = {}
        self.template_cache: Dict[str, str] = {}
        self.rate_limiter = []
        
        logger.info("SendGrid service initialized")
    
    async def send_morning_briefing(
        self,
        recipient_email: str,
        user_name: str,
        recommendations: List[Dict[str, Any]],
        progress: Optional[Dict[str, Any]] = None,
        daily_goals: Optional[Dict[str, Any]] = None,
        market_insights: Optional[Dict[str, Any]] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send morning briefing email with job recommendations"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.MORNING_BRIEFING)
        
        # Prepare template data
        template_data = {
            "user_name": user_name,
            "greeting": self._get_greeting(),
            "current_date": datetime.now(),
            "recommendations": recommendations[:5],  # Top 5 recommendations
            "progress": progress,
            "daily_goals": daily_goals,
            "market_insights": market_insights,
            "tracking_id": tracking_id,
            "dashboard_url": f"{self.settings.frontend_url}/dashboard",
            "jobs_url": f"{self.settings.frontend_url}/jobs"
        }
        
        # Create personalization
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email, "name": user_name}],
            dynamic_template_data=template_data
        )
        
        # Create email message
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=f"🌅 Your Daily Career Briefing - {datetime.now().strftime('%B %d')}",
            categories=["morning_briefing", "career_copilot"],
            custom_args={"user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        # Render and send
        return await self._send_templated_email(
            message, 
            SendGridEmailType.MORNING_BRIEFING,
            template_data,
            tracking_id
        )
    
    async def send_evening_summary(
        self,
        recipient_email: str,
        user_name: str,
        daily_activity: Dict[str, Any],
        achievements: Optional[List[Dict[str, Any]]] = None,
        tomorrow_plan: Optional[Dict[str, Any]] = None,
        motivation: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send evening summary email with daily progress"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.EVENING_SUMMARY)
        
        # Prepare template data
        template_data = {
            "user_name": user_name,
            "current_date": datetime.now(),
            "daily_activity": daily_activity,
            "achievements": achievements or [],
            "tomorrow_plan": tomorrow_plan,
            "motivation": motivation or self._get_motivational_message(),
            "tracking_id": tracking_id,
            "dashboard_url": f"{self.settings.frontend_url}/dashboard"
        }
        
        # Create personalization
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email, "name": user_name}],
            dynamic_template_data=template_data
        )
        
        # Create email message
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=f"🌙 Your Daily Progress Summary - {datetime.now().strftime('%B %d')}",
            categories=["evening_summary", "career_copilot"],
            custom_args={"user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        return await self._send_templated_email(
            message,
            SendGridEmailType.EVENING_SUMMARY,
            template_data,
            tracking_id
        )
    
    async def send_job_alert(
        self,
        recipient_email: str,
        user_name: str,
        new_jobs: List[Dict[str, Any]],
        match_criteria: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send job alert email with new matching opportunities"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.JOB_ALERT)
        
        template_data = {
            "user_name": user_name,
            "new_jobs": new_jobs,
            "match_criteria": match_criteria,
            "job_count": len(new_jobs),
            "tracking_id": tracking_id,
            "jobs_url": f"{self.settings.frontend_url}/jobs"
        }
        
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email, "name": user_name}],
            dynamic_template_data=template_data
        )
        
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=f"🎯 {len(new_jobs)} New Job Match{'es' if len(new_jobs) != 1 else ''} Found!",
            categories=["job_alert", "career_copilot"],
            custom_args={"user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        return await self._send_templated_email(
            message,
            SendGridEmailType.JOB_ALERT,
            template_data,
            tracking_id
        )
    
    async def send_application_confirmation(
        self,
        recipient_email: str,
        user_name: str,
        job_title: str,
        company: str,
        application_date: datetime,
        next_steps: List[str],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send application confirmation email"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.APPLICATION_CONFIRMATION)
        
        template_data = {
            "user_name": user_name,
            "job_title": job_title,
            "company": company,
            "application_date": application_date,
            "next_steps": next_steps,
            "tracking_id": tracking_id,
            "dashboard_url": f"{self.settings.frontend_url}/dashboard"
        }
        
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email, "name": user_name}],
            dynamic_template_data=template_data
        )
        
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=f"✅ Application Confirmed: {job_title} at {company}",
            categories=["application_confirmation", "career_copilot"],
            custom_args={"user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        return await self._send_templated_email(
            message,
            SendGridEmailType.APPLICATION_CONFIRMATION,
            template_data,
            tracking_id
        )
    
    async def send_skill_gap_report(
        self,
        recipient_email: str,
        user_name: str,
        skill_gaps: List[Dict[str, Any]],
        learning_recommendations: List[Dict[str, Any]],
        market_demand: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send skill gap analysis report"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.SKILL_GAP_REPORT)
        
        template_data = {
            "user_name": user_name,
            "skill_gaps": skill_gaps,
            "learning_recommendations": learning_recommendations,
            "market_demand": market_demand,
            "tracking_id": tracking_id,
            "dashboard_url": f"{self.settings.frontend_url}/dashboard"
        }
        
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email, "name": user_name}],
            dynamic_template_data=template_data
        )
        
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=f"📊 Your Skill Gap Analysis Report",
            categories=["skill_gap_report", "career_copilot"],
            custom_args={"user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        return await self._send_templated_email(
            message,
            SendGridEmailType.SKILL_GAP_REPORT,
            template_data,
            tracking_id
        )
    
    async def send_custom_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[SendGridAttachment]] = None,
        categories: Optional[List[str]] = None,
        custom_args: Optional[Dict[str, str]] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send custom email with HTML/text content"""
        
        tracking_id = self._generate_tracking_id(recipient_email, SendGridEmailType.NOTIFICATION)
        
        # Prepare content
        content = [{"type": "text/html", "value": html_content}]
        if text_content:
            content.insert(0, {"type": "text/plain", "value": text_content})
        
        personalization = SendGridPersonalization(
            to=[{"email": recipient_email}]
        )
        
        message = SendGridEmailMessage(
            personalizations=[personalization],
            **{"from": {"email": self.config.from_email, "name": self.config.from_name}},
            subject=subject,
            content=content,
            attachments=attachments,
            categories=categories or ["custom", "career_copilot"],
            custom_args={**(custom_args or {}), "user_id": user_id, "tracking_id": tracking_id},
            tracking_settings=self._get_tracking_settings()
        )
        
        return await self._send_email_message(message, tracking_id)
    
    async def _send_templated_email(
        self,
        message: SendGridEmailMessage,
        email_type: SendGridEmailType,
        template_data: Dict[str, Any],
        tracking_id: str
    ) -> Dict[str, Any]:
        """Send email using Jinja2 template rendering"""
        
        try:
            # Render HTML template
            html_template = self.template_env.get_template(f"{email_type.value}.html")
            html_content = html_template.render(**template_data)
            
            # Try to render text template (optional)
            text_content = None
            try:
                text_template = self.template_env.get_template(f"{email_type.value}.txt")
                text_content = text_template.render(**template_data)
            except:
                # Text template is optional
                pass
            
            # Add content to message
            content = [{"type": "text/html", "value": html_content}]
            if text_content:
                content.insert(0, {"type": "text/plain", "value": text_content})
            
            message.content = content
            
            return await self._send_email_message(message, tracking_id)
            
        except TemplateError as e:
            logger.error(f"Template rendering failed for {email_type.value}: {e}")
            raise EmailServiceError(
                f"Template rendering failed: {e}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH
            )
    
    async def _send_email_message(
        self,
        message: SendGridEmailMessage,
        tracking_id: str
    ) -> Dict[str, Any]:
        """Send email message via SendGrid API"""
        
        # Check rate limiting
        await self._check_rate_limit()
        
        # Create tracking record
        recipient = message.personalizations[0].to[0]["email"]
        tracking_record = EmailTrackingRecord(
            tracking_id=tracking_id,
            message_id="",  # Will be set after sending
            recipient=recipient,
            subject=message.subject or "No Subject",
            email_type=SendGridEmailType.NOTIFICATION,  # Default
            status=EmailDeliveryStatus.QUEUED,
            sent_at=datetime.now()
        )
        
        try:
            # Send email with retry logic
            response = await self._send_with_retry(message)
            
            # Update tracking record
            tracking_record.message_id = response.get("message_id", "")
            tracking_record.status = EmailDeliveryStatus.SENT
            self.delivery_records[tracking_id] = tracking_record
            
            logger.info(f"Email sent successfully to {recipient} (tracking_id: {tracking_id})")
            
            return {
                "success": True,
                "tracking_id": tracking_id,
                "message_id": tracking_record.message_id,
                "recipient": recipient,
                "sent_at": tracking_record.sent_at.isoformat()
            }
            
        except Exception as e:
            # Update tracking record with error
            tracking_record.status = EmailDeliveryStatus.BLOCKED
            tracking_record.error_message = str(e)
            self.delivery_records[tracking_id] = tracking_record
            
            logger.error(f"Failed to send email to {recipient}: {e}")
            raise EmailServiceError(
                f"Email delivery failed: {e}",
                category=ErrorCategory.EXTERNAL_SERVICE,
                severity=ErrorSeverity.HIGH
            )
    
    async def _send_with_retry(self, message: SendGridEmailMessage) -> Dict[str, Any]:
        """Send email with retry logic"""
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Convert message to dict and send
                message_dict = message.dict(by_alias=True, exclude_none=True)
                
                response = await self.client.post("/mail/send", json=message_dict)
                
                if response.status_code == 202:
                    # Success
                    message_id = response.headers.get("X-Message-Id", str(uuid.uuid4()))
                    return {"message_id": message_id, "status_code": response.status_code}
                else:
                    # API error
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("errors", [{"message": "Unknown error"}])[0]["message"]
                    raise EmailServiceError(f"SendGrid API error: {error_msg} (status: {response.status_code})")
                    
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Email send attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} email send attempts failed")
        
        raise last_exception
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        
        # Remove old entries (older than 1 second)
        self.rate_limiter = [
            timestamp for timestamp in self.rate_limiter
            if (current_time - timestamp).total_seconds() < 1.0
        ]
        
        # Check if we're at the limit
        if len(self.rate_limiter) >= self.config.rate_limit_per_second:
            sleep_time = 1.0 - (current_time - self.rate_limiter[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current request
        self.rate_limiter.append(current_time)
    
    def _get_tracking_settings(self) -> Dict[str, Any]:
        """Get tracking settings for email"""
        return {
            "click_tracking": {"enable": self.config.enable_click_tracking},
            "open_tracking": {"enable": self.config.enable_open_tracking},
            "subscription_tracking": {"enable": self.config.enable_subscription_tracking}
        }
    
    def _generate_tracking_id(self, recipient: str, email_type: SendGridEmailType) -> str:
        """Generate unique tracking ID"""
        data = f"{recipient}{email_type.value}{datetime.now().isoformat()}{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"
    
    def _get_motivational_message(self) -> str:
        """Get random motivational message"""
        messages = [
            "Every application brings you one step closer to your dream job. Keep going!",
            "Your persistence and dedication will pay off. Tomorrow is full of new opportunities!",
            "Progress isn't always visible, but every effort counts. You're building something great!",
            "The job market is competitive, but so are you. Your unique skills make you valuable!",
            "Remember: rejection is redirection. The right opportunity is waiting for you!"
        ]
        import random
        return random.choice(messages)
    
    async def get_delivery_status(self, tracking_id: str) -> Optional[EmailTrackingRecord]:
        """Get delivery status for tracking ID"""
        return self.delivery_records.get(tracking_id)
    
    async def update_delivery_status(
        self,
        tracking_id: str,
        status: EmailDeliveryStatus,
        timestamp: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        """Update delivery status (called by webhook handler)"""
        if tracking_id not in self.delivery_records:
            logger.warning(f"Tracking ID not found: {tracking_id}")
            return
        
        record = self.delivery_records[tracking_id]
        record.status = status
        
        if timestamp is None:
            timestamp = datetime.now()
        
        if status == EmailDeliveryStatus.DELIVERED:
            record.delivered_at = timestamp
        elif status == EmailDeliveryStatus.OPENED:
            record.opened_at = timestamp
        elif status == EmailDeliveryStatus.CLICKED:
            record.clicked_at = timestamp
        elif status == EmailDeliveryStatus.BOUNCED:
            record.bounced_at = timestamp
            record.error_message = error_message
        
        logger.info(f"Updated delivery status for {tracking_id}: {status}")
    
    async def get_delivery_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        email_type: Optional[SendGridEmailType] = None
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        
        # Filter records
        filtered_records = []
        for record in self.delivery_records.values():
            if start_date and record.sent_at < start_date:
                continue
            if end_date and record.sent_at > end_date:
                continue
            if email_type and record.email_type != email_type:
                continue
            filtered_records.append(record)
        
        # Calculate statistics
        total_sent = len(filtered_records)
        delivered = len([r for r in filtered_records if r.status in [
            EmailDeliveryStatus.DELIVERED, EmailDeliveryStatus.OPENED, EmailDeliveryStatus.CLICKED
        ]])
        opened = len([r for r in filtered_records if r.opened_at is not None])
        clicked = len([r for r in filtered_records if r.clicked_at is not None])
        bounced = len([r for r in filtered_records if r.status == EmailDeliveryStatus.BOUNCED])
        
        return {
            "total_sent": total_sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "delivery_rate": (delivered / total_sent) if total_sent > 0 else 0,
            "open_rate": (opened / delivered) if delivered > 0 else 0,
            "click_rate": (clicked / delivered) if delivered > 0 else 0,
            "bounce_rate": (bounced / total_sent) if total_sent > 0 else 0
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test SendGrid API connection"""
        try:
            response = await self.client.get("/user/profile")
            if response.status_code == 200:
                profile_data = response.json()
                return {
                    "success": True,
                    "message": "SendGrid connection successful",
                    "profile": profile_data
                }
            else:
                return {
                    "success": False,
                    "message": f"SendGrid API error: {response.status_code}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"SendGrid connection failed: {e}",
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("SendGrid service closed")