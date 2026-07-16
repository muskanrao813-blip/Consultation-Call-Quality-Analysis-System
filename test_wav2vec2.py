"""Test Wav2Vec2 Hindi model on real Bajaj Finserv recording."""

import requests
import tempfile
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.transcription.wav2vec2_provider import Wav2Vec2Provider

def main():
    url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

    print("=" * 80)
    print("WAV2VEC2 HINDI TRANSCRIPTION TEST")
    print("=" * 80)
    print()

    # Step 1: Download audio
    print("[Step 1] Downloading audio from Bajaj Finserv CDN...")
    try:
        response = requests.get(url, verify=False, timeout=30)
        audio_file = os.path.join(tempfile.gettempdir(), "test_wav2vec2.mp3")
        with open(audio_file, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {len(response.content)} bytes")
    except Exception as e:
        print(f"ERROR: Failed to download: {e}")
        return

    # Step 2: Transcribe with Wav2Vec2
    print("\n[Step 2] Transcribing with Wav2Vec2 Hindi model...")
    try:
        provider = Wav2Vec2Provider()
        segments = provider.transcribe(audio_file)

        print(f"Transcription complete: {len(segments)} segment(s)")
        print()

        # Display result
        print("=" * 80)
        print("TRANSCRIPTION OUTPUT")
        print("=" * 80)
        print()

        for i, seg in enumerate(segments, 1):
            text = seg.get('text', '')
            start = seg.get('start_s', 0)
            end = seg.get('end_s', 0)
            print(f"[Segment {i}] ({start:.2f}s - {end:.2f}s)")
            print(f"Speaker: {seg.get('speaker', 'unknown')}")
            print(f"Text ({len(text)} chars):")
            print(f"\n{text}\n")

        # Save to file
        with open(os.path.join(tempfile.gettempdir(), 'wav2vec2_result.txt'), 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("WAV2VEC2 HINDI TRANSCRIPTION\n")
            f.write("=" * 80 + "\n\n")
            for i, seg in enumerate(segments, 1):
                f.write(f"[Segment {i}]\n")
                f.write(f"Time: {seg.get('start_s', 0):.2f}s - {seg.get('end_s', 0):.2f}s\n")
                f.write(f"Speaker: {seg.get('speaker', 'unknown')}\n")
                f.write(f"Text:\n{seg.get('text', '')}\n\n")

        print("=" * 80)
        print(f"Results saved to: {tempfile.gettempdir()}/wav2vec2_result.txt")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: Transcription failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
