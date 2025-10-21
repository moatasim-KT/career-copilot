"""
DocuSign API endpoints for electronic signature workflows.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from ...core.auth import get_current_user
from ...core.database import get_db_session
from ...core.logging import get_logger
from ...models.api_models import User
from ...repositories.contract_repository import ContractRepository
from ...repositories.docusign_envelope_repository import DocuSignEnvelopeRepository
from ...services.docusign_service import DocuSignService, DocuSignRecipient

logger = get_logger(__name__)
router = APIRouter(prefix="/docusign", tags=["docusign"])


class CreateEnvelopeRequest(BaseModel):
    """Request model for creating DocuSign envelope"""
    contract_analysis_id: UUID
    recipients: List[Dict[str, str]]  # [{"email": "...", "name": "..."}]
    email_subject: str = "Contract for Signature"
    email_message: str = "Please review and sign the attached contract."


class EnvelopeStatusResponse(BaseModel):
    """Response model for envelope status"""
    envelope_id: str
    status: str
    created_date: Optional[str] = None
    sent_date: Optional[str] = None
    completed_date: Optional[str] = None
    recipients: Optional[List[Dict]] = None


class SigningUrlRequest(BaseModel):
    """Request model for generating signing URL"""
    envelope_id: str
    recipient_email: EmailStr
    recipient_name: str
    return_url: str
    client_user_id: Optional[str] = None


class SigningUrlResponse(BaseModel):
    """Response model for signing URL"""
    signing_url: str
    expires_at: Optional[str] = None


class WebhookPayload(BaseModel):
    """DocuSign webhook payload model"""
    event: str
    apiVersion: str
    uri: str
    retryCount: int
    configurationId: int
    generatedDateTime: str
    data: Dict


@router.get("/auth-url")
async def get_authorization_url(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Get DocuSign authorization URL for OAuth setup"""
    try:
        docusign_service = DocuSignService()
        auth_url = docusign_service.get_authorization_url()
        
        if not auth_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DocuSign service is not enabled"
            )
        
        return {
            "authorization_url": auth_url,
            "message": "Please visit this URL to authorize DocuSign access"
        }
    except Exception as e:
        logger.error(f"Failed to get DocuSign authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.post("/oauth/callback")
async def handle_oauth_callback(
    code: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Handle DocuSign OAuth callback"""
    try:
        docusign_service = DocuSignService()
        success = await docusign_service.handle_oauth_callback(code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process OAuth callback"
            )
        
        return {"message": "DocuSign authorization successful"}
    except Exception as e:
        logger.error(f"Failed to handle DocuSign OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process OAuth callback"
        )


@router.post("/envelopes", response_model=Dict[str, str])
async def create_envelope(
    request: CreateEnvelopeRequest,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> Dict[str, str]:
    """Create DocuSign envelope for contract signing"""
    try:
        # Verify job application tracking exists and belongs to user
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(request.contract_analysis_id)
        
        if not contract_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract analysis not found"
            )
        
        if contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this job application tracking"
            )
        
        # Get contract content (assuming it's stored as text or we have the file)
        if not contract_analysis.contract_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract text not available for signing"
            )
        
        # Convert contract text to PDF bytes (simplified - in production you'd use proper PDF generation)
        contract_content = contract_analysis.contract_text.encode('utf-8')
        
        # Create DocuSign envelope
        docusign_service = DocuSignService()
        envelope_id = await docusign_service.create_contract_envelope(
            contract_analysis_id=str(request.contract_analysis_id),
            contract_name=contract_analysis.filename,
            contract_content=contract_content,
            recipients=request.recipients,
            subject=request.email_subject,
            message=request.email_message
        )
        
        if not envelope_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create DocuSign envelope"
            )
        
        return {
            "envelope_id": envelope_id,
            "message": "Envelope created and sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create DocuSign envelope: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create envelope"
        )


@router.get("/envelopes/{envelope_id}/status", response_model=EnvelopeStatusResponse)
async def get_envelope_status(
    envelope_id: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> EnvelopeStatusResponse:
    """Get DocuSign envelope status"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        # Get status from DocuSign
        docusign_service = DocuSignService()
        status_data = await docusign_service.get_envelope_status(envelope_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get envelope status from DocuSign"
            )
        
        # Get recipients info
        recipients_data = await docusign_service.get_envelope_recipients(envelope_id)
        
        return EnvelopeStatusResponse(
            envelope_id=envelope_id,
            status=status_data.get("status", "unknown"),
            created_date=status_data.get("createdDateTime"),
            sent_date=status_data.get("sentDateTime"),
            completed_date=status_data.get("completedDateTime"),
            recipients=recipients_data.get("signers", []) if recipients_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get envelope status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get envelope status"
        )


@router.post("/envelopes/{envelope_id}/signing-url", response_model=SigningUrlResponse)
async def get_signing_url(
    envelope_id: str,
    request: SigningUrlRequest,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> SigningUrlResponse:
    """Generate signing URL for recipient"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        # Generate signing URL
        docusign_service = DocuSignService()
        signing_url = await docusign_service.create_embedded_signing_view(
            envelope_id=envelope_id,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            return_url=request.return_url,
            client_user_id=request.client_user_id
        )
        
        if not signing_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate signing URL"
            )
        
        return SigningUrlResponse(
            signing_url=signing_url,
            expires_at=None  # DocuSign URLs typically expire in 5 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate signing URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signing URL"
        )


@router.post("/envelopes/{envelope_id}/void")
async def void_envelope(
    envelope_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> Dict[str, str]:
    """Void DocuSign envelope"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        # Void envelope
        docusign_service = DocuSignService()
        success = await docusign_service.void_envelope(envelope_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to void envelope"
            )
        
        # Update status in database
        await envelope_repo.update_envelope_status(envelope_id, "voided")
        
        return {"message": "Envelope voided successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to void envelope: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to void envelope"
        )


@router.post("/envelopes/{envelope_id}/resend")
async def resend_envelope(
    envelope_id: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> Dict[str, str]:
    """Resend DocuSign envelope to recipients"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        # Resend envelope
        docusign_service = DocuSignService()
        success = await docusign_service.resend_envelope(envelope_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend envelope"
            )
        
        return {"message": "Envelope resent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend envelope: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend envelope"
        )


@router.get("/envelopes/{envelope_id}/download")
async def download_completed_document(
    envelope_id: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
):
    """Download completed document with signatures"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        # Download document
        docusign_service = DocuSignService()
        document_content = await docusign_service.download_completed_document(envelope_id)
        
        if not document_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download document"
            )
        
        from fastapi.responses import Response
        
        return Response(
            content=document_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=signed_{contract_analysis.filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    payload: WebhookPayload
) -> Dict[str, Any]:
    """Handle DocuSign webhook notifications with enhanced processing"""
    try:
        # Get signature from headers for verification
        signature = request.headers.get("X-DocuSign-Signature-1")
        
        # Log the webhook for debugging
        logger.info(f"Received DocuSign webhook: {payload.event}")
        
        # Extract envelope data from webhook
        envelope_data = payload.data
        
        # Handle the webhook with enhanced processing
        docusign_service = DocuSignService()
        result = await docusign_service.handle_webhook(envelope_data, signature)
        
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "message": "Webhook processed successfully",
            "envelope_id": result.get("envelope_id"),
            "event": result.get("event"),
            "processed": result.get("processed", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process DocuSign webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[Dict]]:
    """Get available DocuSign templates"""
    try:
        docusign_service = DocuSignService()
        templates = await docusign_service.get_templates()
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Failed to get DocuSign templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get templates"
        )


@router.get("/account")
async def get_account_info(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get DocuSign account information"""
    try:
        docusign_service = DocuSignService()
        account_info = await docusign_service.get_account_info()
        
        if not account_info:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DocuSign service not available or not authenticated"
            )
        
        return account_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get DocuSign account info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get account information"
        )


@router.get("/test")
async def test_connection(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Test DocuSign connection"""
    try:
        docusign_service = DocuSignService()
        result = await docusign_service.test_connection()
        return result
        
    except Exception as e:
        logger.error(f"Failed to test DocuSign connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test connection"
        )


# Enhanced Template Management Endpoints

class CreateTemplateRequest(BaseModel):
    """Request model for creating DocuSign template"""
    name: str
    description: str
    documents: List[Dict[str, Any]]  # Document data
    recipients: List[Dict[str, str]]  # Recipient data
    email_subject: str = ""
    email_blurb: str = ""


class UpdateTemplateRequest(BaseModel):
    """Request model for updating DocuSign template"""
    name: Optional[str] = None
    description: Optional[str] = None
    email_subject: Optional[str] = None
    email_blurb: Optional[str] = None


@router.post("/templates", response_model=Dict[str, str])
async def create_template(
    request: CreateTemplateRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Create a new DocuSign template"""
    try:
        docusign_service = DocuSignService()
        
        # Convert request data to service models
        from ...services.docusign_service import DocuSignDocument, DocuSignRecipient
        
        documents = [
            DocuSignDocument(**doc_data) for doc_data in request.documents
        ]
        
        recipients = [
            DocuSignRecipient(**recipient_data) for recipient_data in request.recipients
        ]
        
        template_id = await docusign_service.create_template(
            name=request.name,
            description=request.description,
            documents=documents,
            recipients=recipients,
            email_subject=request.email_subject,
            email_blurb=request.email_blurb
        )
        
        if not template_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )
        
        return {
            "template_id": template_id,
            "message": "Template created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create DocuSign template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update an existing DocuSign template"""
    try:
        docusign_service = DocuSignService()
        
        success = await docusign_service.update_template(
            template_id=template_id,
            name=request.name,
            description=request.description,
            email_subject=request.email_subject,
            email_blurb=request.email_blurb
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update template"
            )
        
        return {"message": "Template updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update DocuSign template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a DocuSign template"""
    try:
        docusign_service = DocuSignService()
        
        success = await docusign_service.delete_template(template_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template"
            )
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete DocuSign template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


# Workflow Automation Endpoints

class CreateWorkflowRequest(BaseModel):
    """Request model for creating signing workflow"""
    workflow_name: str
    documents: List[Dict[str, Any]]
    workflow_steps: List[Dict[str, Any]]
    email_subject: str
    email_blurb: str
    custom_fields: Optional[Dict[str, Any]] = None


class BulkSendRequest(BaseModel):
    """Request model for bulk envelope sending"""
    template_id: str
    bulk_recipients: List[List[Dict[str, str]]]
    email_subject: str
    email_blurb: str
    custom_fields_list: Optional[List[Dict[str, Any]]] = None


@router.post("/workflows", response_model=Dict[str, str])
async def create_signing_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Create a multi-step signing workflow"""
    try:
        docusign_service = DocuSignService()
        
        # Convert request data to service models
        from ...services.docusign_service import DocuSignDocument
        
        documents = [
            DocuSignDocument(**doc_data) for doc_data in request.documents
        ]
        
        envelope_id = await docusign_service.create_signing_workflow(
            workflow_name=request.workflow_name,
            documents=documents,
            workflow_steps=request.workflow_steps,
            email_subject=request.email_subject,
            email_blurb=request.email_blurb,
            custom_fields=request.custom_fields
        )
        
        if not envelope_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create signing workflow"
            )
        
        return {
            "envelope_id": envelope_id,
            "message": "Signing workflow created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create signing workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create signing workflow"
        )


@router.post("/bulk-send", response_model=Dict[str, Any])
async def bulk_send_envelopes(
    request: BulkSendRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send multiple envelopes in bulk"""
    try:
        docusign_service = DocuSignService()
        
        # Convert request data to service models
        from ...services.docusign_service import DocuSignRecipient
        
        bulk_recipients = []
        for recipient_list in request.bulk_recipients:
            recipients = [
                DocuSignRecipient(**recipient_data) for recipient_data in recipient_list
            ]
            bulk_recipients.append(recipients)
        
        envelope_ids = await docusign_service.bulk_send_envelopes(
            template_id=request.template_id,
            bulk_recipients=bulk_recipients,
            email_subject=request.email_subject,
            email_blurb=request.email_blurb,
            custom_fields_list=request.custom_fields_list
        )
        
        successful_sends = sum(1 for eid in envelope_ids if eid is not None)
        
        return {
            "envelope_ids": envelope_ids,
            "total_envelopes": len(envelope_ids),
            "successful_sends": successful_sends,
            "message": f"Bulk send completed: {successful_sends}/{len(envelope_ids)} successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk send envelopes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk send envelopes"
        )


# Audit and Compliance Endpoints

@router.get("/envelopes/{envelope_id}/audit-trail")
async def get_audit_trail(
    envelope_id: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get complete audit trail for an envelope"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        docusign_service = DocuSignService()
        audit_trail = await docusign_service.store_audit_trail(envelope_id)
        
        if not audit_trail:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve audit trail"
            )
        
        return audit_trail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit trail"
        )


@router.get("/envelopes/{envelope_id}/certificate")
async def get_certificate_of_completion(
    envelope_id: str,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
):
    """Get certificate of completion for an envelope"""
    try:
        # Verify user has access to this envelope
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
        
        if not envelope_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found"
            )
        
        # Check if user owns the associated job application tracking
        contract_repo = ContractRepository(db_session)
        contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
        
        if not contract_analysis or contract_analysis.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this envelope"
            )
        
        docusign_service = DocuSignService()
        certificate = await docusign_service.get_certificate_of_completion(envelope_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get certificate of completion"
            )
        
        from fastapi.responses import Response
        
        return Response(
            content=certificate,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{envelope_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get certificate of completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get certificate of completion"
        )


@router.post("/compliance-report")
async def generate_compliance_report(
    envelope_ids: List[str],
    include_documents: bool = False,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Generate compliance report for multiple envelopes"""
    try:
        # Verify user has access to all envelopes
        envelope_repo = DocuSignEnvelopeRepository(db_session)
        contract_repo = ContractRepository(db_session)
        
        accessible_envelope_ids = []
        for envelope_id in envelope_ids:
            envelope_record = await envelope_repo.get_envelope_by_envelope_id(envelope_id)
            if envelope_record:
                contract_analysis = await contract_repo.get_by_id(envelope_record.contract_analysis_id)
                if contract_analysis and contract_analysis.user_id == current_user.id:
                    accessible_envelope_ids.append(envelope_id)
        
        if not accessible_envelope_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible envelopes found"
            )
        
        docusign_service = DocuSignService()
        compliance_report = await docusign_service.get_compliance_report(
            accessible_envelope_ids,
            include_documents
        )
        
        return compliance_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )