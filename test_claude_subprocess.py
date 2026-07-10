#!/usr/bin/env python3
import subprocess
import json
import tempfile
import os

print("Testing Claude CLI via subprocess with full path...")
print("="*80)

# Test prompt
prompt = """Analyze this call and score it 1-10 on friendliness.

Call: "Hello, how are you? I'm here to help you with your diet plan."

Respond with JSON only:
{"score": <number>, "reason": "<explanation>"}"""

# Write to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(prompt)
    temp_file = f.name

try:
    # Use full path
    claude_cmd = r"C:\Users\muskan.rao\AppData\Roaming\npm\claude.cmd"

    print(f"Running: {claude_cmd}")
    print(f"With prompt file: {temp_file}")

    result = subprocess.run(
        f'"{claude_cmd}" < "{temp_file}"',
        shell=True,
        capture_output=True,
        text=True,
        timeout=30
    )

    print(f"\nReturn code: {result.returncode}")
    print(f"Output length: {len(result.stdout)} chars")

    if result.returncode == 0:
        print("\n✓ SUCCESS! Claude CLI works via subprocess!")
        print("\nOutput (first 500 chars):")
        print(result.stdout[:500])
    else:
        print(f"\n✗ Failed with return code {result.returncode}")
        print(f"Error: {result.stderr[:500]}")

finally:
    os.remove(temp_file)

print("\n" + "="*80)
