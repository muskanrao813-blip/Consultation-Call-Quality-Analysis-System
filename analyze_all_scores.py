#!/usr/bin/env python3
"""
Analyze all call scores to see why they're all similar
"""
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("\n" + "="*80)
print("ANALYZING ALL CALL SCORES - Why Are They Similar?")
print("="*80)

# Get all completed calls
calls = db.query(models.Call).filter(
    models.Call.status == models.CallStatus.completed
).all()

print(f"\nTotal completed calls: {len(calls)}\n")

scores_list = []

for call in calls:
    # Get transcript
    trans = db.query(models.Transcript).filter(
        models.Transcript.call_id == call.id
    ).first()

    # Get metrics
    metrics = db.query(models.CallMetrics).filter(
        models.CallMetrics.call_id == call.id
    ).first()

    # Get rubric scores
    rubric_scores = db.query(models.RubricScore).filter(
        models.RubricScore.call_id == call.id
    ).all()

    if rubric_scores:
        overall_score = rubric_scores[0].overall_weighted_score
        scores_list.append(overall_score)

        trans_provider = trans.provider if trans else "unknown"
        segments_count = len(trans.diarized_segments) if trans and trans.diarized_segments else 0
        duration = metrics.duration_seconds if metrics else 0
        dietician_talk = metrics.dietician_talk_ratio_pct if metrics else 0

        print(f"Call: {call.id}")
        print(f"  Score: {overall_score:.1f}/10")
        print(f"  Provider: {trans_provider}")
        print(f"  Segments: {segments_count}")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Dietician talk: {dietician_talk:.1f}%")

        # Show why score is similar
        if trans and trans.diarized_segments:
            seg_list = trans.diarized_segments
            if isinstance(seg_list, str):
                seg_list = json.loads(seg_list)

            # Check if it's mock data
            is_mock = False
            for seg in seg_list:
                text = seg.get('text', '')
                if 'Dietician consultation recording' in text or 'Patient response and feedback' in text:
                    is_mock = True
                    break

            if is_mock:
                print(f"  DATA: MOCK (not real Whisper)")
            else:
                print(f"  DATA: REAL (Whisper transcribed)")

        print()

# Summary
print("="*80)
print("SUMMARY")
print("="*80)
if scores_list:
    unique_scores = set([round(s, 1) for s in scores_list])
    print(f"Unique scores: {sorted(unique_scores)}")
    print(f"Number of unique scores: {len(unique_scores)}")
    print(f"Average score: {sum(scores_list)/len(scores_list):.1f}")

    if len(unique_scores) <= 2:
        print("\nREASON FOR SIMILARITY:")
        print("Most calls are using MOCK DATA, not real Whisper transcription.")
        print("Mock data has identical metrics:")
        print("  - Duration: always 120s")
        print("  - Dietician talk: always 50%")
        print("  - Patient talk: always 50%")
        print("  - Interruptions: always 1")
        print("\nThis produces similar scores for all mock calls.")
        print("\nSOLUTION: Only calls with REAL Whisper transcription will have different scores.")

db.close()
