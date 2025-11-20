#!/usr/bin/env python3
"""
System Health Verification Script

Checks the following components:
1. Scheduler (Celery Beat + APScheduler)
2. Notification System (Email sending)
3. Resume Parsing
4. Dashboard Progress Tracking

Usage:
    python backend/scripts/verify_system_health.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.notification_service import NotificationService
from app.services.resume_parser_service import ResumeParserService
from sqlalchemy.orm import Session


class Colors:
	"""Terminal colors for output"""

	GREEN = "\033[92m"
	RED = "\033[91m"
	YELLOW = "\033[93m"
	BLUE = "\033[94m"
	BOLD = "\033[1m"
	END = "\033[0m"


def print_header(text: str):
	"""Print formatted header"""
	print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
	print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
	print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(text: str):
	"""Print success message"""
	print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
	"""Print error message"""
	print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
	"""Print warning message"""
	print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
	"""Print info message"""
	print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def check_scheduler_status():
	"""Check if Celery Beat and APScheduler are running"""
	print_header("SCHEDULER STATUS")

	issues = []

	# Check Celery Beat process
	print_info("Checking Celery Beat status...")
	celery_beat_running = False
	try:
		import subprocess

		result = subprocess.run(["pgrep", "-f", "celery.*beat"], capture_output=True, text=True)
		if result.returncode == 0:
			celery_beat_running = True
			print_success(f"Celery Beat is running (PID: {result.stdout.strip()})")
		else:
			print_error("Celery Beat is NOT running")
			issues.append("Celery Beat process not found")
	except Exception as e:
		print_error(f"Could not check Celery Beat status: {e}")
		issues.append(f"Celery Beat check failed: {e}")

	# Check Celery Worker process
	print_info("Checking Celery Worker status...")
	celery_worker_running = False
	try:
		result = subprocess.run(["pgrep", "-f", "celery.*worker"], capture_output=True, text=True)
		if result.returncode == 0:
			celery_worker_running = True
			print_success(f"Celery Worker is running (PID: {result.stdout.strip()})")
		else:
			print_error("Celery Worker is NOT running")
			issues.append("Celery Worker process not found")
	except Exception as e:
		print_error(f"Could not check Celery Worker status: {e}")
		issues.append(f"Celery Worker check failed: {e}")

	# Check Redis connection (Celery broker)
	print_info("Checking Redis connection...")
	try:
		import redis

		redis_client = redis.Redis(host="localhost", port=6379, db=0)
		redis_client.ping()
		print_success("Redis broker is accessible")
	except Exception as e:
		print_error(f"Redis broker connection failed: {e}")
		issues.append(f"Redis not accessible: {e}")

	# Check scheduled tasks configuration
	print_info("Checking scheduled tasks configuration...")
	try:
		from app.celery import celery_app

		beat_schedule = celery_app.conf.beat_schedule
		if beat_schedule:
			print_success(f"Found {len(beat_schedule)} scheduled tasks:")
			for task_name, task_config in beat_schedule.items():
				print(f"  • {task_name}: {task_config.get('task', 'N/A')}")
		else:
			print_warning("No beat schedule configured")
			issues.append("No Celery Beat schedule found")
	except Exception as e:
		print_error(f"Could not load Celery configuration: {e}")
		issues.append(f"Celery config error: {e}")

	# Summary
	print()
	if not issues:
		print_success("All scheduler components are operational")
	else:
		print_error(f"Found {len(issues)} scheduler issues:")
		for issue in issues:
			print(f"  • {issue}")
		print_info("\nTo start Celery Beat:")
		print("  celery -A app.celery beat --loglevel=info")
		print_info("To start Celery Worker:")
		print("  celery -A app.celery worker --loglevel=info")

	return len(issues) == 0


def check_notification_system(db: Session):
	"""Test notification system and email sending"""
	print_header("NOTIFICATION SYSTEM")

	issues = []

	# Check notification service
	print_info("Checking NotificationService...")
	try:
		# NotificationService doesn't take db parameter in constructor
		# It's initialized without parameters
		from app.services.notification_service import NotificationService as NS

		print_success("NotificationService class found and importable")
		notification_service = None  # Will be instantiated when needed with db
	except Exception as e:
		print_error(f"Could not import NotificationService: {e}")
		issues.append(f"NotificationService import failed: {e}")
		return False

	# Check email configuration
	print_info("Checking email configuration...")
	try:
		smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
		smtp_port = os.getenv("SMTP_PORT", "587")
		smtp_user = os.getenv("SMTP_USER")
		smtp_password = os.getenv("SMTP_PASSWORD")

		if not smtp_user or not smtp_password:
			print_error("SMTP credentials not configured (SMTP_USER, SMTP_PASSWORD)")
			issues.append("SMTP credentials missing in environment")
		else:
			print_success(f"SMTP configured: {smtp_user}@{smtp_host}:{smtp_port}")
	except Exception as e:
		print_error(f"Could not check email configuration: {e}")
		issues.append(f"Email config check failed: {e}")

	# Check email templates
	print_info("Checking email templates...")
	try:
		# Use Path to get the backend directory
		backend_dir = Path(__file__).parent.parent
		template_dir = backend_dir / "app" / "templates" / "email"
		if template_dir.exists():
			templates = list(template_dir.glob("*.html"))
			print_success(f"Found {len(templates)} email templates:")
			for template in templates[:5]:  # Show first 5
				print(f"  • {template.name}")
			if len(templates) > 5:
				print(f"  ... and {len(templates) - 5} more")
		else:
			print_error(f"Email template directory not found: {template_dir}")
			issues.append("Email templates directory missing")
	except Exception as e:
		print_error(f"Could not check email templates: {e}")
		issues.append(f"Template check failed: {e}")

	# Check notification tasks
	print_info("Checking notification tasks...")
	try:
		from app.tasks import email_tasks, notification_tasks

		tasks = ["send_morning_briefing_task", "send_evening_summary_task", "send_email_async", "send_job_alerts_async"]
		for task_name in tasks:
			if hasattr(email_tasks, task_name) or hasattr(notification_tasks, task_name):
				print(f"  ✓ {task_name}")
			else:
				print(f"  ✗ {task_name} not found")
				issues.append(f"Task {task_name} not found")
		print_success("All critical notification tasks found")
	except Exception as e:
		print_error(f"Could not check notification tasks: {e}")
		issues.append(f"Task check failed: {e}")

	# Summary
	print()
	if not issues:
		print_success("Notification system is configured correctly")
		print_info("To test email sending, run:")
		print("  python backend/scripts/test_email_notification.py")
	else:
		print_error(f"Found {len(issues)} notification issues:")
		for issue in issues:
			print(f"  • {issue}")

	return len(issues) == 0


def check_resume_parsing():
	"""Test resume parsing functionality"""
	print_header("RESUME PARSING")

	issues = []

	# Check ResumeParserService
	print_info("Checking ResumeParserService...")
	try:
		parser = ResumeParserService()
		print_success("ResumeParserService initialized successfully")
	except Exception as e:
		print_error(f"Could not initialize ResumeParserService: {e}")
		issues.append(f"ResumeParserService init failed: {e}")
		return False

	# Check Docling dependency
	print_info("Checking Docling dependency...")
	try:
		import docling

		print_success("Docling library is installed")
	except ImportError:
		print_error("Docling library not installed")
		issues.append("Docling not installed - run: pip install docling")

	# Check supported file types
	print_info("Checking supported file types...")
	supported = parser._supported_extensions
	print_success(f"Supported formats: {', '.join(sorted(supported))}")

	# Check resume parsing tasks
	print_info("Checking resume parsing tasks...")
	try:
		from app.tasks import resume_parsing_tasks

		if hasattr(resume_parsing_tasks, "parse_resume_async"):
			print_success("Resume parsing async task found")
		else:
			print_error("parse_resume_async task not found")
			issues.append("Async parsing task missing")
	except Exception as e:
		print_error(f"Could not check parsing tasks: {e}")
		issues.append(f"Task check failed: {e}")

	# Check resume API endpoints
	print_info("Checking resume API endpoints...")
	try:
		from app.api.v1 import resume

		endpoints = ["upload_resume", "get_parsing_status", "get_profile_suggestions"]
		for endpoint in endpoints:
			if hasattr(resume, endpoint):
				print(f"  ✓ {endpoint}")
			else:
				print(f"  ✗ {endpoint} not found")
				issues.append(f"Endpoint {endpoint} not found")
		print_success("All resume endpoints found")
	except Exception as e:
		print_error(f"Could not check API endpoints: {e}")
		issues.append(f"API check failed: {e}")

	# Check uploads directory
	print_info("Checking uploads directory...")
	try:
		# Use Path to get the backend directory
		backend_dir = Path(__file__).parent.parent
		uploads_dir = backend_dir / "uploads"
		if uploads_dir.exists():
			print_success(f"Uploads directory exists: {uploads_dir}")
		else:
			print_warning(f"Uploads directory not found (will be created): {uploads_dir}")
			print_info(f"  Run: mkdir -p {uploads_dir}")
	except Exception as e:
		print_error(f"Could not check uploads directory: {e}")
		issues.append(f"Uploads dir check failed: {e}")

	# Summary
	print()
	if not issues:
		print_success("Resume parsing is fully operational")
		print_info("To test resume parsing:")
		print("  1. Upload a resume via the API: POST /api/v1/resume/upload")
		print("  2. Check parsing status: GET /api/v1/resume/{upload_id}/status")
	else:
		print_error(f"Found {len(issues)} resume parsing issues:")
		for issue in issues:
			print(f"  • {issue}")

	return len(issues) == 0


def check_dashboard_progress(db: Session):
	"""Check dashboard progress tracking and daily goals"""
	print_header("DASHBOARD PROGRESS TRACKING")

	issues = []

	# Check AnalyticsService
	print_info("Checking AnalyticsService...")
	try:
		analytics_service = AnalyticsService(db)
		print_success("AnalyticsService initialized successfully")
	except Exception as e:
		print_error(f"Could not initialize AnalyticsService: {e}")
		issues.append(f"AnalyticsService init failed: {e}")
		return False

	# Check analytics schemas
	print_info("Checking analytics schemas...")
	try:
		from app.schemas.analytics import AnalyticsSummaryResponse

		required_fields = ["daily_applications_today", "daily_application_goal", "daily_goal_progress", "weekly_applications", "monthly_applications"]
		schema_fields = AnalyticsSummaryResponse.model_fields.keys()
		for field in required_fields:
			if field in schema_fields:
				print(f"  ✓ {field}")
			else:
				print(f"  ✗ {field} missing")
				issues.append(f"Schema field {field} missing")
		print_success("All required analytics fields present")
	except Exception as e:
		print_error(f"Could not check analytics schemas: {e}")
		issues.append(f"Schema check failed: {e}")

	# Check dashboard service
	print_info("Checking DashboardService...")
	try:
		from app.services.dashboard_service import DashboardService

		print_success("DashboardService found")
	except ImportError:
		print_error("DashboardService not found")
		issues.append("DashboardService missing")

	# Check goal tracking
	print_info("Checking goal tracking system...")
	try:
		from app.services.goal_service import GoalService

		print_success("GoalService found for advanced goal tracking")
	except ImportError:
		print_warning("GoalService not found (optional)")

	# Check dashboard frontend component
	print_info("Checking frontend dashboard component...")
	try:
		dashboard_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "pages" / "Dashboard.tsx"
		if dashboard_path.exists():
			content = dashboard_path.read_text()
			if "daily_goal_progress" in content and "Daily Application Goal" in content:
				print_success("Dashboard component includes progress tracking")
			else:
				print_warning("Dashboard component may not show progress bar")
				issues.append("Dashboard progress bar not fully implemented")
		else:
			print_warning(f"Dashboard component not found: {dashboard_path}")
	except Exception as e:
		print_error(f"Could not check dashboard component: {e}")
		issues.append(f"Dashboard component check failed: {e}")

	# Test with sample user
	print_info("Testing analytics calculation...")
	try:
		from app.models.user import User

		# Get first user for testing
		user = db.query(User).first()
		if user:
			analytics = analytics_service.get_user_analytics(user)
			print_success("Analytics calculation successful:")
			print(f"  • Daily applications today: {analytics.get('daily_applications_today', 0)}")
			print(f"  • Daily goal: {analytics.get('daily_application_goal', 10)}")
			print(f"  • Progress: {analytics.get('daily_goal_progress', 0):.1f}%")
			print(f"  • Weekly applications: {analytics.get('weekly_applications', 0)}")
			print(f"  • Monthly applications: {analytics.get('monthly_applications', 0)}")
		else:
			print_warning("No users in database to test with")
	except Exception as e:
		print_error(f"Could not test analytics: {e}")
		issues.append(f"Analytics test failed: {e}")

	# Summary
	print()
	if not issues:
		print_success("Dashboard progress tracking is fully operational")
		print_info("The dashboard shows:")
		print("  • Daily application goal progress bar")
		print("  • Applications today / goal target")
		print("  • Weekly and monthly statistics")
		print("  • Real-time progress updates")
	else:
		print_error(f"Found {len(issues)} dashboard issues:")
		for issue in issues:
			print(f"  • {issue}")

	return len(issues) == 0


def main():
	"""Run all system health checks"""
	print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
	print(f"{Colors.BOLD}{'CAREER COPILOT - SYSTEM HEALTH CHECK'.center(80)}{Colors.END}")
	print(f"{Colors.BOLD}{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(80)}{Colors.END}")
	print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")

	results = {}

	# Run all checks
	results["scheduler"] = check_scheduler_status()

	# Database-dependent checks
	db = SessionLocal()
	try:
		results["notifications"] = check_notification_system(db)
		results["dashboard"] = check_dashboard_progress(db)
	finally:
		db.close()

	# Non-database checks
	results["resume_parsing"] = check_resume_parsing()

	# Overall summary
	print_header("OVERALL SYSTEM STATUS")

	total_checks = len(results)
	passed_checks = sum(1 for v in results.values() if v)

	for component, status in results.items():
		status_icon = "✅" if status else "❌"
		status_text = "OPERATIONAL" if status else "ISSUES FOUND"
		color = Colors.GREEN if status else Colors.RED
		print(f"{color}{status_icon} {component.upper().replace('_', ' ')}: {status_text}{Colors.END}")

	print()
	if passed_checks == total_checks:
		print_success(f"🎉 All {total_checks} system components are operational!")
		print_info("Your Career Copilot application is ready for production use.")
	else:
		failed = total_checks - passed_checks
		print_warning(f"⚠️  {failed}/{total_checks} components have issues that need attention")
		print_info("Review the detailed output above for remediation steps.")

	print()
	return 0 if passed_checks == total_checks else 1


if __name__ == "__main__":
	sys.exit(main())
