#!/usr/bin/env python3
"""Test pipeline directly with detailed logging."""

import logging
import sys

# Verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call

# Get a pending call
db = SessionLocal()
pending_call = db.query(models.Call).filter(
    models.Call.status == models.CallStatus.pending
).first()

if not pending_call:
    print("[INFO] No pending calls, trying processing or failed...")
    pending_call = db.query(models.Call).filter(
        models.Call.status.in_([models.CallStatus.processing, models.CallStatus.failed])
    ).first()

if pending_call:
    call_id = str(pending_call.id)
    print(f"\n{'='*60}")
    print(f"Processing call: {call_id}")
    print(f"Patient: {pending_call.patient_name}")
    print(f"{'='*60}\n")

    try:
        process_call(call_id)

        # Refresh and check result
        db.refresh(pending_call)
        print(f"\n[OK] Processing complete")
        print(f"Status: {pending_call.status}")
        print(f"Error: {pending_call.error_message}")

        # Get scores
        rubric_scores = db.query(models.RubricScore).filter(
            models.RubricScore.call_id == pending_call.id
        ).all()

        if rubric_scores:
            print(f"\n[OK] Got {len(rubric_scores)} dimension scores:")
            for score in rubric_scores:
                print(f"  {score.dimension}: {score.score}")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[ERROR] No calls to process")

db.close()
