from celery import Celery
from app.core.config import settings
import ssl  

redis_ssl_options = {
    "ssl_cert_reqs": ssl.CERT_NONE
}

celery_app = Celery(
    "stock_alert_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    broker_use_ssl=redis_ssl_options,
    redis_backend_use_ssl=redis_ssl_options,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# AUTO DISCOVER TASKS HERE (VERY IMPORTANT)
celery_app.autodiscover_tasks(["app.tasks"])

# ADD BEAT SCHEDULE
celery_app.conf.beat_schedule = {
    "check-alerts-every-10-seconds": {
        "task": "check_alerts",
        "schedule": 10.0,
    }
}
