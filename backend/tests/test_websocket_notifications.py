"""
Tests for WebSocket notification system
"""

import pytest

pytestmark = pytest.mark.skip(reason="Service refactored - websocket_notification_service no longer exists")

import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator

from fastapi import WebSocket
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.user import User
from app.services.notification_service import NotificationService

# from app.services.websocket_notification_service import websocket_notification_service  # Service refactored


class MockWebSocket:
	"""Mock WebSocket for testing"""

	def __init__(self):
		self.messages_sent = []
		self.messages_received = []
		self.accepted = False
		self.closed = False
		self.close_code = None

	async def accept(self):
		"""Accept the WebSocket connection"""
		self.accepted = True

	async def send_text(self, data: str):
		"""Send text message"""
		self.messages_sent.append(data)

	async def send_json(self, data: dict):
		"""Send JSON message"""
		self.messages_sent.append(json.dumps(data))

	async def receive_text(self):
		"""Receive text message"""
		if self.messages_received:
			return self.messages_received.pop(0)
		# Simulate disconnect if no messages
		from fastapi import WebSocketDisconnect

		raise WebSocketDisconnect()

	async def close(self, code: int = 1000):
		"""Close the WebSocket"""
		self.closed = True
		self.close_code = code

	def add_received_message(self, message: str):
		"""Add a message to the received queue"""
		self.messages_received.append(message)


