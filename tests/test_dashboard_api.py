import pytest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.routes import dashboard as dashboard_route

class DummyConn:
    async def fetchrow(self, query, *args):
        return {
            "total_orders": 3,
            "processing_orders": 1,
            "completed_orders": 2,
            "total_spent": 12.5,
        }

    async def fetch(self, query, *args):
        return [
            {
                "id": 1,
                "status": "completed",
                "total_amount": 5.0,
                "created_at": "2024-01-01T00:00:00",
                "total_duration": 60,
            }
        ]

class DummyConnOrders(DummyConn):
    async def fetchrow(self, query, *args):
        if "FROM videos" in query:
            return {"original_filename": "video.mp4", "duration": 60}
        return await super().fetchrow(query, *args)


@pytest.mark.asyncio
async def test_dashboard_overview():
    conn = DummyConn()
    result = await dashboard_route.dashboard_overview(conn, {"id": 1})
    assert result["total_orders"] == 3
    assert result["completed_orders"] == 2


@pytest.mark.asyncio
async def test_recent_orders():
    conn = DummyConnOrders()
    result = await dashboard_route.recent_orders(conn=conn, current_user={"id": 1})
    assert result[0].id == 1
    assert result[0].video_title == "video.mp4"


@pytest.mark.asyncio
async def test_available_downloads(monkeypatch):
    class Conn(DummyConn):
        async def fetch(self, query, *args):
            return [{"id": 7, "file_path": "file.srt", "original_filename": "vid.mp4"}]

    conn = Conn()
    monkeypatch.setattr(dashboard_route.storage, "generate_presigned_url", lambda *a, **k: "url")
    monkeypatch.setattr(dashboard_route.settings, "USE_OBJECT_STORAGE", False)
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    monkeypatch.setattr(os.path, "getsize", lambda p: 123)

    result = await dashboard_route.available_downloads(conn=conn, current_user={"id": 1})
    assert result[0].download_url == "url"
    assert result[0].file_size == 123
