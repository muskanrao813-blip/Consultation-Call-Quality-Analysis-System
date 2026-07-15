#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Gemini 2.0 Flash transcription on real Bajaj audio files"""

import sys, os, io, json, tempfile
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.transcription.gemini_provider import GeminiTranscriptionProvider

TEST_URLS = [
    ("Call 1 (19s)", "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3"),
    ("Call 2 (41s)", "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"),
    ("Call 3 (new)", "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3"),
]

def download(url, name):
    path = os.path.join(tempfile.gettempdir(), f"gemini_test_{name}.mp3")
    print(f"  Downloading {name}...", end=" ", flush=True)
    with httpx.stream("GET", url, verify=False, timeout=60) as r:
        with open(path, 'wb') as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    size_kb = os.path.getsize(path) / 1024
    print(f"{size_kb:.1f} KB")
    return path

def separator(char="=", width=70):
    print(char * width)

def main():
    separator()
    print("GEMINI 2.0 FLASH — TRANSCRIPTION ACCURACY TEST")
    separator()
    print("Engine: Gemini 2.0 Flash (full audio, no chunking, native Hindi)")
    print("Rate limit: 1500 requests/hour (free tier)")
    print()

    provider = GeminiTranscriptionProvider()

    all_results = []

    for label, url in TEST_URLS[:2]:  # test first 2 URLs
        separator("-")
        print(f"TEST: {label}")
        separator("-")

        # Download
        safe_name = label.replace(" ", "_").replace("(", "").replace(")", "")
        audio_path = download(url, safe_name)

        # Transcribe with Gemini
        print(f"\n  Sending to Gemini 2.0 Flash...")
        try:
            result = provider.transcribe_and_extract(audio_path)

            transcript = result.get("transcript", "")
            entities = result.get("entities", {})
            audio_quality = result.get("audio_quality", "unknown")
            confidence = result.get("confidence", "unknown")

            print(f"\n  Audio Quality (Gemini assessment): {audio_quality}")
            print(f"  Confidence (Gemini assessment):    {confidence}")
            print(f"  Transcript length: {len(transcript)} chars")

            separator()
            print("FULL TRANSCRIPT:")
            separator()
            print(transcript)

            separator()
            print("EXTRACTED ENTITIES:")
            separator()
            for key, value in entities.items():
                if value and value not in ["Not mentioned", "Unknown", ""]:
                    print(f"  {key:25s}: {value}")

            all_results.append({
                "label": label,
                "transcript": transcript,
                "entities": entities,
                "audio_quality": audio_quality,
                "confidence": confidence,
            })

        except Exception as e:
            print(f"\n  ERROR: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Save results
    out_path = "gemini_transcription_results.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    separator()
    print(f"Results saved to: {out_path}")
    separator()

if __name__ == "__main__":
    main()
