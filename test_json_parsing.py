#!/usr/bin/env python3
import json
import re

# Test the JSON parsing with markdown format
test_output = '''```json
{"dimension_scores": {"discovery_assessment": {"score": 7.2}}}
```'''

print("Testing JSON parsing...")
print(f"Input: {test_output[:100]}")

# Try markdown code block first
markdown_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', test_output, re.DOTALL)
if markdown_match:
    json_str = markdown_match.group(1).strip()
    print(f"Matched markdown: {json_str[:100]}")
    try:
        result = json.loads(json_str)
        print(f"[OK] JSON parsed successfully: {result}")
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON decode error: {e}")
else:
    print("[FAIL] No markdown match")

# Also test without markdown
test_output2 = '{"dimension_scores": {"discovery_assessment": {"score": 7.2}}}'
print(f"\nTesting raw JSON: {test_output2[:50]}")
try:
    result = json.loads(test_output2)
    print(f"[OK] Raw JSON parsed: {result}")
except:
    print("[FAIL] Raw JSON failed")
