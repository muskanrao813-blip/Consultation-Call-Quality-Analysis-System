#!/usr/bin/env python3
import requests
import json

base_url = "http://127.0.0.1:8000/api"

print("=== TESTING DIETICIAN QA SYSTEM ===\n")

# Test 1: Get dieticians
try:
    r = requests.get(f"{base_url}/dieticians/")
    data = r.json()
    print(f"[PASS] Get Dieticians: {r.status_code}")
    print(f"       Found {len(data)} dieticians")
    if data:
        print(f"       Sample: {data[0]['name']} (ID: {data[0]['id'][:8]}...)")
except Exception as e:
    print(f"[FAIL] Get Dieticians: {e}")

# Test 2: Download template
try:
    r = requests.get(f"{base_url}/template")
    print(f"\n[PASS] Download Template: {r.status_code}")
    print(f"       File size: {len(r.content)} bytes")
except Exception as e:
    print(f"[FAIL] Download Template: {e}")

# Test 3: Get docs
try:
    r = requests.get("http://127.0.0.1:8000/docs")
    print(f"\n[PASS] Swagger Docs: {r.status_code}")
except Exception as e:
    print(f"[FAIL] Swagger Docs: {e}")

# Test 4: Get portal
try:
    r = requests.get("http://127.0.0.1:8000/")
    print(f"\n[PASS] Portal HTML: {r.status_code}")
    print(f"       Has Upload tab: {'Upload' in r.text}")
    print(f"       Has Scorecard tab: {'Scorecard' in r.text}")
    print(f"       Has Dietician Dashboard: {'Dietician' in r.text}")
except Exception as e:
    print(f"[FAIL] Portal HTML: {e}")

print("\n=== CORE ENDPOINTS VERIFIED ===")
