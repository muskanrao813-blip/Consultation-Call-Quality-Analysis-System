#!/usr/bin/env python3
"""
Test if the recording URLs are accessible
"""
import requests
import ssl

# Disable SSL warnings
ssl._create_default_https_context = ssl._create_unverified_context

urls = [
    "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3",
    "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3",
]

print("\n" + "="*80)
print("TESTING AUDIO URL ACCESSIBILITY")
print("="*80)

for url in urls:
    print(f"\nURL: {url[:70]}...")
    try:
        response = requests.head(url, timeout=5, verify=False, allow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Content-Length: {response.headers.get('content-length', 'unknown')} bytes")

        if response.status_code == 200:
            print(f"  Result: ACCESSIBLE")
        elif response.status_code in [401, 403]:
            print(f"  Result: REQUIRES AUTHENTICATION")
        else:
            print(f"  Result: ERROR")

    except Exception as e:
        print(f"  Error: {type(e).__name__}: {str(e)[:60]}")
        print(f"  Result: NOT ACCESSIBLE")

print("\n" + "="*80)
print("SOLUTION")
print("="*80)
print("""
If URLs are NOT accessible:
  1. They may require authentication
  2. They may be behind a firewall
  3. They may have expired or been deleted

OPTION 1: Use public URLs
  - Upload audio to a public cloud storage (AWS S3, Google Drive, etc)
  - Use public URLs that don't require auth

OPTION 2: Upload audio files directly
  - Modify the portal to accept audio file uploads
  - System stores files locally and processes them

OPTION 3: Use local test files
  - Create sample audio files
  - Place them in a public directory
  - Reference them with file:// URLs (localhost only)
""")
