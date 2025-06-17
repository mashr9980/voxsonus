from typing import List
from fastapi import APIRouter
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app
from app.models.task import TaskInfo, TaskDetail

router = APIRouter()


def _collect(tasks_by_worker, state: str) -> List[TaskInfo]:
    items: List[TaskInfo] = []
    if not tasks_by_worker:
        return items
    for worker, task_list in tasks_by_worker.items():
        for t in task_list:
            items.append(
                TaskInfo(
                    id=t.get("id"),
                    name=t.get("name"),
                    status=state,
                    worker=worker,
                    args=t.get("args"),
                    kwargs=t.get("kwargs"),
                    eta=t.get("eta"),
                    time_start=t.get("time_start"),
                    runtime=t.get("runtime"),
                )
            )
    return items


@router.get("/tasks", response_model=List[TaskInfo])
async def list_tasks() -> List[TaskInfo]:
    inspector = celery_app.control.inspect()
    tasks: List[TaskInfo] = []
    tasks += _collect(inspector.active() or {}, "active")
    tasks += _collect(inspector.scheduled() or {}, "scheduled")
    tasks += _collect(inspector.reserved() or {}, "reserved")
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task_details(task_id: str) -> TaskDetail:
    result = AsyncResult(task_id, app=celery_app)
    meta = result.backend.get_task_meta(task_id)
    return TaskDetail(
        id=task_id,
        name=getattr(result, "task_name", None),
        status=result.status,
        result=meta.get("result"),
        date_done=meta.get("date_done"),
        traceback=meta.get("traceback"),
        runtime=meta.get("runtime"),
    )
