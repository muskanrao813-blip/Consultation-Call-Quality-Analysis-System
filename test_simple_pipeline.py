"""
Simplified test: download audio, transcribe with local Whisper, clean with Claude CLI.
"""

import requests
import tempfile
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.transcription.local_whisper import LocalWhisperProvider
from app.services.llm.transcript_cleaner import TranscriptCleaner

def download_audio(url):
    """Download audio from URL."""
    logger.info(f"[Download] Getting {url[:60]}...")
    try:
        response = requests.get(url, verify=False, timeout=30)
        temp_path = os.path.join(tempfile.gettempdir(), "test_audio.mp3")
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"[Download] Success: {len(response.content)} bytes → {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"[Download] Failed: {e}")
        raise

def transcribe_audio(audio_path):
    """Transcribe with local Whisper."""
    logger.info(f"[Whisper] Starting transcription...")
    provider = LocalWhisperProvider()
    segments = provider.transcribe(audio_path)
    logger.info(f"[Whisper] Got {len(segments)} segments")
    return segments

def clean_transcript(segments):
    """Clean transcription with Claude CLI."""
    if not segments:
        logger.warning("[Clean] No segments to clean")
        return None

    raw_text = '\n'.join([seg.get('text', '') for seg in segments])
    logger.info(f"[Clean] Raw transcript: {len(raw_text)} chars")
    logger.info(f"[Clean] Calling Claude CLI...")

    cleaner = TranscriptCleaner()
    result = cleaner.clean_transcript(raw_text)

    if result.get('cleaned'):
        logger.info(f"[Clean] Cleaned: {len(result['cleaned'])} chars (confidence: {result.get('confidence')})")
        return result
    else:
        logger.warning(f"[Clean] Failed: {result.get('error')}")
        return None

def main():
    url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

    print("=" * 80)
    print("SIMPLE TRANSCRIPTION PIPELINE TEST")
    print("=" * 80)
    print()

    try:
        # Step 1: Download
        audio_path = download_audio(url)

        # Step 2: Transcribe
        segments = transcribe_audio(audio_path)

        # Display raw
        print("\n" + "=" * 80)
        print("RAW TRANSCRIPT")
        print("=" * 80)

        raw_full = '\n'.join([seg.get('text', '') for seg in segments])
        print(f"\nTotal raw length: {len(raw_full)} chars")
        print(f"Segments: {len(segments)}")
        for i, seg in enumerate(segments):
            text = seg.get('text', '')[:80]
            print(f"  [{i+1}] {seg.get('start_s', 0):.1f}s: {len(seg.get('text', ''))} chars")

        # Step 3: Clean
        clean_result = clean_transcript(segments)

        if clean_result and clean_result.get('cleaned'):
            print("\n" + "=" * 80)
            print("CLEANED TRANSCRIPT")
            print("=" * 80)
            cleaned = clean_result['cleaned']
            print(f"\nCleaned length: {len(cleaned)} chars")
            print(f"Confidence: {clean_result.get('confidence')}")
            reduction = len(raw_full) - len(cleaned)
            print(f"Reduction: {reduction} chars ({abs(reduction/len(raw_full)*100):.1f}%)")

            # Save results
            with open(os.path.join(tempfile.gettempdir(), 'test_results.txt'), 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RAW TRANSCRIPT\n")
                f.write("=" * 80 + "\n")
                f.write(raw_full)
                f.write("\n\n")
                f.write("=" * 80 + "\n")
                f.write("CLEANED TRANSCRIPT\n")
                f.write("=" * 80 + "\n")
                f.write(cleaned)

            logger.info(f"\n[Save] Results saved to {tempfile.gettempdir()}/test_results.txt")

        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)

    except Exception as e:
        logger.error(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
