#!/usr/bin/env python3
"""
Test Email Notification Script

Sends test emails to verify the notification system is working properly.

Usage:
    python backend/scripts/test_email_notification.py --email your@email.com
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User
from app.services.notification_service import NotificationService
from sqlalchemy.orm import Session


def send_test_email(recipient_email: str, test_type: str = "simple"):
	"""Send a test email"""

	print(f"\n{'=' * 80}")
	print(f"Testing Email Notification System")
	print(f"{'=' * 80}\n")

	db: Session = SessionLocal()

	try:
		# Initialize notification service
		notification_service = NotificationService(db)

		# Check if user exists with this email
		user = db.query(User).filter(User.email == recipient_email).first()
		if not user:
			print(f"⚠️  No user found with email: {recipient_email}")
			print("Creating test user...")
			user = User(
				email=recipient_email,
				username=recipient_email.split("@")[0],
				full_name="Test User",
				hashed_password="test",  # Won't be used
			)
			db.add(user)
			db.commit()
			db.refresh(user)
			print(f"✅ Test user created: {user.username}")

		if test_type == "simple":
			# Send simple test email
			print(f"\n📧 Sending simple test email to: {recipient_email}")

			subject = "Career Copilot - Test Email"
			body = """
            This is a test email from Career Copilot.
            
            If you're receiving this, it means the email notification system is working correctly!
            
            Timestamp: {}
            User ID: {}
            Email: {}
            """.format(str(user.created_at), user.id, user.email)

			html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9fafb; }}
                    .success {{ background-color: #D1FAE5; border-left: 4px solid #10B981; padding: 15px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Career Copilot</h1>
                        <p>Email Notification Test</p>
                    </div>
                    <div class="content">
                        <h2>✅ Test Email Successful!</h2>
                        <p>If you're receiving this, it means the email notification system is working correctly.</p>
                        
                        <div class="success">
                            <strong>System Status:</strong> Operational<br>
                            <strong>Timestamp:</strong> {user.created_at}<br>
                            <strong>User ID:</strong> {user.id}<br>
                            <strong>Email:</strong> {user.email}
                        </div>
                        
                        <p>The following notification features are available:</p>
                        <ul>
                            <li>Morning job briefings (8 AM daily)</li>
                            <li>Evening summaries (8 PM daily)</li>
                            <li>Job application confirmations</li>
                            <li>Interview reminders</li>
                            <li>Achievement milestones</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>Career Copilot - Your AI-Powered Career Assistant</p>
                    </div>
                </div>
            </body>
            </html>
            """

			success = notification_service.send_email(to_email=recipient_email, subject=subject, body=body, html=html_body)

			if success:
				print("✅ Test email sent successfully!")
				print(f"   Check your inbox at: {recipient_email}")
			else:
				print("❌ Failed to send test email")
				print("   Check your SMTP configuration in .env file:")
				print("   - SMTP_HOST")
				print("   - SMTP_PORT")
				print("   - SMTP_USER")
				print("   - SMTP_PASSWORD")

		elif test_type == "job_alert":
			# Send job alert test email
			print(f"\n📧 Sending job alert test email to: {recipient_email}")

			# Create mock job data
			mock_jobs = [
				{
					"title": "Senior Python Developer",
					"company": "Tech Corp",
					"location": "Berlin, Germany",
					"url": "https://example.com/job1",
					"salary_range": "€80,000 - €100,000",
					"match_score": 95,
				},
				{
					"title": "Full Stack Engineer",
					"company": "Startup GmbH",
					"location": "Munich, Germany",
					"url": "https://example.com/job2",
					"salary_range": "€70,000 - €90,000",
					"match_score": 88,
				},
			]

			success = notification_service.send_job_alert(user_id=user.id, user_email=recipient_email, jobs=mock_jobs, alert_type="new_matches")

			if success:
				print("✅ Job alert email sent successfully!")
				print(f"   Check your inbox at: {recipient_email}")
			else:
				print("❌ Failed to send job alert email")

		else:
			print(f"❌ Unknown test type: {test_type}")
			print("   Available types: simple, job_alert")

	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback

		traceback.print_exc()

	finally:
		db.close()

	print(f"\n{'=' * 80}\n")


def main():
	parser = argparse.ArgumentParser(description="Test email notification system")
	parser.add_argument("--email", type=str, required=True, help="Email address to send test email to")
	parser.add_argument("--type", type=str, default="simple", choices=["simple", "job_alert"], help="Type of test email to send")

	args = parser.parse_args()

	send_test_email(args.email, args.type)


if __name__ == "__main__":
	main()
	main()
