# app/routers/qstash_alert.py
import asyncio
import json
import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from colorama import Fore, init

from app.core.config import settings
from app.db.models import Alert, AlertHistory, DirectionEnum, User
from app.db.session import get_db
from app.services.email_service import send_alert_email

init(autoreset=True)
router = APIRouter()


@router.post("/schedule")
async def schedule_alert(payload: dict):
    if not getattr(settings, "QSTASH_URL", None) or not getattr(settings, "QSTASH_TOKEN", None):
        raise HTTPException(status_code=500, detail="QStash not configured")

    backend = settings.BACKEND_URL.rstrip("/")
    publish_url = f"{settings.QSTASH_URL.rstrip('/')}/v2/publish/{backend}/tasks/process"

    headers = {
        "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(publish_url, json=payload or {}, headers=headers, timeout=30.0)

    try:
        body = resp.json()
    except:
        body = {"status_code": resp.status_code, "text": resp.text}

    return {"status": "scheduled", "qstash_response": body}


@router.post("/process")
async def process_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    print(Fore.GREEN + "PROCESS TASK STARTED")

    try:
        _incoming = await request.json()
        print(Fore.GREEN + f"Incoming payload: {_incoming}")
    except:
        _incoming = {}

    result = await db.execute(select(Alert).where(Alert.is_triggered == False))
    alerts = result.scalars().all()

    if not alerts:
        print(Fore.BLUE + "No active alerts.")
        return {"message": "No active alerts"}

    print(Fore.YELLOW + f"Found {len(alerts)} active alerts")

    r = redis.from_url(settings.REDIS_URL)

    for alert in alerts:
        symbol = alert.symbol.upper()

        url = (
            f"https://finnhub.io/api/v1/quote?"
            f"symbol={symbol}&token={settings.FINNHUB_API_KEY}"
        )

        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=10.0)
            data = res.json()
            current_price = data.get("c")
            if current_price is None:
                continue
        except:
            continue

        triggered = (
            (alert.direction == DirectionEnum.ABOVE and current_price > alert.target_price)
            or
            (alert.direction == DirectionEnum.BELOW and current_price < alert.target_price)
        )

        if not triggered:
            continue

        alert.is_triggered = True
        history = AlertHistory(alert_id=alert.id, triggered_price=current_price)
        db.add(history)
        await db.commit()
        await db.refresh(alert)

        payload = {
            "type": "alert_triggered",
            "symbol": alert.symbol,
            "current_price": current_price,
            "target_price": alert.target_price,
            "direction": alert.direction.value,
        }

        channel = f"user:{alert.user_id}:alerts"

        try:
            await r.rpush(channel, json.dumps(payload))
            print(Fore.GREEN + f"Redis RPUSH → {channel}")
        except Exception as e:
            print(Fore.RED + f"Redis RPUSH failed: {e}")

        # email sending
        try:
            q = await db.execute(select(User).where(User.id == alert.user_id))
            user = q.scalar_one_or_none()
            if user and user.email:
                asyncio.create_task(
                    asyncio.to_thread(
                        send_alert_email,
                        user.email,
                        alert.symbol,
                        current_price,
                        alert.target_price,
                    )
                )
        except:
            pass

    await r.close()
    return {"status": "processed", "processed": len(alerts)}
