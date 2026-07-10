#!/usr/bin/env python
"""Test importing the pipeline module."""
import sys
sys.path.insert(0, '.')

print("Testing pipeline import...\n")

try:
    print("1. Importing app.services.pipeline...")
    from app.services import pipeline
    print("   [OK] Module imported")

    print("\n2. Checking for process_call function...")
    if hasattr(pipeline, 'process_call'):
        print("   [OK] process_call function found")
        print(f"   Type: {type(pipeline.process_call)}")
        print(f"   Callable: {callable(pipeline.process_call)}")
    else:
        print("   [FAIL] process_call not found")
        print(f"   Available: {dir(pipeline)}")

    print("\n3. Trying direct import...")
    from app.services.pipeline import process_call
    print("   [OK] Direct import successful")

except Exception as e:
    print(f"   [ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
