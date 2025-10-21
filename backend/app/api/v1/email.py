"""
Email API endpoints for Gmail integration service.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr

from ...services.email_service import EmailService, UnifiedEmailMessage, EmailProvider
from ...core.logging import get_logger
from ...core.auth import get_current_user
from ...models.database_models import User

logger = get_logger(__name__)

router = APIRouter(prefix="/email", tags=["email"])

# Initialize unified email service
email_service = EmailService()


# Request/Response Models
class EmailRequest(BaseModel):
    """Base email request model"""
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., max_length=998, description="Email subject")
    body: str = Field(..., description="Email body content")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    priority: Optional[str] = Field("normal", description="Email priority (high, normal, low)")
    preferred_provider: Optional[str] = Field(None, description="Preferred email provider (gmail, smtp, auto)")
    from_email: Optional[EmailStr] = Field(None, description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")


class TemplateEmailRequest(BaseModel):
    """Template-based email request model"""
    to: EmailStr = Field(..., description="Recipient email address")
    template_name: str = Field(..., description="Template name to use")
    template_data: Dict[str, Any] = Field(..., description="Data for template rendering")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    priority: Optional[str] = Field("normal", description="Email priority")
    preferred_provider: Optional[str] = Field(None, description="Preferred email provider (gmail, smtp, auto)")
    from_email: Optional[EmailStr] = Field(None, description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")


class ContractAnalysisEmailRequest(BaseModel):
    """Contract analysis email request model"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    contract_name: str = Field(..., description="Contract name")
    risk_score: float = Field(..., ge=0, le=10, description="Risk score (0-10)")
    risky_clauses: List[Dict[str, Any]] = Field(..., description="List of risky clauses")
    analysis_summary: str = Field(..., description="Analysis summary")
    recommendations: List[str] = Field(..., description="List of recommendations")
    include_attachments: bool = Field(False, description="Include PDF/CSV attachments")
    analysis_id: Optional[str] = Field(None, description="Analysis ID for tracking")
    preferred_provider: Optional[str] = Field(None, description="Preferred email provider (gmail, smtp, auto)")


