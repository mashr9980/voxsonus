import json
import time
import hmac
import hashlib
import os
import sys
from types import SimpleNamespace
import pytest
from fastapi import Request, HTTPException
from starlette.background import BackgroundTasks

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide a minimal stub for asyncpg so `app.routes.payments` can be imported
sys.modules.setdefault("asyncpg", SimpleNamespace(Connection=object))
# Stub for pydantic_settings.BaseSettings used by app.core.config
sys.modules.setdefault("pydantic_settings", SimpleNamespace(BaseSettings=object))
sys.modules.setdefault("jose", SimpleNamespace(jwt=SimpleNamespace()))
sys.modules.setdefault("openai", SimpleNamespace(AsyncOpenAI=object))
sys.modules.setdefault("tensorflow", SimpleNamespace())
sys.modules.setdefault("tensorflow_hub", SimpleNamespace())
sys.modules.setdefault("numpy", SimpleNamespace())
sys.modules.setdefault("soundfile", SimpleNamespace())
sys.modules.setdefault("librosa", SimpleNamespace())
sys.modules.setdefault("assemblyai", SimpleNamespace())
sys.modules.setdefault("scipy", SimpleNamespace(signal=SimpleNamespace()))
sys.modules.setdefault("email_validator", SimpleNamespace())
sys.modules.setdefault("multipart", SimpleNamespace())
sys.modules.setdefault("boto3", SimpleNamespace(session=SimpleNamespace(Session=lambda *a, **k: SimpleNamespace(client=lambda *a, **k: SimpleNamespace()))))
sys.modules.setdefault(
    "botocore.exceptions",
    SimpleNamespace(BotoCoreError=Exception, ClientError=Exception),
)

import types
moviepy_module = types.ModuleType("moviepy")
moviepy_video_module = types.ModuleType("moviepy.video")
moviepy_video_io_module = types.ModuleType("moviepy.video.io")
video_clip_module = types.ModuleType("moviepy.video.io.VideoFileClip")
video_clip_module.VideoFileClip = lambda *a, **k: None
moviepy_video_io_module.VideoFileClip = video_clip_module.VideoFileClip
moviepy_video_module.io = moviepy_video_io_module
moviepy_module.video = moviepy_video_module
sys.modules.setdefault("moviepy", moviepy_module)
sys.modules.setdefault("moviepy.video", moviepy_video_module)
sys.modules.setdefault("moviepy.video.io", moviepy_video_io_module)
sys.modules.setdefault("moviepy.video.io.VideoFileClip", video_clip_module)
class DummyCryptContext:
    def __init__(self, *args, **kwargs):
        pass
    def hash(self, value):
        return "hashed"
    def verify(self, value, hashed):
        return True

_passlib_context = SimpleNamespace(CryptContext=DummyCryptContext)
sys.modules.setdefault("passlib.context", _passlib_context)
sys.modules.setdefault("passlib", SimpleNamespace(context=_passlib_context))

# Provide a lightweight stub for stripe with minimal signature verification
def _construct_event(payload, sig_header, secret):
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode()
    try:
        parts = dict(item.split("=") for item in sig_header.split(","))
        signed = f"{parts['t']}.{payload}"
        expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        if parts.get('v1') != expected:
            raise ValueError("Invalid signature")
    except Exception as e:
        raise ValueError("Invalid signature") from e
    return json.loads(payload)

sys.modules.setdefault(
    "stripe",
    SimpleNamespace(
        Webhook=SimpleNamespace(construct_event=_construct_event),
        checkout=SimpleNamespace(Session=SimpleNamespace(retrieve=lambda *_: None)),
        PaymentIntent=SimpleNamespace(retrieve=lambda *_: None),
    ),
)

from app.routes import payments
from app.routes.payments import stripe_webhook
from app.models.order import PaymentStatus, OrderStatus

class DummyConn:
    def __init__(self):
        self.order = {
            "payment_status": PaymentStatus.UNPAID,
            "status": OrderStatus.CREATED,
            "payment_intent_id": "cs_test",
            "id": 1,
            "user_id": 1,
        }

    async def fetchrow(self, query, *args):
        if "SELECT payment_status" in query:
            return {"payment_status": self.order["payment_status"]}
        if "SELECT id, user_id" in query:
            return {"id": self.order["id"], "user_id": self.order["user_id"]}
        return None

    async def execute(self, query, *args):
        if "UPDATE orders" in query:
            # args may be payment_status, status, payment_intent_id, order_id
            if len(args) == 4:
                self.order["payment_status"] = args[0]
                self.order["status"] = args[1]
                self.order["payment_intent_id"] = args[2]
            elif len(args) == 3:
                self.order["payment_status"] = args[0]
                self.order["status"] = args[1]
        return None

    async def close(self):
        pass

@pytest.fixture
def dummy_conn(monkeypatch):
    conn = DummyConn()

    async def fake_log_activity(*args, **kwargs):
        return

    monkeypatch.setattr(payments, "log_activity", fake_log_activity)
    class DummyTask:
        def delay(self, *args, **kwargs):
            return

    monkeypatch.setattr(payments, "process_order_task", DummyTask())

    payments.settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

    yield conn


def _generate_signature(payload: str, secret: str) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    sig = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def _build_request(event: dict, secret: str) -> Request:
    payload = json.dumps(event)
    signature = _generate_signature(payload, secret)
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"stripe-signature", signature.encode())],
    }

    async def receive():
        return {"type": "http.request", "body": payload.encode(), "more_body": False}

    return Request(scope, receive)


@pytest.mark.asyncio
async def test_checkout_session_completed(dummy_conn):
    event = {
        "id": "evt_test",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test",
                "object": "checkout.session",
                "client_reference_id": "1",
                "payment_intent": "pi_test",
                "metadata": {"order_id": "1", "user_id": "1"},
            }
        },
    }
    req = _build_request(event, payments.settings.STRIPE_WEBHOOK_SECRET)
    tasks = BackgroundTasks()
    result = await stripe_webhook(req, tasks, dummy_conn)
    assert result == {"success": True}
    assert dummy_conn.order["payment_status"] == PaymentStatus.PAID
    assert dummy_conn.order["payment_intent_id"] == "pi_test"


@pytest.mark.asyncio
async def test_invalid_signature(dummy_conn):
    event = {"id": "evt_test", "object": "event", "type": "ping", "data": {"object": {}}}
    payload = json.dumps(event).encode()
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"stripe-signature", b"bad")],
    }

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    request = Request(scope, receive)
    tasks = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        await stripe_webhook(request, tasks, dummy_conn)
    assert exc.value.status_code == 400
