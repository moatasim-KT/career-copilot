from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.config import Settings
from app.core.exceptions import EmailServiceError
from app.services.email_service import (
	EmailEventType,
	EmailPriority,
	EmailProvider,
	EmailService,
	EmailServiceConfig,
	EmailTemplate,
	UnifiedEmailMessage,
)


@pytest.fixture
def mock_settings():
	settings = MagicMock(spec=Settings)
	settings.smtp_host = "smtp.mock.com"
	settings.smtp_port = 587
	settings.smtp_username = "user@mock.com"
	settings.smtp_password = "password"
	settings.smtp_from_email = "from@mock.com"
	settings.smtp_enabled = True
	settings.gmail_enabled = False
	settings.sendgrid_api_key = None
	settings.email_primary_provider = "smtp"
	settings.email_enable_fallback = True
	settings.email_enable_analytics = True
	return settings


@pytest.fixture
def email_service(mock_settings):
	with (
		patch("app.core.config.get_settings", return_value=mock_settings),
		patch("app.services.email_analytics_service.EmailAnalyticsService") as MockEmailAnalyticsService,
		patch("app.services.gmail_service.EnhancedGmailService") as MockGmailService,
		patch("app.services.sendgrid_service.SendGridService") as MockSendGridService,
		patch("app.services.smtp_service.EnhancedSMTPService") as MockSMTPService,
	):
		# Mock analytics service methods
		mock_analytics_instance = MockEmailAnalyticsService.return_value
		mock_analytics_instance.record_email_event = AsyncMock()

		# Mock provider services
		mock_gmail_instance = MockGmailService.return_value
		mock_gmail_instance.send_email = AsyncMock(return_value={"success": True, "provider": "gmail", "tracking_id": "gmail_track"})
		mock_gmail_instance.test_authentication = AsyncMock(return_value=True)

		mock_sendgrid_instance = MockSendGridService.return_value
		mock_sendgrid_instance.send_email_message = AsyncMock(return_value={"success": True, "provider": "sendgrid", "tracking_id": "sg_track"})
		mock_sendgrid_instance.test_connection = AsyncMock(return_value={"success": True})

		mock_smtp_instance = MockSMTPService.return_value
		mock_smtp_instance.send_email = AsyncMock(return_value={"success": True, "provider": "smtp", "tracking_id": "smtp_track"})
		mock_smtp_instance.test_connection = AsyncMock(return_value={"success": True})

		service = EmailService()
		service.email_analytics_service = mock_analytics_instance
		service.gmail_service = mock_gmail_instance
		service.sendgrid_service = mock_sendgrid_instance
		service.smtp_service = mock_smtp_instance
		return service


@pytest.fixture
def mock_unified_email_message():
	return UnifiedEmailMessage(
		to=["recipient@example.com"],
		subject="Test Subject",
		body_html="<h1>Test</h1>",
		body_text="Test",
		priority=EmailPriority.NORMAL,
		template_id="welcome",
		template_data={"user_name": "Test User"},
	)


class TestEmailService:
	@pytest.mark.asyncio
	async def test_send_email_smtp_success(self, email_service, mock_unified_email_message):
		email_service.config.primary_provider = EmailProvider.SMTP
		email_service.provider_health[EmailProvider.SMTP].available = True
		email_service.smtp_service.send_email.return_value = {"success": True, "provider": "smtp", "tracking_id": "smtp_track"}

		result = await email_service.send_email(mock_unified_email_message)

		assert result["success"] is True
		assert result["provider_used"] == "smtp"
		email_service.smtp_service.send_email.assert_called_once()
		email_service.email_analytics_service.record_email_event.assert_called_once()

	@pytest.mark.asyncio
	async def test_send_email_fallback_success(self, email_service, mock_unified_email_message):
		email_service.config.primary_provider = EmailProvider.SENDGRID
		email_service.provider_health[EmailProvider.SENDGRID].available = False
		email_service.provider_health[EmailProvider.SMTP].available = True
		email_service.sendgrid_service.send_email_message.side_effect = EmailServiceError("SendGrid failed")
		email_service.smtp_service.send_email.return_value = {"success": True, "provider": "smtp", "tracking_id": "smtp_track"}

		result = await email_service.send_email(mock_unified_email_message)

		assert result["success"] is True
		assert result["provider_used"] == "smtp"
		email_service.sendgrid_service.send_email_message.assert_called_once()
		email_service.smtp_service.send_email.assert_called_once()

	@pytest.mark.asyncio
	async def test_send_email_all_providers_fail(self, email_service, mock_unified_email_message):
		email_service.config.primary_provider = EmailProvider.GMAIL
		email_service.provider_health[EmailProvider.GMAIL].available = False
		email_service.provider_health[EmailProvider.SENDGRID].available = False
		email_service.provider_health[EmailProvider.SMTP].available = False

		with pytest.raises(EmailServiceError, match="No email providers available"):
			await email_service.send_email(mock_unified_email_message)

	@pytest.mark.asyncio
	async def test_get_email_templates(self, email_service):
		# Assuming some templates are loaded during init
		email_service.template_cache = {
			"welcome": EmailTemplate(template_id="welcome", name="Welcome", template_type="WELCOME", subject_template="Hi", html_template="<p>Hi</p>")
		}
		templates = await email_service.get_email_templates()
		assert len(templates) == 1
		assert templates[0].template_id == "welcome"

	@pytest.mark.asyncio
	async def test_get_delivery_status(self, email_service):
		tracking_id = "test_track_id"
		email_service.events[tracking_id] = [
			MagicMock(
				event_type=EmailEventType.SEND,
				recipient="test@example.com",
				provider=EmailProvider.SMTP,
				timestamp=datetime.now() - timedelta(minutes=5),
			),
			MagicMock(event_type=EmailEventType.DELIVERY, recipient="test@example.com", provider=EmailProvider.SMTP, timestamp=datetime.now()),
		]
		status = await email_service.get_delivery_status(tracking_id)
		assert status["status"] == EmailEventType.DELIVERY.value

	@pytest.mark.asyncio
	async def test_send_morning_briefing(self, email_service, mock_user):
		email_service.config.primary_provider = EmailProvider.SMTP
		email_service.provider_health[EmailProvider.SMTP].available = True
		email_service.smtp_service.send_email.return_value = {"success": True, "provider": "smtp", "tracking_id": "smtp_track"}

		result = await email_service.send_morning_briefing(mock_user.email, mock_user.username, [], {}, {}, {})
		assert result["success"] is True
		email_service.smtp_service.send_email.assert_called_once()

	@pytest.mark.asyncio
	async def test_test_authentication_success(self, email_service, mock_settings):
		mock_settings.smtp_host = "smtp.mock.com"
		mock_settings.smtp_username = "user@mock.com"
		mock_settings.smtp_password = "password"
		email_service.config.primary_provider = EmailProvider.SMTP
		email_service.settings = mock_settings

		result = await email_service.test_authentication()
		assert result is True

	@pytest.mark.asyncio
	async def test_test_authentication_fail(self, email_service, mock_settings):
		mock_settings.smtp_host = None
		email_service.config.primary_provider = EmailProvider.SMTP
		email_service.settings = mock_settings

		result = await email_service.test_authentication()
		assert result is False
		assert result is True

	@pytest.mark.asyncio
	async def test_test_authentication_fail(self, email_service, mock_settings):
		mock_settings.smtp_host = None
		email_service.config.primary_provider = EmailProvider.SMTP
		email_service.settings = mock_settings

		result = await email_service.test_authentication()
		assert result is False
