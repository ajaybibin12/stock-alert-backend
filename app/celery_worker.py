from app.celery_app import celery_app

# IMPORT TASKS FOR REGISTRATION
import app.tasks.alerts

if __name__ == "__main__":
    celery_app.start()
