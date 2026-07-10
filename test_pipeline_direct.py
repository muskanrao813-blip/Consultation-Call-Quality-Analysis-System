#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:\Users\muskan.rao\Documents\claude\dietician-qa")

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call
import uuid
from datetime import datetime

print("="*80)
print("Direct Pipeline Test")
print("="*80)

db = SessionLocal()

# Create a test call
print("\n1. Creating test call...")
call = models.Call(
    dietician_id=None,
    patient_id="TEST-P001",
    patient_name="Test Patient",
    appointment_id="TEST-APT-001",
    call_datetime=datetime.utcnow(),
    recording_url="https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3",
    status=models.CallStatus.pending,
)

# First create dietician
dietician = models.Dietician(
    name="Test Dietician",
    needs_admin_confirmation=True,
)
db.add(dietician)
db.flush()

call.dietician_id = dietician.id
db.add(call)
db.flush()

call_id = call.id
db.commit()

print(f"Created call: {call_id}")

# Now try to process it
print("\n2. Processing call...")
try:
    process_call(str(call_id))
    print("Processing completed!")
except Exception as e:
    print(f"Processing failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Check result
print("\n3. Checking result...")
db = SessionLocal()
call = db.query(models.Call).filter(models.Call.id == call_id).first()
if call:
    print(f"Call status: {call.status}")
    print(f"Call error: {call.error_message}")
else:
    print("Call not found!")

db.close()
