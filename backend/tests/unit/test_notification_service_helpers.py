"""Unit tests covering helper utilities in UnifiedNotificationService."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from app.models.notification import NotificationPriority, NotificationType
from app.services.notification_service import NotificationChannel, UnifiedNotificationService


class _WebSocketStub:
	"""Simple stub to capture messages sent via send_json."""

	def __init__(self) -> None:
		self.sent: List[Dict[str, Any]] = []

	async def send_json(self, payload: Dict[str, Any]) -> None:
		self.sent.append(payload)


@pytest.mark.asyncio
async def test_get_user_preferred_channels_defaults() -> None:
	service = UnifiedNotificationService()

	channels = await service._get_user_preferred_channels(user_id=1)

	assert channels == [NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]


@pytest.mark.asyncio
async def test_queue_notification_trims_old_entries() -> None:
	service = UnifiedNotificationService()
	service.MAX_OFFLINE_QUEUE_SIZE = 2

	for idx in range(3):
		await service._queue_notification(user_id=99, notification_data={"id": idx})

	assert len(service.offline_notification_queues[99]) == 2
	assert [item["id"] for item in service.offline_notification_queues[99]] == [1, 2]


@pytest.mark.asyncio
async def test_send_queued_notifications_flushes_queue() -> None:
	service = UnifiedNotificationService()
	service.offline_notification_queues[5] = [{"id": 1}, {"id": 2}]
	websocket = _WebSocketStub()

	await service._send_queued_notifications(websocket, user_id=5)

	assert websocket.sent == [{"id": 1}, {"id": 2}]
	assert service.offline_notification_queues[5] == []


@pytest.mark.asyncio
async def test_send_websocket_notification_falls_back_to_queue(monkeypatch) -> None:
	service = UnifiedNotificationService()
	mock_manager = SimpleNamespace(send_to_user=AsyncMock(return_value=False))
	service.websocket_manager = mock_manager

	payload = {"id": 123, "message": "hello"}
	await service.send_websocket_notification(user_id=7, notification_data=payload)

	assert service.offline_notification_queues[7] == [payload]
	mock_manager.send_to_user.assert_awaited_once_with(7, payload)


@pytest.mark.asyncio
async def test_deliver_notification_routes_to_websocket(monkeypatch) -> None:
	service = UnifiedNotificationService()
	mock_send = AsyncMock()
	monkeypatch.setattr(service, "send_websocket_notification", mock_send)

	notification = SimpleNamespace(
		id=1,
		type=NotificationType.SYSTEM_ANNOUNCEMENT,
		title="Hello",
		message="World",
		priority=NotificationPriority.MEDIUM,
		data={},
		action_url="/",
		created_at=datetime.now(UTC),
		user_id=42,
	)

	await service._deliver_notification(notification, [NotificationChannel.WEBSOCKET])

	mock_send.assert_awaited_once()
