"""
Enhanced Groq transcription - multiple preprocessing strategies
Goal: Get more complete output from Groq while preserving the accurate context it captures
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
from groq import Groq
import httpx

logging.basicConfig(level=logging.WARNING)

url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

print("Downloading audio...")
response = requests.get(url, verify=False, timeout=30)
audio_file = os.path.join(tempfile.gettempdir(), "groq_enhanced.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)

results = {}

# ============================================================================
# ENHANCED GROQ TEST 1: Wiener Filtering (Better than spectral subtraction)
# ============================================================================
print("\n[GROQ-E1] Wiener Filtering + Groq (Auto-detect)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Wiener filtering using Wiener-Khinchin theorem approach
    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    # Estimate noise power from first 1.5 seconds (assumed silence)
    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    # Wiener filter: emphasis speech, suppress noise
    # H(f) = (speech_power) / (speech_power + noise_power)
    signal_power = power - noise_power
    signal_power = np.maximum(signal_power, 0.01 * noise_power)
    wiener_gain = signal_power / (signal_power + noise_power)

    mag_filtered = mag * wiener_gain
    stft_filtered = mag_filtered * np.exp(1j * phase)
    y_filtered = librosa.istft(stft_filtered, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_filtered, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_filtered

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "groq_e1_wiener.wav")
    sf.write(processed_file, y_processed, 16000)

    with open(processed_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(processed_file), f, "audio/wav"),
            model="whisper-large-v3-turbo",
            temperature=0.0
        )

    output = transcript.text.strip()
    results['E1_wiener_groq'] = {
        'approach': 'Wiener Filtering + Groq (Auto-detect)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E1_wiener_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# ENHANCED GROQ TEST 2: Mild Spectral Subtraction (preserve speech)
# ============================================================================
print("\n[GROQ-E2] Mild Spectral Subtraction + Groq...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    # Mild subtraction (only 1.5x, not 3x or 4x)
    power_reduced = power - 1.5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.3 * power)  # Floor at 30% of original
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "groq_e2_mild.wav")
    sf.write(processed_file, y_processed, 16000)

    with open(processed_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(processed_file), f, "audio/wav"),
            model="whisper-large-v3-turbo",
            temperature=0.0
        )

    output = transcript.text.strip()
    results['E2_mild_spectral_groq'] = {
        'approach': 'Mild Spectral Subtraction + Groq',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E2_mild_spectral_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# ENHANCED GROQ TEST 3: High-Pass Filter + Wiener + Groq
# ============================================================================
print("\n[GROQ-E3] HP Filter + Wiener + Groq...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Stage 1: High-pass to remove rumble/background
    sos = signal.butter(4, 150, 'hp', fs=sr, output='sos')
    y_filtered = signal.sosfilt(sos, y)

    # Stage 2: Wiener filtering
    stft = librosa.stft(y_filtered, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    signal_power = power - noise_power
    signal_power = np.maximum(signal_power, 0.02 * noise_power)
    wiener_gain = signal_power / (signal_power + noise_power)

    mag_filtered = mag * wiener_gain
    stft_filtered = mag_filtered * np.exp(1j * phase)
    y_wiener = librosa.istft(stft_filtered, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_wiener, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_wiener

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "groq_e3_hp_wiener.wav")
    sf.write(processed_file, y_processed, 16000)

    with open(processed_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(processed_file), f, "audio/wav"),
            model="whisper-large-v3-turbo",
            temperature=0.0
        )

    output = transcript.text.strip()
    results['E3_hp_wiener_groq'] = {
        'approach': 'HP Filter + Wiener + Groq',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E3_hp_wiener_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# ENHANCED GROQ TEST 4: Groq with temperature tuning (temperature=0.1)
# ============================================================================
print("\n[GROQ-E4] Mild Spectral + Groq (temperature=0.1)...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    power_reduced = power - 1.5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.3 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "groq_e4_temp.wav")
    sf.write(processed_file, y_processed, 16000)

    with open(processed_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(processed_file), f, "audio/wav"),
            model="whisper-large-v3-turbo",
            temperature=0.1
        )

    output = transcript.text.strip()
    results['E4_mild_temp01_groq'] = {
        'approach': 'Mild Spectral + Groq (temperature=0.1)',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E4_mild_temp01_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# ENHANCED GROQ TEST 5: Speech Equalization + Groq
# ============================================================================
print("\n[GROQ-E5] Speech EQ (300-3400Hz) + Groq...")
try:
    y, sr = librosa.load(audio_file, sr=None, mono=True)

    # Design bandpass filter for speech range (300-3400 Hz)
    sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
    y_eq = signal.sosfilt(sos, y)

    # Apply mild spectral subtraction to the EQ'd signal
    stft = librosa.stft(y_eq, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)
    power = mag ** 2

    noise_frames = int(1.5 * sr / 512)
    noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

    power_reduced = power - 1.2 * noise_power
    power_reduced = np.maximum(power_reduced, 0.2 * power)
    mag_reduced = np.sqrt(power_reduced)

    stft_reduced = mag_reduced * np.exp(1j * phase)
    y_reduced = librosa.istft(stft_reduced, hop_length=512)

    if sr != 16000:
        y_processed = librosa.resample(y_reduced, orig_sr=sr, target_sr=16000)
    else:
        y_processed = y_reduced

    y_processed = y_processed / np.max(np.abs(y_processed)) * 0.95
    processed_file = os.path.join(tempfile.gettempdir(), "groq_e5_eq.wav")
    sf.write(processed_file, y_processed, 16000)

    with open(processed_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(processed_file), f, "audio/wav"),
            model="whisper-large-v3-turbo",
            temperature=0.0
        )

    output = transcript.text.strip()
    results['E5_speech_eq_groq'] = {
        'approach': 'Speech EQ (300-3400Hz) + Groq',
        'output': output,
        'length': len(output)
    }
    print(f"  Success: {len(output)} chars")
except Exception as e:
    results['E5_speech_eq_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# Save results
output_file = os.path.join(tempfile.gettempdir(), 'groq_enhanced_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ Enhanced Groq test complete! Results saved.")
print(f"\nQuick Summary:")
for key, val in results.items():
    if 'error' not in val:
        print(f"  {val['approach']:<40} | {val['length']:>3} chars")