@pytest.mark.asyncio
class TestWebSocketNotificationService:
	"""Test WebSocket notification service"""

	async def test_authenticate_websocket_success(self, db_session: AsyncSession, test_user: User):
		"""Test successful WebSocket authentication"""
		user_id = await websocket_notification_service.authenticate_websocket(
			websocket=MockWebSocket(),
			token=None,  # Token not used in current implementation
			db=db_session,
		)

		assert user_id is not None
		assert isinstance(user_id, int)

	async def test_send_notification_to_connected_user(self, db_session: AsyncSession, test_user: User):
		"""Test sending notification to connected user"""
		# Create a notification
		notification = await NotificationService.create_notification(
			db=db_session,
			user_id=test_user.id,
			notification_type=NotificationType.APPLICATION_UPDATE,
			title="Test Notification",
			message="This is a test notification",
			priority=NotificationPriority.HIGH,
		)

		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Send notification
		await websocket_notification_service.send_notification(test_user.id, notification)

		# Verify notification was sent
		assert len(mock_ws.messages_sent) > 0

		# Parse the last message
		last_message = json.loads(mock_ws.messages_sent[-1])
		assert last_message["type"] == "notification"
		assert last_message["notification"]["id"] == notification.id
		assert last_message["notification"]["title"] == "Test Notification"

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_queue_notification_for_offline_user(self, db_session: AsyncSession, test_user: User):
		"""Test queuing notification for offline user"""
		# Create a notification
		notification = await NotificationService.create_notification(
			db=db_session,
			user_id=test_user.id,
			notification_type=NotificationType.JOB_STATUS_CHANGE,
			title="Offline Notification",
			message="This notification should be queued",
			priority=NotificationPriority.MEDIUM,
		)

		# Ensure user is not connected
		assert not websocket_notification_service.is_user_online(test_user.id)

		# Send notification (should be queued)
		await websocket_notification_service.send_notification(test_user.id, notification)

		# Verify notification was queued
		assert test_user.id in websocket_notification_service.offline_notification_queues
		queue = websocket_notification_service.offline_notification_queues[test_user.id]
		assert len(queue) > 0
		assert queue[0]["notification"]["id"] == notification.id

		# Cleanup
		if test_user.id in websocket_notification_service.offline_notification_queues:
			del websocket_notification_service.offline_notification_queues[test_user.id]

	async def test_send_queued_notifications_on_reconnect(self, db_session: AsyncSession, test_user: User):
		"""Test sending queued notifications when user reconnects"""
		# Create notifications while user is offline
		notifications = []
		for i in range(3):
			notification = await NotificationService.create_notification(
				db=db_session,
				user_id=test_user.id,
				notification_type=NotificationType.NEW_JOB_MATCH,
				title=f"Queued Notification {i + 1}",
				message=f"This is queued notification {i + 1}",
				priority=NotificationPriority.LOW,
			)
			notifications.append(notification)

		# Verify notifications were queued
		assert test_user.id in websocket_notification_service.offline_notification_queues
		queue = websocket_notification_service.offline_notification_queues[test_user.id]
		assert len(queue) == 3

		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user (this should send queued notifications)
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Manually trigger sending queued notifications
		await websocket_notification_service._send_queued_notifications(test_user.id)

		# Verify all queued notifications were sent
		assert test_user.id not in websocket_notification_service.offline_notification_queues

		# Verify messages were sent
		notification_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "notification"]
		assert len(notification_messages) == 3

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_heartbeat_mechanism(self, db_session: AsyncSession, test_user: User):
		"""Test heartbeat/ping-pong mechanism"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Start heartbeat
		await websocket_notification_service._start_heartbeat(test_user.id)

		# Wait a bit for heartbeat to potentially send
		await asyncio.sleep(0.1)

		# Stop heartbeat
		await websocket_notification_service._stop_heartbeat(test_user.id)

		# Verify heartbeat task was created and stopped
		assert test_user.id not in websocket_notification_service._heartbeat_tasks

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_handle_ping_message(self, db_session: AsyncSession, test_user: User):
		"""Test handling ping message from client"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Send ping message
		ping_message = json.dumps({"type": "ping"})
		await websocket_notification_service._handle_client_message(test_user.id, ping_message, db_session)

		# Verify pong was sent
		pong_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "pong"]
		assert len(pong_messages) > 0

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_mark_notification_read_via_websocket(self, db_session: AsyncSession, test_user: User):
		"""Test marking notification as read via WebSocket"""
		# Create a notification
		notification = await NotificationService.create_notification(
			db=db_session,
			user_id=test_user.id,
			notification_type=NotificationType.INTERVIEW_REMINDER,
			title="Interview Tomorrow",
			message="You have an interview tomorrow",
			priority=NotificationPriority.URGENT,
		)

		assert not notification.is_read

		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Send mark_read message
		mark_read_message = json.dumps({"type": "mark_read", "notification_id": notification.id})
		await websocket_notification_service._handle_client_message(test_user.id, mark_read_message, db_session)

		# Refresh notification from database
		await db_session.refresh(notification)

		# Verify notification was marked as read
		assert notification.is_read
		assert notification.read_at is not None

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_subscribe_to_notification_types(self, db_session: AsyncSession, test_user: User):
		"""Test subscribing to specific notification types"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Subscribe to notification types
		subscribe_message = json.dumps({"type": "subscribe", "notification_types": ["application_update", "interview_reminder"]})
		await websocket_notification_service._handle_client_message(test_user.id, subscribe_message, db_session)

		# Verify subscription confirmation was sent
		subscription_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "subscription_updated"]
		assert len(subscription_messages) > 0
		assert "application_update" in subscription_messages[0].get("subscribed_types", [])

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_broadcast_notification(self, db_session: AsyncSession, test_user: User):
		"""Test broadcasting notification to multiple users"""
		# Mock WebSocket connections for multiple users
		mock_ws1 = MockWebSocket()
		await mock_ws1.accept()
		await websocket_notification_service.manager.connect(test_user.id, mock_ws1)

		# Broadcast notification
		notification_data = {"title": "System Announcement", "message": "This is a system-wide announcement"}

		await websocket_notification_service.broadcast_notification(
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT, notification_data=notification_data, target_users={test_user.id}
		)

		# Verify notification was sent
		assert len(mock_ws1.messages_sent) > 0

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_connection_stats(self, db_session: AsyncSession, test_user: User):
		"""Test getting connection statistics"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Get stats
		stats = websocket_notification_service.get_connection_stats()

		# Verify stats
		assert "active_connections" in stats
		assert stats["active_connections"] >= 1
		assert "offline_queues" in stats
		assert "channels" in stats

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_offline_queue_size_limit(self, db_session: AsyncSession, test_user: User):
		"""Test that offline queue respects size limit"""
		# Ensure user is offline
		assert not websocket_notification_service.is_user_online(test_user.id)

		# Create more notifications than the queue limit
		max_size = websocket_notification_service.MAX_OFFLINE_QUEUE_SIZE
		for i in range(max_size + 10):
			notification = await NotificationService.create_notification(
				db=db_session,
				user_id=test_user.id,
				notification_type=NotificationType.NEW_JOB_MATCH,
				title=f"Notification {i + 1}",
				message=f"This is notification {i + 1}",
				priority=NotificationPriority.LOW,
			)

		# Verify queue size is limited
		if test_user.id in websocket_notification_service.offline_notification_queues:
			queue = websocket_notification_service.offline_notification_queues[test_user.id]
			assert len(queue) <= max_size

		# Cleanup
		if test_user.id in websocket_notification_service.offline_notification_queues:
			del websocket_notification_service.offline_notification_queues[test_user.id]

	async def test_invalid_json_message_handling(self, db_session: AsyncSession, test_user: User):
		"""Test handling of invalid JSON messages"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Send invalid JSON
		invalid_message = "this is not valid json {"
		await websocket_notification_service._handle_client_message(test_user.id, invalid_message, db_session)

		# Verify error message was sent
		error_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "error"]
		assert len(error_messages) > 0
		assert error_messages[0].get("error") == "invalid_json"

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_unknown_message_type_handling(self, db_session: AsyncSession, test_user: User):
		"""Test handling of unknown message types"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Send unknown message type
		unknown_message = json.dumps({"type": "unknown_type", "data": "test"})
		await websocket_notification_service._handle_client_message(test_user.id, unknown_message, db_session)

		# Verify error message was sent
		error_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "error"]
		assert len(error_messages) > 0
		assert "unknown_message_type" in error_messages[0].get("error", "")

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)


