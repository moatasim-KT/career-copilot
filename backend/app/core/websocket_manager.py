from typing import List, Dict
from fastapi import WebSocket
import asyncio
from ..core.logging import get_logger

logger = get_logger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}. Total active connections: {len(self.active_connections)}")

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}. Total active connections: {len(self.active_connections)}")

    async def send_personal_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                await self.disconnect(user_id) # Disconnect if sending fails
        else:
            logger.warning(f"Attempted to send message to disconnected user: {user_id}")

    async def broadcast(self, message: str):
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to user {user_id}: {e}")
                await self.disconnect(user_id) # Disconnect if sending fails

websocket_manager = WebSocketManager()
