"""
Advanced Hindi transcription approaches - test 8 different methods.
"""

import requests
import tempfile
import os
import json
import logging
from pathlib import Path
import numpy as np
import librosa
from scipy import signal
import soundfile as sf
import whisper
import base64
from groq import Groq
import httpx

logging.basicConfig(level=logging.WARNING)

url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

print("Downloading audio...")
response = requests.get(url, verify=False, timeout=30)
audio_file = os.path.join(tempfile.gettempdir(), "advanced_hindi.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)

results = {}

# ============================================================================
# APPROACH A: AGGRESSIVE PREPROCESSING + WHISPER BASE (HINDI)
# ============================================================================
print("\n[A] Aggressive preprocessing + Whisper Base (Hindi)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Aggressive spectral subtraction
    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 4 * noise_power
    power_reduced = np.maximum(power_reduced, 0.01 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9
    processed_file = os.path.join(tempfile.gettempdir(), "approach_a.wav")
    sf.write(processed_file, y_processed, 16000)

    model = whisper.load_model("base")
    result = model.transcribe(processed_file, language="hi", temperature=0, beam_size=5)
    output = result["text"].strip()
    results['A_aggressive_base_hindi'] = {
        'approach': 'Aggressive preprocessing + Whisper Base (Hindi)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['A_aggressive_base_hindi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# ============================================================================
# APPROACH B: MULTI-STAGE NOISE REDUCTION + WHISPER BASE (HINDI)
# ============================================================================
print("\n[B] Multi-stage noise reduction + Whisper Base (Hindi)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Stage 1: High-pass filter to remove rumble
    sos = signal.butter(4, 100, 'hp', fs=sr, output='sos')
    y_filtered = signal.sosfilt(sos, y)

    # Stage 2: Spectral subtraction (moderate)
    stft = librosa.stft(y_filtered, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.0 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 2.5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.05 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    # Stage 3: Resample
    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9
    processed_file = os.path.join(tempfile.gettempdir(), "approach_b.wav")
    sf.write(processed_file, y_processed, 16000)

    model = whisper.load_model("base")
    result = model.transcribe(processed_file, language="hi", temperature=0.2)
    output = result["text"].strip()
    results['B_multistage_base_hindi'] = {
        'approach': 'Multi-stage noise reduction + Whisper Base (Hindi)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['B_multistage_base_hindi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# ============================================================================
# APPROACH C: WHISPER SMALL (HINDI) - Better accuracy than Base
# ============================================================================
print("\n[C] Preprocessing + Whisper Small (Hindi)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.0 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 2 * noise_power
    power_reduced = np.maximum(power_reduced, 0.1 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9
    processed_file = os.path.join(tempfile.gettempdir(), "approach_c.wav")
    sf.write(processed_file, y_processed, 16000)

    model = whisper.load_model("small")
    result = model.transcribe(processed_file, language="hi", temperature=0)
    output = result["text"].strip()
    results['C_small_hindi'] = {
        'approach': 'Preprocessing + Whisper Small (Hindi)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['C_small_hindi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# ============================================================================
# APPROACH D: GROQ + ENGLISH LANGUAGE (Not Hindi)
# ============================================================================
print("\n[D] Groq with English language hint...")
try:
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    audio_base64 = base64.standard_b64encode(audio_data).decode('utf-8')

    http_client = httpx.Client(verify=False)
    groq_client = Groq(api_key="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", http_client=http_client)

    with open(audio_file, 'rb') as f:
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), f, "audio/mpeg"),
            model="whisper-large-v3-turbo",
            language="en",
            temperature=0.0,
        )

    output = transcript.text.strip()
    results['D_groq_english'] = {
        'approach': 'Groq (English language)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['D_groq_english'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# ============================================================================
# APPROACH E: EXTREME NOISE REDUCTION + WHISPER SMALL (HINDI)
# ============================================================================
print("\n[E] Extreme noise reduction + Whisper Small (Hindi)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Super aggressive spectral subtraction
    stft = librosa.stft(y, n_fft=4096, hop_length=1024)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(2.0 * sr / 1024)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.001 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=1024)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "approach_e.wav")
    sf.write(processed_file, y_processed, 16000)

    model = whisper.load_model("small")
    result = model.transcribe(processed_file, language="hi", temperature=0.1, beam_size=8)
    output = result["text"].strip()
    results['E_extreme_small_hindi'] = {
        'approach': 'Extreme noise reduction + Whisper Small (Hindi)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E_extreme_small_hindi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# ============================================================================
# APPROACH F: WHISPER MEDIUM (HINDI) WITH PREPROCESSING
# ============================================================================
print("\n[F] Whisper Medium (Hindi) with preprocessing...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.0 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)
    power_reduced = power - 1.5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.2 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.9
    processed_file = os.path.join(tempfile.gettempdir(), "approach_f.wav")
    sf.write(processed_file, y_processed, 16000)

    model = whisper.load_model("medium")
    result = model.transcribe(processed_file, language="hi", temperature=0)
    output = result["text"].strip()
    results['F_medium_hindi'] = {
        'approach': 'Whisper Medium (Hindi)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['F_medium_hindi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:80]}")

# Save results
output_file = os.path.join(tempfile.gettempdir(), 'advanced_hindi_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\nResults saved to: {output_file}")

PYEOF
