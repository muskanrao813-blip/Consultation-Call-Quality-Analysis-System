#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()

calls = db.query(models.Call).limit(5).all()
print('='*70)
print('CALLS IN DATABASE')
print('='*70)
for i, call in enumerate(calls, 1):
    print(f'\nCall {i}:')
    print(f'  Patient: {call.patient_name}')
    print(f'  Dietician: {call.dietician.name if call.dietician else "Unknown"}')
    print(f'  Recording URL: {call.recording_url}')
    print(f'  Status: {call.status}')
    print(f'  Duration: {call.call_duration_seconds}s')

db.close()
