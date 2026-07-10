#!/usr/bin/env python
import sys

print("Testing Whisper installation...")
try:
    import whisper
    print("[OK] Whisper is installed")
    print("[OK] Ready for transcription")
except ImportError as e:
    print(f"[INSTALL] Whisper not installed: {e}")
    print("\nInstalling Whisper...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper", "-q"])
    import whisper
    print("[OK] Whisper installed successfully")

print("\nTesting Ollama client...")
try:
    from ollama import Client
    print("[OK] Ollama client is installed")
except ImportError:
    print("[INSTALL] Ollama client not installed")
    print("Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama", "-q"])
    from ollama import Client
    print("[OK] Ollama client installed")

print("\n" + "="*50)
print("READY FOR LOCAL PROCESSING")
print("="*50)
print("\nNext steps:")
print("1. Install Ollama: https://ollama.ai")
print("2. Run: ollama pull mistral")
print("3. Run: ollama serve")
print("4. Upload file to http://localhost:8001")
print("5. Watch automatic processing")
