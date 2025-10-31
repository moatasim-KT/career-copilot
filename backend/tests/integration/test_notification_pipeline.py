"""
Integration tests for the notification system.
Tests the complete notification pipeline from trigger to delivery.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.services.email_template_manager import EmailTemplateManager
from app.services.notification_manager import NotificationManager


@pytest_asyncio.fixture
async def notification_system():
	"""Create notification system components for testing."""
	manager = NotificationManager()
	optimizer = EmailTemplateManager()
	await optimizer.initialize()
	return {"manager": manager, "optimizer": optimizer}


@pytest.mark.asyncio
async def test_morning_briefing_complete_flow(notification_system):
	"""Test complete morning briefing flow from trigger to delivery."""
	with patch.multiple(
		"app.services.notification_manager.NotificationManager",
		_send_email_notification=AsyncMock(return_value={"success": True}),
		_send_in_app_notification=AsyncMock(return_value={"success": True}),
	):
		manager = notification_system["manager"]
		optimizer = notification_system["optimizer"]

		# Setup test data
		test_user = {
			"id": "test_user",
			"email": "test@example.com",
			"preferences": {"morning_briefing_time": "09:00", "notification_channels": ["email", "in_app"]},
		}

		# Trigger morning briefing
		briefing_data = {"pending_applications": 3, "new_jobs": 5, "upcoming_deadlines": 2, "skill_recommendations": ["Python", "React"]}

		# Schedule and verify initial queueing
		scheduled_time = datetime.now().replace(hour=9, minute=0)
		await optimizer.schedule_morning_briefing(
			user_id=test_user["id"], email=test_user["email"], briefing_data=briefing_data, scheduled_time=scheduled_time
		)

		# Verify notification was queued
		assert len(optimizer.notification_queue) > 0

		# Process the queue
		await optimizer._process_notification_queue()

		# Verify notifications were sent through both channels
		manager._send_email_notification.assert_called_once()
		manager._send_in_app_notification.assert_called_once()


@pytest.mark.asyncio
async def test_job_match_notification_pipeline(notification_system):
	"""Test job match notification pipeline from match to delivery."""
	with patch.multiple(
		"app.services.notification_manager.NotificationManager",
		_send_email_notification=AsyncMock(return_value={"success": True}),
		_send_in_app_notification=AsyncMock(return_value={"success": True}),
	):
		manager = notification_system["manager"]

		# Test data
		test_job = {"id": "job123", "title": "Senior Developer", "company": "Tech Corp", "match_score": 0.92, "url": "https://example.com/jobs/123"}

		test_user = {
			"id": "user123",
			"email": "test@example.com",
			"preferences": {"job_match_threshold": 0.8, "notification_channels": ["email", "in_app"]},
		}

		# Trigger job match notification
		await manager.notify_job_match(user_id=test_user["id"], email=test_user["email"], job_data=test_job, match_score=test_job["match_score"])

		# Verify notifications were sent
		call_args_email = manager._send_email_notification.call_args[0][1]
		assert call_args_email["type"] == "job_match"
		assert test_job["title"] in call_args_email["subject"]

		call_args_inapp = manager._send_in_app_notification.call_args[0][1]
		assert call_args_inapp["type"] == "job_match"
		assert test_job["id"] in str(call_args_inapp)


@pytest.mark.asyncio
async def test_deadline_reminder_integration(notification_system):
	"""Test deadline reminder integration through the entire pipeline."""
	with patch.multiple(
		"app.services.notification_manager.NotificationManager",
		_send_email_notification=AsyncMock(return_value={"success": True}),
		_send_in_app_notification=AsyncMock(return_value={"success": True}),
	):
		manager = notification_system["manager"]
		optimizer = notification_system["optimizer"]

		# Test data
		test_application = {
			"id": "app123",
			"company": "Tech Corp",
			"position": "Senior Developer",
			"deadline": datetime.now() + timedelta(days=2),
			"user_id": "user123",
			"user_email": "test@example.com",
		}

		# Schedule deadline reminder
		reminder_time = test_application["deadline"] - timedelta(days=1)
		await optimizer.schedule_deadline_reminder(
			application_id=test_application["id"],
			user_id=test_application["user_id"],
			email=test_application["user_email"],
			deadline_data={
				"company": test_application["company"],
				"position": test_application["position"],
				"deadline": test_application["deadline"],
			},
			scheduled_time=reminder_time,
		)

		# Verify reminder was queued
		assert len(optimizer.notification_queue) > 0

		# Process queue
		await optimizer._process_notification_queue()

		# Verify notifications were sent
		manager._send_email_notification.assert_called_once()
		manager._send_in_app_notification.assert_called_once()


@pytest.mark.asyncio
async def test_notification_delivery_tracking(notification_system):
	"""Test notification delivery tracking and status updates."""
	manager = notification_system["manager"]

	# Test data
	test_notification = {
		"id": "notif123",
		"user_id": "user123",
		"type": "job_match",
		"channels": ["email", "in_app"],
		"content": {"job_id": "job123", "title": "Senior Developer"},
	}

	with patch.multiple(
		"app.services.notification_manager.NotificationManager",
		_send_email_notification=AsyncMock(return_value={"success": True, "message_id": "email123"}),
		_send_in_app_notification=AsyncMock(return_value={"success": True, "notification_id": "inapp123"}),
		_update_notification_status=AsyncMock(),
	):
		# Send notification through multiple channels
		await manager.send_notification(
			notification_id=test_notification["id"], user_id=test_notification["user_id"], notification_data=test_notification
		)

		# Verify delivery status was tracked
		tracking_calls = manager._update_notification_status.call_args_list
		assert len(tracking_calls) == 2  # One call for each channel

		# Verify status updates for each channel
		email_status = tracking_calls[0][1]
		assert email_status["channel"] == "email"
		assert email_status["status"] == "delivered"

		inapp_status = tracking_calls[1][1]
		assert inapp_status["channel"] == "in_app"
		assert inapp_status["status"] == "delivered"
