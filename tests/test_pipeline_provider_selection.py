import subprocess

import pytest

from app.services.pipeline import _get_llm_provider, _get_transcription_provider


def test_transcription_provider_prefers_local_whisper_when_ffmpeg_absent(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    provider = _get_transcription_provider()

    assert provider.__name__ == "LocalWhisperProvider"


def test_llm_provider_requires_claude_cli(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="Claude CLI"):
        _get_llm_provider()
