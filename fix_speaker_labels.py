#!/usr/bin/env python3
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()
fixed_total = 0

calls = db.query(models.Call).filter(models.Call.status == "completed").all()
for call in calls:
    tr = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
    if not tr or not tr.raw_transcript_json:
        continue

    raw = tr.raw_transcript_json
    lines = raw.get("diarized_lines", [])
    if not lines:
        continue

    fixed = 0
    for line in lines:
        text = line.get("text", "")
        speaker = line.get("speaker", "")

        # Rule 1: "X bol rahe hain sir/ma'am/ji?" → always DIETICIAN (asking if patient is there)
        if re.search(r'bol rahe h[aā]in|bol raha h[uū]n|speaking to', text, re.IGNORECASE):
            if speaker == "patient":
                line["speaker"] = "dietician"
                fixed += 1

        # Rule 2: "market mein hoon / sunai nahi de raha / baad mein call" → always CUSTOMER
        if re.search(r'market mein|sunai nahi|baad mein (bol|call|baat)|call later', text, re.IGNORECASE):
            if speaker == "dietician":
                line["speaker"] = "patient"
                fixed += 1

        # Rule 3: "TVS Bajaj / consultation book / general guideline bhej" → DIETICIAN
        if re.search(r'(TVS Bajaj|consultation book|guideline bhej|WhatsApp par aayeg)', text, re.IGNORECASE):
            if speaker == "patient":
                line["speaker"] = "dietician"
                fixed += 1

    if fixed > 0:
        # Rebuild full transcript text from fixed lines
        full_text_lines = []
        for l in lines:
            sp = "Dietician" if l["speaker"] == "dietician" else "Customer"
            full_text_lines.append(f"[{sp}]: {l['text']}")
        new_text = "\n".join(full_text_lines)

        raw["diarized_lines"] = lines
        raw["text"] = new_text
        raw["text_reconstructed"] = new_text
        tr.raw_transcript_json = raw
        db.add(tr)
        fixed_total += fixed
        print(f"  Fixed {fixed} lines in call {str(call.id)[:8]} ({call.patient_name})")

db.commit()
db.close()
print(f"\nTotal lines fixed: {fixed_total}")
