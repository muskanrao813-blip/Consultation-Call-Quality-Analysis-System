#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the upload endpoint to find the issue."""

import requests
import sys
from pathlib import Path
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://127.0.0.1:8000"

def test_upload():
    # Try to find test file
    test_files = [
        "test_calls.xlsx",
        "test_calls_unique.xlsx"
    ]

    test_file = None
    for f in test_files:
        if Path(f).exists():
            test_file = f
            break

    if not test_file:
        print("[FAIL] No test file found")
        return False

    print(f"[OK] Found test file: {test_file}")

    # Test upload
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BASE_URL}/api/calls/bulk-upload",
                files=files,
                timeout=10
            )

        print(f"[OK] Upload request sent")
        print(f"[INFO] Status: {response.status_code}")
        print(f"[INFO] Response: {response.text[:500]}")

        return response.status_code == 200

    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload()
    sys.exit(0 if success else 1)
