#!/usr/bin/env python3
import subprocess
import tempfile
import os
import json

print("Testing Claude CLI with stdin...")
print("="*80)

# Simple test prompt
prompt = 'Respond with: {"test": "ok"}'

# Test 1: Via temp file redirect
print("\nTest 1: Via temp file (< redirect)...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(prompt)
    temp_file = f.name

try:
    cmd = f'"{r"C:\Users\muskan.rao\AppData\Roaming\npm\claude.cmd"}" < "{temp_file}"'
    print(f"Command: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

    print(f"Return code: {result.returncode}")
    print(f"Output length: {len(result.stdout)} chars")
    print(f"First 200 chars: {result.stdout[:200]}")

    if result.returncode == 0 and len(result.stdout) > 0:
        print("SUCCESS: Claude CLI responded!")
    else:
        print("FAILED: No response from Claude")
        if result.stderr:
            print(f"Error: {result.stderr[:200]}")

finally:
    os.remove(temp_file)

# Test 2: Via echo pipe
print("\n\nTest 2: Via echo pipe (|)...")
cmd = f'echo {json.dumps({"ask": "hello"})} | "{r"C:\Users\muskan.rao\AppData\Roaming\npm\claude.cmd"}"'
print(f"Command: {cmd}")

result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

print(f"Return code: {result.returncode}")
print(f"Output length: {len(result.stdout)} chars")

if result.returncode == 0 and len(result.stdout) > 0:
    print("SUCCESS: Claude CLI responded via pipe!")
    print(f"First 200 chars: {result.stdout[:200]}")
else:
    print("FAILED: No response from Claude")

print("\n" + "="*80)
