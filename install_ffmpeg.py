#!/usr/bin/env python3
"""
Download and install ffmpeg for Windows
"""
import os
import zipfile
import urllib.request
import sys

print("=" * 70)
print("Installing ffmpeg for Windows")
print("=" * 70)

# Download URL
url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
download_dir = os.path.expanduser("~\\Downloads")
zip_path = os.path.join(download_dir, "ffmpeg.zip")
extract_path = os.path.join(download_dir, "ffmpeg_extracted")

print(f"\nDownload directory: {download_dir}")
print(f"Zip file: {zip_path}")
print(f"Extract to: {extract_path}")

try:
    print("\n[1] Downloading ffmpeg from GitHub...")
    print(f"    URL: {url}")

    # Download with progress (skip SSL verification)
    import ssl
    import urllib.request

    ssl._create_default_https_context = ssl._create_unverified_context

    def download_with_progress(url, destination):
        def reporthook(blocknum, blocksize, totalsize):
            downloaded = blocknum * blocksize
            if totalsize > 0:
                percent = min(downloaded * 100 / totalsize, 100)
            else:
                percent = 0
            sys.stdout.write(f'\r    Progress: {percent:.0f}%')
            sys.stdout.flush()

        urllib.request.urlretrieve(url, destination, reporthook)
        print("\r    Download complete! ")  # New line after progress

    download_with_progress(url, zip_path)
    print("    Download complete!")

    print("\n[2] Extracting ffmpeg...")
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    print("    Extraction complete!")

    # Find ffmpeg.exe
    print("\n[3] Finding ffmpeg.exe...")
    ffmpeg_exe = None
    for root, dirs, files in os.walk(extract_path):
        if 'ffmpeg.exe' in files:
            ffmpeg_exe = os.path.join(root, 'ffmpeg.exe')
            break

    if ffmpeg_exe:
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        print(f"    Found at: {ffmpeg_dir}")

        print("\n[4] Adding to system PATH...")
        # Get current PATH
        current_path = os.environ.get('PATH', '')

        # Add ffmpeg directory if not already there
        if ffmpeg_dir not in current_path:
            new_path = f"{ffmpeg_dir};{current_path}"
            os.environ['PATH'] = new_path

            # Also set for subprocess calls
            os.putenv('PATH', new_path)
            print(f"    PATH updated")

        print("\n[5] Testing ffmpeg...")
        result = os.system(f'"{ffmpeg_exe}" -version 2>&1 | findstr /I "ffmpeg version" ')

        if result == 0:
            print("    ffmpeg is working!")
            print(f"\n{'='*70}")
            print("SUCCESS: ffmpeg installed and ready to use!")
            print(f"Location: {ffmpeg_exe}")
            print(f"{'='*70}")
        else:
            print("    Warning: Could not verify ffmpeg")
    else:
        print("    ERROR: ffmpeg.exe not found in extracted files")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

finally:
    # Clean up zip
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
            print("\nCleaned up download file")
        except:
            pass
