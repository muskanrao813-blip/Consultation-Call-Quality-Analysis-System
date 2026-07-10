from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_audio_upload_endpoint_accepts_audio_file(tmp_path: Path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt ")

    with patch("app.api.calls.IngestService") as mock_ingest_cls:
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.validate_and_ingest_audio = AsyncMock(return_value={"status": "queued", "call_id": "call-123"})

        with audio_path.open("rb") as audio_file:
            response = client.post(
                "/api/calls/audio-upload",
                files={"file": ("sample.wav", audio_file, "audio/wav")},
            )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["call_id"] == "call-123"
