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
        if not self.smtp_enabled:
            logger.warning(f"SMTP is disabled. Not sending email to {to_email}")
            return False

        if not self.smtp_host or not self.smtp_username or not self.smtp_password or not self.smtp_from_email:
            logger.error("SMTP settings (host, user, password, from_email) are not fully configured. Cannot send email.")
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
            logger.info(f"Email sent successfully to {to_email} with subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} with subject {subject}: {e}")
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