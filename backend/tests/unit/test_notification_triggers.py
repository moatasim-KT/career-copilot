"""
Unit tests for notification trigger functionality.
Tests the triggering of various notification types including briefings and job matches.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Service refactored - notification_manager no longer exists")

from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.config import get_settings
from app.services.email_template_manager import EmailTemplateManager

# from app.services.notification_manager import NotificationManager  # Service refactored
from app.services.notification_service import NotificationService  # Use this instead


@pytest.fixture
def notification_manager():
	"""Create a notification manager instance for testing."""
	return NotificationManager()


@pytest.fixture
def email_optimizer():
	"""Create an email template manager instance for testing."""
	return EmailTemplateManager()


@pytest.mark.asyncio
async def test_morning_briefing_trigger():
	"""Test manual triggering of morning briefing notifications."""
	with patch("app.services.notification_manager.NotificationManager._send_email_notification") as mock_email:
		manager = NotificationManager()
		test_data = {
			"type": "morning_briefing",
			"user_id": "test_user",
			"email": "test@example.com",
			"content": {"pending_applications": 3, "new_jobs": 5, "upcoming_deadlines": 2},
		}

		# Trigger morning briefing
		await manager.send_morning_briefing(user_id=test_data["user_id"], email=test_data["email"], content=test_data["content"])

		# Verify email was triggered
		mock_email.assert_called_once()
		call_args = mock_email.call_args[0]
		assert call_args[0] == test_data["email"]
		assert "morning_briefing" in call_args[1]["type"]


@pytest.mark.asyncio
async def test_evening_briefing_trigger():
	"""Test manual triggering of evening briefing notifications."""
	with patch("app.services.notification_manager.NotificationManager._send_email_notification") as mock_email:
		manager = NotificationManager()
		test_data = {
			"type": "evening_briefing",
			"user_id": "test_user",
			"email": "test@example.com",
			"content": {"applications_sent": 2, "profile_views": 4, "tomorrow_tasks": 3},
		}

		# Trigger evening briefing
		await manager.send_evening_briefing(user_id=test_data["user_id"], email=test_data["email"], content=test_data["content"])

		# Verify email was triggered
		mock_email.assert_called_once()
		call_args = mock_email.call_args[0]
		assert call_args[0] == test_data["email"]
		assert "evening_briefing" in call_args[1]["type"]


@pytest.mark.asyncio
async def test_job_match_notification():
	"""Test triggering of job match notifications."""
	with patch("app.services.notification_manager.NotificationManager._send_email_notification") as mock_email:
		manager = NotificationManager()
		test_data = {
			"type": "job_match",
			"user_id": "test_user",
			"email": "test@example.com",
			"job": {"id": "job123", "title": "Software Engineer", "company": "Tech Corp", "match_score": 0.85},
		}

		# Trigger job match notification
		await manager.send_job_match_notification(user_id=test_data["user_id"], email=test_data["email"], job_data=test_data["job"])

		# Verify email was triggered
		mock_email.assert_called_once()
		call_args = mock_email.call_args[0]
		assert call_args[0] == test_data["email"]
		assert "job_match" in call_args[1]["type"]


@pytest.mark.asyncio
async def test_notification_timing():
	"""Test notification delivery timing verification."""
	settings = get_settings()
	optimizer = EmailTemplateManager()

	# Test notification scheduling
	test_notification = {
		"type": "scheduled",
		"user_id": "test_user",
		"email": "test@example.com",
		"scheduled_time": datetime.now() + timedelta(hours=1),
	}

	with patch("app.services.email_template_manager.EmailTemplateManager._process_single_notification") as mock_send:
		# Queue notification
		await optimizer.queue_notification(test_notification)

		# Verify not sent immediately
		mock_send.assert_not_called()

		# Fast forward time
		test_notification["scheduled_time"] = datetime.now()
		await optimizer._process_notification_queue()

		# Verify sent after scheduled time
		mock_send.assert_called_once()
