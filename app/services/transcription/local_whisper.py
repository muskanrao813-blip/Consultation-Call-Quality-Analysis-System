"""Local Whisper implementation for speech-to-text (no API key needed)."""

import logging
import os
from typing import List, Dict
from app.services.transcription.base import TranscriptionProvider, Segment
import ssl

logger = logging.getLogger(__name__)

# Disable SSL verification for model download
ssl._create_default_https_context = ssl._create_unverified_context

# Lazy import to defer until needed
_whisper_model = None

def _get_whisper_model():
    """Lazy load Whisper model."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    try:
        import whisper
        logger.info("Loading Whisper model (base)...")
        _whisper_model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
        return _whisper_model
    except Exception as e:
        logger.error(f"Error loading Whisper: {e}")
        raise


class LocalWhisperProvider(TranscriptionProvider):
    """Whisper-based transcription with speaker diarization approximation."""

    def __init__(self):
        self.raw_response = None
        self.model = None

    def transcribe(self, audio_path: str) -> List[Segment]:
        """Transcribe audio using local Whisper model."""
        try:
            import os
            import subprocess
            import tempfile

            logger.info(f"🎤 Transcribing {audio_path} with Whisper...")

            # Verify audio file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            file_size = os.path.getsize(audio_path)
            logger.info(f"   Audio file: {os.path.basename(audio_path)} ({file_size} bytes)")

            if file_size == 0:
                raise ValueError("Audio file is empty (0 bytes)")

            # Pre-convert MP3/M4A to WAV if needed (Whisper needs FFmpeg for non-WAV formats)
            model = _get_whisper_model()
            logger.info("   Model loaded, starting transcription...")

            transcribe_path = audio_path
            converted_path = None

            # Check if file is MP3 or needs conversion
            if audio_path.lower().endswith(('.mp3', '.m4a', '.flac', '.ogg')):
                logger.info(f"   Audio is {audio_path.split('.')[-1].upper()} format, converting to WAV...")
                try:
                    converted_path = self._convert_audio_to_wav(audio_path)
                    logger.info(f"   Converted to WAV: {os.path.getsize(converted_path)} bytes")
                    transcribe_path = converted_path
                except Exception as e:
                    logger.error(f"Conversion failed: {e}")
                    raise RuntimeError("Unable to transcribe: FFmpeg not installed. Please install FFmpeg from https://ffmpeg.org/download.html")

            try:
                # Transcribe with word-level timestamps
                result = model.transcribe(
                    transcribe_path,
                    language="hi",  # Hinglish support
                    task="transcribe",
                    verbose=False,
                    fp16=False,  # Set to False for CPU
                    temperature=0.0,
                )
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise

            # Cleanup converted file if one was created
            if converted_path:
                try:
                    os.remove(converted_path)
                except:
                    pass

            self.raw_response = result
            num_segments = len(result.get('segments', []))
            logger.info(f"✅ Transcription complete: {num_segments} segments")

            # Extract segments from Whisper output
            segments = self._extract_segments(result)
            return segments

        except Exception as e:
            logger.error(f"❌ Error transcribing audio: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _convert_audio_to_wav(self, input_path: str) -> str:
        """Convert audio to WAV format using ffmpeg."""
        import subprocess
        import tempfile
        import os
        import shutil

        try:
            # Check input file
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            input_size = os.path.getsize(input_path)
            logger.info(f"   Input file: {input_size} bytes")

            if input_size == 0:
                raise ValueError(f"Input audio file is empty (0 bytes)")

            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"audio_converted_{os.getpid()}.wav")

            logger.info(f"   Converting to WAV: {input_path} -> {output_path}")

            # Find ffmpeg - try multiple locations
            ffmpeg_cmd = None

            logger.info("   Searching for ffmpeg...")

            # 1. Try Windows path with forward slashes
            path1 = "C:/ffmpeg/ffmpeg.exe"
            exists1 = os.path.exists(path1)
            logger.info(f"   Checking {path1}: {exists1}")
            if exists1:
                ffmpeg_cmd = path1

            # 2. Try with backslashes
            if not ffmpeg_cmd:
                path2 = "C:\\ffmpeg\\ffmpeg.exe"
                exists2 = os.path.exists(path2)
                logger.info(f"   Checking {path2}: {exists2}")
                if exists2:
                    ffmpeg_cmd = path2

            # 3. Try using shutil.which (searches PATH)
            if not ffmpeg_cmd:
                found = shutil.which("ffmpeg")
                logger.info(f"   shutil.which('ffmpeg'): {found}")
                if found:
                    ffmpeg_cmd = found

            if not ffmpeg_cmd:
                logger.error("FFmpeg not found anywhere")
                raise RuntimeError("FFmpeg not found in C:/ffmpeg, C:\\ffmpeg, or PATH")

            logger.info(f"   Using ffmpeg: {ffmpeg_cmd}")

            cmd = [
                ffmpeg_cmd,
                "-i", input_path,
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "16000",  # 16kHz sample rate (Whisper standard)
                "-ac", "1",  # Mono
                "-y",  # Overwrite output
                output_path
            ]

            # Properly quote command for shell=True (important for paths with spaces)
            import shlex
            cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)
            logger.info(f"   Running: {cmd_str}")

            # Use shell=True to bypass Windows permission issues with directly executing exe
            result = subprocess.run(
                cmd_str,
                capture_output=True,
                text=True,
                timeout=60,
                shell=True
            )

            logger.info(f"   ffmpeg return code: {result.returncode}")

            if result.stderr:
                logger.info(f"   ffmpeg stderr (first 500 chars): {result.stderr[:500]}")

            if result.returncode != 0:
                logger.error(f"   ffmpeg conversion failed!")
                logger.error(f"   stderr: {result.stderr}")
                raise RuntimeError(f"ffmpeg failed with code {result.returncode}")

            # Verify output
            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file not created: {output_path}")

            output_size = os.path.getsize(output_path)
            logger.info(f"   Output file: {output_size} bytes")

            if output_size == 0:
                raise RuntimeError(f"Converted audio file is empty (0 bytes) - ffmpeg may have failed silently")

            logger.info(f"   Conversion successful!")
            return output_path

        except Exception as e:
            logger.error(f"   Error converting audio: {type(e).__name__}: {e}")
            raise

    def _extract_segments(self, result: Dict) -> List[Segment]:
        """Extract segments from Whisper response.

        Note: Whisper doesn't do speaker diarization natively.
        We use a simple heuristic: if audio is long, assume alternating speakers.
        For real diarization, consider adding pyannote.audio or similar.
        """
        segments = []

        for idx, seg in enumerate(result.get("segments", [])):
            # Approximate speaker detection: alternate between speaker 0 and 1
            # This is a simplification - real diarization would require additional model
            speaker_tag = idx % 2

            segment = Segment({
                "speaker": f"speaker_{speaker_tag}",
                "text": seg.get("text", "").strip(),
                "start_s": round(seg.get("start", 0), 2),
                "end_s": round(seg.get("end", 0), 2),
            })

            if segment.get("text"):  # Only add non-empty segments
                segments.append(segment)

        if not segments:
            # Fallback if no segments extracted
            full_text = result.get("text", "")
            if full_text:
                segments.append(Segment(
                    speaker="speaker_0",
                    text=full_text,
                    start_s=0,
                    end_s=0,
                ))

        logger.info(f"Extracted {len(segments)} segments from transcription")
        return segments

    def get_raw_response(self) -> Dict:
        """Return raw Whisper response for audit."""
        if self.raw_response:
            return self.raw_response
        return {}
