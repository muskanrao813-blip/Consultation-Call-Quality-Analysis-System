"""
Test ALL approaches on new audio file to find best extraction
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
import whisper

logging.basicConfig(level=logging.WARNING)

url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/06937a25-f363-444c-912a-e31d43ad1804.mp3"

print("Downloading audio...")
response = requests.get(url, verify=False, timeout=30)
audio_file = os.path.join(tempfile.gettempdir(), "test_all_audio.mp3")
with open(audio_file, 'wb') as f:
    f.write(response.content)

y, sr = librosa.load(audio_file, sr=None, mono=True)
duration = len(y) / sr
print(f"Audio: {duration:.1f}s at {sr}Hz\n")

results = {}

# ============================================================================
# GROUP A: BASIC WHISPER APPROACHES
# ============================================================================
print("="*70)
print("GROUP A: BASIC WHISPER APPROACHES")
print("="*70 + "\n")

# A1: Whisper Tiny + English
print("[A1] Whisper Tiny + English...")
try:
    y_norm = y / (np.max(np.abs(y)) + 1e-10) * 0.95
    if sr != 16000:
        y_16k = librosa.resample(y_norm, orig_sr=sr, target_sr=16000)
    else:
        y_16k = y_norm
    temp_file = os.path.join(tempfile.gettempdir(), "a1_tiny_en.wav")
    sf.write(temp_file, y_16k, 16000)

    model = whisper.load_model("tiny")
    result = model.transcribe(temp_file, language="en", temperature=0.0)
    output = result["text"].strip()
    results['A1_whisper_tiny_en'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['A1_whisper_tiny_en'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# A2: Whisper Tiny + Hindi
print("[A2] Whisper Tiny + Hindi...")
try:
    y_norm = y / (np.max(np.abs(y)) + 1e-10) * 0.95
    if sr != 16000:
        y_16k = librosa.resample(y_norm, orig_sr=sr, target_sr=16000)
    else:
        y_16k = y_norm
    temp_file = os.path.join(tempfile.gettempdir(), "a2_tiny_hi.wav")
    sf.write(temp_file, y_16k, 16000)

    model = whisper.load_model("tiny")
    result = model.transcribe(temp_file, language="hi", temperature=0.0)
    output = result["text"].strip()
    results['A2_whisper_tiny_hi'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['A2_whisper_tiny_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# A3: Whisper Base + English
print("[A3] Whisper Base + English...")
try:
    y_norm = y / (np.max(np.abs(y)) + 1e-10) * 0.95
    if sr != 16000:
        y_16k = librosa.resample(y_norm, orig_sr=sr, target_sr=16000)
    else:
        y_16k = y_norm
    temp_file = os.path.join(tempfile.gettempdir(), "a3_base_en.wav")
    sf.write(temp_file, y_16k, 16000)

    model = whisper.load_model("base")
    result = model.transcribe(temp_file, language="en", temperature=0.0)
    output = result["text"].strip()
    results['A3_whisper_base_en'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['A3_whisper_base_en'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# ============================================================================
# GROUP B: GROQ APPROACHES (Single chunk, no preprocessing)
# ============================================================================
print("="*70)
print("GROUP B: GROQ APPROACHES (No preprocessing)")
print("="*70 + "\n")

# B1: Groq Auto-detect
print("[B1] Groq (Auto-detect)...")
try:
    with open(audio_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), f, "audio/mpeg"),
            model="whisper-large-v3-turbo",
            temperature=0.0
        )
    output = transcript.text.strip()
    results['B1_groq_auto'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['B1_groq_auto'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# B2: Groq English
print("[B2] Groq (English)...")
try:
    with open(audio_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), f, "audio/mpeg"),
            model="whisper-large-v3-turbo",
            language="en",
            temperature=0.0
        )
    output = transcript.text.strip()
    results['B2_groq_en'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['B2_groq_en'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# B3: Groq Hindi
print("[B3] Groq (Hindi)...")
try:
    with open(audio_file, 'rb') as f:
        http_client = httpx.Client(verify=False)
        groq_client = Groq(api_key="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", http_client=http_client)
        transcript = groq_client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), f, "audio/mpeg"),
            model="whisper-large-v3-turbo",
            language="hi",
            temperature=0.0
        )
    output = transcript.text.strip()
    results['B3_groq_hi'] = {'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars\n")
except Exception as e:
    results['B3_groq_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# ============================================================================
# GROUP C: CHUNKED APPROACHES WITH GROQ (5-second chunks)
# ============================================================================
print("="*70)
print("GROUP C: CHUNKED GROQ APPROACHES (5-second chunks)")
print("="*70 + "\n")

# C1: 5-sec chunks + Groq Auto-detect
print("[C1] 5-sec chunks + Groq (Auto-detect)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_norm = chunk / (np.max(np.abs(chunk)) + 1e-10) * 0.95
        if sr != 16000:
            chunk_16k = librosa.resample(chunk_norm, orig_sr=sr, target_sr=16000)
        else:
            chunk_16k = chunk_norm

        chunk_file = os.path.join(tempfile.gettempdir(), "c1_chunk.wav")
        sf.write(chunk_file, chunk_16k, 16000)

        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                temperature=0.0
            )
        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)

    output = " ".join(transcripts)
    results['C1_5sec_groq_auto'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['C1_5sec_groq_auto'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# C2: 5-sec chunks + Groq English
print("[C2] 5-sec chunks + Groq (English)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_norm = chunk / (np.max(np.abs(chunk)) + 1e-10) * 0.95
        if sr != 16000:
            chunk_16k = librosa.resample(chunk_norm, orig_sr=sr, target_sr=16000)
        else:
            chunk_16k = chunk_norm

        chunk_file = os.path.join(tempfile.gettempdir(), "c2_chunk.wav")
        sf.write(chunk_file, chunk_16k, 16000)

        with open(chunk_file, 'rb') as f:
            http_client = httpx.Client(verify=False)
            groq_client = Groq(api_key="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", http_client=http_client)
            transcript = groq_client.audio.transcriptions.create(
                file=(os.path.basename(chunk_file), f, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="en",
                temperature=0.0
            )
        text = transcript.text.strip()
        if text and text not in ['.', ',', '']:
            transcripts.append(text)

    output = " ".join(transcripts)
    results['C2_5sec_groq_en'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['C2_5sec_groq_en'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# C3: 5-sec chunks + Groq Hindi
print("[C3] 5-sec chunks + Groq (Hindi)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_norm = chunk / (np.max(np.abs(chunk)) + 1e-10) * 0.95
        if sr != 16000:
            chunk_16k = librosa.resample(chunk_norm, orig_sr=sr, target_sr=16000)
        else:
            chunk_16k = chunk_norm

        chunk_file = os.path.join(tempfile.gettempdir(), "c3_chunk.wav")
        sf.write(chunk_file, chunk_16k, 16000)

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

    output = " ".join(transcripts)
    results['C3_5sec_groq_hi'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['C3_5sec_groq_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# ============================================================================
# GROUP D: ADVANCED PREPROCESSING + CHUNKED
# ============================================================================
print("="*70)
print("GROUP D: ADVANCED PREPROCESSING + CHUNKED GROQ")
print("="*70 + "\n")

# D1: Spectral Gating + 5-sec chunks + Hindi (OUR BEST)
print("[D1] Spectral Gating (100-4000Hz) + 5-sec chunks + Groq (Hindi)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]

        # Spectral gating
        stft = librosa.stft(chunk, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        speech_mask = (freqs >= 100) & (freqs <= 4000)
        gate = np.where(speech_mask[:, np.newaxis], 1.5, 0.3)
        mag_gated = mag * gate

        # Spectral subtraction
        power_gated = mag_gated ** 2
        noise_frames = int(1.0 * sr / 512)
        if noise_frames > power_gated.shape[1]:
            noise_frames = max(1, power_gated.shape[1] // 2)
        noise_power = np.mean(power_gated[:, :noise_frames], axis=1, keepdims=True)
        power_reduced = power_gated - 1.5 * noise_power
        power_reduced = np.maximum(power_reduced, 0.2 * power_gated)
        mag_final = np.sqrt(power_reduced)

        stft_final = mag_final * np.exp(1j * phase)
        chunk_proc_time = librosa.istft(stft_final, hop_length=512)

        chunk_proc = librosa.resample(chunk_proc_time, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_proc_time
        max_val = np.max(np.abs(chunk_proc))
        if max_val > 0:
            chunk_proc = chunk_proc / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), "d1_chunk.wav")
        sf.write(chunk_file, chunk_proc, 16000)

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

    output = " ".join(transcripts)
    results['D1_spectral_gating_hi'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['D1_spectral_gating_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# D2: Wiener + 5-sec chunks + Hindi
print("[D2] Wiener Filtering + 5-sec chunks + Groq (Hindi)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]

        # Wiener filtering
        stft = librosa.stft(chunk, n_fft=2048, hop_length=512)
        mag = np.abs(stft)
        phase = np.angle(stft)
        power = mag ** 2

        noise_frames = int(1.0 * sr / 512)
        if noise_frames > power.shape[1]:
            noise_frames = max(1, power.shape[1] // 2)
        noise_power = np.mean(power[:, :noise_frames], axis=1, keepdims=True)

        signal_power = power - noise_power
        signal_power = np.maximum(signal_power, 0.01 * noise_power)
        wiener_gain = signal_power / (signal_power + noise_power)

        mag_filtered = mag * wiener_gain
        stft_filtered = mag_filtered * np.exp(1j * phase)
        chunk_proc_time = librosa.istft(stft_filtered, hop_length=512)

        chunk_proc = librosa.resample(chunk_proc_time, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_proc_time
        max_val = np.max(np.abs(chunk_proc))
        if max_val > 0:
            chunk_proc = chunk_proc / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), "d2_chunk.wav")
        sf.write(chunk_file, chunk_proc, 16000)

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

    output = " ".join(transcripts)
    results['D2_wiener_hi'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['D2_wiener_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# D3: Speech EQ + 5-sec chunks + Hindi
print("[D3] Speech EQ (300-3400Hz) + 5-sec chunks + Groq (Hindi)...")
try:
    chunk_duration = 5
    chunk_samples = int(chunk_duration * sr)
    transcripts = []

    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]

        # Speech EQ
        sos = signal.butter(4, [300, 3400], 'bp', fs=sr, output='sos')
        chunk_eq = signal.sosfilt(sos, chunk)

        # Spectral subtraction
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
        chunk_proc_time = librosa.istft(stft_reduced, hop_length=512)

        chunk_proc = librosa.resample(chunk_proc_time, orig_sr=sr, target_sr=16000) if sr != 16000 else chunk_proc_time
        max_val = np.max(np.abs(chunk_proc))
        if max_val > 0:
            chunk_proc = chunk_proc / max_val * 0.95

        chunk_file = os.path.join(tempfile.gettempdir(), "d3_chunk.wav")
        sf.write(chunk_file, chunk_proc, 16000)

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

    output = " ".join(transcripts)
    results['D3_speech_eq_hi'] = {'chunks': len(transcripts), 'output': output, 'length': len(output)}
    print(f"  Success: {len(output)} chars from {len(transcripts)} chunks\n")
except Exception as e:
    results['D3_speech_eq_hi'] = {'error': str(e)[:80]}
    print(f"  Failed: {str(e)[:60]}\n")

# Save results
output_file = os.path.join(tempfile.gettempdir(), 'all_approaches_new_file.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "="*70)
print("SUMMARY - ALL APPROACHES")
print("="*70 + "\n")

# Rank by length
ranked = sorted(
    [(k, v.get('length', 0)) for k, v in results.items() if 'error' not in v],
    key=lambda x: x[1],
    reverse=True
)

print("Ranked by transcript length:\n")
for i, (key, length) in enumerate(ranked, 1):
    approach_name = results[key].get('output', '')[:50].replace('\n', ' ')
    print(f"{i}. {key:<30} | {length:>5} chars | {approach_name[:40]}...")

print(f"\nResults saved to: {output_file}")
