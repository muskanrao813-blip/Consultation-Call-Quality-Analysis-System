#!/usr/bin/env python3
"""Test Gemini LLM directly"""
import logging
from app.config import get_settings
from app.services.llm.gemini import GeminiLLMProvider

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("="*80)
print("Testing Gemini LLM Directly")
print("="*80)

settings = get_settings()
print(f"\nGemini API Key: {settings.gemini_api_key[:20]}...")

try:
    print("\nInitializing Gemini Provider...")
    llm = GeminiLLMProvider(settings.gemini_api_key)
    print("[OK] Provider initialized")

    # Test with sample data
    segments = [
        {
            "speaker": "speaker_0",
            "text": "Hello patient, how are you feeling today?",
            "start_s": 0,
            "end_s": 5
        },
        {
            "speaker": "speaker_1",
            "text": "I'm feeling good, a bit tired from work",
            "start_s": 5,
            "end_s": 10
        }
    ]

    metrics = {
        "duration_seconds": 600,
        "dietician_talk_ratio_pct": 60,
        "patient_talk_ratio_pct": 40,
        "interruption_count": 0,
        "avg_response_latency_seconds": 2.5,
        "time_to_first_plan_mention_seconds": 150,
        "silence_pct": 5,
    }

    print("\nCalling analyze_all_dimensions...")
    result = llm.analyze_all_dimensions(
        segments,
        metrics,
        "test-call-id",
        "Dr. Test",
        "patient-123"
    )

    print("\n[SUCCESS] LLM Response successful!")
    print(f"Dimensions returned: {list(result.get('dimension_scores', {}).keys())}")

    # Show sample dimension score
    discovery = result.get('dimension_scores', {}).get('discovery_assessment', {})
    print(f"\nDiscovery Assessment Score: {discovery.get('score')}")
    print(f"Evidence: {discovery.get('evidence')}")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
