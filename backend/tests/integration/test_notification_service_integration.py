"""
Integration tests for NotificationService.
Tests email notifications with SMTP and template rendering.
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.services.notification_service import NotificationService


class MockUser:
	"""Mock user object for testing."""

	def __init__(self, id, username, email):
		self.id = id
		self.username = username
		self.email = email


@pytest_asyncio.fixture
async def notification_service():
	"""Create notification service for testing."""
	settings = get_settings()
	service = NotificationService(settings)
	return service


@pytest_asyncio.fixture
async def test_user():
	"""Create a test user."""
	return MockUser(id=1, username="testuser", email="test@example.com")


class TestEmailNotifications:
	"""Test email notification functionality."""

	@pytest.mark.asyncio
	async def test_send_morning_briefing_success(self, notification_service, test_user):
		"""Test sending morning briefing email successfully."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_server = MagicMock()
			mock_smtp.return_value.__enter__.return_value = mock_server

			recommendations = [
				{"title": "Senior Python Developer", "company": "TechCorp", "match_score": 0.95},
				{"title": "Backend Engineer", "company": "StartupXYZ", "match_score": 0.88},
			]

			result = notification_service.send_morning_briefing(user=test_user, recommendations=recommendations)

			assert result == True
			mock_smtp.assert_called_once()

	@pytest.mark.asyncio
	async def test_send_evening_summary_success(self, notification_service, test_user):
		"""Test sending evening summary email successfully."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_server = MagicMock()
			mock_smtp.return_value.__enter__.return_value = mock_server

			analytics_summary = {"total_jobs": 150, "total_applications": 12, "interviews_scheduled": 3}

			result = notification_service.send_evening_summary(user=test_user, analytics_summary=analytics_summary)

			assert result == True
			mock_smtp.assert_called_once()

	@pytest.mark.asyncio
	async def test_send_job_alert_success(self, notification_service, test_user):
		"""Test sending job alert email successfully."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_server = MagicMock()
			mock_smtp.return_value.__enter__.return_value = mock_server

			jobs = [
				{"title": "Senior Python Developer", "company": "AI Startup", "match_score": 0.92},
				{"title": "Full Stack Developer", "company": "FinTech Co", "match_score": 0.85},
			]

			result = notification_service.send_job_alert(user=test_user, jobs=jobs, total_count=2)

			assert result == True
			mock_smtp.assert_called_once()

	@pytest.mark.asyncio
	async def test_email_with_no_user_email(self, notification_service):
		"""Test handling of user without email."""
		user_no_email = MockUser(id=2, username="noemail", email=None)

		recommendations = [{"title": "Test Job", "company": "Test Co"}]
		result = notification_service.send_morning_briefing(user=user_no_email, recommendations=recommendations)

		assert result == False

	@pytest.mark.asyncio
	async def test_email_with_smtp_connection_error(self, notification_service, test_user):
		"""Test error handling when SMTP connection fails."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Cannot connect")

			recommendations = [{"title": "Test Job", "company": "Test Co", "match_score": 0.85}]
			result = notification_service.send_morning_briefing(user=test_user, recommendations=recommendations)

			assert result == False

	@pytest.mark.asyncio
	async def test_email_with_authentication_error(self, notification_service, test_user):
		"""Test error handling when SMTP authentication fails."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_server = MagicMock()
			mock_smtp.return_value.__enter__.return_value = mock_server
			mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Auth failed")

			recommendations = [{"title": "Test Job", "company": "Test Co", "match_score": 0.85}]
			result = notification_service.send_morning_briefing(user=test_user, recommendations=recommendations)

			assert result == False


class TestSlackNotifications:
	"""Test Slack notification functionality."""

	@pytest.mark.asyncio
	async def test_slack_notification_not_implemented(self, notification_service):
		"""Test that Slack notifications are not yet implemented."""
		result = notification_service.send_slack_notification(channel="#general", message="Test")
		assert result == False


class TestPushNotifications:
	"""Test push notification functionality."""

	@pytest.mark.asyncio
	async def test_push_notification_not_implemented(self, notification_service, test_user):
		"""Test that push notifications are not yet implemented."""
		result = notification_service.send_push_notification(user=test_user, title="Test", message="Test")
		assert result == False


class TestNotificationBatching:
	"""Test sending multiple notifications in sequence."""

	@pytest.mark.asyncio
	async def test_multiple_notifications_sent_sequentially(self, notification_service, test_user):
		"""Test sending multiple notifications in sequence."""
		with patch("smtplib.SMTP_SSL") as mock_smtp:
			mock_server = MagicMock()
			mock_smtp.return_value.__enter__.return_value = mock_server

			r1 = notification_service.send_morning_briefing(user=test_user, recommendations=[])
			r2 = notification_service.send_evening_summary(user=test_user, analytics_summary={})
			r3 = notification_service.send_job_alert(user=test_user, jobs=[], total_count=0)

			assert r1 == True
			assert r2 == True
			assert r3 == True
			assert mock_smtp.call_count == 3
