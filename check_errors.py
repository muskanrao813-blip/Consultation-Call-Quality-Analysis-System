#!/usr/bin/env python3
"""Check error messages for failed calls."""

from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()
calls = db.query(models.Call).filter(models.Call.status == models.CallStatus.failed).all()

print(f"[INFO] Failed calls: {len(calls)}\n")

for call in calls[:5]:
    print(f"Call: {call.patient_name}")
    print(f"  ID: {call.id}")
    print(f"  Status: {call.status}")
    print(f"  Error: {call.error_message}")
    print()

db.close()
