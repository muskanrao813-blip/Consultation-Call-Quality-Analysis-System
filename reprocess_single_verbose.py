#!/usr/bin/env python3
"""
Reprocess a single call with verbose logging to see what's happening
"""
import os
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

os.environ['PATH'] = r"C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin;" + os.environ['PATH']

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call

db = SessionLocal()

print("\n" + "="*80)
print("PROCESSING SINGLE CALL WITH VERBOSE LOGGING")
print("="*80)

# Get the first pending call
call = db.query(models.Call).filter(
    models.Call.status == models.CallStatus.pending
).first()

if not call:
    print("\nNo pending calls. Creating test call...")
    dietician = db.query(models.Dietician).first()
    call = models.Call(
        dietician_id=dietician.id,
        patient_id="TEST_PATIENT",
        patient_name="Test Patient",
        appointment_id="TEST_APT",
        recording_url="https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3",
        call_duration_seconds=0,
        status=models.CallStatus.pending
    )
    db.add(call)
    db.commit()

print(f"\nProcessing call: {call.id}")
print(f"URL: {call.recording_url}")

try:
    process_call(str(call.id))
    print("\n✓ Processing completed")

    # Check result
    db.expunge_all()
    result = db.query(models.Call).filter(models.Call.id == call.id).first()
    print(f"Final status: {result.status}")

    # Get transcript
    trans = db.query(models.Transcript).filter(
        models.Transcript.call_id == call.id
    ).first()

    if trans:
        print(f"Transcript provider: {trans.provider}")
        segs = trans.diarized_segments
        print(f"Segments: {len(segs) if segs else 0}")

except Exception as e:
    print(f"\n✗ Processing failed: {e}")
    import traceback
    traceback.print_exc()

db.close()
