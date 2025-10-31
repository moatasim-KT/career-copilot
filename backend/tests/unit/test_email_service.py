import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.email_service import EmailService, UnifiedEmailMessage, EmailProvider
from app.core.config import Settings


@pytest.fixture
def mock_settings():
	settings = Settings(sendgrid_api_key="test_sendgrid_key", sendgrid_from_email="test@example.com", frontend_url="http://localhost:3000")
	with patch("app.core.config.get_settings", return_value=settings):
		yield settings


@pytest.fixture
def mock_email_service(mock_settings):
	service = EmailService()
	# Mock the consolidated service components
	service.smtp_service = AsyncMock()
	service.gmail_service = AsyncMock()
	service.sendgrid_service = AsyncMock()
	return service


@pytest.mark.asyncio
async def test_sendgrid_service_send_morning_briefing_success(mock_sendgrid_service):
	mock_sendgrid_service.client.post.return_value = MagicMock(status_code=202, headers={"X-Message-Id": "test_message_id"})
	mock_sendgrid_service.client.post.return_value.json.return_value = {}

	# Mock template rendering
	mock_template = MagicMock()
	mock_template.render.return_value = "<html>Mocked HTML</html>"
	mock_sendgrid_service.template_env.get_template.return_value = mock_template

	result = await mock_sendgrid_service.send_morning_briefing(
		recipient_email="test@user.com", user_name="Test User", recommendations=[{"title": "Job1", "company": "Comp1"}]
	)

	assert result["success"] is True
	assert "message_id" in result
	mock_sendgrid_service.client.post.assert_called_once()


@pytest.mark.asyncio
async def test_sendgrid_service_test_connection_success(mock_sendgrid_service):
	mock_sendgrid_service.client.get.return_value = MagicMock(status_code=200)
	mock_sendgrid_service.client.get.return_value.json.return_value = {"user": "test"}

	result = await mock_sendgrid_service.test_connection()
	assert result["success"] is True
	assert "profile" in result


@pytest.mark.asyncio
async def test_email_service_send_email_sendgrid_primary_success(mock_email_service):
	mock_email_service.config.primary_provider = EmailProvider.SENDGRID
	mock_email_service.sendgrid_service.send_morning_briefing.return_value = {"success": True}

	message = UnifiedEmailMessage(to="test@user.com", subject="Test", body="Test Body", template_name="morning_briefing", template_data={})
	result = await mock_email_service.send_email(message)

	assert result["success"] is True
	mock_email_service.sendgrid_service.send_morning_briefing.assert_called_once()
	mock_email_service.smtp_service.send_email.assert_not_called()


@pytest.mark.asyncio
async def test_email_service_send_email_sendgrid_fallback_to_smtp(mock_email_service):
	mock_email_service.config.primary_provider = EmailProvider.SENDGRID
	mock_email_service.config.enable_fallback = True
	mock_email_service.sendgrid_service.send_morning_briefing.return_value = {"success": False, "message": "SendGrid failed"}
	mock_email_service.smtp_service.send_email.return_value = {"success": True}

	message = UnifiedEmailMessage(to="test@user.com", subject="Test", body="Test Body", template_name="morning_briefing", template_data={})
	result = await mock_email_service.send_email(message)

	assert result["success"] is True
	mock_email_service.sendgrid_service.send_morning_briefing.assert_called_once()
	mock_email_service.smtp_service.send_email.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_send_morning_briefing_success(mock_email_service):
	mock_email_service.sendgrid_service.send_morning_briefing.return_value = {"success": True}

	result = await mock_email_service.send_morning_briefing(
		recipient_email="test@user.com", user_name="Test User", recommendations=[{"title": "Job1", "company": "Comp1"}]
	)

	assert result["success"] is True
	mock_email_service.sendgrid_service.send_morning_briefing.assert_called_once()
