"""Script for the Celery application, using RabbitMQ (setting.rabbitmq_url) as the message broker
Results are stored in the same Postgres database as everything else, via SQLAlchemy in each
task itself. Using Celery's result backend as well would be a second, redundant
source of truth for the same data.`
"""

from __future__ import annotations

from celery import Celery

from cmo_platform.config import settings

celery_app = Celery(
    "cmo_platform", broker=settings.rabbitmq_url, include=["cmo_platform.worker.tasks"]
)
celery_app.conf.task_default_queue = "cmo_platform"
