"""Authenticated WebSocket endpoint with connection tracking."""

import asyncio
import json

from quart import Blueprint, session, websocket

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
    user_id = session.get("_user_id")
    if not user_id:
        await websocket.close(4001, "Unauthorized")
        return

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
