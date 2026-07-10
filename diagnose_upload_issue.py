#!/usr/bin/env python3
"""
Diagnose why uploaded files are showing mock data
"""
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("\n" + "="*80)
print("DIAGNOSING UPLOAD ISSUE")
print("="*80)

# Check for any calls
calls = db.query(models.Call).all()
print(f"\nTotal calls in database: {len(calls)}")

if calls:
    print("\nCall Details:")
    for call in calls[:3]:
        print(f"\n  Call ID: {call.id}")
        print(f"  Patient: {call.patient_name}")
        print(f"  Recording URL: {call.recording_url}")
        print(f"  Status: {call.status}")
        print(f"  Created: {call.created_at}")

        # Check transcript
        trans = db.query(models.Transcript).filter(
            models.Transcript.call_id == call.id
        ).first()

        if trans:
            print(f"  Transcript Provider: {trans.provider}")
            segs = trans.diarized_segments
            if isinstance(segs, str):
                segs = json.loads(segs)
            print(f"  Segments: {len(segs) if segs else 0}")

            # Check if it's mock
            is_mock = False
            for seg in segs:
                text = seg.get('text', '')
                if 'Dietician consultation recording' in text or 'Patient response' in text:
                    is_mock = True
                    break

            if is_mock:
                print(f"  Type: MOCK DATA (NOT WHISPER)")
            else:
                print(f"  Type: REAL WHISPER")

    print("\n" + "="*80)
    print("ISSUE FOUND")
    print("="*80)
    print("\nThe system is generating MOCK DATA instead of using Whisper.")
    print("\nREASON: The pipeline is falling back to mock data when:")
    print("  1. Audio download fails")
    print("  2. Whisper transcription fails")
    print("  3. An error occurs during processing")
    print("\nCHECK:")
    print("  - Are the recording URLs publicly accessible?")
    print("  - Can they be accessed without authentication?")
    print("  - Are they valid audio files (WAV, MP3, etc)?")

else:
    print("\nNo calls found in database.")
    print("Check if the upload was successful.")
    print("\nDEBUG:")
    print("  1. Go to http://localhost:3000")
    print("  2. Upload tab -> check for validation errors")
    print("  3. Check batch status in 'Scorecard' tab")

# Check upload batches
batches = db.query(models.UploadBatch).all()
print(f"\nUpload Batches: {len(batches)}")
if batches:
    for batch in batches[:2]:
        print(f"  Batch {batch.id}: {batch.total_rows} rows, {batch.valid_rows} valid")

db.close()
