import os

from celery import Celery


broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("vrptw", broker=broker_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Good defaults for long CPU tasks
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
# Discover tasks in api.tasks
celery_app.autodiscover_tasks(["api"])
