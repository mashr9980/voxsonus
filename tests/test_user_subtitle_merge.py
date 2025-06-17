import os
import sys
from types import SimpleNamespace
import tempfile
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.modules.setdefault("asyncpg", SimpleNamespace())
sys.modules.setdefault("tensorflow", SimpleNamespace())
sys.modules.setdefault("tensorflow_hub", SimpleNamespace())
sys.modules.setdefault("numpy", SimpleNamespace())
sys.modules.setdefault("soundfile", SimpleNamespace())
sys.modules.setdefault("librosa", SimpleNamespace())
sys.modules.setdefault("assemblyai", SimpleNamespace())
sys.modules.setdefault("scipy", SimpleNamespace(signal=SimpleNamespace()))
sys.modules.setdefault("boto3", SimpleNamespace(session=SimpleNamespace(Session=lambda *a, **k: SimpleNamespace(client=lambda *a, **k: SimpleNamespace()))))
sys.modules.setdefault(
    "botocore.exceptions",
    SimpleNamespace(BotoCoreError=Exception, ClientError=Exception),
)
sys.modules.setdefault("pydantic_settings", SimpleNamespace(BaseSettings=object))
sys.modules.setdefault(
    "pydantic",
    SimpleNamespace(BaseModel=object, Field=object, Extra=SimpleNamespace(ignore="ignore")),
)
sys.modules.setdefault(
    "fastapi",
    SimpleNamespace(
        UploadFile=object,
        HTTPException=Exception,
        File=object,
        Form=object,
        APIRouter=object,
        Depends=lambda *a, **k: None,
        Request=object,
        Security=object,
        status=SimpleNamespace(HTTP_500_INTERNAL_SERVER_ERROR=500),
    ),
)
sys.modules.setdefault("jose", SimpleNamespace(jwt=SimpleNamespace()))
sys.modules.setdefault("passlib.context", SimpleNamespace(CryptContext=lambda *a, **k: None))
sys.modules.setdefault("passlib", SimpleNamespace())
sys.modules.setdefault(
    "pydantic",
    SimpleNamespace(BaseModel=object, Field=object, Extra=SimpleNamespace(ignore="ignore")),
)
sys.modules.setdefault("openai", SimpleNamespace(AsyncOpenAI=object))
import types
moviepy_module = types.ModuleType("moviepy")
moviepy_video_module = types.ModuleType("moviepy.video")
moviepy_video_io_module = types.ModuleType("moviepy.video.io")
video_clip_module = types.ModuleType("moviepy.video.io.VideoFileClip")
video_clip_module.VideoFileClip = lambda *a, **k: SimpleNamespace(audio=SimpleNamespace(write_audiofile=lambda *a, **k: None, close=lambda: None), close=lambda: None)
moviepy_video_io_module.VideoFileClip = video_clip_module.VideoFileClip
moviepy_video_module.io = moviepy_video_io_module
moviepy_module.video = moviepy_video_module
sys.modules.setdefault("moviepy", moviepy_module)
sys.modules.setdefault("moviepy.video", moviepy_video_module)
sys.modules.setdefault("moviepy.video.io", moviepy_video_io_module)
sys.modules.setdefault("moviepy.video.io.VideoFileClip", video_clip_module)

from app.services import subtitle_processor as sp

@pytest.mark.asyncio
async def test_merge_user_subtitles(monkeypatch, tmp_path):
    srt_text = "1\n00:00:00,000 --> 00:00:01,000\nHello\n\n2\n00:00:02,000 --> 00:00:03,000\nWorld\n"
    sub_file = tmp_path / "orig.srt"
    sub_file.write_text(srt_text)
    video_path = tmp_path / "video.mp4"
    video_path.write_text("dummy")

    async def fake_generate(path, genre):
        return [{"start": 500, "end": 700, "text": "[laughter]", "type": "sound", "confidence": 1.0}]

    monkeypatch.setattr(sp, "generate_sound_subtitles", fake_generate)

    output = await sp.merge_user_subtitles_with_sounds(
        str(video_path),
        str(sub_file),
        "general",
        True,
        0,
    )
    assert os.path.exists(output)
    subs = sp.parse_srt_file(output)
    assert any(s["text"] == "[laughter]" for s in subs)

