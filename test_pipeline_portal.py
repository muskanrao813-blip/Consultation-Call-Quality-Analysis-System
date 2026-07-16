"""
Test Runner: Upload recording → Run Pipeline → Display Results → Upload to Portal
"""

import sys
import requests
import json
import tempfile
import os

# Backend URL
BACKEND_URL = "http://localhost:8000"

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_section(text):
    """Print formatted section"""
    print(f"\n[INFO] {text}")
    print("-"*70)

def run_pipeline(audio_url):
    """Run the unified transcription pipeline"""
    print_section("Running Unified Pipeline")

    # Import the pipeline
    sys.path.insert(0, "C:\\Users\\muskan.rao\\Documents\\claude\\dietician-qa")
    from unified_transcription_pipeline import UnifiedTranscriptionPipeline

    pipeline = UnifiedTranscriptionPipeline(audio_url)
    report = pipeline.run()

    return report

def upload_to_portal(report):
    """Upload pipeline results to portal"""
    print_section("Uploading Results to Portal")

    try:
        # Create call record with transcript
        payload = {
            "recording_url": report["audio_url"],
            "language": report["language"],
            "raw_transcript": report["raw_transcript"],
            "reconstructed_transcript": report["reconstructed_transcript"],
            "duration": report["metadata"]["duration_seconds"],
            "patient_name": report["entities"].get("patient_name", "Unknown"),
            "organization": report["entities"].get("organization", "Unknown"),
            "call_type": report["entities"].get("call_type", "Unknown"),
            "health_status": report["entities"].get("health_status", "Unknown"),
            "location": report["entities"].get("location", "Unknown"),
            "accuracy": report["accuracy_estimate"],
        }

        response = requests.post(
            f"{BACKEND_URL}/api/calls/",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Uploaded successfully!")
            print(f"   Call ID: {result.get('id', 'N/A')}")
            return result
        else:
            print(f"[WARN]  Upload warning: {response.status_code}")
            print(f"   {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[WARN]  Upload error: {e}")
        return None

def display_results(report):
    """Display pipeline results"""
    print_section("PIPELINE RESULTS")

    print("[METRICS] METADATA:")
    print(f"  Language Detected: {report['language']}")
    print(f"  Duration: {report['metadata']['duration_seconds']:.1f} seconds")
    print(f"  Sample Rate: {report['metadata']['sample_rate']} Hz")
    print(f"  Raw Transcript: {report['raw_transcript_chars']} chars")
    print(f"  Reconstructed: {report['reconstructed_transcript_chars']} chars")
    print(f"  Accuracy: {report['accuracy_estimate']}")
    print(f"  Status: {report['status']}")

    print("\n[NOTES] RAW TRANSCRIPT (First 300 chars):")
    print(f"  {report['raw_transcript'][:300]}...")

    print("\n[RECONSTRUCT] RECONSTRUCTED TRANSCRIPT (First 300 chars):")
    print(f"  {report['reconstructed_transcript'][:300]}...")

    print("\n[EXTRACT] EXTRACTED ENTITIES:")
    for key, value in report['entities'].items():
        if value and value != "Not mentioned":
            print(f"  • {key.replace('_', ' ').title()}: {value}")

    return report

def main():
    """Main test runner"""
    print_header("DIETICIAN QA PORTAL - PIPELINE TEST")

    # Get audio URL from user
    print("[INPUT] Enter Recording Details:")
    print("-"*70)
    audio_url = input("\nEnter audio URL (or press Enter for example): ").strip()

    if not audio_url:
        # Use example from earlier testing
        audio_url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/06937a25-f363-444c-912a-e31d43ad1804.mp3"
        print(f"Using example: {audio_url[:80]}...")

    # Run pipeline
    try:
        report = run_pipeline(audio_url)

        if not report:
            print("[FAIL] Pipeline failed!")
            return

        # Display results
        display_results(report)

        # Ask to upload
        print("\n" + "="*70)
        upload = input("\n[UPLOAD] Upload results to portal? (y/n): ").strip().lower()

        if upload == 'y':
            upload_to_portal(report)

        # Save report locally
        output_file = os.path.join(tempfile.gettempdir(), 'latest_pipeline_report.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Report saved: {output_file}")

        print("\n" + "="*70)
        print("[OK] TEST COMPLETE")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
