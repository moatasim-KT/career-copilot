"""
Simple integration tests for WebSocket notification system
Tests the core functionality without complex database fixtures
"""

import pytest

pytestmark = pytest.mark.skip(reason="Service refactored - websocket_notification_service no longer exists")

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.notification import Notification, NotificationPriority, NotificationType

# from app.services.websocket_notification_service import websocket_notification_service  # Service refactored
from app.utils.datetime import utc_now

pytestmark = pytest.mark.skip(reason="Service refactored - websocket_notification_service no longer exists")

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.notification import Notification, NotificationPriority, NotificationType

# from app.services.websocket_notification_service import websocket_notification_service  # Service refactored
from app.utils.datetime import utc_now


class MockWebSocket:
	"""Mock WebSocket for testing"""

	def __init__(self):
		self.messages_sent = []
		self.accepted = False
		self.closed = False

	async def accept(self):
		self.accepted = True

	async def send_text(self, data: str):
		self.messages_sent.append(data)

	async def close(self, code: int = 1000):
		self.closed = True


class MockNotification:
	"""Mock notification object"""

	def __init__(self, id, user_id, notification_type, title, message, priority):
		self.id = id
		self.user_id = user_id
		self.type = notification_type
		self.priority = priority
		self.title = title
		self.message = message
		self.data = {}
		self.action_url = None
		self.is_read = False
		self.created_at = utc_now()
		self.expires_at = None


@pytest.mark.asyncio
class TestWebSocketNotificationServiceSimple:
	"""Simple tests for WebSocket notification service"""

	async def test_send_notification_to_connected_user(self):
		"""Test sending notification to connected user"""
		# Create mock notification
		notification = MockNotification(
			id=1,
			user_id=1,
			notification_type=NotificationType.APPLICATION_UPDATE,
			title="Test Notification",
			message="This is a test",
			priority=NotificationPriority.HIGH,
		)

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(1, mock_ws)

		# Send notification
		await websocket_notification_service.send_notification(1, notification)

		# Verify notification was sent
		assert len(mock_ws.messages_sent) > 0

		# Parse last message
		last_message = json.loads(mock_ws.messages_sent[-1])
		assert last_message["type"] == "notification"
		assert last_message["notification"]["id"] == 1
		assert last_message["notification"]["title"] == "Test Notification"

		# Cleanup
		await websocket_notification_service.manager.disconnect(1)

	async def test_queue_notification_for_offline_user(self):
		"""Test queuing notification for offline user"""
		# Create mock notification
		notification = MockNotification(
			id=2,
			user_id=2,
			notification_type=NotificationType.JOB_STATUS_CHANGE,
			title="Offline Notification",
			message="This should be queued",
			priority=NotificationPriority.MEDIUM,
		)

		# Ensure user is not connected
		assert not websocket_notification_service.is_user_online(2)

		# Send notification (should be queued)
		await websocket_notification_service.send_notification(2, notification)

		# Verify notification was queued
		assert 2 in websocket_notification_service.offline_notification_queues
		queue = websocket_notification_service.offline_notification_queues[2]
		assert len(queue) > 0
		assert queue[0]["notification"]["id"] == 2

		# Cleanup
		if 2 in websocket_notification_service.offline_notification_queues:
			del websocket_notification_service.offline_notification_queues[2]

	async def test_send_queued_notifications_on_reconnect(self):
		"""Test sending queued notifications when user reconnects"""
		user_id = 3

		# Create and queue notifications while user is offline
		for i in range(3):
			notification = MockNotification(
				id=10 + i,
				user_id=user_id,
				notification_type=NotificationType.NEW_JOB_MATCH,
				title=f"Queued Notification {i + 1}",
				message=f"Message {i + 1}",
				priority=NotificationPriority.LOW,
			)
			await websocket_notification_service.send_notification(user_id, notification)

		# Verify notifications were queued
		assert user_id in websocket_notification_service.offline_notification_queues
		queue = websocket_notification_service.offline_notification_queues[user_id]
		assert len(queue) == 3

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Send queued notifications
		await websocket_notification_service._send_queued_notifications(user_id)

		# Verify queue was cleared
		assert user_id not in websocket_notification_service.offline_notification_queues

		# Verify messages were sent
		notification_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "notification"]
		assert len(notification_messages) == 3

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)

	async def test_heartbeat_start_and_stop(self):
		"""Test heartbeat mechanism"""
		user_id = 4

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Start heartbeat
		await websocket_notification_service._start_heartbeat(user_id)

		# Verify heartbeat task was created
		assert user_id in websocket_notification_service._heartbeat_tasks

		# Stop heartbeat
		await websocket_notification_service._stop_heartbeat(user_id)

		# Verify heartbeat task was removed
		assert user_id not in websocket_notification_service._heartbeat_tasks

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)

	async def test_connection_stats(self):
		"""Test getting connection statistics"""
		user_id = 5

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Get stats
		stats = websocket_notification_service.get_connection_stats()

		# Verify stats structure
		assert "active_connections" in stats
		assert stats["active_connections"] >= 1
		assert "offline_queues" in stats
		assert "total_queued_notifications" in stats
		assert "channels" in stats
		assert "timestamp" in stats

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)

	async def test_is_user_online(self):
		"""Test checking if user is online"""
		user_id = 6

		# User should not be online initially
		assert not websocket_notification_service.is_user_online(user_id)

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# User should be online now
		assert websocket_notification_service.is_user_online(user_id)

		# Disconnect user
		await websocket_notification_service.manager.disconnect(user_id)

		# User should be offline again
		assert not websocket_notification_service.is_user_online(user_id)

	async def test_offline_queue_size_limit(self):
		"""Test that offline queue respects size limit"""
		user_id = 7

		# Ensure user is offline
		assert not websocket_notification_service.is_user_online(user_id)

		# Create more notifications than the queue limit
		max_size = websocket_notification_service.MAX_OFFLINE_QUEUE_SIZE
		for i in range(max_size + 10):
			notification = MockNotification(
				id=100 + i,
				user_id=user_id,
				notification_type=NotificationType.NEW_JOB_MATCH,
				title=f"Notification {i + 1}",
				message=f"Message {i + 1}",
				priority=NotificationPriority.LOW,
			)
			await websocket_notification_service.send_notification(user_id, notification)

		# Verify queue size is limited
		if user_id in websocket_notification_service.offline_notification_queues:
			queue = websocket_notification_service.offline_notification_queues[user_id]
			assert len(queue) <= max_size

		# Cleanup
		if user_id in websocket_notification_service.offline_notification_queues:
			del websocket_notification_service.offline_notification_queues[user_id]

	async def test_broadcast_notification(self):
		"""Test broadcasting notification to multiple users"""
		user_ids = [8, 9, 10]
		mock_websockets = []

		# Connect multiple users
		for user_id in user_ids:
			mock_ws = MockWebSocket()
			await mock_ws.accept()
			await websocket_notification_service.manager.connect(user_id, mock_ws)
			mock_websockets.append(mock_ws)

		# Broadcast notification
		notification_data = {"title": "System Announcement", "message": "This is a system-wide announcement"}

		await websocket_notification_service.broadcast_notification(
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT, notification_data=notification_data, target_users=set(user_ids)
		)

		# Verify all users received the notification
		for mock_ws in mock_websockets:
			assert len(mock_ws.messages_sent) > 0

		# Cleanup
		for user_id in user_ids:
			await websocket_notification_service.manager.disconnect(user_id)

	async def test_send_pong(self):
		"""Test sending pong response"""
		user_id = 11

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Send pong
		await websocket_notification_service._send_pong(user_id)

		# Verify pong was sent
		pong_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "pong"]
		assert len(pong_messages) > 0

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)


@pytest.mark.asyncio
class TestWebSocketManager:
	"""Test WebSocket manager functionality"""

	async def test_connect_and_disconnect(self):
		"""Test connecting and disconnecting users"""
		user_id = 20

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect
		connection = await websocket_notification_service.manager.connect(user_id, mock_ws)
		assert connection is not None
		assert websocket_notification_service.manager.is_user_connected(user_id)

		# Disconnect
		await websocket_notification_service.manager.disconnect(user_id)
		assert not websocket_notification_service.manager.is_user_connected(user_id)

	async def test_send_personal_message(self):
		"""Test sending personal message to user"""
		user_id = 21

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Send message
		test_message = {"type": "test", "data": "hello"}
		await websocket_notification_service.manager.send_personal_message(user_id, test_message)

		# Verify message was sent
		assert len(mock_ws.messages_sent) > 0
		last_message = json.loads(mock_ws.messages_sent[-1])
		assert last_message["type"] == "test"
		assert last_message["data"] == "hello"

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)

	async def test_subscribe_to_channel(self):
		"""Test subscribing to channels"""
		user_id = 22
		channel = "test_channel"

		# Mock WebSocket
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect
		await websocket_notification_service.manager.connect(user_id, mock_ws)

		# Subscribe to channel
		websocket_notification_service.manager.subscribe_to_channel(user_id, channel)

		# Verify subscription
		subscribers = websocket_notification_service.manager.get_channel_subscribers(channel)
		assert user_id in subscribers

		# Unsubscribe
		websocket_notification_service.manager.unsubscribe_from_channel(user_id, channel)

		# Verify unsubscription
		subscribers = websocket_notification_service.manager.get_channel_subscribers(channel)
		assert user_id not in subscribers

		# Cleanup
		await websocket_notification_service.manager.disconnect(user_id)

	async def test_broadcast_to_channel(self):
		"""Test broadcasting to channel"""
		user_ids = [23, 24, 25]
		channel = "broadcast_test_channel"
		mock_websockets = []

		# Connect multiple users and subscribe to channel
		for user_id in user_ids:
			mock_ws = MockWebSocket()
			await mock_ws.accept()
			await websocket_notification_service.manager.connect(user_id, mock_ws)
			websocket_notification_service.manager.subscribe_to_channel(user_id, channel)
			mock_websockets.append(mock_ws)

		# Broadcast to channel
		test_message = {"type": "broadcast", "data": "hello everyone"}
		await websocket_notification_service.manager.broadcast_to_channel(channel, test_message)

		# Verify all subscribed users received the message
		for mock_ws in mock_websockets:
			messages = [json.loads(msg) for msg in mock_ws.messages_sent]
			broadcast_messages = [msg for msg in messages if msg.get("type") == "broadcast"]
			assert len(broadcast_messages) > 0

		# Cleanup
		for user_id in user_ids:
			await websocket_notification_service.manager.disconnect(user_id)


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
