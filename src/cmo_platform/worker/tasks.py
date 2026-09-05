"""Celery tasks. `ping` is a placeholder proving the queue is wired correctly end to end;
real analysis tasks (run_differential_expression, etc.) land once GEO
ingestion provides data to analyze."""

from __future__ import annotations

import logging

from cmo_platform.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="cmo_platform_ping")
def ping(message: str = "pong") -> str:
    logger.info("ping task receieved: %s", message)
    return message
