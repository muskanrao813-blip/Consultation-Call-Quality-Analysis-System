#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:\Users\muskan.rao\Documents\claude\dietician-qa")

from app.services.pipeline import _get_llm_provider

print("Testing provider detection...")

try:
    provider = _get_llm_provider()
    print(f"Selected provider: {provider.__name__}")

    if "Claude" in provider.__name__:
        print("[OK] Claude provider selected")
    else:
        print(f"[FAIL] Non-Claude provider selected: {provider.__name__}")
except Exception as e:
    print(f"[FAIL] Error getting provider: {e}")
    import traceback
    traceback.print_exc()
