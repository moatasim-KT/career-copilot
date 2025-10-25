"""
Email Template API endpoints for comprehensive email template management.
Provides REST API for template CRUD, rendering, and delivery tracking.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, Response
from pydantic import EmailStr
import aiofiles

from ...core.logging import get_logger
from ...core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from ...services.email_template_manager import EmailTemplateManager, TemplateType
from ...services.email_service import EmailProvider
from ...models.email_template_models import (
    EmailTemplate, EmailTemplateCreate, EmailMessage, EmailMessageCreate,
    EmailAttachment, EmailAttachmentCreate, EmailDeliveryRecord, DeliveryStatistics,
    TemplateRenderRequest, TemplateRenderResponse, TemplateListResponse,
    AttachmentUploadRequest, AttachmentUploadResponse, EmailHealthStatus,
    TemplateValidationResult, BulkEmailRequest, BulkEmailResponse, BulkEmailStatus
)

logger = get_logger(__name__)

router = APIRouter(prefix="/email-templates", tags=["Email Templates"])

# Global service instance
email_template_service: Optional[EmailTemplateManager] = None


async def get_email_template_service() -> EmailTemplateManager:
    """Get email template service instance"""
    global email_template_service
    if email_template_service is None:
        email_template_service = EmailTemplateManager()
        await email_template_service.initialize()
    return email_template_service


@router.get("/health", response_model=EmailHealthStatus)
async def get_health_status(
    service: EmailTemplateManager = Depends(get_email_template_service)
):
    """Get email template service health status"""
    try:
        return await service.get_health_status()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@router.post("/templates", response_model=EmailTemplate)
async def create_template(
    template_data: EmailTemplateCreate,
    service: EmailTemplateManager = Depends(get_email_template_service)
):
    """Create a new email template"""
    try:
        template = await service.create_template(
            template_id=template_data.template_id,
            name=template_data.name,
            template_type=template_data.template_type,
            subject_template=template_data.subject_template,
            html_template=template_data.html_template,
            text_template=template_data.text_template,
            variables=template_data.variables,
            default_values=template_data.default_values
        )
        
        logger.info(f"Created email template: {template.template_id}")
        return template
        
    except EmailServiceError as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    template_type: Optional[TemplateType] = None,
    service: EmailTemplateManager = Depends(get_email_template_service)
):
    """List all available email templates"""
    try:
        templates = await service.list_templates(template_type=template_type)
        
        return TemplateListResponse(
            templates=templates,
            total_count=len(templates),
            template_types=[t.value for t in TemplateType]
        )
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/{template_id}", response_model=EmailTemplate)
async def get_template(
    template_id: str,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Get email template by ID"""
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/templates/{template_id}/validate", response_model=TemplateValidationResult)
async def validate_template(
    template_id: str,
    variables: Dict[str, Any],
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Validate template with provided variables"""
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        # Try to render template to validate
        try:
            await service.render_template(
                template_id=template_id,
                variables=variables,
                recipient="test@example.com"
            )
            
            return TemplateValidationResult(
                valid=True,
                variables_found=template.variables,
                missing_variables=[]
            )
            
        except Exception as render_error:
            missing_vars = []
            for var in template.variables:
                if var not in variables and var not in template.default_values:
                    missing_vars.append(var)
            
            return TemplateValidationResult(
                valid=False,
                errors=[str(render_error)],
                variables_found=template.variables,
                missing_variables=missing_vars
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/templates/{template_id}/render", response_model=TemplateRenderResponse)
async def render_template(
    template_id: str,
    render_request: TemplateRenderRequest,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Render email template with variables"""
    try:
        start_time = datetime.now()
        
        message = await service.render_template(
            template_id=render_request.template_id,
            variables=render_request.variables,
            recipient=render_request.recipient,
            tracking_id=render_request.tracking_id
        )
        
        render_time = (datetime.now() - start_time).total_seconds()
        
        return TemplateRenderResponse(
            message=message,
            tracking_id=message.tracking_id,
            variables_used=render_request.variables,
            render_time=render_time
        )
        
    except EmailServiceError as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error rendering template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/attachments/upload", response_model=AttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    attachment_type: AttachmentType = Form(AttachmentType.DOCUMENT),
    description: Optional[str] = Form(None),
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Upload email attachment"""
    try:
        # Validate file size
        content = await file.read()
        if len(content) > service.max_attachment_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {len(content)} bytes (max: {service.max_attachment_size})"
            )
        
        # Generate attachment ID and hash
        attachment_id = str(uuid.uuid4())
        import hashlib
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Store attachment (in production, this would go to cloud storage)
        attachment_dir = service.templates_dir / "attachments"
        attachment_dir.mkdir(exist_ok=True)
        
        file_path = attachment_dir / f"{attachment_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return AttachmentUploadResponse(
            attachment_id=attachment_id,
            filename=file.filename,
            size=len(content),
            content_hash=content_hash
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload attachment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/messages/{message_id}/attachments/file")
async def add_file_attachment(
    message_id: str,
    file_path: str,
    attachment_type: AttachmentType = AttachmentType.DOCUMENT,
    filename: Optional[str] = None,
    description: Optional[str] = None,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Add file attachment to email message"""
    try:
        # This would typically retrieve the message from database
        # For now, we'll create a dummy message
        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test Message",
            tracking_id=message_id
        )
        
        updated_message = await service.add_attachment_from_file(
            message=message,
            file_path=file_path,
            attachment_type=attachment_type,
            filename=filename,
            description=description
        )
        
        return {
            "success": True,
            "message": "Attachment added successfully",
            "attachment_count": len(updated_message.attachments)
        }
        
    except EmailServiceError as e:
        logger.error(f"Failed to add file attachment: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding attachment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reports/pdf")
