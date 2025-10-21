"""
Notification manager for sending various types of notifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Manager for sending notifications via various channels."""
    
    def __init__(self):
        pass
    
    async def send_contract_analysis_complete(
        self,
        user_id: str,
        contract_name: str,
        risk_score: float,
        risky_clauses: List[Dict[str, Any]],
        analysis_summary: str,
        analysis_url: str,
        user_email: Optional[str] = None
    ):
        """Send notification when job application tracking is complete."""
        try:
            logger.info(f"Sending job application tracking completion notification for {contract_name}")
            
            # Prepare notification data
            notification_data = {
                "type": "contract_analysis_complete",
                "user_id": user_id,
                "contract_name": contract_name,
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "risky_clauses_count": len(risky_clauses),
                "analysis_summary": analysis_summary,
                "analysis_url": analysis_url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send email notification if email is provided
            if user_email:
                await self._send_email_notification(user_email, notification_data)
            
            # Send in-app notification
            await self._send_in_app_notification(user_id, notification_data)
            
            # Send Slack notification if configured
            await self._send_slack_notification(notification_data)
            
            logger.info(f"Contract analysis completion notifications sent for {contract_name}")
            
        except Exception as e:
            logger.error(f"Failed to send job application tracking completion notification: {e}", exc_info=True)
    
    async def send_high_risk_alert(
        self,
        contract_name: str,
        risk_score: float,
        urgent_clauses: List[Dict[str, Any]]
    ):
        """Send high-risk alert notification."""
        try:
            logger.info(f"Sending high-risk alert for {contract_name} (score: {risk_score})")
            
            # Prepare alert data
            alert_data = {
                "type": "high_risk_alert",
                "contract_name": contract_name,
                "risk_score": risk_score,
                "urgent_clauses_count": len(urgent_clauses),
                "urgent_clauses": urgent_clauses,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send urgent notifications
            await self._send_urgent_email_alert(alert_data)
            await self._send_urgent_slack_alert(alert_data)
            
            logger.info(f"High-risk alert sent for {contract_name}")
            
        except Exception as e:
            logger.error(f"Failed to send high-risk alert: {e}", exc_info=True)
    
    async def send_batch_completion_notification(
        self,
        batch_id: str,
        total_items: int,
        successful_items: int,
        failed_items: int
    ):
        """Send batch processing completion notification."""
        try:
            logger.info(f"Sending batch completion notification for {batch_id}")
            
            # Prepare notification data
            notification_data = {
                "type": "batch_completion",
                "batch_id": batch_id,
                "total_items": total_items,
                "successful_items": successful_items,
                "failed_items": failed_items,
                "success_rate": (successful_items / total_items * 100) if total_items > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send notifications
            await self._send_batch_email_notification(notification_data)
            await self._send_batch_slack_notification(notification_data)
            
            logger.info(f"Batch completion notification sent for {batch_id}")
            
        except Exception as e:
            logger.error(f"Failed to send batch completion notification: {e}", exc_info=True)
    
    async def send_task_completion_notification(self, notification_data: Dict[str, Any]):
        """Send task completion notification."""
        try:
            logger.info(f"Sending task completion notification for {notification_data.get('task_id')}")
            
            # Prepare notification
            notification_data.update({
                "type": "task_completion",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send notifications based on task type and user preferences
            await self._send_task_email_notification(notification_data)
            await self._send_task_slack_notification(notification_data)
            await self._send_task_webhook_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send task completion notification: {e}", exc_info=True)
    
    async def send_task_failure_notification(self, notification_data: Dict[str, Any]):
        """Send task failure notification."""
        try:
            logger.info(f"Sending task failure notification for {notification_data.get('task_id')}")
            
            # Prepare notification
            notification_data.update({
                "type": "task_failure",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send urgent notifications for failures
            await self._send_urgent_task_notification(notification_data)
            await self._send_task_webhook_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send task failure notification: {e}", exc_info=True)
    
    async def send_task_cancellation_notification(self, notification_data: Dict[str, Any]):
        """Send task cancellation notification."""
        try:
            logger.info(f"Sending task cancellation notification for {notification_data.get('task_id')}")
            
            # Prepare notification
            notification_data.update({
                "type": "task_cancellation",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send notifications
            await self._send_task_email_notification(notification_data)
            await self._send_task_webhook_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send task cancellation notification: {e}", exc_info=True)
    
    async def send_task_retry_notification(self, notification_data: Dict[str, Any]):
        """Send task retry notification."""
        try:
            logger.info(f"Sending task retry notification for {notification_data.get('task_id')}")
            
            # Prepare notification
            notification_data.update({
                "type": "task_retry",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send notifications (usually less urgent than failures)
            await self._send_task_slack_notification(notification_data)
            await self._send_task_webhook_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send task retry notification: {e}", exc_info=True)
    
    async def _send_email_notification(self, email: str, data: Dict[str, Any]):
        """Send email notification."""
        try:
            # This would integrate with the email service
            logger.info(f"Sending email notification to {email}")
            
            # For now, just log the notification
            logger.info(f"Email notification data: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _send_in_app_notification(self, user_id: str, data: Dict[str, Any]):
        """Send in-app notification."""
        try:
            # This would integrate with the WebSocket service for real-time notifications
            logger.info(f"Sending in-app notification to user {user_id}")
            
            # For now, just log the notification
            logger.info(f"In-app notification data: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send in-app notification: {e}")
    
    async def _send_slack_notification(self, data: Dict[str, Any]):
        """Send Slack notification."""
        try:
            # This would integrate with the Slack service
            logger.info("Sending Slack notification")
            
            # For now, just log the notification
            logger.info(f"Slack notification data: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_urgent_email_alert(self, data: Dict[str, Any]):
        """Send urgent email alert."""
        try:
            logger.info("Sending urgent email alert")
            
            # For now, just log the alert
            logger.warning(f"URGENT EMAIL ALERT: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send urgent email alert: {e}")
    
    async def _send_urgent_slack_alert(self, data: Dict[str, Any]):
        """Send urgent Slack alert."""
        try:
            logger.info("Sending urgent Slack alert")
            
            # For now, just log the alert
            logger.warning(f"URGENT SLACK ALERT: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send urgent Slack alert: {e}")
    
    async def _send_batch_email_notification(self, data: Dict[str, Any]):
        """Send batch processing email notification."""
        try:
            logger.info("Sending batch email notification")
            
            # For now, just log the notification
            logger.info(f"Batch email notification: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send batch email notification: {e}")
    
    async def _send_batch_slack_notification(self, data: Dict[str, Any]):
        """Send batch processing Slack notification."""
        try:
            logger.info("Sending batch Slack notification")
            
            # For now, just log the notification
            logger.info(f"Batch Slack notification: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send batch Slack notification: {e}")
    
    async def _send_task_email_notification(self, data: Dict[str, Any]):
        """Send task-related email notification."""
        try:
            logger.info(f"Sending task email notification: {data.get('type')}")
            
            # For now, just log the notification
            logger.info(f"Task email notification: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send task email notification: {e}")
    
    async def _send_task_slack_notification(self, data: Dict[str, Any]):
        """Send task-related Slack notification."""
        try:
            logger.info(f"Sending task Slack notification: {data.get('type')}")
            
            # For now, just log the notification
            logger.info(f"Task Slack notification: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send task Slack notification: {e}")
    
    async def _send_task_webhook_notification(self, data: Dict[str, Any]):
        """Send task-related webhook notification."""
        try:
            logger.info(f"Sending task webhook notification: {data.get('type')}")
            
            # For now, just log the notification
            logger.info(f"Task webhook notification: {data}")
            
        except Exception as e:
            logger.error(f"Failed to send task webhook notification: {e}")
    
    async def _send_urgent_task_notification(self, data: Dict[str, Any]):
        """Send urgent task notification (for failures)."""
        try:
            logger.warning(f"URGENT TASK NOTIFICATION: {data}")
            
            # Send via multiple channels for urgent notifications
            await self._send_task_email_notification(data)
            await self._send_task_slack_notification(data)
            
        except Exception as e:
            logger.error(f"Failed to send urgent task notification: {e}")
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level based on score."""
        if risk_score >= 8.0:
            return "Critical"
        elif risk_score >= 6.0:
            return "High"
        elif risk_score >= 4.0:
            return "Medium"
        else:
            return "Low"


# Global service instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager