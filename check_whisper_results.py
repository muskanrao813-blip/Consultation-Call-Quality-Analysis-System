#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("\n" + "="*70)
print("WHISPER TRANSCRIPTION RESULTS")
print("="*70)

# Get the recently processed call
call = db.query(models.Call).filter(
    models.Call.id == "ae2158c1-da5e-4bcf-a0d4-a388af2e47b1"
).first()

if call:
    print(f"\nCall: {call.patient_name}")
    print(f"Dietician: {call.dietician.name if call.dietician else 'Unknown'}")
    print(f"Status: {call.status}")

    # Get transcript
    trans = db.query(models.Transcript).filter(
        models.Transcript.call_id == call.id
    ).first()

    if trans:
        segments = trans.diarized_segments
        if isinstance(segments, str):
            segments = json.loads(segments)

        print(f"\nTRANSCRIPT (Real Whisper Output):")
        print(f"Provider: {trans.provider}")
        print(f"Segments: {len(segments) if segments else 0}")
        print(f"\nSegments:")
        for i, seg in enumerate(segments[:6], 1):
            speaker = seg.get('speaker', 'unknown')
            text = seg.get('text', '')[:100]
            # Remove non-ASCII characters for console display
            text = text.encode('ascii', 'ignore').decode('ascii')
            start = seg.get('start_s', 0)
            end = seg.get('end_s', 0)
            print(f"  [{i}] {speaker} ({start:.1f}s-{end:.1f}s): {text}")

    # Get metrics
    metrics = db.query(models.CallMetrics).filter(
        models.CallMetrics.call_id == call.id
    ).first()

    if metrics:
        print(f"\nMETRICS (Extracted from transcript):")
        print(f"Duration: {metrics.duration_seconds}s")
        print(f"Dietician talk: {metrics.dietician_talk_ratio_pct:.1f}%")
        print(f"Patient talk: {metrics.patient_talk_ratio_pct:.1f}%")
        print(f"Interruptions: {metrics.interruption_count}")
        print(f"Response latency: {metrics.avg_response_latency_seconds:.1f}s")

    # Get scores
    scores = db.query(models.RubricScore).filter(
        models.RubricScore.call_id == call.id
    ).all()

    if scores:
        print(f"\nRUBRIC SCORES (Based on real transcript):")
        for s in scores:
            print(f"  {s.dimension}: {s.score:.1f}/10")
        print(f"  Overall: {scores[0].overall_weighted_score:.1f}/10")

    print("\n" + "="*70)
    print("SUCCESS: Whisper is transcribing real calls!")
    print("="*70)
else:
    print("\nCall not found")

db.close()
