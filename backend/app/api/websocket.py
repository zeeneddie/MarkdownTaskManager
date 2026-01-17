"""
WebSocket API for Real-Time Updates

Provides real-time communication for:
- Maintenance scan progress
- Agent status updates
- Scheduler job notifications
- Quality gate results

Uses FastAPI WebSocket with connection manager pattern.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class EventType(str, Enum):
    """WebSocket event types"""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Scan events
    SCAN_STARTED = "scan_started"
    SCAN_PROGRESS = "scan_progress"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"

    # Agent events
    AGENT_STATUS = "agent_status"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"

    # Scheduler events
    JOB_SCHEDULED = "job_scheduled"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_PAUSED = "job_paused"
    JOB_RESUMED = "job_resumed"
    JOB_REMOVED = "job_removed"

    # Quality events
    QUALITY_GATE_STARTED = "quality_gate_started"
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"

    # Kanban events (Week 58)
    KANBAN_ITEM_MOVED = "kanban_item_moved"
    KANBAN_ITEM_CREATED = "kanban_item_created"
    KANBAN_ITEM_UPDATED = "kanban_item_updated"
    ESCALATION_CREATED = "escalation_created"
    ESCALATION_RESOLVED = "escalation_resolved"
    AGENT_TRIGGERED = "agent_triggered"


class Channel(str, Enum):
    """WebSocket subscription channels"""
    MAINTENANCE = "maintenance"
    AGENTS = "agents"
    SCHEDULER = "scheduler"
    QUALITY = "quality"
    KANBAN = "kanban"
    ALL = "all"


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections and subscriptions.

    Features:
    - Multiple channels for different event types
    - Client subscription management
    - Broadcast to all or specific channels
    - Connection health monitoring
    """

    def __init__(self):
        # Active connections per channel
        self.connections: Dict[Channel, Set[WebSocket]] = {
            channel: set() for channel in Channel
        }
        # Client metadata
        self.client_info: Dict[WebSocket, Dict[str, Any]] = {}
        # Connection timestamps
        self.connected_at: Dict[WebSocket, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        channels: List[Channel],
        client_id: Optional[str] = None
    ):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            channels: Channels to subscribe to
            client_id: Optional client identifier
        """
        await websocket.accept()

        # Store connection info
        self.connected_at[websocket] = datetime.now(timezone.utc)
        self.client_info[websocket] = {
            "client_id": client_id,
            "channels": channels,
            "connected_at": self.connected_at[websocket].isoformat()
        }

        # Subscribe to channels
        for channel in channels:
            self.connections[channel].add(websocket)
            # Also add to ALL channel for broadcasts
            if channel != Channel.ALL:
                self.connections[Channel.ALL].add(websocket)

        logger.info(f"WebSocket connected: {client_id or 'anonymous'} to channels {channels}")

        # Send connection confirmation
        await self.send_personal(websocket, {
            "type": EventType.CONNECTED,
            "data": {
                "client_id": client_id,
                "channels": [c.value for c in channels],
                "connected_at": self.connected_at[websocket].isoformat()
            }
        })

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect
        """
        # Get client info for logging
        info = self.client_info.get(websocket, {})
        client_id = info.get("client_id", "anonymous")

        # Remove from all channels
        for channel_connections in self.connections.values():
            channel_connections.discard(websocket)

        # Clean up metadata
        self.client_info.pop(websocket, None)
        self.connected_at.pop(websocket, None)

        logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific client.

        Args:
            websocket: Target WebSocket
            message: Message to send
        """
        try:
            # Add timestamp to message
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(
        self,
        channel: Channel,
        event_type: EventType,
        data: Dict[str, Any]
    ):
        """
        Broadcast a message to all clients in a channel.

        Args:
            channel: Target channel
            event_type: Type of event
            data: Event data
        """
        message = {
            "type": event_type,
            "channel": channel.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Get connections for this channel
        connections = self.connections.get(channel, set()).copy()

        if not connections:
            return

        logger.debug(f"Broadcasting {event_type} to {len(connections)} clients on {channel}")

        # Send to all connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_all(self, event_type: EventType, data: Dict[str, Any]):
        """
        Broadcast to all connected clients.

        Args:
            event_type: Type of event
            data: Event data
        """
        await self.broadcast(Channel.ALL, event_type, data)

    def get_connection_count(self, channel: Optional[Channel] = None) -> int:
        """Get number of active connections."""
        if channel:
            return len(self.connections.get(channel, set()))
        return len(self.connections.get(Channel.ALL, set()))

    def get_connections_info(self) -> List[Dict[str, Any]]:
        """Get info about all active connections."""
        return [
            {
                **info,
                "duration_seconds": (datetime.now(timezone.utc) - self.connected_at[ws]).total_seconds()
            }
            for ws, info in self.client_info.items()
        ]


# Singleton connection manager
manager = ConnectionManager()


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@router.websocket("/ws/maintenance")
async def websocket_maintenance(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for maintenance scan updates.

    **Events received:**
    - `scan_started`: Scan has begun
    - `scan_progress`: Progress update with percentage
    - `scan_completed`: Scan finished successfully
    - `scan_failed`: Scan encountered an error

    **Example connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/maintenance?client_id=dashboard-1');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data.type, data.data);
    };
    ```
    """
    await manager.connect(websocket, [Channel.MAINTENANCE], client_id)

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": EventType.ERROR,
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/agents")
async def websocket_agents(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for agent status updates.

    **Events received:**
    - `agent_status`: Agent availability/status change
    - `agent_task_started`: Agent began a task
    - `agent_task_completed`: Agent finished a task

    **Example connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/agents?client_id=monitor-1');
    ```
    """
    await manager.connect(websocket, [Channel.AGENTS], client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": EventType.ERROR,
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/scheduler")
async def websocket_scheduler(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for scheduler updates.

    **Events received:**
    - `job_scheduled`: New job added
    - `job_started`: Job execution began
    - `job_completed`: Job finished
    - `job_paused`: Job was paused
    - `job_resumed`: Job was resumed
    - `job_removed`: Job was deleted
    """
    await manager.connect(websocket, [Channel.SCHEDULER], client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": EventType.ERROR,
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/kanban")
async def websocket_kanban(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for Kanban board updates.

    **Events received:**
    - `kanban_item_moved`: Item moved between lanes (auto-progression)
    - `kanban_item_created`: New item created
    - `kanban_item_updated`: Item data changed
    - `agent_triggered`: Agent started working on item
    - `escalation_created`: Item escalated to human_needed

    **KaibanJS-Style Live Updates:**
    Connect to receive real-time lane progression during migrations.

    **Example connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/kanban?client_id=dashboard-1');
    ws.onmessage = (event) => {
        const { type, data } = JSON.parse(event.data);
        if (type === 'kanban_item_moved') {
            animateCardMove(data.item_id, data.from_lane, data.to_lane);
        }
    };
    ```
    """
    await manager.connect(websocket, [Channel.KANBAN], client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": EventType.ERROR,
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/all")
async def websocket_all(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for all updates.

    Subscribes to all channels: maintenance, agents, scheduler, quality, kanban.

    **Example connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/all?client_id=admin-1');
    ```
    """
    all_channels = [Channel.MAINTENANCE, Channel.AGENTS, Channel.SCHEDULER, Channel.QUALITY, Channel.KANBAN]
    await manager.connect(websocket, all_channels, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": EventType.ERROR,
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# HTTP ENDPOINTS FOR WEBSOCKET INFO
# ============================================================================

@router.get("/api/websocket/status")
async def get_websocket_status():
    """
    Get WebSocket server status and connection counts.

    **Returns:**
    - Connection counts per channel
    - Total active connections
    - Server health
    """
    return {
        "status": "running",
        "connections": {
            "total": manager.get_connection_count(),
            "maintenance": manager.get_connection_count(Channel.MAINTENANCE),
            "agents": manager.get_connection_count(Channel.AGENTS),
            "scheduler": manager.get_connection_count(Channel.SCHEDULER),
            "quality": manager.get_connection_count(Channel.QUALITY)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/websocket/connections")
async def get_active_connections():
    """
    Get details about active WebSocket connections.

    **Returns:**
    - List of active connections with metadata
    """
    return {
        "connections": manager.get_connections_info(),
        "total": manager.get_connection_count()
    }


# ============================================================================
# BROADCAST HELPER FUNCTIONS (for use by other services)
# ============================================================================

async def broadcast_scan_started(scan_id: str, scope: str, focus_areas: List[str]):
    """Broadcast scan started event."""
    await manager.broadcast(Channel.MAINTENANCE, EventType.SCAN_STARTED, {
        "scan_id": scan_id,
        "scope": scope,
        "focus_areas": focus_areas
    })


async def broadcast_scan_progress(
    scan_id: str,
    progress: int,
    current_step: str,
    findings_count: int = 0
):
    """Broadcast scan progress event."""
    await manager.broadcast(Channel.MAINTENANCE, EventType.SCAN_PROGRESS, {
        "scan_id": scan_id,
        "progress": progress,
        "current_step": current_step,
        "findings_count": findings_count
    })


async def broadcast_scan_completed(
    scan_id: str,
    findings_count: int,
    tasks_created: int,
    duration_seconds: float
):
    """Broadcast scan completed event."""
    await manager.broadcast(Channel.MAINTENANCE, EventType.SCAN_COMPLETED, {
        "scan_id": scan_id,
        "findings_count": findings_count,
        "tasks_created": tasks_created,
        "duration_seconds": duration_seconds
    })


async def broadcast_scan_failed(scan_id: str, error: str):
    """Broadcast scan failed event."""
    await manager.broadcast(Channel.MAINTENANCE, EventType.SCAN_FAILED, {
        "scan_id": scan_id,
        "error": error
    })


async def broadcast_agent_status(
    agent_name: str,
    status: str,
    current_task: Optional[str] = None
):
    """Broadcast agent status update."""
    await manager.broadcast(Channel.AGENTS, EventType.AGENT_STATUS, {
        "agent_name": agent_name,
        "status": status,
        "current_task": current_task
    })


async def broadcast_job_event(
    event_type: EventType,
    job_id: str,
    details: Optional[Dict[str, Any]] = None
):
    """Broadcast scheduler job event."""
    await manager.broadcast(Channel.SCHEDULER, event_type, {
        "job_id": job_id,
        **(details or {})
    })


async def broadcast_quality_gate(
    gate_name: str,
    passed: bool,
    score: float,
    details: Optional[Dict[str, Any]] = None
):
    """Broadcast quality gate result."""
    event_type = EventType.QUALITY_GATE_PASSED if passed else EventType.QUALITY_GATE_FAILED
    await manager.broadcast(Channel.QUALITY, event_type, {
        "gate_name": gate_name,
        "passed": passed,
        "score": score,
        **(details or {})
    })


# ============================================================================
# HELPER TO GET MANAGER INSTANCE
# ============================================================================

def get_websocket_manager() -> ConnectionManager:
    """Get the singleton connection manager."""
    return manager
