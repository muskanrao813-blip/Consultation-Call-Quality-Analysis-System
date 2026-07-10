#!/usr/bin/env python3
import os
import subprocess

print("="*80)
print("Verifying Claude CLI Setup")
print("="*80)

# Test 1: Can we find claude command?
print("\n1. Testing 'claude --version'...")
try:
    result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
    print(f"   Return code: {result.returncode}")
    print(f"   Output: {result.stdout.strip()}")
    if result.stderr:
        print(f"   Stderr: {result.stderr.strip()}")
    if result.returncode == 0:
        print("   ✓ Claude CLI found!")
    else:
        print("   ✗ Claude CLI failed!")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Import the pipeline provider detection
print("\n2. Testing LLM provider detection in pipeline...")
try:
    import sys
    sys.path.insert(0, "C:\\Users\\muskan.rao\\Documents\\claude\\dietician-qa")
    from app.services.pipeline import _get_llm_provider

    provider = _get_llm_provider()
    print(f"   Detected provider: {provider.__name__}")
    if "claude" in provider.__name__.lower():
        print("   ✓ Claude provider detected!")
    else:
        print("   ✗ Claude provider NOT detected!")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Actually try analyzing
print("\n3. Testing Claude LLM analysis...")
try:
    from app.services.llm.claude_cli_analyzer import ClaudeCliAnalyzer

    analyzer = ClaudeCliAnalyzer()

    test_segments = [
        {"speaker": "speaker_0", "text": "How are you today?", "start_s": 0, "end_s": 3},
        {"speaker": "speaker_1", "text": "I'm doing well, thank you", "start_s": 3, "end_s": 6}
    ]

    test_metrics = {
        "duration_seconds": 600,
        "dietician_talk_ratio_pct": 50,
        "patient_talk_ratio_pct": 50,
        "interruption_count": 0,
        "avg_response_latency_seconds": 2,
        "time_to_first_plan_mention_seconds": 300,
        "silence_pct": 10
    }

    print("   Calling Claude CLI analyzer...")
    result = analyzer.analyze_all_dimensions(test_segments, test_metrics, "test-id", "Dr. Test", "P001")

    print(f"   Result keys: {list(result.keys())}")
    if "dimension_scores" in result:
        discovery = result["dimension_scores"].get("discovery_assessment", {})
        print(f"   Discovery score: {discovery.get('score')}")
        print("   ✓ Claude CLI analysis worked!")
    else:
        print("   ✗ Claude CLI analysis failed - no dimension_scores!")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
