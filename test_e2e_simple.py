#!/usr/bin/env python3
"""
End-to-End Pipeline Test
Processes an existing call through: transcription → metrics → LLM scoring → storage
"""
import sys
from datetime import datetime

print("=" * 70)
print("END-TO-END PIPELINE TEST - Processing Existing Call")
print("=" * 70)

# Initialize database
from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call
import uuid

db = SessionLocal()

try:
    # Find any call in the database
    print("\n[1] Finding call to process...")

    # Get any existing call that's not already being processed
    existing_call = db.query(models.Call).filter(
        models.Call.status != models.CallStatus.processing
    ).first()

    if not existing_call:
        print("    ERROR: No calls found in database")
        sys.exit(1)

    call_id = existing_call.id
    print(f"    Found call: {call_id}")
    print(f"    - Dietician: {existing_call.dietician.name if existing_call.dietician else 'Unknown'}")
    print(f"    - Patient: {existing_call.patient_name}")
    print(f"    - Recording URL: {existing_call.recording_url}")
    print(f"    - Current status: {existing_call.status}")

    print(f"\n[2] Processing call through FULL PIPELINE...")
    print("    Stages:")
    print("    1. Audio -> Transcription")
    print("    2. Diarization & Segmentation")
    print("    3. Metrics Computation (talk ratios, latency, etc.)")
    print("    4. LLM Analysis (Ollama local)")
    print("    5. Rubric Scoring & Flags")
    print("    6. Feedback Generation")
    print("    7. Storage in Database")

    # Run the pipeline synchronously
    try:
        process_call(str(call_id))
        print("\n    [OK] Pipeline execution: SUCCESS")
    except Exception as e:
        print(f"\n    [FAIL] Pipeline execution: FAILED")
        print(f"      Error: {type(e).__name__}: {str(e)[:100]}")

    # Refresh and check results
    db.expunge_all()  # Clear session cache
    result_call = db.query(models.Call).filter(models.Call.id == call_id).first()

    print(f"\n[3] RESULTS")
    print(f"    Call status: {result_call.status}")
    print(f"    Processed at: {result_call.processed_at}")
    print(f"    Error: {result_call.error_message if result_call.error_message else 'None'}")

    # Check transcript
    print(f"\n    === TRANSCRIPT ===")
    transcript = db.query(models.Transcript).filter(
        models.Transcript.call_id == call_id
    ).first()

    if transcript:
        print(f"    [OK] Stored")
        print(f"      Provider: {transcript.provider}")
        print(f"      Segments: {len(transcript.diarized_segments or [])}")
        if transcript.diarized_segments and len(transcript.diarized_segments) > 0:
            seg_list = transcript.diarized_segments
            if isinstance(seg_list, str):
                import json
                seg_list = json.loads(seg_list)
            for i, seg in enumerate(seg_list[:2]):
                speaker = seg.get('speaker', 'unknown')
                text = seg.get('text', '')[:50]
                print(f"        [{speaker}] {text}...")
    else:
        print(f"    [NOT FOUND]")

    # Check metrics
    print(f"\n    === METRICS ===")
    call_metrics = db.query(models.CallMetrics).filter(
        models.CallMetrics.call_id == call_id
    ).first()

    if call_metrics:
        print(f"    [OK] Computed")
        print(f"      Duration: {call_metrics.duration_seconds}s")
        print(f"      Dietician talk: {call_metrics.dietician_talk_ratio_pct:.1f}%")
        print(f"      Patient talk: {call_metrics.patient_talk_ratio_pct:.1f}%")
        print(f"      Interruptions: {call_metrics.interruption_count}")
        print(f"      Response latency: {call_metrics.avg_response_latency_seconds:.1f}s")
        print(f"      Silence: {call_metrics.silence_pct:.1f}%")
    else:
        print(f"    [FAIL] Not found")

    # Check rubric scores
    print(f"\n    === RUBRIC SCORES ===")
    rubric_scores = db.query(models.RubricScore).filter(
        models.RubricScore.call_id == call_id
    ).all()

    if rubric_scores:
        print(f"    [OK] Computed ({len(rubric_scores)} dimensions)")
        for score in rubric_scores:
            dim_name = score.dimension.replace('_', ' ').title() if score.dimension else 'Unknown'
            print(f"      {dim_name}: {score.score:.1f}/10")
        if rubric_scores:
            print(f"      Overall weighted score: {rubric_scores[0].overall_weighted_score:.1f}/10")
    else:
        print(f"    [FAIL] Not found")

    # Check QA flags
    print(f"\n    === QA FLAGS ===")
    qa_flags = db.query(models.QAFlag).filter(
        models.QAFlag.call_id == call_id
    ).all()

    if qa_flags:
        triggered = [f for f in qa_flags if f.triggered]
        print(f"    [OK] Evaluated ({len(triggered)} triggered out of {len(qa_flags)})")
        if triggered:
            for flag in triggered:
                print(f"      - {flag.flag_name}")
        else:
            print(f"      All checks passed")
    else:
        print(f"    [FAIL] Not found")

    # Check feedback
    print(f"\n    === FEEDBACK ===")
    feedback = db.query(models.FeedbackNote).filter(
        models.FeedbackNote.call_id == call_id
    ).first()

    if feedback:
        print(f"    [OK] Generated")
        print(f"      Retraining recommended: {feedback.retraining_recommended}")
        if feedback.feedback_bullets:
            print(f"      Coaching bullets:")
            for bullet in feedback.feedback_bullets[:3]:
                print(f"        - {bullet}")
    else:
        print(f"    [FAIL] Not found")

    print("\n" + "=" * 70)
    if result_call.status == models.CallStatus.completed:
        print("[OK] PIPELINE COMPLETE - Call successfully processed!")
    else:
        print(f"[FAIL] Pipeline incomplete - Status: {result_call.status}")
    print("=" * 70)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

