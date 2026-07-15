#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()
call_id = 'e688cc50-6fef-4e86-a885-1be482d805fd'

# Rubric scores
scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call_id).all()
print(f"Rubric scores: {len(scores)}")
for s in scores:
    print(f"  dim={s.dimension!r}  score={s.score}  overall={s.overall_weighted_score}")
    raw = s.raw_llm_response or {}
    if isinstance(raw, dict):
        print(f"    raw keys: {list(raw.keys())}")
        ins = raw.get("insights")
        if ins:
            print(f"    insights: {ins}")

# QA flags
flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call_id).all()
print(f"\nQA flags: {len(flags)}")
for f in flags[:5]:
    print(f"  [{f.flag_type}] triggered={f.triggered} detail={str(f.detail)[:60]}")

# Dietician
call = db.query(models.Call).filter(models.Call.id == call_id).first()
print(f"\nCall dietician_id: {call.dietician_id}")
print(f"Call dietician obj: {call.dietician}")
if call.dietician:
    print(f"Dietician name: {call.dietician.name}")

# Transcript entities
tr = db.query(models.Transcript).filter(models.Transcript.call_id == call_id).first()
if tr and tr.raw_transcript_json:
    print(f"\nTranscript engine: {tr.raw_transcript_json.get('engine')}")
    print(f"Transcript entities: {tr.raw_transcript_json.get('entities', {})}")
    print(f"Diarized lines count: {len(tr.raw_transcript_json.get('diarized_lines', []))}")

db.close()
