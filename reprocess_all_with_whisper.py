#!/usr/bin/env python3
"""
Reset ALL calls to pending and reprocess with real Whisper
"""
import os
os.environ['PATH'] = r"C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin;" + os.environ['PATH']

from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call
import time

db = SessionLocal()

print("\n" + "="*80)
print("REPROCESSING ALL CALLS WITH WHISPER TRANSCRIPTION")
print("="*80)

# Reset ALL calls to pending
print("\n[1] Resetting all calls to pending status...")
all_calls = db.query(models.Call).all()
count = 0
for call in all_calls:
    if call.status != models.CallStatus.pending:
        call.status = models.CallStatus.pending
        count += 1

db.commit()
print(f"    Reset {count} calls to pending")

# Get calls to process
print("\n[2] Processing calls with Whisper...")
pending_calls = db.query(models.Call).filter(
    models.Call.status == models.CallStatus.pending
).limit(5).all()

print(f"    Processing {len(pending_calls)} calls...\n")

results = {
    'success': 0,
    'failed': 0,
    'scores': []
}

for idx, call in enumerate(pending_calls, 1):
    print(f"\n{'='*80}")
    print(f"[{idx}] Call: {call.patient_name}")
    print(f"    Dietician: {call.dietician.name if call.dietician else 'Unknown'}")
    print(f"    Recording: {call.recording_url[:60]}...")
    print(f"    Processing...", end='', flush=True)

    try:
        # Process
        process_call(str(call.id))

        # Get result
        db.expunge_all()
        result_call = db.query(models.Call).filter(models.Call.id == call.id).first()
        scores = db.query(models.RubricScore).filter(
            models.RubricScore.call_id == call.id
        ).all()

        if result_call.status == models.CallStatus.completed:
            score = scores[0].overall_weighted_score if scores else 0
            results['success'] += 1
            results['scores'].append(score)
            print(f" SUCCESS (Score: {score:.1f}/10)")
        else:
            results['failed'] += 1
            print(f" FAILED ({result_call.status})")

    except Exception as e:
        results['failed'] += 1
        print(f" ERROR: {str(e)[:60]}")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"Processed: {results['success'] + results['failed']}")
print(f"Successful: {results['success']}")
print(f"Failed: {results['failed']}")

if results['scores']:
    unique_scores = set([round(s, 1) for s in results['scores']])
    print(f"\nScores from Whisper transcription:")
    print(f"  Unique scores: {sorted(unique_scores)}")
    print(f"  Average: {sum(results['scores'])/len(results['scores']):.1f}/10")
    print(f"\nNote: If all scores are still similar, the audio files may have")
    print(f"similar content. Check the transcripts in the portal!")

db.close()
