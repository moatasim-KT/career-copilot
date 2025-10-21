"""Notification service for email alerts"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.user import User
from ..core.config import Settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class NotificationService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email with graceful degradation when SMTP not configured"""
        if not self.settings.smtp_enabled:
            logger.info(f"SMTP not enabled. Would send email to {to_email} with subject: {subject}")
            logger.debug(f"Email content: {html_content}")
            return True  # Return True for graceful degradation

        if not self.settings.smtp_username or not self.settings.smtp_password:
            logger.warning("SMTP username or password not configured. Logging email content instead.")
            logger.info(f"Would send email to {to_email} with subject: {subject}")
            logger.debug(f"Email content: {html_content}")
            return True  # Return True for graceful degradation

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.settings.smtp_from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.sendmail(self.settings.smtp_from_email, to_email, msg.as_string())
            logger.info(f"Email sent successfully to {to_email} with subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} with subject {subject}: {e}")
            # Graceful degradation - log the content instead of failing
            logger.info(f"Logging email content due to SMTP failure:")
            logger.debug(f"Subject: {subject}")
            logger.debug(f"Content: {html_content}")
            return False

    def send_morning_briefing(self, user: User, recommendations: List[Dict[str, Any]]) -> bool:
        """Send morning briefing with top job recommendations"""
        if not user.email:
            logger.warning(f"User {user.username} has no email. Skipping morning briefing.")
            return False

        subject = "🌅 Your Daily Job Recommendations - Career Co-Pilot"
        
        # Generate HTML content for recommendations
        recommendations_html = ""
        if recommendations:
            for idx, rec in enumerate(recommendations, 1):
                job = rec["job"]
                score = rec["score"]
                tech_stack_str = ', '.join(job.tech_stack or []) if job.tech_stack else 'Not specified'
                recommendations_html += f"""
                <div style="margin: 20px 0; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f7fafc;">
                    <h3 style="color: #2d3748; margin-top: 0; margin-bottom: 10px;">{idx}. {job.title}</h3>
                    <p style="color: #4a5568; margin: 5px 0; font-size: 16px;"><strong>{job.company}</strong></p>
                    <div style="margin: 15px 0;">
                        <span style="background-color: #48bb78; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: bold;">
                            {score:.0f}% Match
                        </span>
                    </div>
                    <p style="color: #718096; margin: 8px 0;"><strong>📍 Location:</strong> {job.location or 'Remote/Not specified'}</p>
                    <p style="color: #718096; margin: 8px 0;"><strong>💻 Tech Stack:</strong> {tech_stack_str}</p>
                    {f'<p style="color: #718096; margin: 8px 0;"><strong>💰 Salary:</strong> {job.salary_range}</p>' if job.salary_range else ''}
                    {f'<p style="color: #4a5568; margin: 10px 0; font-size: 14px;">{job.description[:200]}...</p>' if job.description else ''}
                    <div style="margin-top: 15px;">
                        {f'<a href="{job.link}" style="background-color: #4299e1; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-right: 10px;">Apply Now</a>' if job.link else ''}
                        <span style="color: #718096; font-size: 12px;">Added: {job.created_at.strftime('%m/%d/%Y')}</span>
                    </div>
                </div>
                """
        else:
            recommendations_html = """
            <div style="margin: 20px 0; padding: 20px; border: 1px solid #fed7d7; border-radius: 8px; background-color: #fff5f5; text-align: center;">
                <p style="color: #4a5568; font-size: 16px;">No new recommendations for you today.</p>
                <p style="color: #718096; font-size: 14px;">Check back tomorrow for fresh opportunities!</p>
            </div>
            """

        # Create the full HTML email body
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #4299e1; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ background-color: #f7fafc; padding: 15px; text-align: center; color: #718096; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="margin: 0;">🌅 Good Morning, {user.username}!</h1>
                    <p style="margin: 5px 0 0 0;">Your personalized job recommendations are ready</p>
                </div>
                <div class="content">
                    <p>Here are your top job matches for today:</p>
                    {recommendations_html}
                    <div style="margin-top: 30px; padding: 15px; background-color: #e6fffa; border-radius: 8px; border-left: 4px solid #38b2ac;">
                        <p style="margin: 0; color: #2d3748;"><strong>💡 Pro Tip:</strong> The best time to apply is early morning when hiring managers are most active!</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Best of luck with your job search!</p>
                    <p><strong>Career Co-Pilot Team</strong></p>
                </div>
            </body>
        </html>
        """
        return self._send_email(user.email, subject, html_content)

    def send_evening_summary(self, user: User, analytics_summary: Dict[str, Any]) -> bool:
        """Send evening summary with daily statistics"""
        if not user.email:
            logger.warning(f"User {user.username} has no email. Skipping evening summary.")
            return False

        subject = "🌙 Your Daily Job Search Summary - Career Co-Pilot"
        
        # Extract metrics from analytics_summary
        total_jobs = analytics_summary.get("total_jobs", 0)
        total_applications = analytics_summary.get("total_applications", 0)
        interviews = analytics_summary.get("interviews", 0)
        offers = analytics_summary.get("offers", 0)
        applications_today = analytics_summary.get("applications_today", 0)
        jobs_saved = analytics_summary.get("jobs_saved", total_jobs)

        # Calculate progress indicators
        response_rate = round((interviews / total_applications * 100), 1) if total_applications > 0 else 0
        offer_rate = round((offers / total_applications * 100), 1) if total_applications > 0 else 0

        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .stats-grid {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }}
                    .stat-card {{ flex: 1; min-width: 200px; padding: 15px; background-color: #f7fafc; border-radius: 8px; text-align: center; }}
                    .stat-number {{ display: block; font-size: 24px; font-weight: bold; color: #4299e1; }}
                    .stat-label {{ font-size: 14px; color: #718096; margin-top: 5px; }}
                    .footer {{ background-color: #f7fafc; padding: 15px; text-align: center; color: #718096; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="margin: 0;">🌙 Good Evening, {user.username}!</h1>
                    <p style="margin: 5px 0 0 0;">Here's how your job search went today</p>
                </div>
                <div class="content">
                    <h2 style="color: #2d3748; margin-bottom: 20px;">📋 Today's Activity</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-number">{applications_today}</span>
                            <span class="stat-label">Applications Today</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{total_jobs}</span>
                            <span class="stat-label">Jobs Saved</span>
                        </div>
                    </div>
                    
                    <h2 style="color: #2d3748; margin: 30px 0 20px 0;">📊 Overall Progress</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-number">{total_applications}</span>
                            <span class="stat-label">Total Applications</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{interviews}</span>
                            <span class="stat-label">Interviews</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{offers}</span>
                            <span class="stat-label">Offers</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{response_rate}%</span>
                            <span class="stat-label">Response Rate</span>
                        </div>
                    </div>
                    
                    {f'''
                    <div style="margin: 30px 0; padding: 20px; background-color: #f0fff4; border-radius: 8px; border-left: 4px solid #48bb78;">
                        <h3 style="color: #2d3748; margin-top: 0;">🎉 Great Progress Today!</h3>
                        <p style="color: #4a5568; margin-bottom: 0;">You submitted {applications_today} application{"s" if applications_today != 1 else ""} today. Keep up the momentum!</p>
                    </div>
                    ''' if applications_today > 0 else '''
                    <div style="margin: 30px 0; padding: 20px; background-color: #fffaf0; border-radius: 8px; border-left: 4px solid #ed8936;">
                        <h3 style="color: #2d3748; margin-top: 0;">💪 Tomorrow's Opportunity</h3>
                        <p style="color: #4a5568; margin-bottom: 0;">No applications today, but tomorrow is a fresh start! Check your morning briefing for new opportunities.</p>
                    </div>
                    '''}
                    
                    <div style="margin: 30px 0; padding: 15px; background-color: #e6fffa; border-radius: 8px; border-left: 4px solid #38b2ac;">
                        <p style="margin: 0; color: #2d3748;"><strong>💡 Evening Tip:</strong> Review your applications and prepare for tomorrow's opportunities. Consistency is key!</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Rest well and get ready for tomorrow's opportunities!</p>
                    <p><strong>Career Co-Pilot Team</strong></p>
                </div>
            </body>
        </html>
        """
        return self._send_email(user.email, subject, html_content)
