import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

from ..core.config import get_settings
from ..models.user import User

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.smtp_host = self.settings.smtp_host
        self.smtp_port = self.settings.smtp_port
        self.smtp_username = self.settings.smtp_username
        self.smtp_password = self.settings.smtp_password
        self.smtp_from_email = self.settings.smtp_from_email
        self.smtp_enabled = self.settings.smtp_enabled

        # Setup Jinja2 environment for email templates
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(["html", "xml"])
        )

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email with graceful degradation.
        Logs email content if SMTP is not configured or fails.
        """
        if not self.smtp_enabled:
            logger.warning(f"SMTP is disabled. Email would be sent to {to_email}")
            logger.info(f"Email subject: {subject}")
            logger.debug(f"Email content (first 200 chars): {html_content[:200]}...")
            return False

        if not self.smtp_host or not self.smtp_username or not self.smtp_password or not self.smtp_from_email:
            logger.warning("SMTP settings not fully configured. Email would be sent to {to_email}")
            logger.info(f"Email subject: {subject}")
            logger.debug(f"Email content (first 200 chars): {html_content[:200]}...")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self.smtp_from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_from_email, to_email, msg.as_string())
            logger.info(f"✓ Email sent successfully to {to_email} with subject: {subject}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"✗ SMTP authentication failed for {to_email}: {e}")
            logger.warning("Continuing operation despite email failure (graceful degradation)")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"✗ SMTP error sending email to {to_email}: {e}")
            logger.warning("Continuing operation despite email failure (graceful degradation)")
            return False
        except ConnectionError as e:
            logger.error(f"✗ Connection error sending email to {to_email}: {e}")
            logger.warning("Continuing operation despite email failure (graceful degradation)")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error sending email to {to_email}: {e}", exc_info=True)
            logger.warning("Continuing operation despite email failure (graceful degradation)")
            return False

    def send_morning_briefing(self, user: User, recommendations: List[Dict[str, Any]]) -> bool:
        if not user.email:
            logger.warning(f"User {user.username} has no email. Skipping morning briefing.")
            return False

        subject = "🚀 Your Daily Job Recommendations from Career Copilot"
        template = self.jinja_env.get_template("morning_briefing.html")
        
        # Prepare data for template
        template_data = {
            "user_name": user.username,
            "recommendations": recommendations,
            "jobs_url": f"{self.settings.frontend_url}/jobs" # Assuming a frontend URL setting
        }
        html_content = template.render(template_data)
        
        return self._send_email(user.email, subject, html_content)

    def send_evening_summary(self, user: User, analytics_summary: Dict[str, Any]) -> bool:
        if not user.email:
            logger.warning(f"User {user.username} has no email. Skipping evening summary.")
            return False

        subject = "📊 Your Daily Job Search Summary from Career Copilot"
        template = self.jinja_env.get_template("evening_summary.html")

        # Prepare data for template
        template_data = {
            "user_name": user.username,
            "daily_stats": {
                "total_jobs": analytics_summary.get("total_jobs", 0),
                "total_applications": analytics_summary.get("total_applications", 0),
                "interviews_scheduled": analytics_summary.get("interviews_scheduled", 0),
                "offers_received": analytics_summary.get("offers_received", 0),
                "daily_applications_today": analytics_summary.get("daily_applications_today", 0)
            },
            "jobs_url": f"{self.settings.frontend_url}/jobs"
        }
        html_content = template.render(template_data)

        return self._send_email(user.email, subject, html_content)

    def send_job_alert(self, user: User, jobs: List[Dict[str, Any]], total_count: int) -> bool:
        """Send job alert notification to user."""
        if not user.email:
            logger.warning(f"User {user.username} has no email. Skipping job alert.")
            return False

        subject = f"🎯 {total_count} New Job Matches Found - Career Copilot"
        template = self.jinja_env.get_template("job_alert.html")
        
        # Prepare data for template
        template_data = {
            "user_name": user.username,
            "jobs": jobs,
            "total_count": total_count,
            "jobs_url": f"{self.settings.frontend_url}/jobs" if hasattr(self.settings, 'frontend_url') else "#"
        }
        html_content = template.render(template_data)
        
        return self._send_email(user.email, subject, html_content)