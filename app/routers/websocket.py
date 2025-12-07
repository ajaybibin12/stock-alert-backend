from fastapi import APIRouter, WebSocket
import asyncio
import redis.asyncio as redis
from colorama import Fore, Style, init
from app.core.config import settings
init(autoreset=True)

router = APIRouter()

@router.websocket("/ws/alerts/{user_id}")
async def websocket_alerts(websocket: WebSocket, user_id: int):
    await websocket.accept()

    print(Fore.GREEN + f"WS connected: user={user_id}")

    # Redis subscriber
    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    channel = f"user:{user_id}:alerts"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message["data"].decode())

            # also allow client to send messages without blocking
            await asyncio.sleep(0.01)

    except Exception as e:
        print(Fore.RED + "WebSocket closed:", e)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()
