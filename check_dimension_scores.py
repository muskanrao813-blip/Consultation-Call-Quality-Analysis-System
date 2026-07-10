#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
import json

db = SessionLocal()

# Get the latest 3 calls
calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(3).all()

for call in calls:
    print(f"\n{'='*80}")
    print(f"Call: {str(call.id)[:8]}")
    print(f"{'='*80}")

    # Get all dimension scores for this call
    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()

    for score in scores:
        print(f"\nDimension: {score.dimension}")
        print(f"  Score: {score.score}")
        print(f"  Overall Weighted: {score.overall_weighted_score}")

        # Show sub-criteria
        if score.sub_criteria:
            print(f"  Sub-criteria met: {score.sub_criteria}")

        # Show evidence count
        if score.evidence:
            print(f"  Evidence items: {len(score.evidence)}")

db.close()
