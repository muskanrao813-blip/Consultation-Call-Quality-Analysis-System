#!/usr/bin/env python3
"""Debug Claude CLI analysis with actual pipeline."""

import logging
import sys

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.services.llm.claude_cli_analyzer import ClaudeCliAnalyzer
from app.services.pipeline import _get_llm_provider

print("=" * 60)
print("DEBUG: Claude CLI Analysis")
print("=" * 60)

# Check which LLM provider is being used
print("\n[1] Checking LLM Provider...")
LLMProvider = _get_llm_provider()
print(f"Provider: {LLMProvider.__name__}")

if LLMProvider.__name__ != "ClaudeCliAnalyzer":
    print(f"\nWARNING: Expected ClaudeCliAnalyzer but got {LLMProvider.__name__}")
    print("This means Claude CLI is not being selected")
    sys.exit(1)

# Test with real transcript data
print("\n[2] Testing Claude CLI with mock transcript...")

segments = [
    {'speaker': 'dietician', 'text': 'Good morning, how are you doing today?', 'start_s': 0, 'end_s': 5},
    {'speaker': 'patient', 'text': 'I am doing well, ready to discuss my diet plan', 'start_s': 5, 'end_s': 12},
    {'speaker': 'dietician', 'text': 'Great! Let me start by understanding your medical history. Do you have any conditions?', 'start_s': 12, 'end_s': 25},
    {'speaker': 'patient', 'text': 'Yes, I have diabetes and high blood pressure', 'start_s': 25, 'end_s': 32},
    {'speaker': 'dietician', 'text': 'Thank you for sharing. How is your current lifestyle? Exercise routine?', 'start_s': 32, 'end_s': 42},
    {'speaker': 'patient', 'text': 'I try to walk 30 minutes daily and eat healthy', 'start_s': 42, 'end_s': 50},
]

metrics = {
    'duration_seconds': 300,
    'dietician_talk_ratio_pct': 55,
    'patient_talk_ratio_pct': 40,
    'interruption_count': 1,
    'avg_response_latency_seconds': 2.5,
    'time_to_first_plan_mention_seconds': 180,
    'silence_pct': 5
}

analyzer = LLMProvider()
print(f"Analyzer initialized: {type(analyzer).__name__}")

try:
    print("\n[3] Running analysis...")
    result = analyzer.analyze_all_dimensions(
        segments,
        metrics,
        'test-call-123',
        'Dr. Smith',
        'patient-456'
    )

    print("\n[OK] Analysis successful!")
    print(f"Dimensions returned: {len(result.get('dimension_scores', {}))}")

    # Show scores
    for dim_name, dim_data in result.get('dimension_scores', {}).items():
        score = dim_data.get('score', 'N/A')
        print(f"  {dim_name}: {score}")

    # Calculate overall
    weights = {
        'discovery_assessment': 0.20,
        'empathy_communication': 0.20,
        'rushed_forced_detection': 0.15,
        'adherence_counselling': 0.20,
        'consultation_completeness': 0.25,
    }
    overall = sum(
        result['dimension_scores'][dim]['score'] * weight
        for dim, weight in weights.items()
        if dim in result['dimension_scores']
    )
    print(f"\nOverall Score: {overall:.2f}/10")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
