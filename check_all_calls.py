#!/usr/bin/env python3
from app.db.session import SessionLocal
from app.db import models
from datetime import datetime, timedelta

db = SessionLocal()

# Get all calls from last 24 hours
calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(20).all()

print(f"Total recent calls: {len(calls)}\n")

for call in calls[:10]:
    print(f"{'='*80}")
    print(f"Call ID: {str(call.id)[:8]}")
    print(f"Dietician: {call.dietician.name if call.dietician else 'Unknown'}")
    print(f"Created: {call.created_at}")
    print(f"Status: {call.status}")
    print(f"Error: {call.error_message}")

    # Check scores
    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
    if scores:
        print(f"Dimension Scores: {len(scores)} dimensions")
        for score in scores[:2]:
            print(f"  - {score.dimension}: {score.score}")
    else:
        print(f"Dimension Scores: NONE")

    # Check feedback
    feedback = db.query(models.FeedbackNote).filter(models.FeedbackNote.call_id == call.id).first()
    if feedback:
        print(f"Feedback: {feedback.bullet[:100]}")
    else:
        print(f"Feedback: NONE")

    print()

db.close()
