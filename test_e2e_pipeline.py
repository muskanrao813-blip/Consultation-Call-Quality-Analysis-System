#!/usr/bin/env python3
"""
End-to-End Pipeline Test
Processes a queued call through: transcription → metrics → LLM scoring → storage
"""
import sys
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

print("=" * 70)
print("END-TO-END PIPELINE TEST")
print("=" * 70)

# Initialize database
from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call

db = SessionLocal()

try:
    # Get a pending call
    print("\n[1] Finding queued call...")
    pending_call = db.query(models.Call).filter(
        models.Call.status == models.CallStatus.pending
    ).first()

    if not pending_call:
        print("    No pending calls found. Creating test call...")
        # Create a test call manually
        dietician = db.query(models.Dietician).first()
        if not dietician:
            dietician = models.Dietician(name="Dr. Test E2E")
            db.add(dietician)
            db.flush()

        test_call = models.Call(
            dietician_id=dietician.id,
            patient_id="PATIENT_TEST_E2E",
            patient_name="Test Patient",
            appointment_id=f"APT_TEST_{uuid.uuid4().hex[:8]}",
            recording_url="https://example.com/test_call.wav",
            call_duration_seconds=900,
            status=models.CallStatus.pending,
        )
        db.add(test_call)
        db.commit()
        pending_call = test_call
        print(f"    Created test call: {pending_call.id}")
    else:
        print(f"    Found pending call: {pending_call.id}")
        print(f"    - Dietician: {pending_call.dietician.name if pending_call.dietician else 'Unknown'}")
        print(f"    - Patient: {pending_call.patient_name}")
        print(f"    - Recording URL: {pending_call.recording_url}")

    print(f"\n[2] Processing call through pipeline...")
    print("    - Stages: Transcription → Metrics → LLM Analysis → Scoring → Storage")

    # Run the pipeline
    try:
        process_call(str(pending_call.id))
        print("    Pipeline execution: SUCCESS")
    except Exception as e:
        print(f"    Pipeline execution: FAILED - {e}")
        import traceback
        traceback.print_exc()

    # Refresh call from database
    db.refresh(pending_call)

    print(f"\n[3] Verifying results...")
    print(f"    Call status: {pending_call.status}")
    print(f"    Processed at: {pending_call.processed_at}")

    # Check transcript
    transcript = db.query(models.Transcript).filter(
        models.Transcript.call_id == pending_call.id
    ).first()

    if transcript:
        print(f"\n    ✓ Transcript stored")
        print(f"      - Provider: {transcript.provider}")
        print(f"      - Segments: {len(transcript.diarized_segments or [])}")
        if transcript.diarized_segments:
            for i, seg in enumerate(transcript.diarized_segments[:2]):
                print(f"        Segment {i+1}: {seg.get('text', '')[:60]}...")

    # Check metrics
    call_metrics = db.query(models.CallMetrics).filter(
        models.CallMetrics.call_id == pending_call.id
    ).first()

    if call_metrics:
        print(f"\n    ✓ Metrics computed")
        print(f"      - Duration: {call_metrics.duration_seconds}s")
        print(f"      - Dietician talk: {call_metrics.dietician_talk_ratio_pct:.1f}%")
        print(f"      - Patient talk: {call_metrics.patient_talk_ratio_pct:.1f}%")
        print(f"      - Interruptions: {call_metrics.interruption_count}")
        print(f"      - Response latency: {call_metrics.avg_response_latency_seconds:.1f}s")

    # Check rubric scores
    rubric_scores = db.query(models.RubricScore).filter(
        models.RubricScore.call_id == pending_call.id
    ).all()

    if rubric_scores:
        print(f"\n    ✓ Rubric scores computed")
        print(f"      - Dimensions scored: {len(rubric_scores)}")
        for score in rubric_scores[:3]:
            print(f"        {score.dimension}: {score.score:.1f}/10")
        print(f"      - Overall weighted score: {rubric_scores[0].overall_weighted_score if rubric_scores else 'N/A'}")

    # Check QA flags
    qa_flags = db.query(models.QAFlag).filter(
        models.QAFlag.call_id == pending_call.id
    ).all()

    if qa_flags:
        print(f"\n    ✓ QA flags evaluated")
        triggered = [f for f in qa_flags if f.triggered]
        print(f"      - Total flags: {len(qa_flags)}")
        print(f"      - Triggered: {len(triggered)}")
        for flag in triggered[:3]:
            print(f"        • {flag.flag_name}")

    # Check feedback
    feedback = db.query(models.FeedbackNote).filter(
        models.FeedbackNote.call_id == pending_call.id
    ).first()

    if feedback:
        print(f"\n    ✓ Feedback generated")
        print(f"      - Retraining recommended: {feedback.retraining_recommended}")
        if feedback.feedback_bullets:
            print(f"      - Coaching bullets: {len(feedback.feedback_bullets)}")
            for bullet in feedback.feedback_bullets[:2]:
                print(f"        • {bullet}")

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 70)

    # Get all results
    call_count = db.query(models.Call).count()
    processed_count = db.query(models.Call).filter(
        models.Call.status == models.CallStatus.completed
    ).count()

    print(f"\nDatabase Summary:")
    print(f"  Total calls: {call_count}")
    print(f"  Processed (completed): {processed_count}")
    print(f"  Success rate: {100*processed_count/call_count if call_count > 0 else 0:.1f}%")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
