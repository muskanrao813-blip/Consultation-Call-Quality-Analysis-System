#!/usr/bin/env python
"""Test upload with detailed error reporting."""
import requests
import json

BASE_URL = "http://localhost:8001"

# Create test CSV
csv_content = """dietician_name,appointment_id,recording_url
Dr. Hitesh,APT-001,https://example.com/call1.wav
Dr. Priya,APT-002,https://example.com/call2.wav"""

print("Testing upload with detailed error reporting...\n")

files = {'file': ('test.csv', csv_content, 'text/csv')}
resp = requests.post(f"{BASE_URL}/api/calls/bulk-upload", files=files, timeout=15)

if resp.status_code == 200:
    data = resp.json()
    print(f"Upload status: {data['valid_rows']} valid, {data['invalid_rows']} invalid")
    print(f"Batch ID: {data['batch_id']}\n")

    if data['invalid_rows'] > 0:
        print("Validation errors:")
        for row in data['rows']:
            if row['status'] != 'valid':
                print(f"  Row {row['row_num']}: {row['reason']}")

    if data['valid_rows'] > 0:
        print("\nValid rows:")
        for row in data['rows']:
            if row['status'] == 'valid':
                print(f"  Row {row['row_num']}: Valid")
else:
    print(f"Upload error: {resp.status_code}")
    print(resp.text)
