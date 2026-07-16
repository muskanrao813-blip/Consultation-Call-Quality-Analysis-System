"""
Test the unified transcription pipeline on a real recording URL.
Stages:
1. Download audio from URL
2. Convert to WAV with enhancement
3. Transcribe with faster-whisper
4. Clean with Claude CLI
5. Display results
"""

import requests
import tempfile
import os
import subprocess
import sys

# Add app to path
sys.path.insert(0, '/root/dietician-qa')

from app.services.transcription.unified_transcriber import UnifiedTranscriber

def test_pipeline():
    url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

    print("=" * 80)
    print("UNIFIED TRANSCRIPTION PIPELINE TEST")
    print("=" * 80)

    # Step 0: Download
    print("\n[Step 0] Downloading audio...")
    try:
        response = requests.get(url, verify=False, timeout=30)
        temp_path = os.path.join(tempfile.gettempdir(), "test_unified.mp3")
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {len(response.content)} bytes")
    except Exception as e:
        print(f"ERROR: Failed to download: {e}")
        return

    # Step 1-3: Run unified pipeline
    print("\n[Steps 1-3] Running transcription pipeline...")
    try:
        segments, metadata = UnifiedTranscriber.transcribe_and_cleanup(temp_path)

        print(f"\nPipeline Results:")
        print(f"  Provider: {metadata.get('provider')}")
        print(f"  Segments: {len(segments)}")

        print(f"\nPipeline Steps:")
        for step in metadata.get('steps', []):
            status = "✓" if step['status'] == 'success' else "✗" if step['status'] == 'failed' else "-"
            print(f"  {status} {step['step']}: {step['status']}")

        # Display transcriptions
        print("\n" + "=" * 80)
        print("TRANSCRIPTION RESULTS")
        print("=" * 80)

        for i, seg in enumerate(segments):
            print(f"\n[Segment {i+1}]")
            print(f"  Time: {seg.get('start_s', 0):.1f}s - {seg.get('end_s', 0):.1f}s")
            print(f"  Speaker: {seg.get('speaker', 'unknown')}")

            raw_text = seg.get('text', '')
            cleaned_text = seg.get('text_cleaned', '')

            if raw_text:
                print(f"\n  RAW TRANSCRIPT:")
                print(f"    {raw_text[:150]}")
                if len(raw_text) > 150:
                    print(f"    ... ({len(raw_text)} chars total)")

            if cleaned_text and cleaned_text != raw_text:
                print(f"\n  CLEANED TRANSCRIPT:")
                print(f"    {cleaned_text[:150]}")
                if len(cleaned_text) > 150:
                    print(f"    ... ({len(cleaned_text)} chars total)")

                improvement = ((len(cleaned_text) - len(raw_text)) / len(raw_text) * 100) if raw_text else 0
                print(f"\n  Quality: {seg.get('cleanup_confidence', 'unknown')}")

        # Save full results
        with open('/tmp/pipeline_results.txt', 'w', encoding='utf-8') as f:
            f.write(f"UNIFIED PIPELINE TEST RESULTS\n")
            f.write(f"Provider: {metadata.get('provider')}\n")
            f.write(f"Total Segments: {len(segments)}\n\n")

            for i, seg in enumerate(segments):
                f.write(f"[Segment {i+1}] {seg.get('start_s', 0):.1f}s\n")
                if seg.get('text'):
                    f.write(f"Raw: {seg.get('text')}\n")
                if seg.get('text_cleaned'):
                    f.write(f"Cleaned: {seg.get('text_cleaned')}\n")
                f.write("\n")

        print("\n" + "=" * 80)
        print("Results saved to /tmp/pipeline_results.txt")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: Pipeline failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
