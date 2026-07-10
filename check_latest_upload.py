#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(3).all()
print(f'Latest calls: {len(calls)}\n')

for call in calls:
    print(f'Call: {call.id}')
    print(f'  Created: {call.created_at}')
    print(f'  Patient: {call.patient_name}')
    print(f'  Status: {call.status}')
    if call.error_message:
        print(f'  Error: {call.error_message}')

    trans = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
    if trans:
        segs = trans.diarized_segments
        if isinstance(segs, str):
            segs = json.loads(segs)
        print(f'  Transcript Provider: {trans.provider}')
        print(f'  Segments: {len(segs)}')
        if segs:
            first_text = str(segs[0].get('text', ''))[:80]
            print(f'  First segment: {first_text}')
    else:
        print(f'  No transcript found')

    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
    if scores:
        print(f'  Overall Score: {scores[0].overall_weighted_score:.1f}/10')
    print()

db.close()
