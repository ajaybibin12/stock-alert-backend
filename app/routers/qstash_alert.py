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


# ------------------------------------------------------------------
# 1) schedule endpoint - publishes a QStash message that will call /tasks/process
#    (frontend does not need to call this; it's provided for manual triggers)
# ------------------------------------------------------------------
@router.post("/schedule")
async def schedule_alert(payload: dict):
    """
    Publishes a message to QStash which will POST to BACKEND_URL/tasks/process.
    """
    if not getattr(settings, "QSTASH_URL", None) or not getattr(settings, "QSTASH_TOKEN", None):
        raise HTTPException(status_code=500, detail="QStash not configured")

    backend = settings.BACKEND_URL.rstrip("/")  # ensure no trailing slash
    publish_url = f"{settings.QSTASH_URL.rstrip('/')}/v2/publish/{backend}/tasks/process"

    headers = {
        "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(publish_url, json=payload or {}, headers=headers, timeout=30.0)

    try:
        body = resp.json()
    except Exception:
        body = {"status_code": resp.status_code, "text": resp.text}

    return {"status": "scheduled", "qstash_response": body}


# ------------------------------------------------------------------
# 2) process endpoint - QStash (or manual POST) calls this to run the alert logic
#    This is the exact replacement of your Celery check_alerts() logic.
# ------------------------------------------------------------------
@router.post("/process")
async def process_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
    upstash_signature: str | None = Header(None),
):
    """
    Called by QStash (or by you manually) to run alert checks.
    Keeps the exact logic of the previous Celery task:
      - query untriggered alerts
      - call Finnhub
      - if triggered: mark alert, insert AlertHistory, commit, publish to Redis channel, send email
    """
    # read body if any (QStash sends payload)
    try:
        _incoming = await request.json()
    except Exception:
        _incoming = {}

    # Query untriggered alerts
    result = await db.execute(select(Alert).where(Alert.is_triggered == False))
    alerts = result.scalars().all()

    if not alerts:
        print(Fore.BLUE + "No active alerts.")
        return {"message": "No active alerts"}

    print(Fore.YELLOW + f"Found {len(alerts)} active alerts")

    # Redis async client (pub/sub)
    r = redis.from_url(settings.REDIS_URL)

    try:
        for alert in alerts:
            symbol = alert.symbol.upper()

            # Finnhub Quote API
            url = (
                f"https://finnhub.io/api/v1/quote?"
                f"symbol={symbol}&token={settings.FINNHUB_API_KEY}"
            )

            try:
                async with httpx.AsyncClient() as client:
                    res = await client.get(url, timeout=10.0)

                if res.status_code == 429:
                    print(Fore.RED + "Rate Limit Exceeded!")
                    # stop current run; QStash will handle retries (or you can schedule again)
                    return {"error": "rate_limit"}

                data = res.json()
                current_price = data.get("c")
                if current_price is None:
                    print(Fore.RED + f"No price returned for {symbol}")
                    continue

            except Exception as e:
                print(Fore.RED + f"Error fetching {symbol}: {e}")
                continue

            print(Fore.CYAN + f"{symbol} → Current: {current_price}, Target: {alert.target_price}")

            # Determine trigger condition (same as before)
            triggered = (
                (alert.direction == DirectionEnum.ABOVE and current_price > alert.target_price)
                or
                (alert.direction == DirectionEnum.BELOW and current_price < alert.target_price)
            )

            if not triggered:
                continue

            # 1. Mark alert as triggered
            alert.is_triggered = True

            # 2. Create history record
            history = AlertHistory(alert_id=alert.id, triggered_price=current_price)
            db.add(history)

            # 3. Commit to DB
            await db.commit()

            # 4. Refresh alert object
            await db.refresh(alert)

            # 5. Publish WebSocket message via Redis
            payload = {
                "type": "alert_triggered",
                "symbol": alert.symbol,
                "current_price": current_price,
                "target_price": alert.target_price,
                "direction": alert.direction.value,
            }

            channel = f"user:{alert.user_id}:alerts"
            try:
                # redis.publish returns int in sync; async publish returns int as awaitable
                await r.publish(channel, json.dumps(payload))
                print(Fore.GREEN + f"ALERT TRIGGERED → Published to {channel}")
            except Exception as e:
                print(Fore.RED + f"Redis publish failed: {e}")

            # 6. Send email (non-blocking)
            # schedule email send in background thread to avoid blocking event loop
            if alert.user_id:
                try:
                    q = await db.execute(select(User).where(User.id == alert.user_id))
                    user = q.scalar_one_or_none()
                except Exception as e:
                    print(Fore.RED + f"Failed to load user: {e}")
                    user = None

                if user and getattr(user, "email", None):
                    try:
                        # run blocking email send in thread so it doesn't block the asyncio loop
                        asyncio.create_task(
                            asyncio.to_thread(
                                send_alert_email,
                                user.email,
                                alert.symbol,
                                current_price,
                                alert.target_price,
                            )
                        )
                        print(Fore.MAGENTA + f"EMAIL QUEUED → {user.email}")
                    except Exception as e:
                        print(Fore.RED + f"EMAIL FAILED (queued): {e}")

        return {"status": "processed", "processed": len(alerts)}

    finally:
        try:
            await r.close()
        except Exception:
            pass
