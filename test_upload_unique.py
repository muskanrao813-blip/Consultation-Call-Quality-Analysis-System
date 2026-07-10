#!/usr/bin/env python3
import requests

print("Testing upload with unique IDs...\n")

with open('test_calls_unique.xlsx', 'rb') as f:
    files = {'file': ('test_calls_unique.xlsx', f)}
    r = requests.post('http://127.0.0.1:8000/api/calls/bulk-upload', files=files)

data = r.json()
print(f'Upload Status: {r.status_code}')
print(f'Batch ID: {data.get("batch_id")}')
print(f'Valid rows: {data.get("valid_rows")}')
print(f'Invalid rows: {data.get("invalid_rows")}')

if data.get('rows'):
    print(f'\nValidation details:')
    for row in data.get('rows', []):
        status = row.get('status', 'unknown')
        reason = row.get('reason', 'OK')
        print(f'  Row {row["row_num"]}: {status.upper():7} - {reason}')

batch_id = data.get("batch_id")
if batch_id:
    print(f'\nBatch Progress:')
    progress_r = requests.get(f'http://127.0.0.1:8000/api/batches/{batch_id}/progress')
    if progress_r.status_code == 200:
        progress = progress_r.json()
        print(f'  Total: {progress.get("total")}')
        print(f'  Completed: {progress.get("completed")}')
        print(f'  Pending: {progress.get("pending")}')
        print(f'  Failed: {progress.get("failed")}')
        print(f'  Progress: {progress.get("pct_complete", 0)}%')
