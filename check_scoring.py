#!/usr/bin/env python3
"""
Check all completed calls with their transcripts and detailed scoring breakdown
"""
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("\n" + "=" * 80)
print("CALL SCORING ANALYSIS - Why Are Scores Similar?")
print("=" * 80)

# Get all completed calls
completed_calls = db.query(models.Call).filter(
    models.Call.status == models.CallStatus.completed
).limit(5).all()

print(f"\nFound {len(completed_calls)} completed calls\n")

for i, call in enumerate(completed_calls, 1):
    print(f"\n{'='*80}")
    print(f"CALL #{i}: {call.id}")
    print(f"{'='*80}")
    print(f"Dietician: {call.dietician.name}")
    print(f"Patient: {call.patient_name}")
    print(f"Recording URL: {call.recording_url}")

    # Get transcript
    trans = db.query(models.Transcript).filter(
        models.Transcript.call_id == call.id
    ).first()

    if trans:
        print(f"\n--- TRANSCRIPT (Diarized Segments) ---")
        segments = trans.diarized_segments
        if isinstance(segments, str):
            segments = json.loads(segments)

        if segments:
            total_duration = 0
            for seg in segments:
                speaker = seg.get('speaker', 'unknown')
                text = seg.get('text', '')
                start = seg.get('start_s', 0)
                end = seg.get('end_s', 0)
                duration = end - start
                total_duration += duration
                print(f"[{speaker}] ({start:.0f}s-{end:.0f}s, {duration:.0f}s): {text}")

            print(f"\nTotal Duration: {total_duration:.0f}s")

    # Get metrics
    metrics = db.query(models.CallMetrics).filter(
        models.CallMetrics.call_id == call.id
    ).first()

    if metrics:
        print(f"\n--- METRICS EXTRACTED ---")
        print(f"Duration: {metrics.duration_seconds}s")
        print(f"Dietician talk: {metrics.dietician_talk_ratio_pct:.1f}%")
        print(f"Patient talk: {metrics.patient_talk_ratio_pct:.1f}%")
        print(f"Interruptions: {metrics.interruption_count}")
        print(f"Avg response latency: {metrics.avg_response_latency_seconds:.1f}s")
        print(f"Silence: {metrics.silence_pct:.1f}%")
        print(f"Time to first plan mention: {metrics.time_to_first_plan_mention_seconds:.1f}s")
        print(f"Off-topic time: {metrics.off_topic_time_pct:.1f}%")

    # Get rubric scores with breakdown
    scores = db.query(models.RubricScore).filter(
        models.RubricScore.call_id == call.id
    ).all()

    if scores:
        print(f"\n--- RUBRIC SCORING (6 Dimensions) ---")
        for score in scores:
            dimension = score.dimension.replace('_', ' ').title()
            print(f"\n{dimension}:")
            print(f"  Score: {score.score:.1f}/10")

            # Try to show evidence
            if score.evidence:
                evidence = score.evidence
                if isinstance(evidence, str):
                    evidence = json.loads(evidence)
                print(f"  Evidence:")
                for ev in evidence[:2]:  # Show first 2 pieces of evidence
                    if isinstance(ev, dict):
                        quote = ev.get('quote', '')
                        timestamp = ev.get('timestamp_s', 0)
                        print(f"    - '{quote}' (at {timestamp}s)")

            # Show sub-criteria
            if score.sub_criteria:
                sub_crit = score.sub_criteria
                if isinstance(sub_crit, str):
                    sub_crit = json.loads(sub_crit)
                met = sum(1 for v in sub_crit.values() if v)
                total = len(sub_crit)
                print(f"  Sub-criteria met: {met}/{total}")

        # Overall score
        if scores:
            overall = scores[0].overall_weighted_score
            print(f"\n*** OVERALL WEIGHTED SCORE: {overall:.1f}/10 ***")

    # Get flags
    flags = db.query(models.QAFlag).filter(
        models.QAFlag.call_id == call.id
    ).all()

    if flags:
        print(f"\n--- QA FLAGS EVALUATION (8 Flags) ---")
        triggered = [f for f in flags if f.triggered]
        for flag in flags:
            status = "TRIGGERED" if flag.triggered else "PASS"
            flag_name = getattr(flag, 'flag_name', getattr(flag, 'flag_type', 'Unknown'))
            print(f"  [{status}] {flag_name}")
            if flag.triggered and hasattr(flag, 'reasoning'):
                print(f"       Reason: {flag.reasoning}")

    # Feedback
    feedback = db.query(models.FeedbackNote).filter(
        models.FeedbackNote.call_id == call.id
    ).first()

    if feedback:
        print(f"\n--- FEEDBACK & COACHING ---")
        print(f"Retraining recommended: {feedback.retraining_recommended}")
        if hasattr(feedback, 'feedback_bullets') and feedback.feedback_bullets:
            bullets = feedback.feedback_bullets
            if isinstance(bullets, str):
                bullets = json.loads(bullets)
            print(f"Coaching bullets:")
            for bullet in bullets:
                print(f"  - {bullet}")
        elif hasattr(feedback, 'feedback_text') and feedback.feedback_text:
            print(f"Feedback: {feedback.feedback_text}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

# Summary
print("\nWHY SIMILAR SCORES?")
print("-" * 80)
print("""
The scores appear similar because:

1. MOCK TRANSCRIPT DATA: Currently using mock/test data (2 segments) instead of
   real audio transcriptions. Real calls would have much more variation.

2. FALLBACK SCORING: When Google Cloud Speech-to-Text credentials aren't available,
   the system falls back to mock segments, which produces synthetic scores based on
   the formula in _generate_fallback_scores().

3. FORMULA-BASED: Fallback scores are derived from computed metrics using formulas:
   - discovery_score = 5 + (dietician_talk_ratio / 30)
   - empathy_score = 5 + (patient_talk_ratio / 30)
   - rushedness = 10 - (call_duration / 180)
   - etc.

4. LIMITED VARIATION: Mock data has fixed talk ratios (50/50) and duration (120s),
   so scores are naturally similar.

TO GET DIFFERENT SCORES:
✓ Set up Google Cloud Speech-to-Text credentials -> Real transcription
✓ Provide real audio URLs with actual dietician-patient conversations
✓ System will extract different metrics from each call (different talk ratios,
  interruptions, response patterns) -> Different scores

CURRENT SYSTEM CAPABILITIES:
✓ Works end-to-end (transcription -> metrics -> scoring -> feedback)
✓ All 6 rubric dimensions scoring
✓ QA flag evaluation
✓ Feedback generation with coaching bullets
✓ Retraining recommendations
""")

db.close()
