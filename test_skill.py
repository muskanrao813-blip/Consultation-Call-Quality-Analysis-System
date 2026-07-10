#!/usr/bin/env python3
import json
import subprocess

# Test if Claude Skill is available
print("Testing Claude Skill availability...")
print("="*80)

# Check if claude command exists
result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
print(f"Claude CLI version check:")
print(f"  Return code: {result.returncode}")
print(f"  Output: {result.stdout}")
print(f"  Error: {result.stderr}")

print("\n" + "="*80)
print("Testing skill invocation...")

# Test data
test_data = {
    "call_id": "test-123",
    "dietician_name": "Dr. Test",
    "patient_id": "P001",
    "transcript_segments": [
        {"speaker": "speaker_0", "text": "Hello how are you?", "start_s": 0, "end_s": 5},
        {"speaker": "speaker_1", "text": "I'm fine thank you", "start_s": 5, "end_s": 10}
    ],
    "metrics": {
        "duration_seconds": 600,
        "dietician_talk_ratio_pct": 60,
        "patient_talk_ratio_pct": 40,
        "interruption_count": 0,
        "avg_response_latency_seconds": 2.5,
        "time_to_first_plan_mention_seconds": 150,
        "silence_pct": 5
    }
}

try:
    print("Calling: claude skill dietician-qa-analyzer")
    result = subprocess.run(
        ["claude", "skill", "dietician-qa-analyzer"],
        input=json.dumps(test_data),
        capture_output=True,
        text=True,
        timeout=30
    )

    print(f"Return code: {result.returncode}")
    print(f"\nSTDOUT:")
    print(result.stdout[:500])
    print(f"\nSTDERR:")
    print(result.stderr[:500] if result.stderr else "(none)")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
