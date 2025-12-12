from fastapi import APIRouter, WebSocket
import asyncio
import redis.asyncio as redis
from colorama import Fore, init
from app.core.config import settings

init(autoreset=True)
router = APIRouter()

# Active connections per user
active_connections: dict[int, list[WebSocket]] = {}

async def send_to_user(user_id: int, message: str):
    """Send message to all active WebSocket connections for a user."""
    if user_id not in active_connections:
        return

    to_remove = []
    for ws in active_connections[user_id]:
        if ws.client_state.name == "CONNECTED":
            try:
                await ws.send_text(message)
                print(Fore.YELLOW + f"WS sending → {message}")
            except Exception as e:
                print(Fore.RED + f"Failed to send WS message: {e}")
                to_remove.append(ws)
        else:
            to_remove.append(ws)

    # Cleanup disconnected sockets
    for ws in to_remove:
        if ws in active_connections[user_id]:
            active_connections[user_id].remove(ws)


@router.websocket("/ws/alerts/{user_id}")
async def websocket_alerts(websocket: WebSocket, user_id: int):
    await websocket.accept()
    print(Fore.GREEN + f"WS connected: user={user_id}")

    # Add connection to active list
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)

    r = redis.from_url(settings.REDIS_URL)
    channel = f"user:{user_id}:alerts"

    try:
        while True:
            # Poll Redis for new messages
            msg = await r.lpop(channel)
            if msg:
                msg_text = msg.decode()
                await send_to_user(user_id, msg_text)

            # Prevent CPU overload
            await asyncio.sleep(0.3)

    except Exception as e:
        print(Fore.RED + f"WebSocket error: {e}")

    finally:
        # Remove connection from active list
        if websocket in active_connections.get(user_id, []):
            active_connections[user_id].remove(websocket)
        try:
            await r.aclose()
        except Exception:
            pass
        print(Fore.RED + f"WS closed for user={user_id}")
