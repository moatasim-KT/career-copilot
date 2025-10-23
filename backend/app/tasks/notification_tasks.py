"""
Background tasks for notifications
"""

from celery import current_task
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import traceback

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.services.notification_service import NotificationService
from app.services.cache_service import cache_service

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_email_async")
def send_email_async(
    self,
    user_id: int,
    subject: str,
    content: str,
    email_type: str = "general"
) -> Dict[str, Any]:
    """
    Send an email asynchronously
    
    Args:
        user_id: ID of the user to send email to
        subject: Email subject
        content: Email content
        email_type: Type of email (briefing, summary, alert, etc.)
        
    Returns:
        Dictionary with send results
    """
    db = next(get_db())
    
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Loading user data..."}
        )
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.email:
            raise ValueError(f"User {user_id} has no email address")
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Sending email..."}
        )
        
        # Send email
        success = notification_service._send_email(
            to_email=user.email,
            subject=subject,
            content=content
        )
        
        if not success:
            raise Exception("Email sending failed")
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Email sent successfully"}
        )
        
        logger.info(f"Successfully sent {email_type} email to user {user_id}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "email_type": email_type,
            "message": "Email sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sending email to user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(e)}"}
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.send_morning_briefings_async")
def send_morning_briefings_async() -> Dict[str, Any]:
    """
    Send morning briefings to all users asynchronously
    
    Returns:
        Dictionary with briefing results
    """
    db = next(get_db())
    
    try:
        # Get all active users
        users = db.query(User).filter(
            User.email.isnot(None),
            User.skills.isnot(None)  # Only users with skills set
        ).all()
        
        if not users:
            logger.info("No users found for morning briefings")
            return {"status": "success", "sent": 0, "message": "No users to send briefings to"}
        
        notification_service = NotificationService()
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Send morning briefing
                success = notification_service.send_morning_briefing(user)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending morning briefing to user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Morning briefings completed: {sent_count} sent, {failed_count} failed")
        
        return {
            "status": "success",
            "sent": sent_count,
            "failed": failed_count,
            "total_users": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error sending morning briefings: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.send_evening_summaries_async")
def send_evening_summaries_async() -> Dict[str, Any]:
    """
    Send evening summaries to all users asynchronously
    
    Returns:
        Dictionary with summary results
    """
    db = next(get_db())
    
    try:
        # Get all active users
        users = db.query(User).filter(
            User.email.isnot(None)
        ).all()
        
        if not users:
            logger.info("No users found for evening summaries")
            return {"status": "success", "sent": 0, "message": "No users to send summaries to"}
        
        notification_service = NotificationService()
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Send evening summary
                success = notification_service.send_evening_summary(user)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending evening summary to user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Evening summaries completed: {sent_count} sent, {failed_count} failed")
        
        return {
            "status": "success",
            "sent": sent_count,
            "failed": failed_count,
            "total_users": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error sending evening summaries: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_job_alerts_async")
def send_job_alerts_async(self, user_id: int, job_matches: List[Dict]) -> Dict[str, Any]:
    """
    Send job match alerts to a user
    
    Args:
        user_id: ID of the user
        job_matches: List of job matches with scores
        
    Returns:
        Dictionary with alert results
    """
    db = next(get_db())
    
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Preparing job alerts..."}
        )
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.email:
            logger.warning(f"User {user_id} has no email address for job alerts")
            return {"status": "skipped", "reason": "No email address"}
        
        if not job_matches:
            logger.info(f"No job matches to send to user {user_id}")
            return {"status": "skipped", "reason": "No job matches"}
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Generating alert email..."}
        )
        
        # Generate email content
        subject = f"🎯 New Job Matches Found - {len(job_matches)} opportunities"
        
        content = f"""
        Hi {user.username},

        We found {len(job_matches)} new job opportunities that match your profile!

        Top Matches:
        """
        
        for i, match in enumerate(job_matches[:5], 1):
            content += f"""
        {i}. {match.get('title', 'Unknown Title')} at {match.get('company', 'Unknown Company')}
           Match Score: {match.get('match_score', 0):.1f}%
           Location: {match.get('location', 'Not specified')}
           
        """
        
        content += """
        
        Log in to your Career Copilot dashboard to view all matches and apply!
        
        Best regards,
        Career Copilot Team
        """
        
        # Send email
        notification_service = NotificationService()
        success = notification_service._send_email(
            to_email=user.email,
            subject=subject,
            content=content
        )
        
        if not success:
            raise Exception("Job alert email sending failed")
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Job alerts sent successfully"}
        )
        
        logger.info(f"Successfully sent job alerts to user {user_id} for {len(job_matches)} matches")
        
        return {
            "status": "success",
            "user_id": user_id,
            "matches_sent": len(job_matches),
            "message": "Job alerts sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sending job alerts to user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(e)}"}
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.notification_tasks.batch_send_notifications")
def batch_send_notifications(
    self,
    notification_requests: List[Dict]
) -> Dict[str, Any]:
    """
    Send multiple notifications in batch
    
    Args:
        notification_requests: List of notification requests
        Each request should have: user_id, subject, content, email_type
        
    Returns:
        Dictionary with batch send results
    """
    try:
        total_requests = len(notification_requests)
        processed = 0
        successful = 0
        failed = 0
        
        for i, request in enumerate(notification_requests):
            try:
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": total_requests,
                        "status": f"Sending notification {i + 1} of {total_requests}",
                        "successful": successful,
                        "failed": failed
                    }
                )
                
                # Send email
                result = send_email_async.delay(
                    user_id=request.get("user_id"),
                    subject=request.get("subject"),
                    content=request.get("content"),
                    email_type=request.get("email_type", "general")
                )
                
                # Wait for result (with timeout)
                try:
                    result.get(timeout=60)  # 1 minute timeout
                    successful += 1
                except Exception as e:
                    logger.error(f"Batch notification failed for request {i}: {e}")
                    failed += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error in batch processing notification {i}: {e}")
                failed += 1
                processed += 1
        
        self.update_state(
            state="SUCCESS",
            meta={
                "current": total_requests,
                "total": total_requests,
                "status": "Batch notifications completed",
                "successful": successful,
                "failed": failed
            }
        )
        
        logger.info(f"Batch notifications completed: {successful} successful, {failed} failed")
        
        return {
            "status": "success",
            "total": total_requests,
            "processed": processed,
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Error in batch notification sending: {e}")
        
        self.update_state(
            state="FAILURE",
            meta={"status": f"Batch processing failed: {str(e)}"}
        )
        
        raise