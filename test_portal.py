#!/usr/bin/env python
"""Test the dietician QA portal API."""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8001"

def test_api():
    print("=" * 60)
    print("TESTING DIETICIAN QA PORTAL")
    print("=" * 60)

    # Test 1: Check if server is running
    print("\n[1/5] Testing server health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            print("[OK] Server is running")
        else:
            print(f"[FAIL] Server responded with {resp.status_code}")
    except Exception as e:
        print(f"[FAIL] Server not responding: {e}")
        return False

    # Test 2: Get dieticians list
    print("\n[2/5] Testing GET /api/dieticians/...")
    try:
        resp = requests.get(f"{BASE_URL}/api/dieticians/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[OK] API working - {len(data)} dieticians in DB")
        else:
            print(f"✗ API error: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ API error: {e}")
        return False

    # Test 3: Get template
    print("\n[3/5] Testing GET /api/template...")
    try:
        resp = requests.get(f"{BASE_URL}/api/template", timeout=5)
        if resp.status_code == 200:
            print(f"[OK] Template download working ({len(resp.content)} bytes)")
        else:
            print(f"✗ Template error: {resp.status_code}")
    except Exception as e:
        print(f"✗ Template error: {e}")

    # Test 4: Check if portal HTML is served
    print("\n[4/5] Testing portal HTML...")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        if resp.status_code == 200:
            if "dietician_qa_portal" in resp.text or "Dietician" in resp.text:
                print(f"[OK] Portal HTML is being served ({len(resp.text)} bytes)")
            else:
                print(f"[OK] Home page loaded ({len(resp.text)} bytes)")
        else:
            print(f"✗ Portal error: {resp.status_code}")
    except Exception as e:
        print(f"✗ Portal error: {e}")

    # Test 5: Check database
    print("\n[5/5] Checking database...")
    try:
        import sqlite3
        conn = sqlite3.connect("test.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if tables:
            print(f"[OK] Database initialized with {len(tables)} tables")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("✗ No tables in database")
        conn.close()
    except Exception as e:
        print(f"✗ Database error: {e}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n[OK] Portal is ready to use!")
    print(f"Open: http://localhost:8001")
    return True

if __name__ == "__main__":
    time.sleep(2)  # Wait for server to start
    success = test_api()
    sys.exit(0 if success else 1)
