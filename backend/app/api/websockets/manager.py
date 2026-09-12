"""WebSocket Connection & Live Broadcast Manager

Enables real-time push updates to the Next.js dashboard whenever interactions
are ingested, queued, enriched by RAG/Gemini AI, or dispatched to customers.
"""

import json
from typing import Any, Dict, List
from fastapi import WebSocket
from app.core.logging import logger


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcasts a JSON-formatted event message to all connected clients."""
        if not self.active_connections:
            return

        payload = {
            "event": event_type,
            "data": data
        }
        message = json.dumps(payload, default=str)
        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket client: {e}")
                dead_connections.append(connection)

        # Clean up any broken sockets
        for dead in dead_connections:
            self.disconnect(dead)


# Singleton instance
ws_manager = WebSocketManager()
