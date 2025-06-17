from celery import Celery
import os
try:
    import psutil
except Exception:  # pragma: no cover - optional
    psutil = None
from app.core.config import settings

broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND or broker_url

celery_app = Celery('voxsonus', broker=broker_url, backend=result_backend)
celery_app.autodiscover_tasks(["app.tasks"])

def _calculate_concurrency() -> int:
    cpus = os.cpu_count() or 1
    try:
        mem_gb = psutil.virtual_memory().available // (1024 ** 3) if psutil else 1
    except Exception:
        mem_gb = 1
    return max(1, min(cpus, mem_gb * 2))

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    worker_concurrency=_calculate_concurrency(),
)
