#!/usr/bin/env python3
import os
from app.config import get_settings

settings = get_settings()

print("="*80)
print("LLM Configuration Check")
print("="*80)

print(f"\nGemini API Key from env:")
print(f"  - Length: {len(os.getenv('GEMINI_API_KEY', ''))}")
print(f"  - Set: {'Yes' if os.getenv('GEMINI_API_KEY') else 'NO'}")

print(f"\nGemini API Key from settings:")
print(f"  - Length: {len(settings.gemini_api_key)}")
print(f"  - Value: {settings.gemini_api_key[:20] if settings.gemini_api_key else 'EMPTY'}")

print(f"\nLLM Provider: {settings.llm_provider}")

# Test which provider would be loaded
from app.services.pipeline import _get_llm_provider

try:
    LLMProvider = _get_llm_provider()
    print(f"\nActive LLM Provider: {LLMProvider.__name__}")
except Exception as e:
    print(f"\nError loading LLM: {e}")

print("\n" + "="*80)
