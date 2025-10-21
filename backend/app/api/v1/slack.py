"""
Slack integration API endpoints for job application tracking notifications
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...core.auth import get_current_user
from ...core.logging import get_logger
from ...models.database_models import User
from ...services.slack_service import EnhancedSlackService as SlackService
from ...models.database_models import UserNotificationPreference as NotificationPreference

logger = get_logger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])


class SlackNotificationRequest(BaseModel):
    """Request model for sending Slack notifications"""
    
    title: str
    message: str
    priority: str = "normal"
    channel: Optional[str] = None


class ContractAnalysisNotificationRequest(BaseModel):
    """Request model for job application tracking notifications"""
    
    contract_name: str
    risk_score: float
    risky_clauses: List[Dict]
    analysis_summary: str
    analysis_url: Optional[str] = None


class NotificationPreferenceRequest(BaseModel):
    """Request model for notification preferences"""
    
    notification_type: str
    channel_id: str
    is_enabled: bool = True


class CollaborativeWorkflowRequest(BaseModel):
    """Request model for collaborative workflow notifications"""
    
    workflow_type: str
    contract_name: str
    collaborators: List[str]
    workflow_url: Optional[str] = None


@router.post("/send-notification")
async def send_notification(
    request: SlackNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a general notification to Slack"""
    try:
        slack_service = SlackService()
        
        success = await slack_service.send_notification(
            title=request.title,
            message=request.message,
            priority=request.priority,
            channel=request.channel
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send Slack notification")
        
        return {"success": True, "message": "Notification sent successfully"}
        
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-contract-analysis-alert")
async def send_contract_analysis_alert(
    request: ContractAnalysisNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Send job application tracking alert to Slack"""
    try:
        slack_service = SlackService()
        
        success = await slack_service.send_contract_analysis_alert(
            user_id=current_user.id,
            contract_name=request.contract_name,
            risk_score=request.risk_score,
            risky_clauses=request.risky_clauses,
            analysis_summary=request.analysis_summary,
            analysis_url=request.analysis_url
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send job application tracking alert")
        
        return {"success": True, "message": "Contract analysis alert sent successfully"}
        
    except Exception as e:
        logger.error(f"Error sending job application tracking alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-collaborative-workflow")
async def send_collaborative_workflow_notification(
    request: CollaborativeWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """Send collaborative workflow notification to Slack"""
    try:
        slack_service = SlackService()
        
        success = await slack_service.send_collaborative_workflow_notification(
            workflow_type=request.workflow_type,
            contract_name=request.contract_name,
            initiator=current_user.username,
            collaborators=request.collaborators,
            workflow_url=request.workflow_url
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send collaborative workflow notification")
        
        return {"success": True, "message": "Collaborative workflow notification sent successfully"}
        
    except Exception as e:
        logger.error(f"Error sending collaborative workflow notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels")
async def get_channels(current_user: User = Depends(get_current_user)):
    """Get available Slack channels"""
    try:
        slack_service = SlackService()
        channels = await slack_service.get_channels()
        
        return {"channels": channels}
        
    except Exception as e:
        logger.error(f"Error getting Slack channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channels")
async def create_channel(
    channel_name: str,
    is_private: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Create a new Slack channel"""
    try:
        slack_service = SlackService()
        channel = await slack_service.create_channel(channel_name, is_private)
        
        if not channel:
            raise HTTPException(status_code=500, detail="Failed to create Slack channel")
        
        return {"success": True, "channel": channel}
        
    except Exception as e:
        logger.error(f"Error creating Slack channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification-preferences")
async def create_notification_preference(
    request: NotificationPreferenceRequest,
    current_user: User = Depends(get_current_user)
):
    """Create or update notification preference"""
    try:
        slack_service = SlackService()
        
        success = await slack_service.update_user_notification_preference(
            user_id=current_user.id,
            notification_type=request.notification_type,
            channel_id=request.channel_id,
            is_enabled=request.is_enabled
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update notification preference")
        
        return {"success": True, "message": "Notification preference updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating notification preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification-preferences")
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
    """Get user's notification preferences"""
    try:
        slack_service = SlackService()
        preferences = await slack_service.get_user_notification_preferences(current_user.id)
        
        return {"preferences": preferences}
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_connection(current_user: User = Depends(get_current_user)):
    """Test Slack connection"""
    try:
        slack_service = SlackService()
        result = await slack_service.test_connection()
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing Slack connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def handle_slack_webhook(request: Request):
    """Handle incoming Slack webhooks for interactive messages"""
    try:
        payload = await request.json()
        
        slack_service = SlackService()
        await slack_service.handle_interactive_webhook(payload)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error handling Slack webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))