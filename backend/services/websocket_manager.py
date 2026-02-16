from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections keyed by session_id."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send(self, session_id: str, message: dict):
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WS message for {session_id}: {e}")
                self.disconnect(session_id)
        else:
            logger.warning(f"Attempted to send message to session {session_id}, but no active WebSocket connection found in this process.")


# Global singleton instance
ws_manager = WebSocketManager()
