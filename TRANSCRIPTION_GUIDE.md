# Transcription Service Setup & Integration Guide

## Overview

The transcription service handles:
1. **Audio download** from recording URLs with retry logic
2. **Speaker diarization** via Google Cloud Speech-to-Text
3. **Hinglish support** (Hindi + English code-switching)
4. **Segment storage** with timestamps and speaker labels

## Google Cloud Speech-to-Text Setup

### Prerequisites

1. **Google Cloud Project**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable APIs**
   ```bash
   gcloud services enable speech.googleapis.com
   gcloud services enable storage-api.googleapis.com
   ```

3. **Create GCS Bucket**
   ```bash
   gsutil mb gs://dietician-qa-audio
   ```

4. **Create Service Account**
   ```bash
   gcloud iam service-accounts create dietician-qa-stt \
     --display-name="Dietician QA STT Service"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member=serviceAccount:dietician-qa-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com \
     --role=roles/speech.client

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member=serviceAccount:dietician-qa-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com \
     --role=roles/storage.objectAdmin

   gcloud iam service-accounts keys create service_account.json \
     --iam-account=dietician-qa-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

5. **Configure Environment**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
   export GCS_BUCKET_NAME=dietician-qa-audio
   ```

### Configuration

Update `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
GCS_BUCKET_NAME=dietician-qa-audio
```

## Audio Download

The audio download utility handles:
- URL validation
- Streaming downloads (chunked for large files)
- Automatic retry with exponential backoff
- Proper file extension detection from Content-Type
- Temporary file cleanup

### Supported Formats

- **Audio**: MP3, WAV, OGG, WebM
- **Video**: MP4, WebM

### Configuration

In `app/services/pipeline.py`, adjust retry logic:
```python
audio_path = download_audio(
    call.recording_url,
    max_retries=3,      # Number of retry attempts
    timeout=30          # Seconds per attempt
)
```

### Error Handling

The download utility automatically:
- Retries on transient failures (connection timeout, temporary network error)
- Fails fast on permanent errors (404, authentication error)
- Logs all attempts for debugging
- Cleans up temporary files after processing

## Transcription Workflow

### Step 1: Audio Download
```python
from app.utils.audio import download_audio, cleanup_audio

audio_path = download_audio("https://example.com/call.wav")
```

### Step 2: Initialize Transcription Provider
```python
from app.services.transcription.google_stt import GoogleSTTProvider

provider = GoogleSTTProvider(
    gcs_bucket="dietician-qa-audio",
    credentials_path="/path/to/service_account.json"
)
```

### Step 3: Transcribe
```python
segments = provider.transcribe(audio_path)
# Returns: [{speaker: "speaker_0", text: "...", start_s: 0, end_s: 3}, ...]
```

### Step 4: Store Transcript
```python
from app.db import models

transcript = models.Transcript(
    call_id=call_id,
    provider="google_stt",
    raw_transcript_json=provider.get_raw_response(),
    diarized_segments=segments,
)
db.add(transcript)
db.commit()
```

### Step 5: Cleanup
```python
cleanup_audio(audio_path)
```

## Diarization Configuration

Google Cloud Speech-to-Text is configured for:

| Setting | Value | Reason |
|---------|-------|--------|
| `enable_speaker_diarization` | `True` | Required for speaker labels |
| `min_speaker_count` | 2 | Minimum speakers (dietician + patient) |
| `max_speaker_count` | 2 | Maximum 2 speakers (assumes bilateral conversation) |
| `language_codes` | `["hi-IN", "en-IN"]` | Hinglish support (Hindi + English) |
| `model` | `latest_long` | Optimized for phone/call audio |
| `use_enhanced` | `True` | Higher accuracy model |

## Segment Format

Each segment represents a contiguous speech turn by one speaker:

```json
{
  "speaker": "speaker_0",                    // or "speaker_1"
  "text": "Please tell me about your diet",
  "start_s": 12.5,                          // Seconds from call start
  "end_s": 18.2,
}
```

**Speaker Labels:**
- `speaker_0` — Usually the dietician (first speaker)
- `speaker_1` — Usually the patient (second speaker)
- `unknown` — Used if diarization fails

## Metrics Derived from Segments

Once transcribed, the metrics engine computes:

```python
from app.services import metrics

segments = transcript.diarized_segments
total_duration = segments[-1]["end_s"]

ratios = metrics.compute_talk_ratios(segments)
# Returns: {dietician_pct: 45.5, patient_pct: 54.5}

interruptions = metrics.compute_interruptions(segments)
# Count of overlapping/near-overlapping speech turns

latency = metrics.compute_response_latency(segments)
# Avg gap (seconds) between speaker turns

silence_pct = metrics.compute_silence_pct(segments, total_duration)
# % of call with no speech

time_to_plan = metrics.compute_time_to_first_plan(segments)
# Timestamp of first plan/diet mention (or None)
```

