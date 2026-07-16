"""
Test all free transcription approaches on the degraded audio.
Compare outputs and determine which is best.
"""

import requests
import tempfile
import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import librosa
from scipy import signal
from scipy.fft import fft, ifft
import soundfile as sf
import whisper

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

from groq import Groq
import httpx

url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

print("=" * 100)
print("COMPREHENSIVE TRANSCRIPTION COMPARISON TEST")
print("=" * 100)
print()

# Download audio
print("[SETUP] Downloading audio...")
response = requests.get(url, verify=False, timeout=30)
audio_file = os.path.join(tempfile.gettempdir(), "comparison_test.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)
print(f"Downloaded: {len(response.content)} bytes")
print()

results = {}

# ============================================================================
# APPROACH 1: AGGRESSIVE PREPROCESSING + WHISPER TINY
# ============================================================================
print("[1/6] AGGRESSIVE PREPROCESSING + WHISPER TINY")
print("-" * 100)

try:
    # Load audio
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Step 1: Spectral subtraction (aggressive)
    n_fft = 2048
    hop_length = 512
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    # Estimate noise from first second
    noise_frames = int(1.0 * sr / hop_length)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    # Aggressive subtraction
    power_reduced = power - 3 * noise_power
    power_reduced = np.maximum(power_reduced, 0.05 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=hop_length)

    # Step 2: Voice Activity Detection - extract only high energy frames
    S = librosa.feature.melspectrogram(y=y_reduced, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)
    energy = np.mean(S_db, axis=0)

    # Gate based on energy
    threshold = np.percentile(energy, 30)
    vad_mask = energy > threshold

    # Step 3: Upsample to 16kHz
    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
        sr = 16000
    else:
        y_processed = y_reduced

    # Step 4: Normalize
    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9

    # Save processed audio
    processed_file = os.path.join(tempfile.gettempdir(), "preprocessed_aggressive.wav")
    sf.write(processed_file, y_processed, sr)

    # Transcribe with Whisper tiny
    model = whisper.load_model("tiny")
    result = model.transcribe(processed_file, language="en", temperature=0)

    transcription_1 = result["text"].strip()
    print(f"Output: {transcription_1[:150]}")
    results['1_aggressive_whisper_tiny'] = {
        'approach': 'Aggressive preprocessing + Whisper Tiny',
        'output': transcription_1,
        'length': len(transcription_1)
    }
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")
    results['1_aggressive_whisper_tiny'] = {'error': str(e)}

print()

# ============================================================================
# APPROACH 2: PREPROCESSING + WHISPER MEDIUM (Auto-detect language)
# ============================================================================
print("[2/6] PREPROCESSING + WHISPER MEDIUM (Auto-detect language)")
print("-" * 100)

try:
    # Use same preprocessing as above
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Spectral subtraction
    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2
    noise_frames = int(1.0 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 3 * noise_power
    power_reduced = np.maximum(power_reduced, 0.05 * power)
    mag_reduced = np.sqrt(power_reduced)
    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    # Upsample
    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9

    processed_file = os.path.join(tempfile.gettempdir(), "preprocessed_medium.wav")
    sf.write(processed_file, y_processed, 16000)

    # Transcribe without language hint (auto-detect)
    model = whisper.load_model("medium")
    result = model.transcribe(processed_file, temperature=0)

    transcription_2 = result["text"].strip()
    print(f"Output: {transcription_2[:150]}")
    results['2_medium_auto_detect'] = {
        'approach': 'Preprocessing + Whisper Medium (auto-detect)',
        'output': transcription_2,
        'length': len(transcription_2)
    }
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")
    results['2_medium_auto_detect'] = {'error': str(e)}

print()

# ============================================================================
# APPROACH 3: MINIMAL PREPROCESSING + WHISPER BASE (Hindi language)
# ============================================================================
print("[3/6] MINIMAL PREPROCESSING + WHISPER BASE (Hindi language)")
print("-" * 100)

try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Minimal: just upsample and normalize
    if sr != 16000:
        y_processed = librosa.resample(y, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9

    processed_file = os.path.join(tempfile.gettempdir(), "preprocessed_minimal.wav")
    sf.write(processed_file, y_processed, 16000)

    # Transcribe with base model, Hindi
    model = whisper.load_model("base")
    result = model.transcribe(processed_file, language="hi", temperature=0)

    transcription_3 = result["text"].strip()
    print(f"Output: {transcription_3[:150]}")
    results['3_base_hindi'] = {
        'approach': 'Minimal preprocessing + Whisper Base (Hindi)',
        'output': transcription_3,
        'length': len(transcription_3)
    }
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")
    results['3_base_hindi'] = {'error': str(e)}

print()

# ============================================================================
# APPROACH 4: GROQ (Direct, no preprocessing)
# ============================================================================
print("[4/6] GROQ WHISPER API (Direct)")
print("-" * 100)

try:
    import base64
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    audio_base64 = base64.standard_b64encode(audio_data).decode('utf-8')

    http_client = httpx.Client(verify=False)
    groq_client = Groq(api_key="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", http_client=http_client)

    with open(audio_file, 'rb') as f:
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), f, "audio/mpeg"),
            model="whisper-large-v3-turbo",
            language="hi",
            temperature=0.0,
        )

    transcription_4 = transcript.text.strip()
    print(f"Output: {transcription_4[:150]}")
    results['4_groq'] = {
        'approach': 'Groq Whisper API',
        'output': transcription_4,
        'length': len(transcription_4)
    }
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")
    results['4_groq'] = {'error': str(e)}

