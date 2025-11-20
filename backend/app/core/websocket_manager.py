import json
import os
from datetime import datetime
from typing import Dict, Optional, Set

from fastapi import WebSocket

from ..core.logging import get_logger

logger = get_logger(__name__)


class WebSocketConnection:
	"""Represents a WebSocket connection with metadata."""

	def __init__(self, user_id: int, websocket: WebSocket, test_mode: bool = False):
		self.user_id = user_id
		self.websocket = websocket
		self.test_mode = test_mode
		self.connected_at = datetime.now()
		self.last_ping = datetime.now()
		self.subscriptions: Set[str] = set()

	async def send_message(self, message: dict):
		"""Send a JSON message to the client."""
		if self.test_mode:
			# In test mode, just log and return success
			logger.debug(f"[TEST MODE] Would send message to user {self.user_id}: {message}")
			return True

		try:
			await self.websocket.send_text(json.dumps(message))
			return True
		except Exception as e:
			logger.error(f"Error sending message to user {self.user_id}: {e}")
			return False

	async def send_text(self, text: str):
		"""Send a text message to the client."""
		if self.test_mode:
			# In test mode, just log and return success
			logger.debug(f"[TEST MODE] Would send text to user {self.user_id}: {text}")
			return True

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

	def __init__(self, test_mode: bool = False):
		"""Initialize WebSocket manager.

		Args:
			test_mode: If True, skip actual WebSocket operations (for testing).
		"""
		self.test_mode = test_mode
		self.active_connections: Dict[int, list[WebSocketConnection]] = {}
		self.channels: Dict[str, Set[int]] = {}

	async def connect(self, user_id: int, websocket: WebSocket) -> WebSocketConnection:
		"""Connect a user's WebSocket.

		The FastAPI endpoint is responsible for accepting the connection. We avoid
		calling `websocket.accept()` here because doing so after the endpoint already
		accepted the socket raises a runtime error. This helper simply records the
		connection and sends the welcome payload.
		"""
		connection = WebSocketConnection(user_id, websocket, test_mode=self.test_mode)

		if user_id not in self.active_connections:
			self.active_connections[user_id] = []

		self.active_connections[user_id].append(connection)

		logger.info(f"WebSocket connected for user: {user_id}. Active sessions: {len(self.active_connections[user_id])}")

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

	async def disconnect(self, user_id: int, connection: Optional[WebSocketConnection] = None):
		"""Disconnect a user's WebSocket.

		Args:
			user_id: The user ID.
			connection: Specific connection to disconnect. If None, disconnects all for user.
		"""
		if user_id in self.active_connections:
			connections_to_remove = [connection] if connection else self.active_connections[user_id][:]

			for conn in connections_to_remove:
				if conn in self.active_connections[user_id]:
					# Remove from all channels
					for channel in list(conn.subscriptions):
						# We only unsubscribe from the channel map if this is the last connection
						# for this user that is subscribed to this channel.
						# However, simpler logic is: just remove this connection's subscription.
						# The channel map tracks user_ids. If user has 0 connections left, remove user_id.
						pass
						# Logic for channel map cleanup is complex with multiple connections.
						# For now, we'll clean up channel map only if user has no connections left.

					# Close WebSocket if still open (skip in test mode to avoid hangs)
					if not self.test_mode:
						try:
							await conn.websocket.close()
						except Exception as e:
							logger.debug(f"Error closing WebSocket for user {user_id}: {e}")

					self.active_connections[user_id].remove(conn)

			if not self.active_connections[user_id]:
				del self.active_connections[user_id]
				# Cleanup channels
				for channel in list(self.channels.keys()):
					if user_id in self.channels[channel]:
						self.channels[channel].discard(user_id)
						if not self.channels[channel]:
							del self.channels[channel]

			logger.info(f"WebSocket disconnected for user: {user_id}. Remaining active sessions: {len(self.active_connections.get(user_id, []))}")

	async def send_personal_message(self, user_id: int, message: dict):
		"""Send a JSON message to a specific user (all their active connections)."""
		if user_id in self.active_connections:
			disconnected_connections = []
			for connection in self.active_connections[user_id]:
				success = await connection.send_message(message)
				if not success:
					disconnected_connections.append(connection)

			# Cleanup failed connections
			for conn in disconnected_connections:
				await self.disconnect(user_id, conn)
		else:
			logger.warning(f"Attempted to send message to disconnected user: {user_id}")

	async def send_personal_text(self, user_id: int, text: str):
		"""Send a text message to a specific user (all their active connections)."""
		if user_id in self.active_connections:
			disconnected_connections = []
			for connection in self.active_connections[user_id]:
				success = await connection.send_text(text)
				if not success:
					disconnected_connections.append(connection)

			# Cleanup failed connections
			for conn in disconnected_connections:
				await self.disconnect(user_id, conn)
		else:
			logger.warning(f"Attempted to send text to disconnected user: {user_id}")

	async def broadcast_message(self, message: dict, exclude_users: Optional[Set[int]] = None):
		"""Broadcast a JSON message to all connected users."""
		exclude_users = exclude_users or set()

		for user_id in list(self.active_connections.keys()):
			if user_id not in exclude_users:
				await self.send_personal_message(user_id, message)

	async def broadcast_text(self, text: str, exclude_users: Optional[Set[int]] = None):
		"""Broadcast a text message to all connected users."""
		exclude_users = exclude_users or set()

		for user_id in list(self.active_connections.keys()):
			if user_id not in exclude_users:
				await self.send_personal_text(user_id, text)

	def subscribe_to_channel(self, user_id: int, channel: str):
		"""Subscribe a user to a notification channel (all active connections)."""
		if user_id in self.active_connections:
			for connection in self.active_connections[user_id]:
				connection.subscribe(channel)

			if channel not in self.channels:
				self.channels[channel] = set()
			self.channels[channel].add(user_id)

	def unsubscribe_from_channel(self, user_id: int, channel: str):
		"""Unsubscribe a user from a notification channel (all active connections)."""
		if user_id in self.active_connections:
			for connection in self.active_connections[user_id]:
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

		for user_id in list(self.channels[channel]):
			if user_id not in exclude_users:
				# send_personal_message handles sending to all user's connections
				# and cleaning up disconnected ones
				await self.send_personal_message(user_id, message)

	def get_connection_count(self) -> int:
		"""Get the number of active users."""
		return len(self.active_connections)

	def get_channel_subscribers(self, channel: str) -> Set[int]:
		"""Get the set of user IDs subscribed to a channel."""
		return self.channels.get(channel, set()).copy()

	def is_user_connected(self, user_id: int) -> bool:
		"""Check if a user is connected."""
		return user_id in self.active_connections

	def get_user_subscriptions(self, user_id: int) -> Set[str]:
		"""Get the channels a user is subscribed to (merges from all connections)."""
		subscriptions = set()
		if user_id in self.active_connections:
			for conn in self.active_connections[user_id]:
				subscriptions.update(conn.subscriptions)
		return subscriptions

	async def ping_all_connections(self):
		"""Send ping to all connections to keep them alive."""
		ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
		await self.broadcast_message(ping_message)


# Global WebSocket manager instance
# Test mode is enabled via DISABLE_AUTH environment variable (used in tests)
websocket_manager = WebSocketManager(test_mode=os.getenv("DISABLE_AUTH") == "true")
