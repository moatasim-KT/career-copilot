"""
SendGrid Webhook Handler for Email Delivery Tracking
Handles delivery status updates from SendGrid webhooks.
"""

import json
import hashlib
import hmac
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger
from ...services.sendgrid_service import SendGridService, EmailDeliveryStatus
from ...core.exceptions import EmailServiceError

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks/sendgrid", tags=["sendgrid", "webhooks"])


class SendGridEvent(BaseModel):
    """SendGrid webhook event model"""
    email: str = Field(..., description="Recipient email address")
    timestamp: int = Field(..., description="Unix timestamp of the event")
    event: str = Field(..., description="Event type")
    sg_event_id: str = Field(..., description="SendGrid event ID")
    sg_message_id: str = Field(..., description="SendGrid message ID")
    useragent: Optional[str] = Field(None, description="User agent (for opens/clicks)")
    ip: Optional[str] = Field(None, description="IP address")
    url: Optional[str] = Field(None, description="Clicked URL (for click events)")
    reason: Optional[str] = Field(None, description="Bounce/drop reason")
    status: Optional[str] = Field(None, description="Bounce status")
    type: Optional[str] = Field(None, description="Bounce type")
    category: Optional[List[str]] = Field(None, description="Email categories")
    asm_group_id: Optional[int] = Field(None, description="ASM group ID")
    marketing_campaign_id: Optional[str] = Field(None, description="Marketing campaign ID")
    marketing_campaign_name: Optional[str] = Field(None, description="Marketing campaign name")
    custom_args: Optional[Dict[str, str]] = Field(None, description="Custom arguments")


class SendGridWebhookPayload(BaseModel):
    """SendGrid webhook payload containing multiple events"""
    events: List[SendGridEvent] = Field(..., description="List of events")


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    public_key: str
) -> bool:
    """Verify SendGrid webhook signature"""
    try:
        # SendGrid uses ECDSA signature verification
        # This is a simplified version - in production, use proper ECDSA verification
        expected_signature = base64.b64encode(
            hmac.new(
                public_key.encode(),
                payload,
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False


async def get_sendgrid_service() -> SendGridService:
    """Get SendGrid service instance"""
    # This would typically be injected via dependency injection
    # For now, create a new instance
    return SendGridService()


@router.post("/events")
async def handle_sendgrid_webhook(
    request: Request,
    x_twilio_email_event_webhook_signature: Optional[str] = Header(None),
    x_twilio_email_event_webhook_timestamp: Optional[str] = Header(None),
    sendgrid_service: SendGridService = Depends(get_sendgrid_service)
):
    """Handle SendGrid webhook events for email delivery tracking"""
    
    try:
        # Get raw payload
        payload = await request.body()
        
        # Verify webhook signature if configured
        settings = get_settings()
        webhook_public_key = getattr(settings, "sendgrid_webhook_public_key", None)
        
        if webhook_public_key and x_twilio_email_event_webhook_signature:
            if not verify_webhook_signature(
                payload,
                x_twilio_email_event_webhook_signature,
                webhook_public_key
            ):
                logger.warning("Invalid SendGrid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse JSON payload
        try:
            events_data = json.loads(payload.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process each event
        processed_events = []
        
        for event_data in events_data:
            try:
                event = SendGridEvent(**event_data)
                await process_sendgrid_event(event, sendgrid_service)
                processed_events.append(event.sg_event_id)
                
            except Exception as e:
                logger.error(f"Failed to process event {event_data.get('sg_event_id', 'unknown')}: {e}")
                # Continue processing other events
                continue
        
        logger.info(f"Processed {len(processed_events)} SendGrid webhook events")
        
        return {
            "status": "success",
            "processed_events": len(processed_events),
            "event_ids": processed_events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SendGrid webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def process_sendgrid_event(
    event: SendGridEvent,
    sendgrid_service: SendGridService
):
    """Process individual SendGrid event"""
    
    # Extract tracking ID from custom args
    tracking_id = None
    if event.custom_args:
        tracking_id = event.custom_args.get("tracking_id")
    
    if not tracking_id:
        logger.warning(f"No tracking ID found in event {event.sg_event_id}")
        return
    
    # Map SendGrid event types to our status enum
    event_status_mapping = {
        "delivered": EmailDeliveryStatus.DELIVERED,
        "opened": EmailDeliveryStatus.OPENED,
        "clicked": EmailDeliveryStatus.CLICKED,
        "bounced": EmailDeliveryStatus.BOUNCED,
        "dropped": EmailDeliveryStatus.DROPPED,
        "spam_report": EmailDeliveryStatus.SPAM_REPORT,
        "unsubscribe": EmailDeliveryStatus.UNSUBSCRIBE,
        "blocked": EmailDeliveryStatus.BLOCKED,
        "deferred": EmailDeliveryStatus.DEFERRED
    }
    
    status = event_status_mapping.get(event.event)
    if not status:
        logger.warning(f"Unknown event type: {event.event}")
        return
    
    # Convert timestamp
    event_timestamp = datetime.fromtimestamp(event.timestamp)
    
    # Prepare error message for bounces/drops
    error_message = None
    if event.event in ["bounced", "dropped", "blocked"]:
        error_parts = []
        if event.reason:
            error_parts.append(f"Reason: {event.reason}")
        if event.status:
            error_parts.append(f"Status: {event.status}")
        if event.type:
            error_parts.append(f"Type: {event.type}")
        error_message = "; ".join(error_parts) if error_parts else "Unknown error"
    
    # Update delivery status
    try:
        await sendgrid_service.update_delivery_status(
            tracking_id=tracking_id,
            status=status,
            timestamp=event_timestamp,
            error_message=error_message
        )
        
        logger.info(f"Updated delivery status for {tracking_id}: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update delivery status for {tracking_id}: {e}")
        raise


@router.get("/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "ok",
        "message": "SendGrid webhook endpoint is accessible",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/test-event")
async def test_webhook_event(
    test_event: Dict[str, Any],
    sendgrid_service: SendGridService = Depends(get_sendgrid_service)
):
    """Test endpoint for webhook event processing (development only)"""
    
    settings = get_settings()
    if getattr(settings, "environment", "development") != "development":
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        # Create test event
        event = SendGridEvent(**test_event)
        await process_sendgrid_event(event, sendgrid_service)
        
        return {
            "status": "success",
            "message": "Test event processed successfully",
            "event_id": event.sg_event_id
        }
        
    except Exception as e:
        logger.error(f"Test event processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Test event processing failed: {e}")


# Health check endpoint
@router.get("/health")
async def webhook_health_check():
    """Health check for webhook endpoint"""
    return {
        "status": "healthy",
        "service": "sendgrid_webhooks",
        "timestamp": datetime.now().isoformat()
    }