#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick transcription quality test
Tests current pipeline on a provided audio URL
"""

import sys
import os
import logging

# Fix Windows console encoding for Unicode output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.services.transcription.unified_integrated import UnifiedIntegratedTranscriber
import httpx
import tempfile

def test_transcription(audio_url: str):
    """Test transcription on a provided audio URL"""

    print("\n" + "="*70)
    print("TRANSCRIPTION QUALITY TEST")
    print("="*70)
    print(f"\nInput URL: {audio_url}\n")

    try:
        # Download the audio file
        print("[1/5] Downloading audio...")
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "test_audio.mp3")

        with httpx.stream("GET", audio_url, verify=False, timeout=60) as response:
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        file_size = os.path.getsize(audio_path)
        print(f"    [OK] Downloaded: {file_size} bytes")

        # Run transcription
        print("\n[2/5] Loading audio...")
        transcriber = UnifiedIntegratedTranscriber(audio_path)

        if not transcriber.load_audio():
            print("    [FAIL] Failed to load audio")
            return

        print(f"    [OK] Loaded: {transcriber.duration:.1f}s @ {transcriber.sr}Hz")

        print("\n[3/5] Detecting language...")
        if not transcriber.detect_language():
            print("    [FAIL] Failed to detect language")
            return

        print(f"    [OK] Detected: {transcriber.language}")

        print("\n[4/5] Transcribing...")
        if transcriber.language == "HINDI":
            if not transcriber.transcribe_spectral_gating_hindi():
                print("    [FAIL] Failed to transcribe Hindi")
                return
        else:
            if not transcriber.transcribe_whisper_english():
                print("    [FAIL] Failed to transcribe English")
                return

        print(f"    [OK] Raw transcript: {len(transcriber.raw_transcript)} chars")

        print("\n[5/5] Reconstructing with Claude...")
        if not transcriber.reconstruct_transcript():
            print("    [FAIL] Failed to reconstruct")
            return

        print(f"    [OK] Reconstructed: {len(transcriber.reconstructed_transcript)} chars")

        # Display results
        print("\n" + "="*70)
        print("RAW TRANSCRIPTION (from Whisper/Groq)")
        print("="*70)
        print(transcriber.raw_transcript[:500])
        if len(transcriber.raw_transcript) > 500:
            print(f"... ({len(transcriber.raw_transcript) - 500} more chars)")

        print("\n" + "="*70)
        print("RECONSTRUCTED TRANSCRIPTION (Claude fixed)")
        print("="*70)
        print(transcriber.reconstructed_transcript[:500])
        if len(transcriber.reconstructed_transcript) > 500:
            print(f"... ({len(transcriber.reconstructed_transcript) - 500} more chars)")

        print("\n" + "="*70)
        print("EXTRACTED ENTITIES")
        print("="*70)
        for key, value in transcriber.entities.items():
            print(f"  {key}: {value}")

        print("\n" + "="*70)
        print("QUALITY METRICS")
        print("="*70)
        print(f"Language: {transcriber.language}")
        print(f"Duration: {transcriber.duration:.1f}s")
        print(f"Raw length: {len(transcriber.raw_transcript)} chars")
        print(f"Reconstructed length: {len(transcriber.reconstructed_transcript)} chars")
        print(f"Improvement: {((len(transcriber.reconstructed_transcript) - len(transcriber.raw_transcript)) / max(1, len(transcriber.raw_transcript))) * 100:.1f}%")
        print(f"Claude available: {hasattr(transcriber, 'claude_available')}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test URL from user
    test_url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3"

    test_transcription(test_url)
