#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose transcription accuracy at each stage of the pipeline"""

import sys, os, io, logging, tempfile
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

import numpy as np
import librosa, soundfile as sf
import httpx
from groq import Groq
import ssl

GROQ_API_KEY = "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"

TEST_URL = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/3f2d205b-8e28-4a2e-b4be-0e76442b3ac6.mp3"

def download(url):
    path = os.path.join(tempfile.gettempdir(), "diag_audio.mp3")
    with httpx.stream("GET", url, verify=False, timeout=60) as r:
        with open(path, 'wb') as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return path

def groq_transcribe(wav_path, language, prompt=None):
    http_client = httpx.Client(verify=False)
    client = Groq(api_key=GROQ_API_KEY, http_client=http_client)
    kwargs = dict(model="whisper-large-v3-turbo", language=language, temperature=0.0)
    if prompt:
        kwargs["prompt"] = prompt
    with open(wav_path, 'rb') as f:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(wav_path), f, "audio/wav"), **kwargs)
    return result.text.strip()

def save_wav(y, sr, path):
    sf.write(path, y, sr)

def main():
    print("=" * 70)
    print("TRANSCRIPTION DIAGNOSIS")
    print("=" * 70)

    # Download
    print("\n[1] Downloading audio...")
    audio_path = download(TEST_URL)
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    print(f"    Duration: {len(y)/sr:.1f}s  |  Sample rate: {sr}Hz  |  RMS: {np.sqrt(np.mean(y**2)):.4f}")

    tmp = tempfile.gettempdir()

    # === APPROACH A: Raw audio at 16kHz (baseline) ===
    print("\n[A] RAW AUDIO → Groq (baseline, no preprocessing):")
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000) if sr != 16000 else y
    y16 = y16 / (np.max(np.abs(y16)) + 1e-10) * 0.95
    wav_a = os.path.join(tmp, "diag_a.wav")
    save_wav(y16, 16000, wav_a)
    t_a = groq_transcribe(wav_a, "hi")
    print(f"    Result: {t_a}")

    # === APPROACH B: Same but with initial prompt (vocabulary seeding) ===
    print("\n[B] RAW AUDIO → Groq + INITIAL PROMPT (vocabulary seeding):")
    bajaj_prompt = (
        "बजाज फिनसर्व हेल्थ, health benefits plan, appointment, consultation, "
        "doctor, dietician, नमस्ते, आपका, कॉल, benefits, coverage, insurance"
    )
    t_b = groq_transcribe(wav_a, "hi", prompt=bajaj_prompt)
    print(f"    Result: {t_b}")

    # === APPROACH C: Full audio with stronger normalization ===
    print("\n[C] NORMALIZED AUDIO → Groq:")
    from scipy import signal as scipy_signal
    # aggressive normalize
    y_norm = y / (np.max(np.abs(y)) + 1e-10) * 0.95
    y16_norm = librosa.resample(y_norm, orig_sr=sr, target_sr=16000)
    wav_c = os.path.join(tmp, "diag_c.wav")
    save_wav(y16_norm, 16000, wav_c)
    t_c = groq_transcribe(wav_c, "hi", prompt=bajaj_prompt)
    print(f"    Result: {t_c}")

    # === APPROACH D: Spectral subtraction + prompt ===
    print("\n[D] SPECTRAL SUBTRACTION → Groq + Prompt:")
    D = librosa.stft(y_norm)
    mag, phase = np.abs(D), np.angle(D)
    noise_frames = min(10, mag.shape[1] // 4)
    noise = np.mean(mag[:, :noise_frames], axis=1, keepdims=True)
    mag_clean = np.maximum(mag - 2.0 * noise, 0.05 * mag)
    y_clean = librosa.istft(mag_clean * np.exp(1j * phase))
    y16_clean = librosa.resample(y_clean, orig_sr=sr, target_sr=16000)
    y16_clean = y16_clean / (np.max(np.abs(y16_clean)) + 1e-10) * 0.95
    wav_d = os.path.join(tmp, "diag_d.wav")
    save_wav(y16_clean, 16000, wav_d)
    t_d = groq_transcribe(wav_d, "hi", prompt=bajaj_prompt)
    print(f"    Result: {t_d}")

    # === APPROACH E: Also try English transcription ===
    print("\n[E] RAW AUDIO → Groq ENGLISH (compare):")
    eng_prompt = "Bajaj Finserv Health, health benefits plan, appointment, consultation, doctor, dietician, hello, call, benefits, coverage"
    t_e = groq_transcribe(wav_a, "en", prompt=eng_prompt)
    print(f"    Result: {t_e}")

    # === APPROACH F: Groq on full audio at once (no chunking) ===
    print("\n[F] FULL AUDIO AT ONCE (no chunking) → Groq + Prompt:")
    t_f = groq_transcribe(wav_d, "hi", prompt=bajaj_prompt)
    print(f"    Result: {t_f}")

    # Compare lengths
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    transcripts = {"A: Raw baseline": t_a, "B: Raw + Prompt": t_b, "C: Normalized + Prompt": t_c,
                   "D: Spectral + Prompt": t_d, "E: English + Prompt": t_e, "F: Full audio + Prompt": t_f}
    for name, t in transcripts.items():
        print(f"\n{name}  ({len(t)} chars):")
        print(f"  {t}")

    # Identify best
    print("\n" + "=" * 70)
    print("BEST TRANSCRIPT (longest, most coherent):")
    best = max(transcripts.items(), key=lambda x: len(x[1]))
    print(f"  Winner: {best[0]}")
    print(f"  Text: {best[1]}")

if __name__ == "__main__":
    main()
