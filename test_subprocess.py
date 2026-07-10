#!/usr/bin/env python3
import subprocess
import json

print("Testing Claude CLI subprocess call...")

# Test the exact same way the code does it
claude_cmd = r"C:\Users\muskan.rao\AppData\Roaming\npm\claude.cmd"

# Simple test prompt
prompt = 'Respond with only valid JSON: {"test": "ok"}'

try:
    result = subprocess.run(
        [claude_cmd],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=30
    )

    print(f"Return code: {result.returncode}")
    print(f"Output length: {len(result.stdout)} chars")
    if result.stdout:
        print(f"First 300 chars:\n{result.stdout[:300]}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:300]}")

    if result.returncode == 0:
        print("\n✓ Claude CLI subprocess works!")
    else:
        print("\n✗ Claude CLI subprocess failed!")

except Exception as e:
    print(f"Exception: {e}")
