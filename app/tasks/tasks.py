from .celery_app import celery_app
import asyncio
from app.services.subtitle_processor import process_order
from app.core.utils import perform_cleanup_unpaid_order
from app.core import storage

@celery_app.task
def process_order_task(order_id: int) -> None:
    asyncio.run(process_order(order_id))

@celery_app.task
def delete_object_task(object_key: str) -> None:
    storage.delete_object(object_key)

@celery_app.task
def cleanup_unpaid_order_task(order_id: int) -> None:
    asyncio.run(perform_cleanup_unpaid_order(order_id))
