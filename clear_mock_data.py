#!/usr/bin/env python3
"""
Clear all mock call data - keep only dieticians
"""
from app.db.session import SessionLocal
from app.db import models

db = SessionLocal()

print("\n" + "="*70)
print("CLEARING ALL MOCK DATA")
print("="*70)

# Count before deletion
calls_count = db.query(models.Call).count()
transcripts_count = db.query(models.Transcript).count()
metrics_count = db.query(models.CallMetrics).count()
scores_count = db.query(models.RubricScore).count()
flags_count = db.query(models.QAFlag).count()
feedback_count = db.query(models.FeedbackNote).count()
batches_count = db.query(models.UploadBatch).count()

print(f"\nBefore deletion:")
print(f"  Calls: {calls_count}")
print(f"  Transcripts: {transcripts_count}")
print(f"  Metrics: {metrics_count}")
print(f"  Rubric Scores: {scores_count}")
print(f"  QA Flags: {flags_count}")
print(f"  Feedback Notes: {feedback_count}")
print(f"  Upload Batches: {batches_count}")

# Delete all related data
print(f"\nDeleting all call-related data...")

# Delete in order of dependencies
db.query(models.QAFlag).delete()
db.query(models.FeedbackNote).delete()
db.query(models.RubricScore).delete()
db.query(models.CallMetrics).delete()
db.query(models.Transcript).delete()
db.query(models.Call).delete()
db.query(models.UploadBatch).delete()

db.commit()

# Verify deletion
calls_after = db.query(models.Call).count()
transcripts_after = db.query(models.Transcript).count()
metrics_after = db.query(models.CallMetrics).count()
scores_after = db.query(models.RubricScore).count()

print(f"\nAfter deletion:")
print(f"  Calls: {calls_after}")
print(f"  Transcripts: {transcripts_after}")
print(f"  Metrics: {metrics_after}")
print(f"  Rubric Scores: {scores_after}")

# Check dieticians (should still be there)
dieticians = db.query(models.Dietician).count()
print(f"\nDieticians (kept): {dieticians}")

print(f"\n{'='*70}")
print("CLEAN SLATE READY")
print("="*70)
print("\nAll mock call data has been deleted.")
print("Your portal is ready to accept new recordings!")
print("\nNext steps:")
print("  1. Go to http://localhost:3000")
print("  2. Click 'Upload' tab")
print("  3. Download template")
print("  4. Add your real recordings")
print("  5. Upload - each will be processed with Whisper")
print("  6. View real transcripts and different scores!")

db.close()
