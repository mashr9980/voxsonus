import pytest
from types import SimpleNamespace
from app.routes import tasks as tasks_route


class DummyInspector:
    def active(self):
        return {"worker": [{"id": "abc", "name": "demo", "args": "[]", "kwargs": "{}", "time_start": 1}]}

    def scheduled(self):
        return {}

    def reserved(self):
        return {}


class DummyAsyncResult:
    def __init__(self, task_id):
        self.id = task_id
        self.status = "SUCCESS"
        self.task_name = "demo"
        self.backend = SimpleNamespace(get_task_meta=lambda tid: {"result": "ok", "date_done": "2024-01-01T00:00:00", "traceback": None, "runtime": 0.1})


@pytest.mark.asyncio
async def test_list_tasks(monkeypatch):
    monkeypatch.setattr(tasks_route.celery_app.control, "inspect", lambda: DummyInspector())
    result = await tasks_route.list_tasks()
    assert result[0].id == "abc"
    assert result[0].name == "demo"


@pytest.mark.asyncio
async def test_get_task_details(monkeypatch):
    monkeypatch.setattr(tasks_route, "AsyncResult", lambda tid, app=None: DummyAsyncResult(tid))
    detail = await tasks_route.get_task_details("abc")
    assert detail.id == "abc"
    assert detail.status == "SUCCESS"
    assert detail.result == "ok"
