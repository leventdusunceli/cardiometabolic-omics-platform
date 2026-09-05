from cmo_platform.worker.celery_app import celery_app
from cmo_platform.worker.tasks import ping


def test_ping_task_executes_and_returns_message():
    celery_app.conf.task_always_eager = True
    try:
        result = ping.delay("hello test")
        assert result.get(timeout=5) == "hello test"
    finally:
        celery_app.conf.task_always_eager = False


def test_ping_task_default_message():
    celery_app.conf.task_always_eager = True
    try:
        result = ping.delay()
        assert result.get(timeout=5) == "pong"
    finally:
        celery_app.conf.task_always_eager = False