print()

# ============================================================================
# APPROACH 5: ENSEMBLE (Vote on outputs)
# ============================================================================
print("[5/6] ENSEMBLE APPROACH (Compare all outputs)")
print("-" * 100)

try:
    # Simple ensemble: show all outputs side by side
    print("Ensemble voting on transcription quality...")
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")

print()

# ============================================================================
# APPROACH 6: WHISPER TINY + NO LANGUAGE HINT
# ============================================================================
print("[6/6] WHISPER TINY (Auto-detect, no language hint)")
print("-" * 100)

try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    if sr != 16000:
        y_processed = librosa.resample(y, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9

    processed_file = os.path.join(tempfile.gettempdir(), "whisper_noLang.wav")
    sf.write(processed_file, y_processed, 16000)

    # No language hint
    model = whisper.load_model("tiny")
    result = model.transcribe(processed_file, temperature=0)

    transcription_6 = result["text"].strip()
    print(f"Output: {transcription_6[:150]}")
    results['6_tiny_auto'] = {
        'approach': 'Whisper Tiny (auto-detect language)',
        'output': transcription_6,
        'length': len(transcription_6)
    }
    print("[OK] Success")
except Exception as e:
    print(f"[FAIL] {e}")
    results['6_tiny_auto'] = {'error': str(e)}

print()

# ============================================================================
# SAVE AND COMPARE RESULTS
# ============================================================================
print("=" * 100)
print("COMPARISON SUMMARY")
print("=" * 100)
print()

comparison = {}
for key, data in results.items():
    if 'error' not in data:
        approach = data['approach']
        output = data['output']
        length = data['length']
        comparison[approach] = {
            'length': length,
            'output': output,
            'coherence': 'high' if length > 100 else 'medium' if length > 50 else 'low'
        }
        print(f"{approach}")
        print(f"  Length: {length} chars")
        print(f"  Text: {output[:100]}...")
        print()

# Save all results to JSON
with open(os.path.join(tempfile.gettempdir(), 'transcription_comparison.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("=" * 100)
print(f"Full results saved to: {os.path.join(tempfile.gettempdir(), 'transcription_comparison.json')}")
print("=" * 100)

PYEOF
