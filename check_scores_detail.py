#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("="*80)
print("Detailed Score Analysis")
print("="*80)

calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(5).all()

for call in calls:
    print(f"\nCall: {str(call.id)[:8]}")
    print(f"  Duration: {call.call_duration_seconds}s")
    print(f"  Status: {call.status}")

    # Get metrics
    metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
    if metrics:
        print(f"  Metrics computed: YES")
        print(f"    - Talk ratios: D={metrics.dietician_talk_ratio_pct}%, P={metrics.patient_talk_ratio_pct}%")
        print(f"    - Time to plan: {metrics.time_to_first_plan_mention_seconds}s")
    else:
        print(f"  Metrics: NONE")

    # Get transcript
    trans = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
    if trans:
        segs = trans.diarized_segments
        if isinstance(segs, str):
            segs = json.loads(segs)
        print(f"  Transcript: {len(segs)} segments")
        print(f"  Provider: {trans.provider}")
    else:
        print(f"  Transcript: NONE")

    # Get scores
    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
    if scores:
        for score in scores[:3]:
            print(f"  {score.dimension}: {score.score}")
            # Check if raw response has evidence
            if score.raw_llm_response:
                raw = score.raw_llm_response if isinstance(score.raw_llm_response, dict) else json.loads(score.raw_llm_response)
                evidence = raw.get("evidence", [])
                print(f"    Evidence count: {len(evidence)}")
    else:
        print(f"  Scores: NONE")

    # Get feedback
    feedback = db.query(models.FeedbackNote).filter(models.FeedbackNote.call_id == call.id).first()
    if feedback:
        bullets = feedback.bullet.split(" | ")
        print(f"  Feedback: {len(bullets)} bullets")
        print(f"    First: {bullets[0][:60]}")
    else:
        print(f"  Feedback: NONE")

db.close()
print("\n" + "="*80)