class NotificationEmailRequest(BaseModel):
    """Notification email request model"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field("normal", description="Priority level")
    notification_type: str = Field("general", description="Notification type")
    preferred_provider: Optional[str] = Field(None, description="Preferred email provider (gmail, smtp, auto)")


class RiskAlertEmailRequest(BaseModel):
    """Risk alert email request model"""
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    contract_name: str = Field(..., description="Contract name")
    risk_score: float = Field(..., ge=7, le=10, description="Risk score (7-10 for alerts)")
    urgent_clauses: List[Dict[str, Any]] = Field(..., description="Urgent clauses requiring attention")
    preferred_provider: Optional[str] = Field(None, description="Preferred email provider (gmail, smtp, auto)")


class EmailResponse(BaseModel):
    """Email response model"""
    success: bool
    message: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    quota_info: Optional[Dict[str, Any]] = None
    provider_used: Optional[str] = None
    total_attempts: Optional[int] = None
    providers_tried: Optional[List[str]] = None


class QuotaStatusResponse(BaseModel):
    """Quota status response model"""
    user_id: str
    daily_sent: int
    daily_limit: int
    daily_remaining: int
    hourly_sent: int
    hourly_limit: int
    hourly_remaining: int
    quota_status: str


class EmailTemplateResponse(BaseModel):
    """Email template response model"""
    id: str
    name: str
    description: str
    variables: List[str]
    template_type: str
    category: str
    deprecated: Optional[bool] = None


class DeliveryStatusResponse(BaseModel):
    """Delivery status response model"""
    message_id: str
    recipient: Optional[str] = None
    status: Optional[str] = None
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    error_message: Optional[str] = None


# API Endpoints
@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send a basic email"""
    try:
        # Parse preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = EmailProvider(request.preferred_provider.lower())
            except ValueError:
                preferred_provider = EmailProvider.AUTO
        
        message = UnifiedEmailMessage(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            priority=request.priority,
            preferred_provider=preferred_provider,
            from_email=request.from_email,
            from_name=request.from_name
        )
        
        result = await email_service.send_email(message, str(current_user.id))
        
        return EmailResponse(
            success=result["success"],
            message=result.get("message", "Email processed"),
            message_id=result.get("message_id"),
            error=result.get("error"),
            quota_info=result.get("quota_info"),
            provider_used=result.get("provider_used"),
            total_attempts=result.get("total_attempts"),
            providers_tried=result.get("providers_tried")
        )
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/send-template", response_model=EmailResponse)
async def send_template_email(
    request: TemplateEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send an email using a template"""
    try:
        # Parse preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = EmailProvider(request.preferred_provider.lower())
            except ValueError:
                preferred_provider = EmailProvider.AUTO
        
        message = UnifiedEmailMessage(
            to=request.to,
            subject="",  # Will be set by template
            body="",     # Will be rendered from template
            cc=request.cc,
            bcc=request.bcc,
            priority=request.priority,
            template_name=request.template_name,
            template_data=request.template_data,
            preferred_provider=preferred_provider,
            from_email=request.from_email,
            from_name=request.from_name
        )
        
        result = await email_service.send_email(message, str(current_user.id))
        
        return EmailResponse(
            success=result["success"],
            message=result.get("message", "Template email processed"),
            message_id=result.get("message_id"),
            error=result.get("error"),
            quota_info=result.get("quota_info"),
            provider_used=result.get("provider_used"),
            total_attempts=result.get("total_attempts"),
            providers_tried=result.get("providers_tried")
        )
        
    except Exception as e:
        logger.error(f"Failed to send template email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send template email: {str(e)}")


@router.post("/send-contract-analysis", response_model=EmailResponse)
async def send_contract_analysis_email(
    request: ContractAnalysisEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send job application tracking results email"""
    try:
        # Parse preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = EmailProvider(request.preferred_provider.lower())
            except ValueError:
                preferred_provider = EmailProvider.AUTO
        
        result = await email_service.send_contract_analysis_email(
            recipient_email=request.recipient_email,
            contract_name=request.contract_name,
            risk_score=request.risk_score,
            risky_clauses=request.risky_clauses,
            analysis_summary=request.analysis_summary,
            recommendations=request.recommendations,
            user_id=str(current_user.id),
            include_attachments=request.include_attachments,
            analysis_id=request.analysis_id,
            preferred_provider=preferred_provider
        )
        
        return EmailResponse(
            success=result["success"],
            message=result.get("message", "Contract analysis email processed"),
            message_id=result.get("message_id"),
            error=result.get("error"),
            provider_used=result.get("provider_used"),
            total_attempts=result.get("total_attempts"),
            providers_tried=result.get("providers_tried")
        )
        
    except Exception as e:
        logger.error(f"Failed to send job application tracking email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send job application tracking email: {str(e)}")


@router.post("/send-notification", response_model=EmailResponse)
async def send_notification_email(
    request: NotificationEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send a notification email"""
    try:
        # Parse preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = EmailProvider(request.preferred_provider.lower())
            except ValueError:
                preferred_provider = EmailProvider.AUTO
        
        result = await email_service.send_notification_email(
            recipient_email=request.recipient_email,
            title=request.title,
            message_text=request.message,
            priority=request.priority,
            user_id=str(current_user.id),
            notification_type=request.notification_type,
            preferred_provider=preferred_provider
        )
        
        return EmailResponse(
            success=result["success"],
            message=result.get("message", "Notification email processed"),
            message_id=result.get("message_id"),
            error=result.get("error"),
            provider_used=result.get("provider_used"),
            total_attempts=result.get("total_attempts"),
            providers_tried=result.get("providers_tried")
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification email: {str(e)}")


@router.post("/send-risk-alert", response_model=EmailResponse)
async def send_risk_alert_email(
    request: RiskAlertEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Send a high-risk contract alert email"""
    try:
        # Parse preferred provider
        preferred_provider = None
        if request.preferred_provider:
            try:
                preferred_provider = EmailProvider(request.preferred_provider.lower())
            except ValueError:
                preferred_provider = EmailProvider.AUTO
        
        result = await email_service.send_risk_alert_email(
            recipient_email=request.recipient_email,
            contract_name=request.contract_name,
            risk_score=request.risk_score,
            urgent_clauses=request.urgent_clauses,
            user_id=str(current_user.id),
            preferred_provider=preferred_provider
        )
        
        return EmailResponse(
            success=result["success"],
            message=result.get("message", "Risk alert email processed"),
            message_id=result.get("message_id"),
            error=result.get("error"),
            provider_used=result.get("provider_used"),
            total_attempts=result.get("total_attempts"),
            providers_tried=result.get("providers_tried")
        )
        
    except Exception as e:
        logger.error(f"Failed to send risk alert email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send risk alert email: {str(e)}")


@router.get("/quota/{user_id}")
async def get_quota_status(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get email quota status for a user"""
    try:
        # Only allow users to check their own quota or superusers to check any quota
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        quota_status = await email_service.get_quota_status(user_id)
        
        return quota_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quota status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota status: {str(e)}")


@router.get("/templates", response_model=List[EmailTemplateResponse])
async def get_email_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available email templates"""
    try:
        # Get templates from Gmail service (they share the same template system)
        templates = await email_service.gmail_service.get_email_templates()
        
        return [EmailTemplateResponse(**template) for template in templates]
        
    except Exception as e:
        logger.error(f"Failed to get email templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email templates: {str(e)}")


@router.get("/delivery-status/{message_id}", response_model=DeliveryStatusResponse)
async def get_delivery_status(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get delivery status for a specific message"""
    try:
        # Try Gmail service first, then SMTP service
        status = await email_service.gmail_service.get_delivery_status(message_id)
        
        if "error" in status:
            # Try SMTP service if Gmail doesn't have the message
            if message_id.startswith("smtp_"):
                # For now, SMTP service uses the same delivery status repository
                status = await email_service.gmail_service.get_delivery_status(message_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return DeliveryStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get delivery status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get delivery status: {str(e)}")


@router.get("/statistics/{user_id}")
async def get_email_statistics(
    user_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get email statistics for a user"""
    try:
        # Only allow users to check their own stats or superusers to check any stats
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics from Gmail service (they share the same database)
        stats = await email_service.gmail_service.get_email_statistics(user_id, days)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email statistics: {str(e)}")


@router.get("/test-connection")
async def test_email_connection(
    current_user: User = Depends(get_current_user)
):
    """Test all email service connections"""
    try:
        # Only allow superusers to test connection
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await email_service.test_all_providers()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test email connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test email connections: {str(e)}")


@router.get("/service-status")
async def get_email_service_status(
    current_user: User = Depends(get_current_user)
):
    """Get email service status and health"""
    try:
        # Only allow superusers to check service status
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        status = await email_service.get_service_status()
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email service status: {str(e)}")


@router.post("/reset-provider-health")
async def reset_provider_health(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Reset email provider health status"""
    try:
        # Only allow superusers to reset provider health
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        email_provider = None
        if provider:
            try:
                email_provider = EmailProvider(provider.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        await email_service.reset_provider_health(email_provider)
        
        return {"message": f"Provider health reset successfully", "provider": provider or "all"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset provider health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset provider health: {str(e)}")