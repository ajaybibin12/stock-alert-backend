from app.celery_app import celery_app
from app.db.session_sync import SessionLocal
from app.db.models import Alert, AlertHistory, DirectionEnum, User
from app.core.config import settings
from app.services.email_service import send_alert_email

import httpx
from colorama import Fore, init
import redis
import json

init(autoreset=True)


@celery_app.task(name="check_alerts")
def check_alerts():
    print(Fore.BLUE + "Running Celery alert check...")

    db = SessionLocal()

    try:
        # ✅ Load only active alerts
        alerts = db.query(Alert).filter(Alert.is_triggered == False).all()

        if not alerts:
            print(Fore.BLUE + "No active alerts.")
            return

        print(Fore.YELLOW + f"Found {len(alerts)} active alerts")

        r = redis.from_url(settings.REDIS_URL)

        for alert in alerts:
            symbol = alert.symbol.upper()

            # ✅ Finnhub Quote API
            url = (
                f"https://finnhub.io/api/v1/quote?"
                f"symbol={symbol}&token={settings.FINNHUB_API_KEY}"
            )

            try:
                response = httpx.get(url, timeout=10)

                if response.status_code == 429:
                    print(Fore.RED + "Rate Limit Exceeded!")
                    return

                data = response.json()
                current_price = data.get("c")

                if current_price is None:
                    print(Fore.RED + f"No price returned for {symbol}")
                    continue

            except Exception as e:
                print(Fore.RED + f"Error fetching {symbol}: {e}")
                continue

            print(
                Fore.CYAN
                + f"{symbol} → Current: {current_price}, Target: {alert.target_price}"
            )

            # ✅ Determine trigger condition
            triggered = (
                (alert.direction == DirectionEnum.ABOVE and current_price > alert.target_price)
                or
                (alert.direction == DirectionEnum.BELOW and current_price < alert.target_price)
            )

            if not triggered:
                continue

            # ✅ 1. MARK ALERT AS TRIGGERED FIRST
            alert.is_triggered = True

            history = AlertHistory(
                alert_id=alert.id,
                triggered_price=current_price
            )
            db.add(history)

            # ✅ 2. COMMIT TO DB FIRST (IMPORTANT ✅✅✅)
            db.commit()

            # ✅ 3. REFRESH THE ALERT OBJECT (FIXES UI "NO" BUG ✅✅✅)
            db.refresh(alert)

            # ✅ 4. NOW SEND WS MESSAGE
            payload = {
                "type": "alert_triggered",
                "symbol": alert.symbol,
                "current_price": current_price,
                "target_price": alert.target_price,
                "direction": alert.direction.value,
            }

            channel = f"user:{alert.user_id}:alerts"
            r.publish(channel, json.dumps(payload))

            print(Fore.GREEN + f"ALERT TRIGGERED → Published to {channel}")

            # ✅ 5. GET USER EMAIL
            user = db.query(User).filter(User.id == alert.user_id).first()

            if user and user.email:
                try:
                    send_alert_email(
                        to_email=user.email,
                        symbol=alert.symbol,
                        price=current_price,
                        target=alert.target_price
                    )

                    print(Fore.MAGENTA + f"EMAIL SENT → {user.email}")

                except Exception as e:
                    print(Fore.RED + f"EMAIL FAILED → {e}")

    finally:
        # ✅ ALWAYS CLOSE DB
        db.close()
