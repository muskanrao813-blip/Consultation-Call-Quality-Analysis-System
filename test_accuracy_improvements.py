#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test and measure accuracy improvements from all enhancements
Tier 1: VAD chunking + Domain vocabulary + Validation + Confidence scoring
"""

import sys
import os
import logging
import json
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

from app.services.transcription.unified_integrated import UnifiedIntegratedTranscriber
from app.services.transcription.confidence_scorer import ConfidenceScorer
import httpx
import tempfile


def test_single_call(audio_url: str) -> dict:
    """Test transcription on a single audio file"""

    print(f"\n{'='*80}")
    print(f"TESTING: {audio_url.split('/')[-1]}")
    print(f"{'='*80}")

    try:
        # Download audio
        print("\n[1/6] Downloading audio...")
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "test_audio.mp3")

        with httpx.stream("GET", audio_url, verify=False, timeout=60) as response:
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        file_size = os.path.getsize(audio_path) / 1024
        print(f"      Downloaded: {file_size:.1f} KB")

        # Transcribe
        print("\n[2/6] Running transcription with all improvements...")
        transcriber = UnifiedIntegratedTranscriber(audio_path)

        if not transcriber.load_audio():
            return {"status": "error", "reason": "Failed to load audio"}

        if not transcriber.detect_language():
            return {"status": "error", "reason": "Failed to detect language"}

        lang = transcriber.language
        print(f"      Language: {lang}")

        if lang == "HINDI":
            if not transcriber.transcribe_spectral_gating_hindi():
                return {"status": "error", "reason": "Failed to transcribe Hindi"}
        else:
            if not transcriber.transcribe_whisper_english():
                return {"status": "error", "reason": "Failed to transcribe English"}

        print(f"      Raw: {len(transcriber.raw_transcript)} chars")

        # Reconstruct with validation
        print("\n[3/6] Reconstructing with Claude (+ validation)...")
        if not transcriber.reconstruct_transcript():
            return {"status": "error", "reason": "Failed to reconstruct"}

        print(f"      Reconstructed: {len(transcriber.reconstructed_transcript)} chars")
        if transcriber.validation_metrics:
            print(f"      Validation: {transcriber.validation_metrics}")

        # Extract entities
        print("\n[4/6] Extracting entities...")
        if not transcriber.extract_entities():
            return {"status": "error", "reason": "Failed to extract entities"}

        print(f"      Entities: {list(transcriber.entities.keys())}")

        # Calculate confidence
        print("\n[5/6] Calculating confidence metrics...")
        confidence = ConfidenceScorer.score_transcription(
            transcriber.raw_transcript,
            transcriber.reconstructed_transcript,
            lang
        )

        print(f"      Quality: {confidence.get('reconstruction_quality', 'unknown')}")
        print(f"      Confidence: {confidence['confidence']} ({confidence['confidence_score']})")
        print(f"      Coherence Improved: {confidence.get('coherence_improved', 'N/A')}")
        print(f"      Word Count Reasonable: {confidence.get('word_count_reasonable', 'N/A')}")
        print(f"      Reliable: {confidence.get('is_reliable', 'N/A')}")
        print(f"      Needs Review: {confidence['needs_review']}")

        # Display results
        print("\n[6/6] Results Summary")
        print("-" * 80)
        print(f"RAW TRANSCRIPTION ({len(transcriber.raw_transcript)} chars):")
        print(f"  {transcriber.raw_transcript[:200]}...")

        print(f"\nRECONSTRUCTED ({len(transcriber.reconstructed_transcript)} chars):")
        print(f"  {transcriber.reconstructed_transcript[:200]}...")

        print(f"\nENTITIES:")
        for key, value in transcriber.entities.items():
            print(f"  {key}: {value}")

        return {
            "status": "success",
            "language": lang,
            "duration": transcriber.duration,
            "raw_length": len(transcriber.raw_transcript),
            "reconstructed_length": len(transcriber.reconstructed_transcript),
            "raw_words": len(transcriber.raw_transcript.split()),
            "reconstructed_words": len(transcriber.reconstructed_transcript.split()),
            "confidence_metrics": confidence,
            "validation_metrics": transcriber.validation_metrics,
            "entities": transcriber.entities,
        }

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "reason": str(e)}


def main():
    """Test multiple audio files and measure improvement"""

    print("\n" + "=" * 80)
    print("ACCURACY IMPROVEMENT TEST SUITE - TIER 1 ENHANCEMENTS")
    print("=" * 80)
    print("\nTesting:")
    print("  [1] VAD-based smart chunking")
    print("  [2] Bajaj-specific domain vocabulary")
    print("  [3] Post-reconstruction validation")
    print("  [4] Confidence scoring (WER/CER/BLEU)")

    # Test URLs
    test_cases = [
        {
            "name": "Hindi Call (Bajaj Test 1)",
            "url": "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3",
            "expected_lang": "HINDI",
        },
        {
            "name": "Hindi Call (Bajaj Test 2)",
            "url": "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3",
            "expected_lang": "HINDI",
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"TEST {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'#' * 80}")

        result = test_single_call(test_case['url'])
        result['test_name'] = test_case['name']
        results.append(result)

    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY - ALL TESTS")
    print("=" * 80)

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']

    print(f"\nPassed: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")

    if successful:
        print("\n" + "-" * 80)
        print("RECONSTRUCTION QUALITY METRICS (Average)")
        print("-" * 80)

        avg_confidence_score = sum(r['confidence_metrics']['confidence_score'] for r in successful) / len(successful)
        avg_raw_len = sum(r['raw_length'] for r in successful) / len(successful)
        avg_recon_len = sum(r['reconstructed_length'] for r in successful) / len(successful)

        print(f"  Average Confidence Score: {avg_confidence_score:.2f}/1.0")
        print(f"  Average Raw Length: {avg_raw_len:.0f} chars")
        print(f"  Average Reconstructed Length: {avg_recon_len:.0f} chars")
        print(f"  Average Compression: {(1 - avg_recon_len/avg_raw_len)*100:.1f}%")

        print("\nCONFIDENCE LEVELS:")
        confidence_counts = {}
        for r in successful:
            conf = r['confidence_metrics']['confidence']
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

        for conf_level, count in sorted(confidence_counts.items()):
            print(f"  {conf_level}: {count}")

        print("\nREVIEW FLAGS:")
        needs_review = sum(1 for r in successful if r['confidence_metrics']['needs_review'])
        print(f"  Flagged for review: {needs_review}/{len(successful)}")

        print("\nRECONSTRUCTION QUALITY:")
        quality_counts = {}
        for r in successful:
            qual = r['confidence_metrics'].get('reconstruction_quality', 'unknown')
            quality_counts[qual] = quality_counts.get(qual, 0) + 1

        for quality, count in sorted(quality_counts.items()):
            print(f"  {quality}: {count}")

        print("\n" + "-" * 80)
        print("DETAILED RESULTS")
        print("-" * 80)

        for result in successful:
            print(f"\n{result['test_name']}:")
            print(f"  Language: {result['language']}")
            print(f"  Duration: {result['duration']:.1f}s")
            print(f"  Raw→Reconstructed: {result['raw_length']}→{result['reconstructed_length']} chars")
            print(f"  Quality: {result['confidence_metrics'].get('reconstruction_quality', 'unknown')}")
            print(f"  Confidence: {result['confidence_metrics']['confidence']}")
            print(f"  Coherence Improved: {result['confidence_metrics'].get('coherence_improved', 'N/A')}")
            print(f"  Reliable: {result['confidence_metrics'].get('is_reliable', 'N/A')}")
            print(f"  Needs Review: {result['confidence_metrics']['needs_review']}")

    # Save results
    results_file = "test_accuracy_improvements_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_file}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return len(failed) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
