"""
Chunked transcription approach - segment audio and transcribe each part
Goal: Capture the ENTIRE conversation, not just fragments
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
audio_file = os.path.join(tempfile.gettempdir(), "chunked_audio.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)

# Load audio once
y, sr = librosa.load(audio_file, sr=None, mono=True)
duration = len(y) / sr
print(f"Audio loaded: {duration:.1f} seconds")

results = {}

# ============================================================================
# APPROACH 1: 10-second chunks with Speech EQ + Groq
# ============================================================================
print("\n[CHUNK-1] 10-second chunks with Speech EQ + Groq...")
try:
    chunk_duration = 10  # seconds
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_num = i // chunk_samples

        # Speech EQ: Bandpass filter for speech range (300-3400 Hz)
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Mild spectral subtraction
        stft = librosa.stft(chunk_eq, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(1.0 * sr / 512)
        noise_power = np.mean(power[:, :min(noise_frames, power.shape[1])], axis=1, keepdims=True)

        power_reduced = power - 1.2 * noise_power
        power_reduced = np.maximum(power_reduced, 0.2 * power)
        mag_reduced = np.sqrt(power_reduced)

        stft_reduced = mag_reduced * np.exp(1j * phase)
        chunk_reduced = librosa.istft(stft_reduced, hop_length=512)

        # Resample and normalize
        chunk_processed = librosa.resample(chunk_reduced, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_reduced
        chunk_processed = chunk_processed / (np.max(np.abs(chunk_processed)) + 1e-10) * 0.95

        # Save chunk
        chunk_file = os.path.join(tempfile.gettempdir(), f"chunk_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe chunk
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                temperature=0.0
            )

        text = transcript.text.strip()
        if text:
            transcripts.append(f"[{chunk_num}] {text}")
            print(f"  Chunk {chunk_num}: {len(text)} chars")

    full_text = " ".join(transcripts)
    results['chunk_10s_eq_groq'] = {
        'approach': '10-second chunks + Speech EQ + Groq',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  Total: {len(full_text)} chars from {len(transcripts)} chunks")
except Exception as e:
    results['chunk_10s_eq_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# APPROACH 2: 5-second chunks with Wiener + Groq (finer granularity)
# ============================================================================
print("\n[CHUNK-2] 5-second chunks with Wiener + Groq...")
try:
    chunk_duration = 5
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

        noise_frames = int(1.0 * sr / 512)
        noise_power = np.mean(power[:, :min(noise_frames, power.shape[1])], axis=1, keepdims=True)

        signal_power = power - noise_power
        signal_power = np.maximum(signal_power, 0.01 * noise_power)
        wiener_gain = signal_power / (signal_power + noise_power)

        mag_filtered = mag * wiener_gain
        stft_filtered = mag_filtered * np.exp(1j * phase)
        chunk_wiener = librosa.istft(stft_filtered, hop_length=512)

        # Resample and normalize
        chunk_processed = librosa.resample(chunk_wiener, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_wiener
        chunk_processed = chunk_processed / (np.max(np.abs(chunk_processed)) + 1e-10) * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"chunk_5s_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                temperature=0.0
            )

        text = transcript.text.strip()
        if text:
            transcripts.append(f"[{chunk_num}] {text}")
            print(f"  Chunk {chunk_num}: {len(text)} chars")

    full_text = " ".join(transcripts)
    results['chunk_5s_wiener_groq'] = {
        'approach': '5-second chunks + Wiener + Groq',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  Total: {len(full_text)} chars from {len(transcripts)} chunks")
except Exception as e:
    results['chunk_5s_wiener_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# APPROACH 3: 20-second chunks (larger context) with Speech EQ
# ============================================================================
print("\n[CHUNK-3] 20-second chunks with Speech EQ + Groq...")
try:
    chunk_duration = 20
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_num = i // chunk_samples

        # Speech EQ
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Mild spectral subtraction
        stft = librosa.stft(chunk_eq, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(1.5 * sr / 512)
        noise_power = np.mean(power[:, :min(noise_frames, power.shape[1])], axis=1, keepdims=True)

        power_reduced = power - 1.5 * noise_power
        power_reduced = np.maximum(power_reduced, 0.2 * power)
        mag_reduced = np.sqrt(power_reduced)

        stft_reduced = mag_reduced * np.exp(1j * phase)
        chunk_reduced = librosa.istft(stft_reduced, hop_length=512)

        chunk_processed = librosa.resample(chunk_reduced, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_reduced
        chunk_processed = chunk_processed / (np.max(np.abs(chunk_processed)) + 1e-10) * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"chunk_20s_{chunk_num}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                temperature=0.0
            )

        text = transcript.text.strip()
        if text:
            transcripts.append(f"[{chunk_num}] {text}")
            print(f"  Chunk {chunk_num}: {len(text)} chars")

    full_text = " ".join(transcripts)
    results['chunk_20s_eq_groq'] = {
        'approach': '20-second chunks + Speech EQ + Groq',
        'chunks': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  Total: {len(full_text)} chars from {len(transcripts)} chunks")
except Exception as e:
    results['chunk_20s_eq_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# ============================================================================
# APPROACH 4: Dynamic VAD-based chunking (transcribe only non-silent parts)
# ============================================================================
print("\n[CHUNK-4] VAD-based dynamic chunking + Groq...")
try:
    # Simple energy-based VAD
    frame_length = 2048
    hop_length = 512
    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
    frame_energy = np.sqrt(np.sum(frames ** 2, axis=0))
    mean_energy = np.mean(frame_energy)

    # Threshold: frames above 0.3 * mean are speech
    speech_threshold = 0.3 * mean_energy
    speech_frames = frame_energy > speech_threshold

    # Find contiguous speech regions
    speech_transitions = np.diff(speech_frames.astype(int))
    speech_starts = np.where(speech_transitions == 1)[0]
    speech_ends = np.where(speech_transitions == -1)[0]

    transcripts = []
    for idx, (start_frame, end_frame) in enumerate(zip(speech_starts, speech_ends)):
        start_sample = start_frame * hop_length
        end_sample = end_frame * hop_length

        if end_sample - start_sample < sr * 0.5:  # Skip tiny fragments
            continue

        chunk = y[start_sample:end_sample]

        # Speech EQ
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Spectral subtraction
        stft = librosa.stft(chunk_eq, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames_count = int(0.5 * sr / 512)
        noise_power = np.mean(power[:, :min(noise_frames_count, power.shape[1])], axis=1, keepdims=True)

        power_reduced = power - 1.5 * noise_power
        power_reduced = np.maximum(power_reduced, 0.2 * power)
        mag_reduced = np.sqrt(power_reduced)

        stft_reduced = mag_reduced * np.exp(1j * phase)
        chunk_reduced = librosa.istft(stft_reduced, hop_length=512)

        chunk_processed = librosa.resample(chunk_reduced, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_reduced
        chunk_processed = chunk_processed / (np.max(np.abs(chunk_processed)) + 1e-10) * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), f"chunk_vad_{idx}.wav")
        sf.write(chunk_file, chunk_processed, 16000)

        # Transcribe
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                temperature=0.0
            )

        text = transcript.text.strip()
        if text:
            transcripts.append(f"[{idx}] {text}")
            print(f"  Segment {idx}: {len(text)} chars")

    full_text = " ".join(transcripts)
    results['vad_groq'] = {
        'approach': 'VAD-based dynamic chunks + Groq',
        'segments': len(transcripts),
        'full_transcript': full_text,
        'length': len(full_text)
    }
    print(f"  Total: {len(full_text)} chars from {len(transcripts)} segments")
except Exception as e:
    results['vad_groq'] = {'error': str(e)[:100]}
    print(f"  Failed: {str(e)[:60]}")

# Save results
output_file = os.path.join(tempfile.gettempdir(), 'chunked_transcription_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n--- Chunked Transcription Complete ---")
print(f"Results saved to: {output_file}\n")

for key, val in results.items():
    if 'error' not in val:
        print(f"{val['approach']:<50} | Total: {val['length']:>4} chars")
