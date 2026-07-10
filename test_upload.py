#!/usr/bin/env python3
import requests
import json

print("=== TESTING UPLOAD FUNCTIONALITY ===\n")

# Upload test file
with open('test_calls.xlsx', 'rb') as f:
    files = {'file': ('test_calls.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    r = requests.post('http://127.0.0.1:8000/api/calls/bulk-upload', files=files)

print(f'[TEST] Upload Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'[PASS] Batch uploaded successfully')
    print(f'       Batch ID: {data.get("batch_id", "N/A")[:8] if data.get("batch_id") else "N/A"}...')
    print(f'       Valid rows: {data.get("valid_rows", 0)}')
    print(f'       Invalid rows: {data.get("invalid_rows", 0)}')
    print(f'       Total processed: {data.get("valid_rows", 0) + data.get("invalid_rows", 0)}')

    # Try to get batch progress
    batch_id = data.get("batch_id")
    if batch_id:
        print(f"\n[TEST] Checking batch progress...")
        progress_r = requests.get(f'http://127.0.0.1:8000/api/batches/{batch_id}/progress')
        print(f'       Progress Status: {progress_r.status_code}')
        if progress_r.status_code == 200:
            progress = progress_r.json()
            print(f'       Total: {progress.get("total", 0)}')
            print(f'       Completed: {progress.get("completed", 0)}')
            print(f'       Pending: {progress.get("pending", 0)}')
else:
    print(f'[FAIL] Status: {r.status_code}')
    print(f'       Response: {r.text[:500]}')
