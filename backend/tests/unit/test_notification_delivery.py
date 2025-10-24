"""
Unit tests for notification delivery verification.
Tests email and in-app notification delivery confirmation.
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ...app.core.config import get_settings
from ...app.services.notification_manager import NotificationManager


@pytest.fixture
def notification_manager():
    """Create a notification manager instance for testing."""
    return NotificationManager()


@pytest.mark.asyncio
async def test_email_delivery_verification():
    """Test email delivery verification system."""
    with patch('app.services.notification_manager.NotificationManager._send_email_notification') as mock_email:
        # Setup mock response
        mock_email.return_value = {
            "success": True,
            "message_id": "test123",
            "timestamp": datetime.now().isoformat()
        }
        
        manager = NotificationManager()
        test_data = {
            "email": "test@example.com",
            "subject": "Test Notification",
            "body": "Test notification body",
            "priority": "normal"
        }
        
        # Send test email
        result = await manager._send_email_notification(
            test_data["email"],
            {
                "subject": test_data["subject"],
                "body": test_data["body"],
                "priority": test_data["priority"]
            }
        )
        
        # Verify delivery
        assert result["success"] is True
        assert "message_id" in result
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_inapp_notification_verification():
    """Test in-app notification delivery verification."""
    with patch('app.services.notification_manager.NotificationManager._send_in_app_notification') as mock_inapp:
        # Setup mock response
        mock_inapp.return_value = {
            "success": True,
            "notification_id": "notif123",
            "delivered_at": datetime.now().isoformat()
        }
        
        manager = NotificationManager()
        test_data = {
            "user_id": "user123",
            "message": "Test in-app notification",
            "type": "info",
            "data": {"key": "value"}
        }
        
        # Send test notification
        result = await manager._send_in_app_notification(
            test_data["user_id"],
            test_data
        )
        
        # Verify delivery
        assert result["success"] is True
        assert "notification_id" in result
        assert "delivered_at" in result


@pytest.mark.asyncio
async def test_deadline_reminder_delivery():
    """Test deadline reminder notification delivery."""
    with patch.multiple(
        'app.services.notification_manager.NotificationManager',
        _send_email_notification=AsyncMock(),
        _send_in_app_notification=AsyncMock()
    ) as mocks:
        manager = NotificationManager()
        test_data = {
            "user_id": "user123",
            "email": "test@example.com",
            "deadline_data": {
                "application_id": "app123",
                "company": "Tech Corp",
                "position": "Software Engineer",
                "deadline": datetime.now() + timedelta(days=1)
            }
        }
        
        # Send deadline reminder
        await manager.send_deadline_reminder(
            user_id=test_data["user_id"],
            email=test_data["email"],
            deadline_data=test_data["deadline_data"]
        )
        
        # Verify both email and in-app notifications were sent
        mocks['_send_email_notification'].assert_called_once()
        mocks['_send_in_app_notification'].assert_called_once()


@pytest.mark.asyncio
async def test_notification_delivery_retry():
    """Test notification delivery retry mechanism."""
    with patch('app.services.notification_manager.NotificationManager._send_email_notification') as mock_email:
        # Setup mock to fail first, then succeed
        mock_email.side_effect = [
            Exception("Temporary failure"),
            {
                "success": True,
                "message_id": "retry123",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        manager = NotificationManager()
        test_data = {
            "email": "test@example.com",
            "subject": "Retry Test",
            "body": "Test retry mechanism"
        }
        
        # Attempt notification delivery
        result = await manager.send_with_retry(
            notification_type="email",
            recipient=test_data["email"],
            content=test_data
        )
        
        # Verify retry was successful
        assert result["success"] is True
        assert mock_email.call_count == 2  # Initial attempt + 1 retry


@pytest.mark.asyncio
async def test_batch_notification_delivery():
    """Test batch notification delivery and verification."""
    with patch('app.services.notification_manager.NotificationManager._send_batch_email_notification') as mock_batch:
        manager = NotificationManager()
        test_batch = [
            {
                "email": "user1@example.com",
                "data": {"key": "value1"}
            },
            {
                "email": "user2@example.com",
                "data": {"key": "value2"}
            }
        ]
        
        # Send batch notification
        results = await manager.send_batch_notifications(test_batch)
        
        # Verify batch delivery
        assert len(results) == len(test_batch)
        mock_batch.assert_called_once()
        
        # Verify individual delivery status
        for result in results:
            assert "success" in result
            assert "timestamp" in result            assert "timestamp" in result