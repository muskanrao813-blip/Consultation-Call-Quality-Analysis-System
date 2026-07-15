#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recalculate overall_weighted_score for all completed calls using the fixed scoring formula."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import SessionLocal
from app.db import models
from app.services.scoring import compute_weighted_score

db = SessionLocal()

calls = db.query(models.Call).filter(models.Call.status == "completed").all()
print(f"Recalculating scores for {len(calls)} completed calls...")

for call in calls:
    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
    dim_scores = {}
    for s in scores:
        dim_scores[s.dimension] = s.score or 0

    if not dim_scores:
        print(f"  {str(call.id)[:8]}... SKIPPED (no scores)")
        continue

    new_score = compute_weighted_score(dim_scores)
    old_score = scores[0].overall_weighted_score if scores else None

    # Update all rubric scores for this call
    for s in scores:
        s.overall_weighted_score = new_score

    # Also remove duplicate QA flags
    all_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
    seen_types = set()
    removed = 0
    for flag in all_flags:
        if flag.flag_type in seen_types:
            db.delete(flag)
            removed += 1
        else:
            seen_types.add(flag.flag_type)

    print(f"  {str(call.id)[:8]}... score {old_score} → {new_score} | dims={dim_scores} | dupes removed={removed}")

db.commit()
db.close()
print("\nDone. Scores recalculated and duplicate flags removed.")