@pytest.mark.asyncio
class TestWebSocketNotificationIntegration:
	"""Integration tests for WebSocket notification system"""

	async def test_notification_creation_triggers_websocket_send(self, db_session: AsyncSession, test_user: User):
		"""Test that creating a notification automatically sends it via WebSocket"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Clear any existing messages
		mock_ws.messages_sent.clear()

		# Create a notification (this should automatically send via WebSocket)
		notification = await NotificationService.create_notification(
			db=db_session,
			user_id=test_user.id,
			notification_type=NotificationType.APPLICATION_UPDATE,
			title="Application Status Changed",
			message="Your application status has been updated",
			priority=NotificationPriority.HIGH,
		)

		# Verify notification was sent via WebSocket
		notification_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "notification"]
		assert len(notification_messages) > 0
		assert notification_messages[0]["notification"]["id"] == notification.id

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)

	async def test_multiple_notification_types(self, db_session: AsyncSession, test_user: User):
		"""Test sending different types of notifications"""
		# Mock WebSocket connection
		mock_ws = MockWebSocket()
		await mock_ws.accept()

		# Connect user
		await websocket_notification_service.manager.connect(test_user.id, mock_ws)

		# Clear any existing messages
		mock_ws.messages_sent.clear()

		# Create different types of notifications
		notification_types = [
			NotificationType.JOB_STATUS_CHANGE,
			NotificationType.APPLICATION_UPDATE,
			NotificationType.INTERVIEW_REMINDER,
			NotificationType.NEW_JOB_MATCH,
			NotificationType.APPLICATION_DEADLINE,
		]

		for notification_type in notification_types:
			await NotificationService.create_notification(
				db=db_session,
				user_id=test_user.id,
				notification_type=notification_type,
				title=f"Test {notification_type.value}",
				message=f"This is a {notification_type.value} notification",
				priority=NotificationPriority.MEDIUM,
			)

		# Verify all notifications were sent
		notification_messages = [json.loads(msg) for msg in mock_ws.messages_sent if json.loads(msg).get("type") == "notification"]
		assert len(notification_messages) == len(notification_types)

		# Verify each notification type was sent
		sent_types = [msg["notification"]["type"] for msg in notification_messages]
		for notification_type in notification_types:
			assert notification_type.value in sent_types

		# Cleanup
		await websocket_notification_service.manager.disconnect(test_user.id)
