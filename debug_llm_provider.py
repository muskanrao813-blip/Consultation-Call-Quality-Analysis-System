#!/usr/bin/env python3
import os
import sys
import subprocess

print("="*80)
print("Debugging LLM Provider Selection")
print("="*80)

# Test 1: Direct subprocess call
print("\n1. Testing Claude CLI directly via subprocess...")
try:
    result = subprocess.run(
        [r"C:\Users\muskan.rao\AppData\Roaming\npm\claude.cmd", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"   Return code: {result.returncode}")
    print(f"   Output: {result.stdout.strip()}")
    if result.returncode == 0:
        print("   ✓ Claude CLI accessible via full path")
    else:
        print("   ✗ Claude CLI failed")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Check what provider gets selected
print("\n2. Checking provider detection in pipeline...")
sys.path.insert(0, r"C:\Users\muskan.rao\Documents\claude\dietician-qa")

try:
    from app.services.pipeline import _get_llm_provider

    provider = _get_llm_provider()
    print(f"   Selected provider: {provider.__name__}")

    if "claude" in provider.__name__.lower():
        print("   ✓ Claude provider selected")
    elif "local" in provider.__name__.lower():
        print("   ✗ LOCAL analyzer selected (fallback!)")
    else:
        print(f"   ? Unknown provider: {provider.__name__}")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check if Claude is found via os.popen (what pipeline uses)
print("\n3. Testing os.popen detection (what pipeline uses)...")
try:
    result = os.popen("claude --version 2>&1").read()
    print(f"   Output: {result.strip()}")
    if "claude" in result.lower() and "error" not in result.lower():
        print("   ✓ Claude found via os.popen")
    else:
        print("   ✗ Claude not found via os.popen")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*80)