async def create_pdf_report_attachment(
    report_data: Dict[str, Any],
    filename: str = "contract_analysis_report.pdf",
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Create PDF report attachment from analysis data"""
    try:
        attachment = await service.create_pdf_report_attachment(
            report_data=report_data,
            filename=filename
        )
        
        return {
            "success": True,
            "attachment": {
                "filename": attachment.filename,
                "size": attachment.size,
                "content_type": attachment.content_type,
                "attachment_type": attachment.attachment_type
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create PDF report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reports/docx-redline")
async def create_docx_redline_attachment(
    original_content: str,
    redlined_content: str,
    filename: str = "contract_redlines.docx",
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Create DOCX redline attachment"""
    try:
        attachment = await service.create_docx_redline_attachment(
            original_content=original_content,
            redlined_content=redlined_content,
            filename=filename
        )
        
        return {
            "success": True,
            "attachment": {
                "filename": attachment.filename,
                "size": attachment.size,
                "content_type": attachment.content_type,
                "attachment_type": attachment.attachment_type
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create DOCX redline: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/delivery/track")
async def track_delivery_status(
    tracking_id: str,
    status: str,
    provider: EmailProvider,
    message_id: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Track email delivery status"""
    try:
        from ...services.email_service import EmailStatus as DeliveryStatus
        
        # Convert string status to enum
        try:
            delivery_status = DeliveryStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        record = await service.track_delivery_status(
            tracking_id=tracking_id,
            status=delivery_status,
            provider=provider,
            message_id=message_id,
            error_message=error_message,
            metadata=metadata
        )
        
        return {
            "success": True,
            "tracking_id": record.tracking_id,
            "status": record.status,
            "updated_at": record.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track delivery status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/delivery/{tracking_id}", response_model=EmailDeliveryRecord)
async def get_delivery_status(
    tracking_id: str,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Get delivery status for tracking ID"""
    try:
        record = await service.get_delivery_status(tracking_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Delivery record not found: {tracking_id}")
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get delivery status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics/delivery", response_model=DeliveryStatistics)
async def get_delivery_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    template_id: Optional[str] = None,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Get email delivery statistics"""
    try:
        stats = await service.get_delivery_statistics(
            start_date=start_date,
            end_date=end_date,
            template_id=template_id
        )
        
        return DeliveryStatistics(
            **stats,
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        logger.error(f"Failed to get delivery statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk/send", response_model=BulkEmailResponse)
async def send_bulk_emails(
    bulk_request: BulkEmailRequest,
    background_tasks: BackgroundTasks,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Send bulk emails using template"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Validate template exists
        template = await service.get_template(bulk_request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {bulk_request.template_id}")
        
        # Generate tracking IDs for all recipients
        tracking_ids = []
        for i, recipient in enumerate(bulk_request.recipients):
            tracking_id = f"{job_id}_{i:06d}"
            tracking_ids.append(tracking_id)
        
        # Calculate batches
        total_recipients = len(bulk_request.recipients)
        batches_created = (total_recipients + bulk_request.batch_size - 1) // bulk_request.batch_size
        
        # Estimate completion time (assuming 1 second per email)
        estimated_completion = datetime.now() + timedelta(seconds=total_recipients)
        
        # Start background task for bulk sending
        background_tasks.add_task(
            _process_bulk_email_job,
            job_id,
            bulk_request,
            tracking_ids,
            service
        )
        
        return BulkEmailResponse(
            job_id=job_id,
            total_recipients=total_recipients,
            batches_created=batches_created,
            estimated_completion=estimated_completion,
            tracking_ids=tracking_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start bulk email job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/bulk/{job_id}/status", response_model=BulkEmailStatus)
async def get_bulk_email_status(job_id: str):
    """Get bulk email job status"""
    try:
        # This would typically query a job status database
        # For now, return a mock status
        return BulkEmailStatus(
            job_id=job_id,
            status="processing",
            total_recipients=100,
            processed=50,
            successful=48,
            failed=2,
            progress_percentage=50.0,
            started_at=datetime.now() - timedelta(minutes=5)
        )
        
    except Exception as e:
        logger.error(f"Failed to get bulk email status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    variables: Optional[str] = None,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Preview rendered template with sample data"""
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        # Parse variables if provided
        template_vars = {}
        if variables:
            try:
                template_vars = json.loads(variables)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in variables parameter")
        
        # Use default values for missing variables
        for var in template.variables:
            if var not in template_vars:
                if var in template.default_values:
                    template_vars[var] = template.default_values[var]
                else:
                    # Provide sample values
                    template_vars[var] = f"[{var}]"
        
        # Render template
        message = await service.render_template(
            template_id=template_id,
            variables=template_vars,
            recipient="preview@example.com"
        )
        
        return {
            "subject": message.subject,
            "html_body": message.html_body,
            "text_body": message.text_body,
            "variables_used": template_vars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _process_bulk_email_job(
    job_id: str,
    bulk_request: BulkEmailRequest,
    tracking_ids: List[str],
    service: EnhancedEmailTemplateService
):
    """Background task to process bulk email job"""
    try:
        logger.info(f"Starting bulk email job {job_id} with {len(bulk_request.recipients)} recipients")
        
        # Process recipients in batches
        for i, recipient_data in enumerate(bulk_request.recipients):
            try:
                # Merge common variables with recipient-specific variables
                variables = {**(bulk_request.common_variables or {}), **recipient_data}
                
                # Render and send email
                message = await service.render_template(
                    template_id=bulk_request.template_id,
                    variables=variables,
                    recipient=recipient_data['email'],
                    tracking_id=tracking_ids[i]
                )
                
                # In a real implementation, this would send the email
                logger.debug(f"Processed bulk email {i+1}/{len(bulk_request.recipients)}")
                
                # Add small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to process recipient {i}: {e}")
        
        logger.info(f"Completed bulk email job {job_id}")
        
    except Exception as e:
        logger.error(f"Bulk email job {job_id} failed: {e}")


# Webhook endpoints for delivery tracking

@router.post("/webhooks/delivery/{provider}")
async def delivery_webhook(
    provider: str,
    webhook_data: Dict[str, Any],
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Handle delivery webhooks from email providers"""
    try:
        logger.info(f"Received delivery webhook from {provider}: {webhook_data}")
        
        # Parse webhook data based on provider
        if provider == "gmail":
            # Handle Gmail webhook
            tracking_id = webhook_data.get("tracking_id")
            status = webhook_data.get("status", "unknown")
            
        elif provider == "sendgrid":
            # Handle SendGrid webhook
            tracking_id = webhook_data.get("unique_arg_tracking_id")
            event = webhook_data.get("event")
            status_mapping = {
                "delivered": "delivered",
                "open": "opened",
                "click": "clicked",
                "bounce": "bounced",
                "dropped": "failed"
            }
            status = status_mapping.get(event, "unknown")
            
        else:
            logger.warning(f"Unknown provider webhook: {provider}")
            return {"success": False, "error": "Unknown provider"}
        
        if tracking_id and status != "unknown":
            from ...services.email_service import EmailStatus as DeliveryStatus
            
            try:
                delivery_status = DeliveryStatus(status)
                await service.track_delivery_status(
                    tracking_id=tracking_id,
                    status=delivery_status,
                    provider=EmailProvider(provider),
                    metadata=webhook_data
                )
            except ValueError:
                logger.warning(f"Invalid status in webhook: {status}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Failed to process delivery webhook: {e}")
        return {"success": False, "error": str(e)}


@router.get("/webhooks/open/{tracking_id}")
async def email_open_tracking(
    tracking_id: str,
    service: EnhancedEmailTemplateService = Depends(get_email_template_service)
):
    """Handle email open tracking pixel"""
    try:
        from ...services.email_service import EmailStatus as DeliveryStatus
        
        await service.track_delivery_status(
            tracking_id=tracking_id,
            status=DeliveryStatus.OPENED,
            provider=EmailProvider.SMTP,  # Default provider
            metadata={"source": "tracking_pixel"}
        )
        
        # Return 1x1 transparent pixel
        import base64
        pixel_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        return Response(
            content=pixel_data,
            media_type="image/png",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        logger.error(f"Failed to track email open: {e}")
        # Still return pixel even if tracking fails
        import base64
        pixel_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        return Response(content=pixel_data, media_type="image/png")


# Export router
__all__ = ["router"]