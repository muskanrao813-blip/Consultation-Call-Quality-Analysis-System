#!/usr/bin/env python3
import sys, io, copy, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.db.session import SessionLocal
from app.db import models
from sqlalchemy.orm.attributes import flag_modified

db = SessionLocal()

def swap_speaker(s):
    return "patient" if s == "dietician" else "dietician"

# For calls that are fully inverted, swap ALL lines
# Detect: if line 2 contains "X bol rahe hain" and is labeled [patient] → fully inverted
FULLY_INVERTED = set()

calls = db.query(models.Call).filter(models.Call.status == "completed").all()
for call in calls:
    tr = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
    if not tr or not tr.raw_transcript_json:
        continue
    lines = tr.raw_transcript_json.get("diarized_lines", [])
    if len(lines) < 2:
        continue
    # Check lines 1-4 for the "bol rahe hain" in [patient] label — signs of full inversion
    for l in lines[:5]:
        import re
        if l.get("speaker") == "patient" and re.search(r'bol rahe h[aā]in|speaking to', l.get("text",""), re.I):
            FULLY_INVERTED.add(str(call.id))
            break

print("Fully inverted calls:", FULLY_INVERTED)

for call in calls:
    call_id_str = str(call.id)
    tr = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
    if not tr or not tr.raw_transcript_json:
        continue

    # Deep copy to force SQLAlchemy to detect change
    raw = copy.deepcopy(tr.raw_transcript_json)
    lines = raw.get("diarized_lines", [])
    changed = 0

    if call_id_str in FULLY_INVERTED:
        # Swap ALL speakers
        for l in lines:
            old = l.get("speaker")
            l["speaker"] = swap_speaker(old)
            changed += 1
    else:
        # Apply targeted rules only
        import re
        for l in lines:
            text = l.get("text", "")
            sp = l.get("speaker", "")
            # "X bol rahe hain" in patient line → dietician
            if sp == "patient" and re.search(r'bol rahe h[aā]in|speaking to', text, re.I):
                l["speaker"] = "dietician"; changed += 1
            # "market/sunai nahi/baad mein" in dietician line → patient
            if sp == "dietician" and re.search(r'market mein|sunai nahi|baad mein (bol|call|baat)|call later', text, re.I):
                l["speaker"] = "patient"; changed += 1

    if changed > 0:
        # Rebuild full text
        parts = []
        for l in lines:
            label = "Dietician" if l["speaker"] == "dietician" else "Customer"
            parts.append(f"[{label}]: {l['text']}")
        raw["diarized_lines"] = lines
        raw["text"] = "\n".join(parts)
        raw["text_reconstructed"] = "\n".join(parts)

        tr.raw_transcript_json = raw
        flag_modified(tr, "raw_transcript_json")  # Force SQLAlchemy to detect JSON change
        print(f"  Fixed {changed} lines: {call.patient_name} ({call_id_str[:8]})")

db.commit()
db.close()
print("Done")
