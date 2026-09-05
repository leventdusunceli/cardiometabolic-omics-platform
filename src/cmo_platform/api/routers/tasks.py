"""POST /tasks/ping, this queues a placeholder Celery task
to prove the API-RabbitMQ-Celery wiring is done correctly.
Real analysis endpoints (POST /analyses, GET /analyses/{id})
will be injected once GEO ingestion provides real data to be analyzed
"""

from __future__ import annotations

from fastapi import APIRouter

from cmo_platform.api.schemas import TaskSubmission
from cmo_platform.worker.tasks import ping

router = APIRouter(tags=["tasks"])


@router.post("/tasks/ping", response_model=TaskSubmission)
def submit_ping(message: str = "pong") -> TaskSubmission:
    result = ping.delay(message)
    return TaskSubmission(task_id=result.id)
