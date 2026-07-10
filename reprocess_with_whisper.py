#!/usr/bin/env python3
"""
Reprocess calls with actual Whisper transcription (not mock data)
"""
from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call
import sys

db = SessionLocal()

print("\n" + "=" * 70)
print("REPROCESSING CALLS WITH WHISPER TRANSCRIPTION")
print("=" * 70)

# Get calls with different recording URLs
print("\n[1] Finding calls to reprocess...")
calls_to_process = db.query(models.Call).filter(
    models.Call.status.in_([models.CallStatus.failed, models.CallStatus.completed])
).limit(3).all()

print(f"Found {len(calls_to_process)} calls to reprocess")

for call in calls_to_process:
    print(f"\n{'='*70}")
    print(f"Processing: {call.patient_name} ({call.dietician.name if call.dietician else 'Unknown'})")
    print(f"URL: {call.recording_url}")

    # Reset status to pending for reprocessing
    call.status = models.CallStatus.pending
    db.commit()

    print(f"Status: {call.status} -> Processing...")

    try:
        # Run pipeline with Whisper
        process_call(str(call.id))
        print(f"Result: SUCCESS")

        # Refresh to see results
        db.expunge_all()
        result_call = db.query(models.Call).filter(models.Call.id == call.id).first()

        # Get transcript
        trans = db.query(models.Transcript).filter(
            models.Transcript.call_id == call.id
        ).first()

        if trans:
            segments = trans.diarized_segments
            if isinstance(segments, str):
                import json
                segments = json.loads(segments)

            print(f"\nTranscript (actual Whisper output):")
            print(f"  Segments: {len(segments) if segments else 0}")
            if segments and len(segments) > 0:
                for i, seg in enumerate(segments[:3]):
                    speaker = seg.get('speaker', 'unknown')
                    text = seg.get('text', '')[:80]
                    print(f"  [{i+1}] {speaker}: {text}...")

        # Get metrics
        metrics = db.query(models.CallMetrics).filter(
            models.CallMetrics.call_id == call.id
        ).first()

        if metrics:
            print(f"\nMetrics (from real transcript):")
            print(f"  Duration: {metrics.duration_seconds}s")
            print(f"  Dietician talk: {metrics.dietician_talk_ratio_pct:.1f}%")
            print(f"  Patient talk: {metrics.patient_talk_ratio_pct:.1f}%")
            print(f"  Interruptions: {metrics.interruption_count}")

        # Get score
        scores = db.query(models.RubricScore).filter(
            models.RubricScore.call_id == call.id
        ).all()

        if scores:
            print(f"\nRubric Score (based on real transcript):")
            print(f"  Overall: {scores[0].overall_weighted_score:.1f}/10")
            for s in scores[:3]:
                print(f"  {s.dimension}: {s.score:.1f}/10")

    except Exception as e:
        print(f"Result: FAILED - {type(e).__name__}: {str(e)[:100]}")
        db.expunge_all()

print("\n" + "=" * 70)
print("REPROCESSING COMPLETE")
print("=" * 70)
print("\nNote: If URLs are not accessible, Whisper will fail.")
print("Make sure recording URLs are publicly accessible HTTPS URLs.")

db.close()
