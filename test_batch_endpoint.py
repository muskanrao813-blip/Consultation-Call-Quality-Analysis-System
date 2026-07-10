#!/usr/bin/env python
"""Test batch progress endpoint."""
import requests

BASE_URL = "http://localhost:8001"

print("Testing batch progress endpoint...\n")

# First, get a batch ID from uploaded files
resp = requests.get(f"{BASE_URL}/api/dieticians/")
if resp.status_code == 200:
    dieticians = resp.json()
    print(f"Found {len(dieticians)} dieticians")
    if dieticians:
        print(f"First: {dieticians[0]}\n")

# Now try to get batches - let's list all calls first
print("Getting call list...\n")

# Get database directly
import sqlite3
conn = sqlite3.connect("test.db")
cursor = conn.cursor()

# Get recent batch
cursor.execute("SELECT id, total_rows FROM upload_batches ORDER BY uploaded_at DESC LIMIT 1")
batch = cursor.fetchone()

if batch:
    batch_id, total = batch
    print(f"Testing with batch ID: {batch_id}")
    print(f"Batch has {total} rows\n")

    # Test the endpoint
    print("Testing GET /api/batches/{batch_id}/progress...")
    resp = requests.get(f"{BASE_URL}/api/batches/{batch_id}/progress")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {data}")
    else:
        print(f"Error: {resp.text}")
else:
    print("No batches found in database")

conn.close()
