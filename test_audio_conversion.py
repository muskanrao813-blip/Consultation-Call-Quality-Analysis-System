#!/usr/bin/env python3
import os
import requests
import tempfile
import subprocess

# Add ffmpeg to PATH
ffmpeg_bin = r"C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin"
os.environ['PATH'] = ffmpeg_bin + ";" + os.environ.get('PATH', '')

print("="*80)
print("Testing Audio Download + Conversion")
print("="*80)

url = "https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3"

try:
    # Step 1: Download
    print("\n1. Downloading audio...")
    response = requests.get(url, timeout=30, verify=False, stream=True)
    response.raise_for_status()

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "test_audio.mp3")

    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    file_size = os.path.getsize(temp_path)
    print(f"   Downloaded: {temp_path}")
    print(f"   Size: {file_size} bytes")

    if file_size == 0:
        print("   ERROR: Downloaded file is empty!")
        exit(1)

    # Step 2: Convert with ffmpeg
    print("\n2. Converting to WAV with ffmpeg...")
    output_path = os.path.join(temp_dir, "test_audio.wav")

    cmd = [
        "ffmpeg",
        "-i", temp_path,
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path
    ]

    print(f"   Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    print(f"   Return code: {result.returncode}")
    if result.stderr:
        print(f"   ffmpeg output: {result.stderr[:500]}")

    if os.path.exists(output_path):
        output_size = os.path.getsize(output_path)
        print(f"   Output size: {output_size} bytes")

        if output_size > 0:
            print("\n✓ SUCCESS: Audio converted successfully!")
        else:
            print("\n✗ FAILED: Converted file is empty")
    else:
        print("\n✗ FAILED: Output file not created")

    # Cleanup
    try:
        os.remove(temp_path)
        if os.path.exists(output_path):
            os.remove(output_path)
    except:
        pass

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
