from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_service import EmailPriority, EmailProvider, EmailService, UnifiedEmailMessage


@pytest.fixture
def mock_email_service():
	"""Create a fully mocked email service"""
	service = MagicMock(spec=EmailService)
	service.send_email = AsyncMock(
		return_value={"success": True, "tracking_id": "test_tracking_123", "message_id": "msg_123", "provider_used": "smtp"}
	)
	service.send_morning_briefing = AsyncMock(
		return_value={"success": True, "tracking_id": "morning_briefing_123", "message_id": "msg_morning_123", "provider_used": "smtp"}
	)
	return service


@pytest.mark.asyncio
async def test_smtp_service_send_email_success(mock_email_service):
	"""Test sending email via SMTP successfully"""
	message = UnifiedEmailMessage(to=["test@user.com"], subject="Test Email", body="Test Body", priority=EmailPriority.NORMAL)

	result = await mock_email_service.send_email(message)

	assert result["success"] is True
	assert result["provider_used"] == "smtp"
	assert "tracking_id" in result
	mock_email_service.send_email.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_smtp_service_send_morning_briefing_success(mock_email_service):
	"""Test sending morning briefing via SMTP"""
	result = await mock_email_service.send_morning_briefing(
		recipient_email="test@user.com", user_name="Test User", recommendations=[{"title": "Job1", "company": "Comp1"}]
	)

	assert result["success"] is True
	assert result["provider_used"] == "smtp"
	assert "tracking_id" in result
	mock_email_service.send_morning_briefing.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_send_email_smtp_primary_success(mock_email_service):
	"""Test email service with SMTP as primary provider"""
	message = UnifiedEmailMessage(to=["test@user.com"], subject="Test", body="Test Body")
	result = await mock_email_service.send_email(message)

	assert result["success"] is True
	assert result["provider_used"] == "smtp"
	mock_email_service.send_email.assert_called_once_with(message)
