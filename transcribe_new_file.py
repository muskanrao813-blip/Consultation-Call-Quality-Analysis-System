"""
Transcribe new audio file using best approach: Spectral Gating + Groq (HINDI)
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

# New audio URL
url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/06937a25-f363-444c-912a-e31d43ad1804.mp3"

print("="*70)
print("TRANSCRIBING NEW AUDIO FILE")
print("="*70)
print(f"URL: {url}\n")

print("Downloading audio...")
try:
    response = requests.get(url, verify=False, timeout=30)
    audio_file = os.path.join(tempfile.gettempdir(), "new_audio.mp3")
    with open(audio_file, 'wb') as f:
        f.write(response.content)
    print("Audio downloaded successfully\n")
except Exception as e:
    print(f"Failed to download: {e}")
    exit(1)

# Load audio
print("Loading audio...")
y, sr = librosa.load(audio_file, sr=None, mono=True)
duration = len(y) / sr
print(f"Duration: {duration:.1f} seconds")
print(f"Sample rate: {sr} Hz")
print(f"Channels: Mono\n")

# ============================================================================
# BEST APPROACH: Spectral Gating (100-4000Hz) + Groq (HINDI)
# ============================================================================
print("="*70)
print("APPLYING SPECTRAL GATING + GROQ (HINDI) TRANSCRIPTION")
print("="*70 + "\n")

chunk_duration = 5
chunk_samples = int(chunk_duration * sr)
transcripts = []
chunk_details = []

print(f"Processing in {chunk_duration}-second chunks...\n")

chunk_num = 0
for i in range(0, len(y), chunk_samples):
    chunk = y[i:i + chunk_samples]
    chunk_num_current = i // chunk_samples

    # STFT
    stft = librosa.stft(chunk, n_fft=2048, hop_length=512)
    mag = np.abs(stft)
    phase = np.angle(stft)

    # Spectral gating: only pass frequencies with high energy in speech range (100-4000Hz)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    speech_mask = (freqs >= 100) & (freqs <= 4000)

    # Compute power
    power = mag ** 2
    mean_power = np.mean(power, axis=1, keepdims=True)

    # Gate: amplify speech frequencies, suppress others
    gate = np.where(speech_mask[:, np.newaxis], 1.5, 0.3)
    mag_gated = mag * gate

    # Spectral subtraction on gated signal
    noise_frames = int(1.0 * sr / 512)
    if noise_frames > power.shape[1]:
        noise_frames = max(1, power.shape[1] // 2)
    noise_power = np.mean((mag_gated ** 2)[:, :noise_frames], axis=1, keepdims=True)

    power_gated = mag_gated ** 2
    power_reduced = power_gated - 1.5 * noise_power
    power_reduced = np.maximum(power_reduced, 0.2 * power_gated)
    mag_final = np.sqrt(power_reduced)

    stft_final = mag_final * np.exp(1j * phase)
    chunk_processed_time = librosa.istft(stft_final, hop_length=512)

    # Resample and normalize
    chunk_processed = librosa.resample(chunk_processed_time, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_processed_time
    max_val = np.max(np.abs(chunk_processed))
    if max_val > 0:
        chunk_processed = chunk_processed / max_val * 0.95

    chunk_file = os.path.join(tempfile.gettempdir(), f"best_chunk_{chunk_num_current}.wav")
    sf.write(chunk_file, chunk_processed, 16000)

    # Transcribe with Groq
    try:
        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="hi",
                temperature=0.0
            )

        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)
            chunk_details.append({
                'chunk': chunk_num_current,
                'start_time': f"{i/sr:.1f}s",
                'end_time': f"{min(i + chunk_samples, len(y))/sr:.1f}s",
                'length': len(text)
            })
            try:
                print(f"  Chunk {chunk_num_current}: {len(text)} chars")
            except:
                print(f"  Chunk {chunk_num_current}: {len(text)} chars (non-ASCII)")
        else:
            print(f"  Chunk {chunk_num_current}: (silence/empty)")

    except Exception as e:
        print(f"  Chunk {chunk_num_current}: Error - {str(e)[:50]}")

# Combine results
full_transcript = " ".join(transcripts)

print("\n" + "="*70)
print("TRANSCRIPTION COMPLETE")
print("="*70 + "\n")

print(f"Total chunks processed: {len(chunk_details)}")
print(f"Chunks with speech: {len(transcripts)}")
print(f"Total characters: {len(full_transcript)}")
print(f"Average per chunk: {len(full_transcript) / max(1, len(transcripts)):.0f} chars\n")

print("="*70)
print("FULL TRANSCRIPT")
print("="*70)
output_transcript = f"\n{full_transcript}\n"

# Save to file
output_file = os.path.join(tempfile.gettempdir(), 'new_audio_transcript.txt')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(output_transcript)

# Save detailed JSON
json_output = {
    'url': url,
    'duration_seconds': duration,
    'sample_rate': sr,
    'approach': 'Spectral Gating (100-4000Hz) + Groq (HINDI)',
    'chunks_processed': len(chunk_details),
    'total_characters': len(full_transcript),
    'full_transcript': full_transcript,
    'chunk_details': chunk_details,
    'average_chars_per_chunk': len(full_transcript) / max(1, len(transcripts))
}

json_file = os.path.join(tempfile.gettempdir(), 'new_audio_transcript.json')
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"\nResults saved:")
print(f"  Text: {output_file}")
print(f"  JSON: {json_file}")
