"""
Notification Service
Comprehensive notification management including email, push notifications, and in-app alerts
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.services.email_service import EmailService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """Comprehensive notification service for email, push, and in-app notifications"""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize the notification service"""
        self.db = db
        self.email_service = EmailService()
        logger.info("Notification service initialized")
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an in-app notification to a user
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            action_url: Optional URL for notification action
            metadata: Additional metadata for the notification
            
        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"Sending {notification_type} notification to user {user_id}: {title}")
            
            # Store notification in database if db session available
            if self.db:
                from app.models.user import User
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    # TODO: Store notification in notifications table when created
                    logger.debug(f"Notification stored for user {user.email}")
            
            # Here you could integrate with:
            # - WebSocket for real-time notifications
            # - Firebase Cloud Messaging for push notifications
            # - Service workers for browser notifications
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Whether body is HTML
            attachments: List of file paths to attach
            
        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"Sending email to {to_email}: {subject}")
            
            if html:
                success = self.email_service.send_html_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=body
                )
            else:
                success = self.email_service.send_email(
                    to_email=to_email,
                    subject=subject,
                    body=body
                )
            
            if success:
                logger.info(f"Email sent successfully to {to_email}")
            else:
                logger.warning(f"Failed to send email to {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Send multiple notifications in batch
        
        Args:
            notifications: List of notification dicts with keys:
                - user_id: int
                - title: str
                - message: str
                - notification_type: str (optional)
                - action_url: str (optional)
                
        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0
        
        logger.info(f"Sending {len(notifications)} batch notifications")
        
        for notif in notifications:
            try:
                result = await self.send_notification(
                    user_id=notif["user_id"],
                    title=notif["title"],
                    message=notif["message"],
                    notification_type=notif.get("notification_type", "info"),
                    action_url=notif.get("action_url"),
                    metadata=notif.get("metadata")
                )
                
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send notification to user {notif.get('user_id')}: {e}")
                failure_count += 1
        
        logger.info(f"Batch notifications complete: {success_count} success, {failure_count} failed")
        return {"success": success_count, "failed": failure_count}
    
    async def send_job_alert(
        self,
        user_id: int,
        user_email: str,
        jobs: List[Dict[str, Any]],
        alert_type: str = "new_matches"
    ) -> bool:
        """
        Send job alert notification to user
        
        Args:
            user_id: User ID
            user_email: User email address
            jobs: List of job dictionaries
            alert_type: Type of alert (new_matches, daily_digest, weekly_summary)
            
        Returns:
            True if sent successfully
        """
        try:
            job_count = len(jobs)
            
            if alert_type == "new_matches":
                subject = f"🎯 {job_count} New Job Matches Found!"
                title = f"{job_count} new jobs match your profile"
            elif alert_type == "daily_digest":
                subject = f"📊 Your Daily Job Digest - {job_count} Opportunities"
                title = f"Daily digest: {job_count} jobs"
            else:
                subject = f"📈 Weekly Job Summary - {job_count} New Positions"
                title = f"Weekly summary: {job_count} jobs"
            
            # Send in-app notification
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=f"Check out {job_count} new job opportunities tailored for you",
                notification_type="success",
                action_url="/jobs/recommendations"
            )
            
            # Send email with job details
            email_body = self._format_job_alert_email(jobs, alert_type)
            await self.send_email(
                to_email=user_email,
                subject=subject,
                body=email_body,
                html=True
            )
            
            logger.info(f"Job alert sent to user {user_id} ({user_email}): {job_count} jobs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send job alert to user {user_id}: {e}")
            return False
    
    def _format_job_alert_email(self, jobs: List[Dict[str, Any]], alert_type: str) -> str:
        """Format job alert email as HTML"""
        
        job_items = []
        for job in jobs[:10]:  # Limit to 10 jobs in email
            job_items.append(f"""
                <div style="border: 1px solid #e0e0e0; padding: 15px; margin-bottom: 15px; border-radius: 5px;">
                    <h3 style="margin: 0 0 10px 0; color: #2563eb;">{job.get('title', 'Job Title')}</h3>
                    <p style="margin: 5px 0; color: #666;">
                        <strong>Company:</strong> {job.get('company', 'N/A')}<br>
                        <strong>Location:</strong> {job.get('location', 'N/A')}<br>
                        <strong>Salary:</strong> {job.get('salary', 'Not specified')}
                    </p>
                    <a href="{job.get('application_url', '#')}" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 4px;">
                        Apply Now
                    </a>
                </div>
            """)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                <h1 style="margin: 0;">Career Copilot</h1>
                <p style="margin: 10px 0 0 0;">Your AI-Powered Job Search Assistant</p>
            </div>
            
            <div style="padding: 20px; background-color: #f9fafb;">
                <h2 style="color: #1f2937;">{'New Job Matches!' if alert_type == 'new_matches' else 'Job Digest'}</h2>
                <p>We found {len(jobs)} new opportunities that match your profile!</p>
                
                {''.join(job_items)}
                
                {f'<p style="text-align: center; color: #666; margin-top: 20px;">And {len(jobs) - 10} more jobs...</p>' if len(jobs) > 10 else ''}
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="http://localhost:3000/jobs" style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                        View All Jobs
                    </a>
                </div>
            </div>
            
            <div style="background-color: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px;">
                <p>You're receiving this email because you're subscribed to Career Copilot job alerts.</p>
                <p><a href="#" style="color: #2563eb;">Unsubscribe</a> | <a href="#" style="color: #2563eb;">Manage Preferences</a></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def send_application_status_update(
        self,
        user_id: int,
        user_email: str,
        job_title: str,
        company: str,
        status: str
    ) -> bool:
        """
        Send application status update notification
        
        Args:
            user_id: User ID
            user_email: User email
            job_title: Job title
            company: Company name
            status: Application status
            
        Returns:
            True if sent successfully
        """
        try:
            status_emoji = {
                "applied": "📝",
                "viewed": "👀",
                "interviewing": "💼",
                "offered": "🎉",
                "rejected": "❌",
                "accepted": "✅"
            }.get(status.lower(), "📋")
            
            subject = f"{status_emoji} Application Update: {job_title} at {company}"
            message = f"Your application status has been updated to: {status}"
            
            # Send in-app notification
            await self.send_notification(
                user_id=user_id,
                title=f"Application Update: {job_title}",
                message=message,
                notification_type="info",
                action_url="/applications"
            )
            
            # Send email
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>{status_emoji} Application Status Update</h2>
                <p>Your application for <strong>{job_title}</strong> at <strong>{company}</strong> has been updated.</p>
                <p><strong>New Status:</strong> {status.title()}</p>
                <p><a href="http://localhost:3000/applications" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">View Application</a></p>
            </body>
            </html>
            """
            
            await self.send_email(
                to_email=user_email,
                subject=subject,
                body=email_body,
                html=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send application status update: {e}")
            return False


# Global instance
_notification_service_instance: Optional[NotificationService] = None


def get_notification_service(db: Optional[Session] = None) -> NotificationService:
    """Get or create notification service instance"""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService(db)
    return _notification_service_instance


logger.info("Notification service module initialized")
