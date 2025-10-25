"""
Slack Integration API endpoints.
Provides REST API for Slack integration management and webhooks.
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from ...services.slack_service import (
    EnhancedSlackService, 
    SlackConfiguration, 
    SlackMessage, 
    SlackPriority
)
from ...services.slack_bot_commands import SlackBotCommands
from ...services.analytics_specialized import AnalyticsSpecializedService, SlackEvent, SlackEventType

logger = get_logger(__name__)
router = APIRouter(prefix="/slack", tags=["slack"])

# Global service instances (in production, use dependency injection)
slack_service: Optional[EnhancedSlackService] = None
bot_commands: Optional[SlackBotCommands] = None
analytics_service: Optional[AnalyticsSpecializedService] = None


class SlackMessageRequest(BaseModel):
    """Request model for sending Slack messages"""
    channel: str = Field(..., description="Channel ID or name")
    text: Optional[str] = Field(None, description="Message text")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Block Kit blocks")
    priority: SlackPriority = Field(SlackPriority.NORMAL, description="Message priority")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")


class SlackNotificationRequest(BaseModel):
    """Request model for contract notifications"""
    channel: str = Field(..., description="Channel ID or name")
    contract_name: str = Field(..., description="Contract name")
    risk_score: float = Field(..., ge=0, le=10, description="Risk score (0-10)")
    risk_level: str = Field(..., description="Risk level")
    analysis_summary: str = Field(..., description="Analysis summary")
    risky_clauses: List[str] = Field(default_factory=list, description="Risky clauses")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class SlackConfigurationRequest(BaseModel):
    """Request model for Slack configuration"""
    bot_token: str = Field(..., description="Slack bot token")
    signing_secret: str = Field(..., description="Slack signing secret")
    rate_limit_tier: int = Field(3, ge=1, le=4, description="API rate limit tier")
    enable_interactive_components: bool = Field(True, description="Enable interactive components")
    enable_slash_commands: bool = Field(True, description="Enable slash commands")


async def get_slack_service() -> EnhancedSlackService:
    """Get or initialize Slack service"""
    global slack_service
    if not slack_service:
        settings = get_settings()
        config = SlackConfiguration(
            bot_token=getattr(settings, 'slack_bot_token', 'xoxb-test-token'),
            signing_secret=getattr(settings, 'slack_signing_secret', 'test-secret'),
            rate_limit_tier=getattr(settings, 'slack_rate_limit_tier', 3)
        )
        slack_service = EnhancedSlackService(config)
        await slack_service.initialize()
    return slack_service


async def get_bot_commands() -> SlackBotCommands:
    """Get or initialize bot commands service"""
    global bot_commands
    if not bot_commands:
        service = await get_slack_service()
        bot_commands = SlackBotCommands(service)
    return bot_commands


async def get_analytics_service() -> AnalyticsSpecializedService:
    """Get or initialize analytics service"""
    global analytics_service
    if not analytics_service:
        analytics_service = AnalyticsSpecializedService()
    return analytics_service


def verify_slack_signature(request: Request, body: bytes) -> bool:
    """Verify Slack request signature"""
    try:
        settings = get_settings()
        signing_secret = getattr(settings, 'slack_signing_secret', 'test-secret')
        
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        if not timestamp or not signature:
            return False
        
        # Check timestamp (prevent replay attacks)
        if abs(datetime.now().timestamp() - int(timestamp)) > 300:  # 5 minutes
            return False
        
        # Verify signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected_signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying Slack signature: {e}")
        return False


@router.post("/configure")
async def configure_slack(config: SlackConfigurationRequest):
    """Configure Slack integration"""
    try:
        global slack_service, bot_commands
        
        # Create new configuration
        slack_config = SlackConfiguration(
            bot_token=config.bot_token,
            signing_secret=config.signing_secret,
            rate_limit_tier=config.rate_limit_tier,
            enable_interactive_components=config.enable_interactive_components,
            enable_slash_commands=config.enable_slash_commands
        )
        
        # Initialize new service
        slack_service = EnhancedSlackService(slack_config)
        await slack_service.initialize()
        
        # Initialize bot commands
        bot_commands = SlackBotCommands(slack_service)
        
        return {
            "success": True,
            "message": "Slack integration configured successfully",
            "configuration": {
                "rate_limit_tier": config.rate_limit_tier,
                "interactive_components": config.enable_interactive_components,
                "slash_commands": config.enable_slash_commands
            }
        }
        
    except Exception as e:
        logger.error(f"Error configuring Slack: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.post("/send-message")
async def send_message(message_request: SlackMessageRequest):
    """Send a message to Slack"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Create Slack message
        message = SlackMessage(
            channel=message_request.channel,
            text=message_request.text,
            blocks=message_request.blocks,
            priority=message_request.priority,
            thread_ts=message_request.thread_ts
        )
        
        # Send message
        result = await service.send_message(message)
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"msg_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=message_request.channel,
            metadata={"priority": message_request.priority.value}
        ))
        
        return {
            "success": True,
            "message_ts": result["message_ts"],
            "channel": result["channel"],
            "permalink": result.get("permalink")
        }
        
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        
        # Track failed message
        analytics = await get_analytics_service()
        await analytics.track_slack_event(SlackEvent(
            id=f"msg_fail_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_FAILED,
            timestamp=datetime.now(),
            channel_id=message_request.channel,
            metadata={"error": str(e)}
        ))
        
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/send-contract-notification")
async def send_contract_notification(notification: SlackNotificationRequest):
    """Send job application tracking notification"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Send notification
        result = await service.send_contract_analysis_notification(
            channel=notification.channel,
            contract_name=notification.contract_name,
            risk_score=notification.risk_score,
            risk_level=notification.risk_level,
            analysis_summary=notification.analysis_summary,
            risky_clauses=notification.risky_clauses,
            recommendations=notification.recommendations
        )
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"contract_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=notification.channel,
            metadata={
                "type": "contract_notification",
                "risk_score": notification.risk_score,
                "contract_name": notification.contract_name
            }
        ))
        
        return {
            "success": True,
            "message": "Contract notification sent successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error sending contract notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/send-risk-alert")
async def send_risk_alert(
    channel: str,
    contract_name: str,
    risk_score: float,
    urgent_clauses: List[str],
    alert_level: str = "HIGH"
):
    """Send high-priority risk alert"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Send alert
        result = await service.send_risk_alert(
            channel=channel,
            contract_name=contract_name,
            risk_score=risk_score,
            urgent_clauses=urgent_clauses,
            alert_level=alert_level
        )
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"alert_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=channel,
            metadata={
                "type": "risk_alert",
                "alert_level": alert_level,
                "risk_score": risk_score,
                "contract_name": contract_name
            }
        ))
        
        return {
            "success": True,
            "message": "Risk alert sent successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error sending risk alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")


