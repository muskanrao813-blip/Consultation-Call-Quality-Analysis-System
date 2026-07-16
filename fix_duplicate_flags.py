#!/usr/bin/env python3
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()
calls = db.query(models.Call).filter(models.Call.status == "completed").all()

total_removed = 0
for call in calls:
    flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()

    # Normalize: strip "Sop Violation: " prefix so duplicates collapse
    seen = {}  # normalized_title -> flag object to keep
    to_delete = []

    for flag in flags:
        # Normalize title
        norm = re.sub(r'^sop violation:\s*', '', flag.flag_type, flags=re.IGNORECASE).strip().lower()
        if norm in seen:
            to_delete.append(flag)  # duplicate
        else:
            seen[norm] = flag

    for flag in to_delete:
        db.delete(flag)
    total_removed += len(to_delete)

    remaining = len(flags) - len(to_delete)
    print(f"  {str(call.id)[:8]}: removed {len(to_delete)} dupes, kept {remaining} unique alerts")

db.commit()
db.close()
print(f"\nTotal duplicate flags removed: {total_removed}")
