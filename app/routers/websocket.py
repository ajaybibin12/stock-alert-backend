from fastapi import APIRouter, WebSocket
import asyncio
import redis.asyncio as redis
from colorama import Fore, init
from app.core.config import settings

init(autoreset=True)
router = APIRouter()

@router.websocket("/ws/alerts/{user_id}")
async def websocket_alerts(websocket: WebSocket, user_id: int):
    await websocket.accept()
    print(Fore.GREEN + f"WS connected: user={user_id}")

    r = redis.from_url(settings.REDIS_URL)
    channel = f"user:{user_id}:alerts"

    try:
        while True:
            # Poll Redis LIST for messages (works with Upstash)
            msg = await r.lpop(channel)

            if msg:
                print(Fore.YELLOW + f"WS sending → {msg}")
                # msg is bytes; decode before sending
                try:
                    await websocket.send_text(msg.decode())
                except Exception as e:
                    print(Fore.RED + f"Failed to send WS message: {e}")

            # prevent 100% CPU
            await asyncio.sleep(0.3)

    except Exception as e:
        print(Fore.RED + f"WebSocket error: {e}")

    finally:
        try:
            await r.aclose()
        except Exception:
            pass
        print(Fore.RED + "WebSocket closed")
