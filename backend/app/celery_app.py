"""Celery application for async analytics processing."""
import os

from celery import Celery

from .config import settings

celery_app = Celery(
    "shortx",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    task_default_queue="analytics",
)

# Zero-service local run: execute tasks inline (no broker/worker needed) so a
# redirect still records its click without a running Celery worker.
if os.getenv("SHORTX_LOCAL", "").lower() in {"1", "true", "yes"}:
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=False)
