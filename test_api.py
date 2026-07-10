#!/usr/bin/env python3
import requests
import json

base_url = "http://127.0.0.1:8000/api"

# Test 1: Health check
try:
    r = requests.get("http://127.0.0.1:8000/health")
    print(f"[1] Health: {r.status_code}")
except Exception as e:
    print(f"[1] Health: FAILED - {e}")

# Test 2: Get template
try:
    r = requests.get(f"{base_url}/template")
    print(f"[2] Get Template: {r.status_code}, Size: {len(r.content)} bytes")
except Exception as e:
    print(f"[2] Get Template: FAILED - {e}")

# Test 3: List dieticians
try:
    r = requests.get(f"{base_url}/dieticians/")
    data = r.json()
    print(f"[3] List Dieticians: {r.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}")
    if isinstance(data, list) and len(data) > 0:
        print(f"    First: {data[0]}")
except Exception as e:
    print(f"[3] List Dieticians: {r.status_code if 'r' in locals() else 'ERROR'} - {e}")

# Test 4: Get API docs
try:
    r = requests.get("http://127.0.0.1:8000/docs")
    print(f"[4] API Docs: {r.status_code}")
except Exception as e:
    print(f"[4] API Docs: FAILED - {e}")

print("\nAll basic endpoints working!")
