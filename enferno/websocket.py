"""Authenticated WebSocket endpoint with connection tracking.

Provides real-time push to connected clients. The frontend (layout.html)
auto-connects and reconnects. Extend _onWsMessage() in layout.html and
broadcast() here to add live features (notifications, status updates, etc).
"""

import asyncio
import json

from quart import Blueprint, websocket
from quart_security import current_user

ws_bp = Blueprint("ws", __name__)

# Connected clients: {user_id: set(queue)}
_clients: dict[str, set[asyncio.Queue]] = {}


def get_connected_users() -> list[str]:
    return list(_clients.keys())


async def broadcast(message: dict, user_id: str | None = None):
    """Send message to one user or all connected users."""
    payload = json.dumps(message)
    targets = (
        _clients.get(user_id, set())
        if user_id
        else {q for qs in _clients.values() for q in qs}
    )
    for queue in targets:
        await queue.put(payload)


@ws_bp.websocket("/ws")
async def ws_endpoint():
    if not current_user or not current_user.is_authenticated:
        await websocket.close(4001, "Unauthorized")
        return

    user_id = str(current_user.id)
    queue: asyncio.Queue = asyncio.Queue()
    _clients.setdefault(user_id, set()).add(queue)

    try:
        await websocket.send(json.dumps({"type": "connected", "user_id": user_id}))

        async def _sender():
            while True:
                msg = await queue.get()
                await websocket.send(msg)

        async def _receiver():
            while True:
                await websocket.receive()

        sender = asyncio.create_task(_sender())
        receiver = asyncio.create_task(_receiver())
        try:
            await asyncio.wait([sender, receiver], return_when=asyncio.FIRST_COMPLETED)
        finally:
            sender.cancel()
            receiver.cancel()
            await asyncio.gather(sender, receiver, return_exceptions=True)
    finally:
        _clients[user_id].discard(queue)
        if not _clients[user_id]:
            del _clients[user_id]
