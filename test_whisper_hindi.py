"""Test Whisper with explicit Hindi language and optimized parameters."""

import requests
import tempfile
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

def test_whisper():
    url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

    print("=" * 80)
    print("WHISPER HINDI TRANSCRIPTION TEST (Optimized)")
    print("=" * 80)
    print()

    # Download
    print("[1] Downloading audio...")
    response = requests.get(url, verify=False, timeout=30)
    audio_file = os.path.join(tempfile.gettempdir(), "test_whisper_hindi.mp3")
    with open(audio_file, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded: {len(response.content)} bytes")
    print()

    # Test with Whisper
    print("[2] Loading Whisper and transcribing...")
    try:
        import whisper

        # Try base model for better accuracy
        print("Loading whisper 'base' model (better accuracy than 'tiny' for degraded audio)...")
        model = whisper.load_model("base")

        print("Transcribing with language=hi, temperature=0...")
        result = model.transcribe(
            audio_file,
            language="hi",
            temperature=0,  # Deterministic output
            verbose=False,
        )

        print()
        print("=" * 80)
        print("TRANSCRIPTION RESULT")
        print("=" * 80)
        print()

        print(f"Detected Language: {result.get('language', 'unknown')}")
        print(f"Segments: {len(result.get('segments', []))}")
        print()

        for i, seg in enumerate(result.get('segments', []), 1):
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = seg.get('text', '')
            print(f"[{i}] ({start:.2f}s - {end:.2f}s)")
            print(f"    {text}")
            print()

        # Full text
        full_text = ''.join([seg.get('text', '') for seg in result.get('segments', [])])
        print("=" * 80)
        print("FULL TEXT")
        print("=" * 80)
        print(full_text)

        # Save
        with open(os.path.join(tempfile.gettempdir(), 'whisper_hindi_result.txt'), 'w', encoding='utf-8') as f:
            f.write(full_text)
        print()
        print("Saved to temp/whisper_hindi_result.txt")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_whisper()