## Testing Transcription

### Unit Tests
```bash
# Test audio download
pytest tests/test_audio.py -v

# Test transcription provider
pytest tests/test_transcription.py -v
```

### Integration Tests
```bash
# Test full pipeline with mocks
pytest tests/test_pipeline_e2e.py::TestPipelineEndToEnd::test_pipeline_full_workflow -v
```

### Manual Testing

1. **Create a test call record** (via API or direct DB)
2. **Ensure audio URL is reachable**
3. **Run transcription**:

```python
from app.db.session import SessionLocal
from app.services.transcription.google_stt import GoogleSTTProvider
from app.utils.audio import download_audio, cleanup_audio
import logging

logging.basicConfig(level=logging.DEBUG)

db = SessionLocal()
call = db.query(Call).first()

# Download
audio_path = download_audio(call.recording_url)

# Transcribe
provider = GoogleSTTProvider()
segments = provider.transcribe(audio_path)

print(f"Transcribed {len(segments)} segments")
for seg in segments[:3]:
    print(f"  [{seg['start_s']:.1f}s] {seg['speaker']}: {seg['text'][:50]}...")

# Cleanup
cleanup_audio(audio_path)
```

## Troubleshooting

### "Failed to authenticate" / Credentials Error
```bash
# Verify credentials file
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Re-authenticate
gcloud auth application-default login

# Re-export path
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
```

### "Bucket not found" / Storage Error
```bash
# Verify bucket exists
gsutil ls gs://dietician-qa-audio

# Check permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:dietician-qa-stt*"
```

### "The service does not have sufficient permissions" / IAM Error
```bash
# Grant required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:dietician-qa-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/speech.client

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:dietician-qa-stt@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### "Audio URL is not reachable" / Network Error
- Verify URL is direct link (not a redirect or auth-gated page)
- Check URL is accessible from your network
- Ensure Content-Type header is set to `audio/*` or `video/*`
- Try downloading manually: `curl -I https://example.com/call.wav`

### "Timeout waiting for transcription"
- Large files (>1 hour) may take several minutes
- Check operation status in GCP console
- Increase timeout in pipeline config
- Consider splitting very long calls into segments

### Hinglish Recognition Issues
- Ensure language_codes include both `hi-IN` and `en-IN`
- Test with Google STT console to verify audio quality
- Check that call is not too noisy or compressed
- Consider preprocessing audio (normalize volume, remove silence)

## Performance & Costs

### Transcription Costs (GCP)
- ~$1.44 per hour of audio (Speech-to-Text pricing)
- Diarization adds ~60% to base cost
- Storage: ~$0.02 per GB/month

### Processing Time
- Typical 15–30 min call: 2–5 minutes transcription time (async operation)
- Metrics computation: <1 second
- LLM analysis: 10–20 seconds

### Optimization Tips
1. **Batch uploads**: Process multiple calls in parallel via Celery
2. **Audio preprocessing**: Remove silence, normalize volume before upload
3. **Caching**: Store transcripts to avoid re-transcribing same call
4. **Regional GCS bucket**: Place bucket in same region as compute for faster uploads

## Advanced Configuration

### Custom Language Models

For better accuracy on medical terminology, you can:
1. Create a custom Speech-to-Text model in GCP Console
2. Update `app/services/transcription/google_stt.py`:
   ```python
   config = speech_v1.RecognitionConfig(
       # ... existing config ...
       model="custom:YOUR_MODEL_ID"
   )
   ```

### Non-English/Hindi Support

To add new languages:
1. Update `language_codes` in `google_stt.py`
2. Test with sample audio
3. Update metrics logic if language-specific (e.g., keyword detection for diet plan)

## API Reference

### GoogleSTTProvider

```python
class GoogleSTTProvider(TranscriptionProvider):
    def __init__(self, gcs_bucket: str = None, credentials_path: str = None)
    def transcribe(self, audio_path: str) -> List[Segment]
    def get_raw_response(self) -> Dict
    def _format_transcript(self, segments: List[Dict]) -> str
    def _extract_segments(self, result) -> List[Segment]
    def _upload_to_gcs(self, local_path: str) -> str
```

### Audio Utilities

```python
def download_audio(recording_url: str, max_retries: int = 3, timeout: int = 30) -> str
def cleanup_audio(file_path: str) -> None
def _get_extension_from_content_type(content_type: str) -> str
```

---

## Next Steps

1. **Phase 4**: Unit tests for metrics engine (already done, see test_metrics.py)
2. **Phase 5**: Gemini Flash LLM adapter + rubric prompts + scoring engine
3. **Phase 6**: Full pipeline orchestrator + Celery worker integration
4. **Phase 7**: REST API + React dashboard