@router.post("/webhooks/events")
async def handle_slack_events(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack Events API webhooks"""
    try:
        body = await request.body()
        
        # Verify signature (in production)
        # if not verify_slack_signature(request, body):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body.decode('utf-8'))
        
        # Handle URL verification challenge
        if payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge")}
        
        # Handle events
        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            background_tasks.add_task(process_slack_event, event)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Event processing failed")


@router.post("/webhooks/interactions")
async def handle_slack_interactions(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack interactive component webhooks"""
    try:
        body = await request.body()
        
        # Verify signature (in production)
        # if not verify_slack_signature(request, body):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse form data
        form_data = body.decode('utf-8')
        if form_data.startswith('payload='):
            payload_json = form_data[8:]  # Remove 'payload=' prefix
            payload = json.loads(payload_json)
        else:
            payload = json.loads(form_data)
        
        # Handle interaction
        service = await get_slack_service()
        result = await service.handle_interactive_component(payload)
        
        # Track analytics
        analytics = await get_analytics_service()
        await analytics.track_slack_event(SlackEvent(
            id=f"interaction_{datetime.now().timestamp()}",
            event_type=SlackEventType.INTERACTION,
            timestamp=datetime.now(),
            user_id=payload.get("user", {}).get("id"),
            channel_id=payload.get("channel", {}).get("id"),
            metadata={
                "action_id": payload.get("actions", [{}])[0].get("action_id"),
                "callback_id": payload.get("callback_id")
            }
        ))
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling Slack interaction: {e}")
        raise HTTPException(status_code=500, detail="Interaction processing failed")


@router.post("/webhooks/commands")
async def handle_slash_commands(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack slash command webhooks"""
    try:
        body = await request.body()
        
        # Verify signature (in production)
        # if not verify_slack_signature(request, body):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse form data
        form_data = {}
        for item in body.decode('utf-8').split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                form_data[key] = value.replace('+', ' ').replace('%20', ' ')
        
        # Handle command
        commands = await get_bot_commands()
        result = await commands.handle_slash_command(form_data)
        
        # Track analytics
        analytics = await get_analytics_service()
        await analytics.track_slack_event(SlackEvent(
            id=f"command_{datetime.now().timestamp()}",
            event_type=SlackEventType.COMMAND_USED,
            timestamp=datetime.now(),
            user_id=form_data.get("user_id"),
            channel_id=form_data.get("channel_id"),
            metadata={
                "command": form_data.get("command", "").lstrip("/"),
                "text": form_data.get("text", "")
            }
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling slash command: {e}")
        return {
            "response_type": "ephemeral",
            "text": f"❌ Command processing failed: {str(e)}"
        }


@router.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get Slack analytics dashboard data"""
    try:
        analytics = await get_analytics_service()
        dashboard_data = await analytics.get_slack_dashboard_metrics()
        
        return {
            "success": True,
            "dashboard": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/analytics/user/{user_id}")
async def get_user_analytics(user_id: str):
    """Get analytics for a specific user"""
    try:
        analytics = await get_analytics_service()
        user_data = await analytics.get_user_analytics(user_id)
        
        return {
            "success": True,
            "user_analytics": user_data
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")


@router.get("/analytics/channel/{channel_id}")
async def get_channel_analytics(channel_id: str):
    """Get analytics for a specific channel"""
    try:
        analytics = await get_analytics_service()
        channel_data = await analytics.get_channel_analytics(channel_id)
        
        return {
            "success": True,
            "channel_analytics": channel_data
        }
        
    except Exception as e:
        logger.error(f"Error getting channel analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get channel analytics: {str(e)}")


@router.get("/analytics/commands")
async def get_command_analytics():
    """Get analytics for bot commands"""
    try:
        analytics = await get_analytics_service()
        command_data = await analytics.get_command_analytics()
        
        commands = await get_bot_commands()
        command_stats = commands.get_command_statistics()
        
        return {
            "success": True,
            "command_analytics": command_data,
            "command_statistics": command_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting command analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get command analytics: {str(e)}")


@router.post("/analytics/report")
async def generate_analytics_report(
    start_date: datetime,
    end_date: datetime,
    include_details: bool = False
):
    """Generate comprehensive analytics report"""
    try:
        analytics = await get_analytics_service()
        report = await analytics.generate_analytics_report(
            start_date, end_date, include_details
        )
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/health")
async def get_slack_health():
    """Get Slack integration health status"""
    try:
        health_data = {}
        
        # Slack service health
        try:
            service = await get_slack_service()
            health_data["slack_service"] = await service.get_health_status()
        except Exception as e:
            health_data["slack_service"] = {"healthy": False, "error": str(e)}
        
        # Analytics service health
        try:
            analytics = await get_analytics_service()
            health_data["analytics_service"] = await analytics.get_health_status()
        except Exception as e:
            health_data["analytics_service"] = {"healthy": False, "error": str(e)}
        
        # Bot commands health
        try:
            commands = await get_bot_commands()
            health_data["bot_commands"] = {
                "healthy": True,
                "commands_available": len(commands.commands),
                "statistics": commands.get_command_statistics()
            }
        except Exception as e:
            health_data["bot_commands"] = {"healthy": False, "error": str(e)}
        
        # Overall health
        all_healthy = all(
            service_health.get("healthy", False) 
            for service_health in health_data.values()
        )
        
        return {
            "healthy": all_healthy,
            "services": health_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting Slack health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/upload-file")
async def upload_file_to_slack(
    channel: str,
    file_path: str,
    filename: str,
    title: Optional[str] = None,
    initial_comment: Optional[str] = None,
    thread_ts: Optional[str] = None
):
    """Upload a file to Slack channel"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Upload file
        result = await service.upload_file_to_channel(
            channel=channel,
            file_path=file_path,
            filename=filename,
            title=title,
            initial_comment=initial_comment,
            thread_ts=thread_ts
        )
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"file_upload_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=channel,
            metadata={
                "type": "file_upload",
                "filename": filename,
                "file_id": result.get("file_id")
            }
        ))
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error uploading file to Slack: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.post("/upload-contract")
async def upload_contract_to_slack(
    channel: str,
    contract_file_path: str,
    contract_name: str,
    analysis_summary: Optional[str] = None,
    thread_ts: Optional[str] = None
):
    """Upload contract file with analysis context"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Upload contract
        result = await service.upload_contract_file(
            channel=channel,
            contract_file_path=contract_file_path,
            contract_name=contract_name,
            analysis_summary=analysis_summary,
            thread_ts=thread_ts
        )
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"contract_upload_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=channel,
            metadata={
                "type": "contract_upload",
                "contract_name": contract_name,
                "file_id": result.get("file_id")
            }
        ))
        
        return {
            "success": True,
            "message": "Contract uploaded successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error uploading contract to Slack: {e}")
        raise HTTPException(status_code=500, detail=f"Contract upload failed: {str(e)}")


@router.post("/create-approval-workflow")
async def create_approval_workflow(
    channel: str,
    contract_name: str,
    approvers: List[str],
    approval_deadline: Optional[datetime] = None,
    thread_ts: Optional[str] = None
):
    """Create an approval workflow"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        
        # Create workflow
        result = await service.create_approval_workflow(
            channel=channel,
            contract_name=contract_name,
            approvers=approvers,
            approval_deadline=approval_deadline,
            thread_ts=thread_ts
        )
        
        # Track analytics
        await analytics.track_slack_event(SlackEvent(
            id=f"workflow_{datetime.now().timestamp()}",
            event_type=SlackEventType.MESSAGE_SENT,
            timestamp=datetime.now(),
            channel_id=channel,
            metadata={
                "type": "approval_workflow",
                "contract_name": contract_name,
                "workflow_id": result.get("workflow_id"),
                "approvers_count": len(approvers)
            }
        ))
        
        return {
            "success": True,
            "message": "Approval workflow created successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error creating approval workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")


@router.get("/status")
async def get_slack_status():
    """Get Slack integration status and statistics"""
    try:
        service = await get_slack_service()
        analytics = await get_analytics_service()
        commands = await get_bot_commands()
        
        # Get service analytics
        service_analytics = await service.get_analytics()
        dashboard_metrics = await analytics.get_dashboard_metrics()
        command_stats = commands.get_command_statistics()
        
        return {
            "success": True,
            "status": {
                "service_analytics": service_analytics,
                "dashboard_metrics": dashboard_metrics,
                "command_statistics": command_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Slack status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


async def process_slack_event(event: Dict[str, Any]):
    """Process Slack event in background"""
    try:
        analytics = await get_analytics_service()
        
        event_type = event.get("type")
        user_id = event.get("user")
        channel_id = event.get("channel")
        
        # Map Slack events to our event types
        if event_type == "message":
            await analytics.track_slack_event(SlackEvent(
                id=f"event_{datetime.now().timestamp()}",
                event_type=SlackEventType.MESSAGE_SENT,
                timestamp=datetime.now(),
                user_id=user_id,
                channel_id=channel_id,
                metadata={"slack_event_type": event_type}
            ))
        elif event_type == "member_joined_channel":
            await analytics.track_slack_event(SlackEvent(
                id=f"join_{datetime.now().timestamp()}",
                event_type=SlackEventType.USER_JOINED,
                timestamp=datetime.now(),
                user_id=user_id,
                channel_id=channel_id,
                metadata={"slack_event_type": event_type}
            ))
        
        logger.debug(f"Processed Slack event: {event_type}")
        
    except Exception as e:
        logger.error(f"Error processing Slack event: {e}")