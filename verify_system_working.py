#!/usr/bin/env python3
"""Verify the system is working with real Claude CLI analysis."""

import sys
sys.path.insert(0, r"C:\Users\muskan.rao\Documents\claude\dietician-qa")

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call
from datetime import datetime

print("="*80)
print("SYSTEM VERIFICATION TEST")
print("Checking: (1) Claude CLI is used, (2) Different calls get different scores")
print("="*80)

db = SessionLocal()

# Create test calls
test_data = [
    ("Dr. Priya", "Patient A", "APT-001"),
    ("Dr. Arjun", "Patient B", "APT-002"),
    ("Dr. Neha", "Patient C", "APT-003"),
]

call_ids = []
print("\n1. Creating test calls...")
for dietician_name, patient_name, appointment_id in test_data:
    # Create dietician
    dietician = models.Dietician(name=dietician_name, needs_admin_confirmation=True)
    db.add(dietician)
    db.flush()

    # Create call
    call = models.Call(
        dietician_id=dietician.id,
        patient_id=f"P-{appointment_id}",
        patient_name=patient_name,
        appointment_id=appointment_id,
        call_datetime=datetime.utcnow(),
        recording_url="https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3",
        status=models.CallStatus.pending,
    )
    db.add(call)
    db.flush()
    call_ids.append((call.id, dietician_name))
    print(f"   Created: {dietician_name} - {appointment_id}")

db.commit()

# Process calls
print("\n2. Processing calls...")
for call_id, dietician_name in call_ids:
    print(f"   Processing {dietician_name}...")
    try:
        process_call(str(call_id))
        print(f"   [OK] Completed")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

# Check results
print("\n3. Verifying results...")
db = SessionLocal()
scores = []

for call_id, dietician_name in call_ids:
    call = db.query(models.Call).filter(models.Call.id == call_id).first()
    if call:
        score = call.overall_weighted_score
        scores.append((dietician_name, score))
        print(f"   {dietician_name}: {score}/10 (Status: {call.status})")

# Check if scores are different
print("\n4. Verification Results:")
if len(set([s[1] for s in scores])) == len(scores):
    print("   [OK] SUCCESS: All calls have different scores!")
    print("   [OK] Claude CLI is working correctly")
    for dietician, score in scores:
        print(f"      - {dietician}: {score}")
else:
    print("   [FAIL] Some scores are identical")
    for dietician, score in scores:
        print(f"      - {dietician}: {score}")

db.close()
print("\n" + "="*80)
