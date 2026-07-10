#!/usr/bin/env python3
"""Check database status."""

from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()
calls = db.query(models.Call).all()
batches = db.query(models.UploadBatch).all()

print(f"[INFO] Total calls in DB: {len(calls)}")
print(f"[INFO] Total batches: {len(batches)}")

if batches:
    print("\n[INFO] Latest batch:")
    latest = sorted(batches, key=lambda b: b.uploaded_at, reverse=True)[0]
    print(f"  - ID: {latest.id}")
    print(f"  - Total rows: {latest.total_rows}")
    print(f"  - Valid rows: {latest.valid_rows}")
    print(f"  - Uploaded at: {latest.uploaded_at}")

if calls:
    print("\n[INFO] Latest calls:")
    latest_calls = sorted(calls, key=lambda c: c.created_at, reverse=True)[:3]
    for call in latest_calls:
        print(f"  - {call.id}: status={call.status}, patient={call.patient_name}")

db.close()
