#!/usr/bin/env python3
"""
Test Whisper transcription directly on a real audio file
"""
import os
os.environ['PATH'] = r"C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin;" + os.environ['PATH']

import requests
import tempfile
from app.services.transcription.local_whisper import LocalWhisperProvider

print("\n" + "="*80)
print("TESTING WHISPER TRANSCRIPTION DIRECTLY")
print("="*80)

# Download a test audio file
url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

print(f"\nStep 1: Download audio from URL")
print(f"URL: {url}")

try:
    response = requests.get(url, timeout=30, verify=False, stream=True)
    response.raise_for_status()

    # Save to temp file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "test_audio.mp3")

    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Downloaded: {temp_path}")
    print(f"Size: {os.path.getsize(temp_path)} bytes")

    # Test Whisper transcription
    print(f"\nStep 2: Transcribe with Whisper")
    provider = LocalWhisperProvider()

    print(f"Loading Whisper model...")
    segments = provider.transcribe(temp_path)

    print(f"Transcription complete!")
    print(f"Segments: {len(segments)}")

    print(f"\nTranscription Results:")
    for i, seg in enumerate(segments[:5], 1):
        speaker = seg.get('speaker', 'unknown')
        text = seg.get('text', '')[:100]
        start = seg.get('start_s', 0)
        end = seg.get('end_s', 0)
        print(f"  [{i}] {speaker} ({start:.1f}s-{end:.1f}s): {text}")

    # Check if it's mock or real
    all_text = " ".join([s.get('text', '') for s in segments])
    if "Dietician consultation" in all_text or "Patient response" in all_text:
        print(f"\nResult: MOCK DATA (Not real Whisper!)")
    else:
        print(f"\nResult: REAL WHISPER TRANSCRIPTION!")

    # Cleanup
    os.remove(temp_path)

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
