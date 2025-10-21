"""
Unified email service that combines Gmail API and SMTP with intelligent fallback.
Provides reliable email delivery with automatic provider switching and enhanced error handling.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, EmailStr

from .gmail_service import GmailService, GmailMessage
from .smtp_service import EnhancedSMTPService as SMTPService, EmailMessage as SMTPMessage
from .sendgrid_service import SendGridService, SendGridEmailType
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class EmailProvider(str, Enum):
    """Email provider types"""
    GMAIL = "gmail"
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AUTO = "auto"


class EmailServiceConfig(BaseModel):
    """Email service configuration"""
    primary_provider: EmailProvider = EmailProvider.AUTO
    enable_fallback: bool = True
    fallback_delay_seconds: int = 5
    max_retry_attempts: int = 3
    prefer_gmail_for_templates: bool = True


class UnifiedEmailMessage(BaseModel):
    """Unified email message model"""
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., max_length=998, description="Email subject line")
    body: str = Field(..., description="Email body content")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Email attachments")
    priority: Optional[str] = Field("normal", description="Email priority")
    template_name: Optional[str] = Field(None, description="Template name for rendering")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Data for template rendering")
    from_email: Optional[EmailStr] = Field(None, description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")
    preferred_provider: Optional[EmailProvider] = Field(None, description="Preferred email provider")


class EmailService:
    """Unified email service with Gmail and SMTP support"""

    def __init__(self):
        self.settings = get_settings()
        self.config = EmailServiceConfig(
            primary_provider=EmailProvider(getattr(self.settings, "email_primary_provider", "auto")),
            enable_fallback=getattr(self.settings, "email_enable_fallback", True),
            fallback_delay_seconds=getattr(self.settings, "email_fallback_delay_seconds", 5),
            max_retry_attempts=getattr(self.settings, "email_max_retry_attempts", 3),
            prefer_gmail_for_templates=getattr(self.settings, "email_prefer_gmail_for_templates", True)
        )
        
        # Initialize email services with proper config
        try:
            from .gmail_service import EnhancedGmailService, GmailConfiguration
            gmail_config = GmailConfiguration()  # Use default config
            self.gmail_service = EnhancedGmailService(gmail_config)
        except Exception as e:
            logger.warning(f"Failed to initialize Gmail service: {e}")
            self.gmail_service = None
        
        try:
            self.smtp_service = SMTPService()
        except Exception as e:
            logger.warning(f"Failed to initialize SMTP service: {e}")
            self.smtp_service = None
        
        try:
            self.sendgrid_service = SendGridService()
        except Exception as e:
            logger.warning(f"Failed to initialize SendGrid service: {e}")
            self.sendgrid_service = None
        
        # Track service health
        self._service_health = {
            EmailProvider.GMAIL: {"available": True, "last_failure": None, "failure_count": 0},
            EmailProvider.SMTP: {"available": True, "last_failure": None, "failure_count": 0},
            EmailProvider.SENDGRID: {"available": True, "last_failure": None, "failure_count": 0}
        }
        
        logger.info(f"Email service initialized: primary={self.config.primary_provider}, fallback={self.config.enable_fallback}")

    async def send_email(self, message: UnifiedEmailMessage, user_id: str = "default_user") -> Dict[str, Any]:
        """Send email with intelligent provider selection and fallback"""
        
        # Determine provider order
        provider_order = self._get_provider_order(message)
        
        last_error = None
        attempts = 0
        
        for provider in provider_order:
            if not self._is_provider_available(provider):
                logger.warning(f"Skipping unavailable provider: {provider}")
                continue
            
            attempts += 1
            
            try:
                result = await self._send_via_provider(message, provider, user_id)
                
                if result["success"]:
                    # Reset failure count on success
                    self._service_health[provider]["failure_count"] = 0
                    self._service_health[provider]["last_failure"] = None
                    
                    result["provider_used"] = provider.value
                    result["total_attempts"] = attempts
                    
                    logger.info(f"Email sent successfully via {provider.value} to {message.to}")
                    return result
                else:
                    last_error = result.get("message", "Unknown error")
                    self._record_provider_failure(provider, last_error)
                    
                    # If this is a permanent failure, don't try other providers
                    if result.get("permanent_failure", False):
                        logger.error(f"Permanent failure with {provider.value}: {last_error}")
                        break
                    
                    logger.warning(f"Email send failed with {provider.value}: {last_error}")
                    
                    # Wait before trying next provider
                    if self.config.enable_fallback and len(provider_order) > 1:
                        await asyncio.sleep(self.config.fallback_delay_seconds)
            
            except Exception as e:
                error_msg = f"Unexpected error with {provider.value}: {str(e)}"
                last_error = error_msg
                self._record_provider_failure(provider, error_msg)
                logger.error(error_msg)
        
        # All providers failed
        return {
            "success": False,
            "error": "all_providers_failed",
            "message": f"All email providers failed. Last error: {last_error}",
            "total_attempts": attempts,
            "providers_tried": [p.value for p in provider_order]
        }

    def _get_provider_order(self, message: UnifiedEmailMessage) -> List[EmailProvider]:
        """Determine the order of providers to try"""
        
        # If message specifies a preferred provider, try it first
        if message.preferred_provider and message.preferred_provider != EmailProvider.AUTO:
            if self.config.enable_fallback:
                other_provider = EmailProvider.SMTP if message.preferred_provider == EmailProvider.GMAIL else EmailProvider.GMAIL
                return [message.preferred_provider, other_provider]
            else:
                return [message.preferred_provider]
        
        # Use configuration-based logic
        if self.config.primary_provider == EmailProvider.AUTO:
            # Auto selection based on message characteristics
            if message.template_name and self.config.prefer_gmail_for_templates:
                primary = EmailProvider.GMAIL
                fallback = EmailProvider.SMTP
            else:
                # Prefer SMTP for simple messages (more reliable)
                primary = EmailProvider.SMTP
                fallback = EmailProvider.GMAIL
        else:
            primary = self.config.primary_provider
            fallback = EmailProvider.SMTP if primary == EmailProvider.GMAIL else EmailProvider.GMAIL
        
        if self.config.enable_fallback:
            return [primary, fallback]
        else:
            return [primary]

    def _is_provider_available(self, provider: EmailProvider) -> bool:
        """Check if a provider is available based on health status"""
        health = self._service_health[provider]
        
        # If too many recent failures, consider unavailable temporarily
        if health["failure_count"] >= 3:
            if health["last_failure"]:
                # Allow retry after 10 minutes
                time_since_failure = (datetime.now() - health["last_failure"]).total_seconds()
                if time_since_failure < 600:  # 10 minutes
                    return False
                else:
                    # Reset failure count after cooldown period
                    health["failure_count"] = 0
                    health["last_failure"] = None
        
        return health["available"]

    def _record_provider_failure(self, provider: EmailProvider, error_message: str):
        """Record a provider failure for health tracking"""
        health = self._service_health[provider]
        health["failure_count"] += 1
        health["last_failure"] = datetime.now()
        
        logger.warning(f"Provider {provider.value} failure recorded: {error_message} (count: {health['failure_count']})")

    async def _send_via_provider(self, message: UnifiedEmailMessage, provider: EmailProvider, user_id: str) -> Dict[str, Any]:
        """Send email via specific provider"""
        
        if provider == EmailProvider.GMAIL:
            # Convert to Gmail message format
            gmail_message = GmailMessage(
                to=message.to,
                subject=message.subject,
                body=message.body,
                cc=message.cc,
                bcc=message.bcc,
                attachments=message.attachments,
                priority=message.priority,
                template_name=message.template_name,
                template_data=message.template_data
            )
            
            return await self.gmail_service.send_email(gmail_message, user_id)
        
        elif provider == EmailProvider.SMTP:
            # Convert to SMTP message format
            smtp_message = SMTPMessage(
                to=message.to,
                subject=message.subject,
                body=message.body,
                cc=message.cc,
                bcc=message.bcc,
                attachments=message.attachments,
                priority=message.priority,
                template_name=message.template_name,
                template_data=message.template_data,
                from_email=message.from_email,
                from_name=message.from_name
            )
            
            return await self.smtp_service.send_email(smtp_message, user_id)
        
        elif provider == EmailProvider.SENDGRID:
            # Use SendGrid service directly for Career Co-Pilot specific emails
            if message.template_name == "morning_briefing":
                return await self.sendgrid_service.send_morning_briefing(
                    recipient_email=message.to,
                    user_name=message.template_data.get("user_name", "User"),
                    recommendations=message.template_data.get("recommendations", []),
                    progress=message.template_data.get("progress"),
                    daily_goals=message.template_data.get("daily_goals"),
                    market_insights=message.template_data.get("market_insights"),
                    user_id=user_id
                )
            elif message.template_name == "evening_summary":
                return await self.sendgrid_service.send_evening_summary(
                    recipient_email=message.to,
                    user_name=message.template_data.get("user_name", "User"),
                    daily_activity=message.template_data.get("daily_activity", {}),
                    achievements=message.template_data.get("achievements"),
                    tomorrow_plan=message.template_data.get("tomorrow_plan"),
                    motivation=message.template_data.get("motivation"),
                    user_id=user_id
                )
            else:
                # Use custom email method for other templates
                return await self.sendgrid_service.send_custom_email(
                    recipient_email=message.to,
                    subject=message.subject,
                    html_content=message.body,  # Assume body is HTML
                    categories=[message.template_name] if message.template_name else None,
                    user_id=user_id
                )
        
        else:
            return {
                "success": False,
                "error": "invalid_provider",
                "message": f"Invalid provider: {provider}"
            }

    async def send_contract_analysis_email(
        self,
        recipient_email: str,
        contract_name: str,
        risk_score: float,
        risky_clauses: List[Dict[str, Any]],
        analysis_summary: str,
        recommendations: List[str],
        user_id: str = "default_user",
        include_attachments: bool = False,
        analysis_id: Optional[str] = None,
        preferred_provider: Optional[EmailProvider] = None
    ) -> Dict[str, Any]:
        """Send job application tracking results email"""
        
        # Determine priority based on risk score
        priority = "high" if risk_score >= 7 else "normal"
        
        # Prepare template data
        template_data = {
            "contract_name": contract_name,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "analysis_summary": analysis_summary,
            "risky_clauses": risky_clauses,
            "recommendations": recommendations,
            "num_risky_clauses": len(risky_clauses),
            "analysis_date": datetime.now().strftime("%B %d, %Y"),
            "analysis_time": datetime.now().strftime("%I:%M %p"),
            "analysis_id": analysis_id or f"CA-{datetime.now().strftime('%Y%m%d')}-{hash(contract_name) % 10000:04d}",
            "recipient_name": recipient_email.split("@")[0].title()
        }
        
        # Create unified message
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🔍 Contract Analysis Complete: {contract_name}",
            body="",  # Will be rendered from template
            priority=priority,
            template_name="contract_analysis_enhanced",
            template_data=template_data,
            preferred_provider=preferred_provider
        )
        
        result = await self.send_email(message, user_id)
        
        if result["success"]:
            logger.info(f"Contract analysis email sent successfully to {recipient_email} for contract: {contract_name}")
        else:
            logger.error(f"Failed to send job application tracking email: {result.get('message', 'Unknown error')}")
        
        return result

    async def send_notification_email(
        self,
        recipient_email: str,
        title: str,
        message_text: str,
        priority: str = "normal",
        user_id: str = "default_user",
        notification_type: str = "general",
        preferred_provider: Optional[EmailProvider] = None
    ) -> Dict[str, Any]:
        """Send a notification email"""
        
        template_data = {
            "title": title,
            "message": message_text,
            "priority": priority,
            "notification_type": notification_type,
            "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "recipient_name": recipient_email.split("@")[0].title()
        }
        
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🔔 Career Copilot: {title}",
            body="",  # Will be rendered from template
            priority=priority,
            template_name="notification",
            template_data=template_data,
            preferred_provider=preferred_provider
        )
        
        result = await self.send_email(message, user_id)
        
        if result["success"]:
            logger.info(f"Notification email sent successfully to {recipient_email}: {title}")
        
        return result

    async def send_risk_alert_email(
        self,
        recipient_email: str,
        contract_name: str,
        risk_score: float,
        urgent_clauses: List[Dict[str, Any]],
        user_id: str = "default_user",
        preferred_provider: Optional[EmailProvider] = None
    ) -> Dict[str, Any]:
        """Send high-risk contract alert email"""
        
        template_data = {
            "contract_name": contract_name,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "urgent_clauses": urgent_clauses,
            "num_urgent_clauses": len(urgent_clauses),
            "alert_timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "recipient_name": recipient_email.split("@")[0].title()
        }
        
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🚨 HIGH RISK ALERT: {contract_name}",
            body="",  # Will be rendered from template
            priority="high",
            template_name="risk_alert",
            template_data=template_data,
            preferred_provider=preferred_provider
        )
        
        result = await self.send_email(message, user_id)
        
        if result["success"]:
            logger.info(f"Risk alert email sent successfully to {recipient_email} for contract: {contract_name}")
        
        return result

    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level text based on score"""
        if risk_score >= 7:
            return "High Risk"
        elif risk_score >= 4:
            return "Medium Risk"
        else:
            return "Low Risk"

    async def test_all_providers(self) -> Dict[str, Any]:
        """Test all email providers"""
        results = {}
        
        # Test Gmail service
        try:
            gmail_result = await self.gmail_service.test_connection()
            results["gmail"] = gmail_result
        except Exception as e:
            results["gmail"] = {"status": "error", "message": str(e)}
        
        # Test SMTP service
        try:
            smtp_result = await self.smtp_service.test_connection()
            results["smtp"] = smtp_result
        except Exception as e:
            results["smtp"] = {"status": "error", "message": str(e)}
        
        # Test SendGrid service
        try:
            sendgrid_result = await self.sendgrid_service.test_connection()
            results["sendgrid"] = sendgrid_result
        except Exception as e:
            results["sendgrid"] = {"status": "error", "message": str(e)}
        
        # Overall status
        gmail_working = results.get("gmail", {}).get("status") == "success" or \
                       results.get("gmail", {}).get("working_providers", 0) > 0
        smtp_working = results.get("smtp", {}).get("working_providers", 0) > 0
        sendgrid_working = results.get("sendgrid", {}).get("success", False)
        
        return {
            "email_service_status": "healthy" if (gmail_working or smtp_working or sendgrid_working) else "unhealthy",
            "gmail_available": gmail_working,
            "smtp_available": smtp_working,
            "sendgrid_available": sendgrid_working,
            "fallback_enabled": self.config.enable_fallback,
            "primary_provider": self.config.primary_provider.value,
            "provider_health": self._service_health,
            "detailed_results": results
        }

    async def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and health"""
        return {
            "service_name": "email_service",
            "primary_provider": self.config.primary_provider.value,
            "fallback_enabled": self.config.enable_fallback,
            "provider_health": self._service_health,
            "configuration": {
                "fallback_delay_seconds": self.config.fallback_delay_seconds,
                "max_retry_attempts": self.config.max_retry_attempts,
                "prefer_gmail_for_templates": self.config.prefer_gmail_for_templates
            }
        }

    async def get_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get quota status from all providers"""
        gmail_quota = await self.gmail_service.get_quota_status(user_id)
        smtp_quota = await self.smtp_service.get_quota_status(user_id)
        
        return {
            "user_id": user_id,
            "gmail_quota": gmail_quota,
            "smtp_quota": smtp_quota,
            "combined_daily_remaining": gmail_quota.get("daily_remaining", 0) + smtp_quota.get("daily_remaining", 0),
            "combined_hourly_remaining": gmail_quota.get("hourly_remaining", 0) + smtp_quota.get("hourly_remaining", 0)
        }

    async def reset_provider_health(self, provider: Optional[EmailProvider] = None):
        """Reset provider health status"""
        if provider:
            self._service_health[provider] = {
                "available": True,
                "last_failure": None,
                "failure_count": 0
            }
            logger.info(f"Reset health status for provider: {provider.value}")
        else:
            for p in EmailProvider:
                if p != EmailProvider.AUTO:
                    self._service_health[p] = {
                        "available": True,
                        "last_failure": None,
                        "failure_count": 0
                    }
            logger.info("Reset health status for all providers")
    
    # Career Co-Pilot specific email methods
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
        """Send morning briefing email using best available provider"""
        
        # Prefer SendGrid for Career Co-Pilot emails
        if self.sendgrid_service and self._is_provider_available(EmailProvider.SENDGRID):
            try:
                return await self.sendgrid_service.send_morning_briefing(
                    recipient_email=recipient_email,
                    user_name=user_name,
                    recommendations=recommendations,
                    progress=progress,
                    daily_goals=daily_goals,
                    market_insights=market_insights,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"SendGrid morning briefing failed, falling back: {e}")
                self._record_provider_failure(EmailProvider.SENDGRID, str(e))
        
        # Fallback to unified email with template
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🌅 Your Daily Career Briefing - {datetime.now().strftime('%B %d')}",
            body="",  # Will be rendered from template
            template_name="morning_briefing",
            template_data={
                "user_name": user_name,
                "recommendations": recommendations,
                "progress": progress,
                "daily_goals": daily_goals,
                "market_insights": market_insights
            }
        )
        
        return await self.send_email(message, user_id)
    
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
        """Send evening summary email using best available provider"""
        
        # Prefer SendGrid for Career Co-Pilot emails
        if self.sendgrid_service and self._is_provider_available(EmailProvider.SENDGRID):
            try:
                return await self.sendgrid_service.send_evening_summary(
                    recipient_email=recipient_email,
                    user_name=user_name,
                    daily_activity=daily_activity,
                    achievements=achievements,
                    tomorrow_plan=tomorrow_plan,
                    motivation=motivation,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"SendGrid evening summary failed, falling back: {e}")
                self._record_provider_failure(EmailProvider.SENDGRID, str(e))
        
        # Fallback to unified email with template
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🌙 Your Daily Progress Summary - {datetime.now().strftime('%B %d')}",
            body="",  # Will be rendered from template
            template_name="evening_summary",
            template_data={
                "user_name": user_name,
                "daily_activity": daily_activity,
                "achievements": achievements,
                "tomorrow_plan": tomorrow_plan,
                "motivation": motivation
            }
        )
        
        return await self.send_email(message, user_id)
    
    async def send_job_alert(
        self,
        recipient_email: str,
        user_name: str,
        new_jobs: List[Dict[str, Any]],
        match_criteria: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send job alert email using best available provider"""
        
        # Prefer SendGrid for Career Co-Pilot emails
        if self.sendgrid_service and self._is_provider_available(EmailProvider.SENDGRID):
            try:
                return await self.sendgrid_service.send_job_alert(
                    recipient_email=recipient_email,
                    user_name=user_name,
                    new_jobs=new_jobs,
                    match_criteria=match_criteria,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"SendGrid job alert failed, falling back: {e}")
                self._record_provider_failure(EmailProvider.SENDGRID, str(e))
        
        # Fallback to unified email with template
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"🎯 {len(new_jobs)} New Job Match{'es' if len(new_jobs) != 1 else ''} Found!",
            body="",  # Will be rendered from template
            template_name="job_alert",
            template_data={
                "user_name": user_name,
                "new_jobs": new_jobs,
                "match_criteria": match_criteria,
                "job_count": len(new_jobs)
            }
        )
        
        return await self.send_email(message, user_id)
    
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
        """Send application confirmation email using best available provider"""
        
        # Prefer SendGrid for Career Co-Pilot emails
        if self.sendgrid_service and self._is_provider_available(EmailProvider.SENDGRID):
            try:
                return await self.sendgrid_service.send_application_confirmation(
                    recipient_email=recipient_email,
                    user_name=user_name,
                    job_title=job_title,
                    company=company,
                    application_date=application_date,
                    next_steps=next_steps,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"SendGrid application confirmation failed, falling back: {e}")
                self._record_provider_failure(EmailProvider.SENDGRID, str(e))
        
        # Fallback to unified email with template
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject=f"✅ Application Confirmed: {job_title} at {company}",
            body="",  # Will be rendered from template
            template_name="application_confirmation",
            template_data={
                "user_name": user_name,
                "job_title": job_title,
                "company": company,
                "application_date": application_date,
                "next_steps": next_steps
            }
        )
        
        return await self.send_email(message, user_id)
    
    async def send_skill_gap_report(
        self,
        recipient_email: str,
        user_name: str,
        skill_gaps: List[Dict[str, Any]],
        learning_recommendations: List[Dict[str, Any]],
        market_demand: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Send skill gap analysis report using best available provider"""
        
        # Prefer SendGrid for Career Co-Pilot emails
        if self.sendgrid_service and self._is_provider_available(EmailProvider.SENDGRID):
            try:
                return await self.sendgrid_service.send_skill_gap_report(
                    recipient_email=recipient_email,
                    user_name=user_name,
                    skill_gaps=skill_gaps,
                    learning_recommendations=learning_recommendations,
                    market_demand=market_demand,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"SendGrid skill gap report failed, falling back: {e}")
                self._record_provider_failure(EmailProvider.SENDGRID, str(e))
        
        # Fallback to unified email with template
        message = UnifiedEmailMessage(
            to=recipient_email,
            subject="📊 Your Skill Gap Analysis Report",
            body="",  # Will be rendered from template
            template_name="skill_gap_report",
            template_data={
                "user_name": user_name,
                "skill_gaps": skill_gaps,
                "learning_recommendations": learning_recommendations,
                "market_demand": market_demand
            }
        )
        
        return await self.send_email(message, user_id)