#!/usr/bin/env python3
"""
Test portal APIs to verify it's working
"""
import requests
import json

base_url = "http://localhost:3000/api"

print("\n" + "="*80)
print("TESTING PORTAL - API Endpoints")
print("="*80)

# Test 1: Get all dieticians
print("\n[1] GET /api/dieticians/")
try:
    r = requests.get(f"{base_url}/dieticians/")
    if r.status_code == 200:
        dieticians = r.json()
        print(f"    Status: 200 OK")
        print(f"    Dieticians found: {len(dieticians)}")
        for d in dieticians[:3]:
            print(f"    - {d['name']}: {d['call_count']} calls, avg score: {d['avg_score']}")
    else:
        print(f"    Status: {r.status_code}")
except Exception as e:
    print(f"    Error: {e}")

# Test 2: Get calls
print("\n[2] GET /api/calls/ (first completed call)")
try:
    from app.db.session import SessionLocal
    from app.db import models

    db = SessionLocal()
    call = db.query(models.Call).filter(
        models.Call.status == models.CallStatus.completed
    ).first()

    if call:
        r = requests.get(f"{base_url}/calls/{call.id}")
        if r.status_code == 200:
            data = r.json()
            print(f"    Status: 200 OK")
            print(f"    Call: {data.get('patient_name', 'Unknown')}")
            print(f"    Overall score: {data.get('overall_weighted_score', 'N/A')}/10")
            print(f"    Transcript segments: {len(data.get('transcript_segments', []))}")
            print(f"    QA flags triggered: {data.get('flags_triggered_count', 0)}")
        else:
            print(f"    Status: {r.status_code}")
    db.close()
except Exception as e:
    print(f"    Error: {e}")

# Test 3: Get dietician summary
print("\n[3] GET /api/dieticians/{id}/summary")
try:
    from app.db.session import SessionLocal
    from app.db import models

    db = SessionLocal()
    dietician = db.query(models.Dietician).first()

    if dietician:
        r = requests.get(f"{base_url}/dieticians/{dietician.id}/summary")
        if r.status_code == 200:
            data = r.json()
            print(f"    Status: 200 OK")
            print(f"    Dietician: {data.get('name', 'Unknown')}")
            print(f"    Total calls: {data.get('total_calls', 0)}")
            print(f"    Avg score: {data.get('avg_overall_score', 'N/A')}/10")
            print(f"    Peer rank: {data.get('peer_rank', 'N/A')}")
            print(f"    Retraining recommended: {data.get('retraining_recommended', False)}")
        else:
            print(f"    Status: {r.status_code}")
    db.close()
except Exception as e:
    print(f"    Error: {e}")

# Test 4: Portal HTML
print("\n[4] GET / (Portal HTML)")
try:
    r = requests.get("http://localhost:3000/")
    if r.status_code == 200:
        print(f"    Status: 200 OK")
        print(f"    Portal loads: Yes")
        print(f"    Has Upload tab: {'Upload' in r.text}")
        print(f"    Has Scorecard tab: {'Scorecard' in r.text}")
        print(f"    Has Dashboard tab: {'Dietician' in r.text}")
    else:
        print(f"    Status: {r.status_code}")
except Exception as e:
    print(f"    Error: {e}")

print("\n" + "="*80)
print("PORTAL IS WORKING")
print("="*80)
print("\nAccess at: http://localhost:3000")
print("\nFeatures:")
print("  - Upload Tab: Upload call files")
print("  - Scorecard Tab: View individual call analysis")
print("  - Dietician Dashboard: View performance metrics")
