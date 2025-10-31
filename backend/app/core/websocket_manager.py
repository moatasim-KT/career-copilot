from typing import Dict, Optional, Set
from fastapi import WebSocket
import json
from datetime import datetime
from ..core.logging import get_logger

logger = get_logger(__name__)


class WebSocketConnection:
	"""Represents a WebSocket connection with metadata."""

	def __init__(self, user_id: int, websocket: WebSocket):
		self.user_id = user_id
		self.websocket = websocket
		self.connected_at = datetime.now()
		self.last_ping = datetime.now()
		self.subscriptions: Set[str] = set()

	async def send_message(self, message: dict):
		"""Send a JSON message to the client."""
		try:
			await self.websocket.send_text(json.dumps(message))
			return True
		except Exception as e:
			logger.error(f"Error sending message to user {self.user_id}: {e}")
			return False

	async def send_text(self, text: str):
		"""Send a text message to the client."""
		try:
			await self.websocket.send_text(text)
			return True
		except Exception as e:
			logger.error(f"Error sending text to user {self.user_id}: {e}")
			return False

	def subscribe(self, channel: str):
		"""Subscribe to a notification channel."""
		self.subscriptions.add(channel)
		logger.debug(f"User {self.user_id} subscribed to channel: {channel}")

	def unsubscribe(self, channel: str):
		"""Unsubscribe from a notification channel."""
		self.subscriptions.discard(channel)
		logger.debug(f"User {self.user_id} unsubscribed from channel: {channel}")

	def is_subscribed(self, channel: str) -> bool:
		"""Check if subscribed to a channel."""
		return channel in self.subscriptions


class WebSocketManager:
	"""Enhanced WebSocket manager with authentication and channel support."""

	def __init__(self):
		self.active_connections: Dict[int, WebSocketConnection] = {}
		self.channels: Dict[str, Set[int]] = {}

	async def connect(self, user_id: int, websocket: WebSocket) -> WebSocketConnection:
		"""Connect a user's WebSocket."""
		await websocket.accept()

		# Disconnect existing connection if any
		if user_id in self.active_connections:
			await self.disconnect(user_id)

		connection = WebSocketConnection(user_id, websocket)
		self.active_connections[user_id] = connection

		logger.info(f"WebSocket connected for user: {user_id}. Total active connections: {len(self.active_connections)}")

		# Send welcome message
		await connection.send_message(
			{
				"type": "connection_established",
				"user_id": user_id,
				"timestamp": datetime.now().isoformat(),
				"message": "WebSocket connection established successfully",
			}
		)

		return connection

	async def disconnect(self, user_id: int):
		"""Disconnect a user's WebSocket."""
		if user_id in self.active_connections:
			connection = self.active_connections[user_id]

			# Remove from all channels
			for channel in list(connection.subscriptions):
				self.unsubscribe_from_channel(user_id, channel)

			# Close WebSocket if still open
			try:
				await connection.websocket.close()
			except Exception as e:
				logger.debug(f"Error closing WebSocket for user {user_id}: {e}")

			del self.active_connections[user_id]
			logger.info(f"WebSocket disconnected for user: {user_id}. Total active connections: {len(self.active_connections)}")

	async def send_personal_message(self, user_id: int, message: dict):
		"""Send a JSON message to a specific user."""
		if user_id in self.active_connections:
			connection = self.active_connections[user_id]
			success = await connection.send_message(message)
			if not success:
				await self.disconnect(user_id)
		else:
			logger.warning(f"Attempted to send message to disconnected user: {user_id}")

	async def send_personal_text(self, user_id: int, text: str):
		"""Send a text message to a specific user."""
		if user_id in self.active_connections:
			connection = self.active_connections[user_id]
			success = await connection.send_text(text)
			if not success:
				await self.disconnect(user_id)
		else:
			logger.warning(f"Attempted to send text to disconnected user: {user_id}")

	async def broadcast_message(self, message: dict, exclude_users: Optional[Set[int]] = None):
		"""Broadcast a JSON message to all connected users."""
		exclude_users = exclude_users or set()
		disconnected_users = []

		for user_id, connection in self.active_connections.items():
			if user_id not in exclude_users:
				success = await connection.send_message(message)
				if not success:
					disconnected_users.append(user_id)

		# Clean up disconnected users
		for user_id in disconnected_users:
			await self.disconnect(user_id)

	async def broadcast_text(self, text: str, exclude_users: Optional[Set[int]] = None):
		"""Broadcast a text message to all connected users."""
		exclude_users = exclude_users or set()
		disconnected_users = []

		for user_id, connection in self.active_connections.items():
			if user_id not in exclude_users:
				success = await connection.send_text(text)
				if not success:
					disconnected_users.append(user_id)

		# Clean up disconnected users
		for user_id in disconnected_users:
			await self.disconnect(user_id)

	def subscribe_to_channel(self, user_id: int, channel: str):
		"""Subscribe a user to a notification channel."""
		if user_id in self.active_connections:
			connection = self.active_connections[user_id]
			connection.subscribe(channel)

			if channel not in self.channels:
				self.channels[channel] = set()
			self.channels[channel].add(user_id)

	def unsubscribe_from_channel(self, user_id: int, channel: str):
		"""Unsubscribe a user from a notification channel."""
		if user_id in self.active_connections:
			connection = self.active_connections[user_id]
			connection.unsubscribe(channel)

		if channel in self.channels:
			self.channels[channel].discard(user_id)
			if not self.channels[channel]:
				del self.channels[channel]

	async def broadcast_to_channel(self, channel: str, message: dict, exclude_users: Optional[Set[int]] = None):
		"""Broadcast a message to all users subscribed to a channel."""
		if channel not in self.channels:
			logger.debug(f"No subscribers for channel: {channel}")
			return

		exclude_users = exclude_users or set()
		disconnected_users = []

		for user_id in self.channels[channel]:
			if user_id not in exclude_users and user_id in self.active_connections:
				connection = self.active_connections[user_id]
				success = await connection.send_message(message)
				if not success:
					disconnected_users.append(user_id)

		# Clean up disconnected users
		for user_id in disconnected_users:
			await self.disconnect(user_id)

	def get_connection_count(self) -> int:
		"""Get the number of active connections."""
		return len(self.active_connections)

	def get_channel_subscribers(self, channel: str) -> Set[int]:
		"""Get the set of user IDs subscribed to a channel."""
		return self.channels.get(channel, set()).copy()

	def is_user_connected(self, user_id: int) -> bool:
		"""Check if a user is connected."""
		return user_id in self.active_connections

	def get_user_subscriptions(self, user_id: int) -> Set[str]:
		"""Get the channels a user is subscribed to."""
		if user_id in self.active_connections:
			return self.active_connections[user_id].subscriptions.copy()
		return set()

	async def ping_all_connections(self):
		"""Send ping to all connections to keep them alive."""
		ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
		await self.broadcast_message(ping_message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
