#!/usr/bin/env python3
"""
Reprocess calls with Whisper transcription - Fixed version
"""
import os
os.environ['PATH'] = r"C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin;" + os.environ['PATH']

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call

print("\n" + "=" * 70)
print("REPROCESSING CALLS WITH WHISPER TRANSCRIPTION (Fixed)")
print("=" * 70)

# Get calls to process
print("\n[1] Finding calls to reprocess...")
db = SessionLocal()
calls_data = db.query(
    models.Call.id,
    models.Call.patient_name,
    models.Call.recording_url,
    models.Dietician.name
).outerjoin(models.Dietician).limit(2).all()
db.close()

print(f"Found {len(calls_data)} calls to reprocess\n")

for call_id, patient_name, recording_url, dietician_name in calls_data:
    print(f"{'='*70}")
    print(f"Call ID: {call_id}")
    print(f"Patient: {patient_name}")
    print(f"Dietician: {dietician_name}")
    print(f"Recording: {recording_url[:60]}...")

    # Reset and process
    db = SessionLocal()
    call = db.query(models.Call).filter(models.Call.id == call_id).first()

    if call:
        call.status = models.CallStatus.pending
        db.commit()

        print(f"Processing...")

        try:
            # Run pipeline
            process_call(str(call_id))

            # Check result (fresh session)
            db.expunge_all()
            result_call = db.query(models.Call).filter(models.Call.id == call_id).first()

            print(f"Status: {result_call.status}")

            # Get transcript
            trans = db.query(models.Transcript).filter(
                models.Transcript.call_id == call_id
            ).first()

            if trans:
                segments = trans.diarized_segments
                if isinstance(segments, str):
                    import json
                    segments = json.loads(segments)

                print(f"\nTranscript (real Whisper output):")
                print(f"  Segments: {len(segments) if segments else 0}")
                if segments and len(segments) > 0:
                    for i, seg in enumerate(segments[:2]):
                        speaker = seg.get('speaker', 'unknown')
                        text = seg.get('text', '')[:70]
                        print(f"  [{i+1}] {speaker}: {text}...")

            # Get metrics
            metrics = db.query(models.CallMetrics).filter(
                models.CallMetrics.call_id == call_id
            ).first()

            if metrics:
                print(f"\nMetrics (from real transcript):")
                print(f"  Duration: {metrics.duration_seconds}s")
                print(f"  Dietician: {metrics.dietician_talk_ratio_pct:.1f}%")
                print(f"  Patient: {metrics.patient_talk_ratio_pct:.1f}%")

            # Get score
            scores = db.query(models.RubricScore).filter(
                models.RubricScore.call_id == call_id
            ).all()

            if scores:
                print(f"\nOverall Score: {scores[0].overall_weighted_score:.1f}/10")

        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {str(e)[:80]}")

    db.close()

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
