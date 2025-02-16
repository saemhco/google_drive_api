from celery import Celery
import os

# Configuración de Celery con Redis
celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)


@celery_app.task
def test_task():
    return "✅ Celery está funcionando correctamente"
