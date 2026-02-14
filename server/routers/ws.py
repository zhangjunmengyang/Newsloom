"""WebSocket endpoint for real-time pipeline status"""
import asyncio
import json
from datetime import datetime
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.services.pipeline_service import pipeline_service


router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        # Remove dead connections
        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time pipeline updates

    Message format:
    {
        "type": "status" | "progress" | "log" | "error",
        "data": {...},
        "timestamp": "ISO datetime"
    }
    """
    await manager.connect(websocket)

    try:
        # Send initial status
        # Note: We can't use get_db() dependency in WebSocket, so we'll create session manually
        from server.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            latest_run = await pipeline_service.get_latest_run(db)

            if latest_run:
                await websocket.send_json({
                    "type": "status",
                    "data": {
                        "run_id": latest_run.id,
                        "status": latest_run.status,
                        "current_layer": latest_run.current_layer,
                        "progress_percent": latest_run.progress_percent,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                })

        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive message from client (ping/pong for keep-alive)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {},
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat(),
                })

            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        manager.disconnect(websocket)


async def broadcast_pipeline_update(run_id: int, status: str, current_layer: str = None, progress: int = 0):
    """
    Helper function to broadcast pipeline updates
    Should be called from pipeline_service when status changes
    """
    message = {
        "type": "progress",
        "data": {
            "run_id": run_id,
            "status": status,
            "current_layer": current_layer,
            "progress_percent": progress,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    await manager.broadcast(message)


async def broadcast_pipeline_log(message: str, level: str = "info"):
    """Broadcast pipeline log message"""
    msg = {
        "type": "log",
        "data": {
            "message": message,
            "level": level,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    await manager.broadcast(msg)
