#!/usr/bin/env python
"""Test file upload API."""
import requests
import json

BASE_URL = "http://localhost:8001"

# Create test CSV in memory
csv_content = """dietician_name,appointment_id,recording_url
Dr. Hitesh,APT-001,https://example.com/call1.wav
Dr. Priya,APT-002,https://example.com/call2.wav"""

print("=" * 60)
print("TESTING FILE UPLOAD API")
print("=" * 60)

# Test upload
print("\nUploading test CSV file...")
try:
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    resp = requests.post(
        f"{BASE_URL}/api/calls/bulk-upload",
        files=files,
        timeout=15
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"[OK] Upload successful!")
        print(f"  - Total rows: {data['total_rows']}")
        print(f"  - Valid rows: {data['valid_rows']}")
        print(f"  - Invalid rows: {data['invalid_rows']}")
        print(f"  - Batch ID: {data['batch_id']}")

        # Check batch progress
        batch_id = data['batch_id']
        print(f"\nChecking batch progress...")
        resp2 = requests.get(f"{BASE_URL}/api/batches/{batch_id}/progress", timeout=10)
        if resp2.status_code == 200:
            progress = resp2.json()
            print(f"[OK] Batch progress retrieved:")
            print(f"  - Total calls: {progress['total']}")
            print(f"  - Completed: {progress['completed']}")
            print(f"  - Processing: {progress['processing']}")
            print(f"  - Pending: {progress['pending']}")
            print(f"  - Failed: {progress['failed']}")
        else:
            print(f"[FAIL] Could not get progress: {resp2.status_code}")
    else:
        print(f"[FAIL] Upload error {resp.status_code}: {resp.text[:200]}")

except Exception as e:
    print(f"[FAIL] Error: {e}")

print("\n" + "=" * 60)
print("UPLOAD TEST COMPLETE")
print("=" * 60)
