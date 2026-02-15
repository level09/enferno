"""Authenticated WebSocket endpoint with connection tracking.

Provides real-time push to connected clients. The frontend (layout.html)
auto-connects and reconnects. Extend _onWsMessage() in layout.html and
broadcast() here to add live features (notifications, status updates, etc).
"""

import asyncio
import json

from quart import Blueprint, g, session, websocket
from sqlalchemy import select

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
    # quart-security only loads current_user in before_request, not before_websocket.
    # Read the session cookie directly and verify the user exists.
    fs_uniquifier = session.get("_user_id")
    if not fs_uniquifier:
        await websocket.close(4001, "Unauthorized")
        return

    from enferno.user.models import User

    user = (
        await g.db_session.execute(
            select(User).where(User.fs_uniquifier == fs_uniquifier)
        )
    ).scalar_one_or_none()
    if not user or not user.active:
        await websocket.close(4001, "Unauthorized")
        return

    user_id = str(user.id)
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

        async with asyncio.TaskGroup() as tg:
            tg.create_task(_sender())
            tg.create_task(_receiver())
    finally:
        _clients[user_id].discard(queue)
        if not _clients[user_id]:
            del _clients[user_id]
