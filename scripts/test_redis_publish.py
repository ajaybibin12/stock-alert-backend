import asyncio
import redis.asyncio as aioredis
from app.core.config import settings
import json

async def send_test_alert(user_id: int):
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    channel = f"user:{user_id}:alerts"
    message = {
        "type": "alert_triggered",
        "symbol": "AAPL",
        "target_price": 180,
        "direction": "above"
    }
    await redis_client.publish(channel, json.dumps(message))
    print("Published alert →", channel)

asyncio.run(send_test_alert(1))
