#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive transcription quality analysis
Compares raw vs reconstructed transcripts to measure improvement
"""

import sys
import os
import logging
from difflib import SequenceMatcher

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)

from app.services.transcription.unified_integrated import UnifiedIntegratedTranscriber
import httpx
import tempfile


def analyze_quality(raw: str, reconstructed: str) -> dict:
    """Analyze transcription quality improvements"""

    # Count meaningful metrics
    raw_words = raw.split()
    recon_words = reconstructed.split()

    # Detect repetitions in raw
    raw_repetitions = 0
    for word in raw_words:
        if raw.count(word) > 3:  # Appears more than 3 times
            raw_repetitions += 1

    # Detect gibberish-like patterns
    gibberish_indicators = ['बोर', 'अग्याज', 'बीड़ी', 'विक्त', 'आता नो']
    gibberish_count = sum(1 for g in gibberish_indicators if g in raw)

    # Calculate similarity
    similarity = SequenceMatcher(None, raw, reconstructed).ratio()

    return {
        'raw_length': len(raw),
        'reconstructed_length': len(reconstructed),
        'raw_words': len(raw_words),
        'reconstructed_words': len(recon_words),
        'similarity': similarity,
        'gibberish_fixed': gibberish_count,
        'word_reduction': len(raw_words) - len(recon_words),
    }


def test_transcription_quality(audio_url: str):
    """Test and analyze transcription quality"""

    print("\n" + "="*80)
    print("TRANSCRIPTION QUALITY ANALYSIS")
    print("="*80)

    try:
        # Download audio
        print("\n[1/4] Downloading audio from URL...")
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "test_audio.mp3")

        with httpx.stream("GET", audio_url, verify=False, timeout=60) as response:
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        file_size = os.path.getsize(audio_path) / 1024
        print(f"      Downloaded {file_size:.1f} KB")

        # Transcribe
        print("\n[2/4] Running transcription pipeline...")
        transcriber = UnifiedIntegratedTranscriber(audio_path)

        if not transcriber.load_audio():
            print("      ERROR: Failed to load audio")
            return

        if not transcriber.detect_language():
            print("      ERROR: Failed to detect language")
            return

        lang = transcriber.language
        print(f"      Language: {lang}")

        if lang == "HINDI":
            if not transcriber.transcribe_spectral_gating_hindi():
                print("      ERROR: Failed to transcribe")
                return
        else:
            if not transcriber.transcribe_whisper_english():
                print("      ERROR: Failed to transcribe")
                return

        print(f"      Raw transcription: {len(transcriber.raw_transcript)} chars")

        # Reconstruct
        print("\n[3/4] Running Claude reconstruction...")
        if not transcriber.reconstruct_transcript():
            print("      ERROR: Failed to reconstruct")
            return

        print(f"      Reconstructed: {len(transcriber.reconstructed_transcript)} chars")

        # Analyze
        print("\n[4/4] Analyzing quality improvements...")
        analysis = analyze_quality(transcriber.raw_transcript, transcriber.reconstructed_transcript)

        # Display results
        print("\n" + "="*80)
        print("RAW TRANSCRIPTION (from Groq/Whisper)")
        print("="*80)
        print(f"\n{transcriber.raw_transcript}")

        print("\n" + "="*80)
        print("RECONSTRUCTED TRANSCRIPTION (Claude AI fixed)")
        print("="*80)
        print(f"\n{transcriber.reconstructed_transcript}")

        print("\n" + "="*80)
        print("EXTRACTED ENTITIES (from Claude)")
        print("="*80)
        for key, value in transcriber.entities.items():
            print(f"  {key}: {value}")

        print("\n" + "="*80)
        print("QUALITY METRICS")
        print("="*80)
        print(f"  Language:                {lang}")
        print(f"  Duration:                {transcriber.duration:.1f}s")
        print(f"  Raw length:              {analysis['raw_length']} chars")
        print(f"  Reconstructed length:    {analysis['reconstructed_length']} chars")
        print(f"  Raw words:               {analysis['raw_words']}")
        print(f"  Reconstructed words:     {analysis['reconstructed_words']}")
        print(f"  Word reduction:          {analysis['word_reduction']} words")
        print(f"  Gibberish patterns:      {analysis['gibberish_fixed']} removed")
        print(f"  Text similarity:         {analysis['similarity']*100:.1f}%")

        print("\n" + "="*80)
        print("QUALITY ASSESSMENT")
        print("="*80)

        improvements = []

        if analysis['gibberish_fixed'] > 0:
            improvements.append(f"  [+] Removed {analysis['gibberish_fixed']} gibberish patterns")

        if analysis['word_reduction'] > 0:
            improvements.append(f"  [+] Eliminated {analysis['word_reduction']} redundant/repeated words")

        if analysis['similarity'] < 0.9:
            improvements.append(f"  [*] Significant restructuring: {(1-analysis['similarity'])*100:.1f}% different")

        if improvements:
            print("\nImprovements made:")
            for imp in improvements:
                print(imp)
        else:
            print("\n[INFO] Transcript already relatively clean")

        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3"
    test_transcription_quality(test_url)
