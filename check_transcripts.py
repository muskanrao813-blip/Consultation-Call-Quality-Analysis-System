#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

print("\n" + "="*80)
print("CHECKING ALL TRANSCRIPTS IN DATABASE")
print("="*80)

transcripts = db.query(models.Transcript).all()
print(f"\nTotal transcripts: {len(transcripts)}\n")

for trans in transcripts[:5]:
    print(f"Call ID: {trans.call_id}")
    print(f"Provider: {trans.provider}")

    segs = trans.diarized_segments
    if isinstance(segs, str):
        segs = json.loads(segs)

    print(f"Segments: {len(segs)}")
    for i, seg in enumerate(segs[:2]):
        text = seg.get('text', '')[:60]
        print(f"  [{i+1}] {text}")

    # Check if it looks like real Whisper or mock
    all_text = " ".join([s.get('text', '') for s in segs])
    if "Dietician consultation" in all_text or "Patient response" in all_text:
        print(f"Type: MOCK")
    elif len(segs) > 2:
        print(f"Type: LIKELY REAL WHISPER (many segments)")
    else:
        print(f"Type: UNKNOWN")

    print()

db.close()
