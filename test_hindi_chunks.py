"""
Hindi-specific chunked transcription
Force Groq to transcribe as Hindi throughout
"""

import requests
import tempfile
import os
import json
import logging
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
audio_file = os.path.join(tempfile.gettempdir(), "hindi_chunks.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)

# Load audio
y, sr = librosa.load(audio_file, sr=None, mono=True)
duration = len(y) / sr
print(f"Audio loaded: {duration:.1f} seconds\n")

results = {}

# ============================================================================
# APPROACH 1: 5-second chunks with Speech EQ + Groq (HINDI language)
# ============================================================================
print("[HINDI-1] 5-second chunks + Speech EQ + Groq (HINDI)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_num = i // chunk_samples

        # Speech EQ: 300-3400 Hz (Hindi speech intelligibility range)
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Mild spectral subtraction
        stft = librosa.stft(chunk_eq, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(1.0 * sr / 512)
        if noise_frames > power.shape[1]:
            noise_frames = max(1, power.shape[1] // 2)
        noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

        power_reduced = power - 1.2 * noise_power
        power_reduced = np.maximum(power_reduced, 0.2 * power)
        mag_reduced = np.sqrt(power_reduced)

        stft_reduced = mag_reduced * np.exp(1j * phase)
        chunk_reduced = librosa.istft(stft_reduced, hop_length=512)

        chunk_processed = librosa.resample(chunk_reduced, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_reduced
        max_val = np.max(np.abs(chunk_processed))
        if max_val > 0:
            chunk_processed = chunk_processed / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"hindi_chunk1_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe with HINDI language hint
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="hi",  # FORCE HINDI
                temperature=0.0
            )

        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)
            try:
                print(f"  Chunk {chunk_num}: {len(text)} chars")
            except:
                print(f"  Chunk {chunk_num}: {len(text)} chars (non-ASCII)")

    full_text = " ".join(transcripts)
    results['hindi_5s_eq'] = {
        'approach': '5-second chunks + Speech EQ + Groq (HINDI)',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  TOTAL: {len(full_text)} chars\n")
except Exception as e:
    results['hindi_5s_eq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}\n")

# ============================================================================
# APPROACH 2: 10-second chunks with Wiener + Groq (HINDI)
# ============================================================================
print("[HINDI-2] 10-second chunks + Wiener + Groq (HINDI)...")
try:
    chunk_duration = 10
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_num = i // chunk_samples

        # Wiener filtering
        stft = librosa.stft(chunk, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(1.5 * sr / 512)
        if noise_frames > power.shape[1]:
            noise_frames = max(1, power.shape[1] // 2)
        noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

        signal_power = power - noise_power
        signal_power = np.maximum(signal_power, 0.01 * noise_power)
        wiener_gain = signal_power / (signal_power + noise_power)

        mag_filtered = mag * wiener_gain
        stft_filtered = mag_filtered * np.exp(1j * phase)
        chunk_wiener = librosa.istft(stft_filtered, hop_length=512)

        chunk_processed = librosa.resample(chunk_wiener, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_wiener
        max_val = np.max(np.abs(chunk_processed))
        if max_val > 0:
            chunk_processed = chunk_processed / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"hindi_chunk2_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe with HINDI
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="hi",  # FORCE HINDI
                temperature=0.0
            )

        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)
            try:
                print(f"  Chunk {chunk_num}: {len(text)} chars")
            except:
                print(f"  Chunk {chunk_num}: {len(text)} chars (non-ASCII)")

    full_text = " ".join(transcripts)
    results['hindi_10s_wiener'] = {
        'approach': '10-second chunks + Wiener + Groq (HINDI)',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  TOTAL: {len(full_text)} chars\n")
except Exception as e:
    results['hindi_10s_wiener'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}\n")

# ============================================================================
# APPROACH 3: 3-second overlap sliding window (capture transitions better)
# ============================================================================
print("[HINDI-3] 3-second chunks with overlap + Groq (HINDI)...")
try:
    chunk_duration = 3
    overlap = 1.5  # 50% overlap
    chunk_samples = int(chunk_duration * sr)
    overlap_samples = int(overlap * sr)
    hop_samples = chunk_samples - overlap_samples

    transcripts = []
    chunk_num = 0

    for i in range(0, len(y) - chunk_samples, hop_samples):
        chunk = y[i:i + chunk_samples]

        # Speech EQ
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Spectral subtraction
        stft = librosa.stft(chunk_eq, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(0.8 * sr / 512)
        if noise_frames > power.shape[1]:
            noise_frames = max(1, power.shape[1] // 3)
        noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

        power_reduced = power - 1.3 * noise_power
        power_reduced = np.maximum(power_reduced, 0.15 * power)
        mag_reduced = np.sqrt(power_reduced)

        stft_reduced = mag_reduced * np.exp(1j * phase)
        chunk_reduced = librosa.istft(stft_reduced, hop_length=512)

        chunk_processed = librosa.resample(chunk_reduced, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_reduced
        max_val = np.max(np.abs(chunk_processed))
        if max_val > 0:
            chunk_processed = chunk_processed / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"hindi_chunk3_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe with HINDI
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="hi",  # FORCE HINDI
                temperature=0.0
            )

        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)
            print(f"  Chunk {chunk_num}: {len(text)} chars | {text[:50]}")

        chunk_num += 1

    full_text = " ".join(transcripts)
    results['hindi_3s_overlap'] = {
        'approach': '3-second overlapping chunks + Groq (HINDI)',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  TOTAL: {len(full_text)} chars\n")
except Exception as e:
    results['hindi_3s_overlap'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}\n")

# Save results
output_file = os.path.join(tempfile.gettempdir(), 'hindi_chunked_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "="*70)
print("HINDI CHUNKED TRANSCRIPTION SUMMARY")
print("="*70)
for key, val in results.items():
    if 'error' not in val:
        try:
            print(f"{val['approach']:<50} | {val['length']:>4} chars")
        except:
            print(f"Approach | {val['length']:>4} chars")
