# Google Cloud Setup for Full Processing

**Status:** Portal is running and ready to accept data uploads. Audio processing requires Google Cloud credentials (free tier available).

---

## What You Get After Setup

✅ Automatic audio transcription with speaker diarization  
✅ AI-powered quality scoring on 6 dimensions  
✅ QA flag detection (8 automated checks)  
✅ Personalized coaching feedback  
✅ Complete call analytics and dietician dashboards  

---

## Prerequisites

- Google account (personal or business)
- ~30 minutes to set up
- Free tier covers testing (first $300 credits)

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter project name: `dietician-qa-portal` (or your choice)
5. Click "CREATE"
6. Wait for project creation (2-3 minutes)

---

## Step 2: Enable Required APIs

1. In Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for and enable these APIs (click each, then "ENABLE"):

   **Required APIs:**
   - **Google Cloud Speech-to-Text API**
   - **Google Cloud Storage API**
   - **Compute Engine API** (if not already enabled)

3. Wait for each to show "Status: ENABLED" (blue checkmark)

---

## Step 3: Create Service Account (for Speech-to-Text & Storage)

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"Service Account"**
3. Fill in:
   - **Service account name:** `dietician-qa-app`
   - **Service account ID:** auto-filled (ok to keep)
   - Click "CREATE AND CONTINUE"
4. Grant roles (click "CONTINUE" for now, then add roles):
   - Click "SELECT A ROLE" dropdown
   - Search and select: **"Cloud Speech-to-Text Client"**
   - Click "ADD ANOTHER ROLE"
   - Search and select: **"Storage Object Creator"**
   - Search and select: **"Storage Object Viewer"**
   - Click "CONTINUE"
5. Review and click "DONE"

---

## Step 4: Create and Download Service Account Key

1. In **"APIs & Services"** → **"Credentials"**, find your service account in the list
2. Click on the service account name (not the email) → "dietician-qa-app"
3. Click the **"KEYS"** tab at the top
4. Click **"ADD KEY"** → **"Create new key"**
5. Select **"JSON"** → **"CREATE"**
6. A JSON file will auto-download (e.g., `dietician-qa-portal-abc123.json`)
7. **Keep this file safe** — it contains your credentials

---

## Step 5: Move Service Account Key to Project Directory

1. Move the downloaded JSON file to your project:
   ```
   C:\Users\muskan.rao\Documents\claude\dietician-qa\google-cloud-key.json
   ```
   (Or any location you remember)

---

## Step 6: Create Gemini API Key (for AI Scoring)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Click **"Get API Key"**
3. Click **"Create API key"** (or "Create new API key" if you have existing keys)
4. A dialog will show your API key
5. **Copy it** (you'll need it in next step)

---

## Step 7: Update .env File

Open `C:\Users\muskan.rao\Documents\claude\dietician-qa\.env` and add/update:

```env
# Google Cloud Settings
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\muskan.rao\Documents\claude\dietician-qa\google-cloud-key.json
GCS_BUCKET_NAME=dietician-qa-audio
GEMINI_API_KEY=your-api-key-here

# Database
DATABASE_URL=sqlite:///./test.db

# Server
PORT=8001
```

Replace:
- `your-api-key-here` with the Gemini API key from Step 6
- Path to match where you saved the JSON file

---

## Step 8: Create GCS Bucket (for Audio Storage)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **"Cloud Storage"** → **"Buckets"**
3. Click **"CREATE"**
4. Enter:
   - **Name:** `dietician-qa-audio-[your-unique-id]` (must be globally unique, add random numbers)
   - Example: `dietician-qa-audio-2026-07-02`
5. **Location:** Choose your region (e.g., "asia-south1" for India)
6. **Storage class:** Standard
7. **Uncheck** "Enforce public access prevention" (for testing)
8. Click **"CREATE"**
9. Copy the bucket name exactly as shown
10. Update your `.env` file:
    ```
    GCS_BUCKET_NAME=dietician-qa-audio-2026-07-02
    ```

---

## Step 9: Verify Setup

Run this test to verify credentials work:

```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python -c "
import os
from app.config import get_settings

settings = get_settings()
print('GOOGLE_APPLICATION_CREDENTIALS:', settings.google_application_credentials)
print('GCS_BUCKET_NAME:', settings.gcs_bucket_name)
print('GEMINI_API_KEY:', 'SET' if settings.gemini_api_key else 'NOT SET')
"
```

Expected output:
```
GOOGLE_APPLICATION_CREDENTIALS: C:\Users\muskan.rao\Documents\claude\dietician-qa\google-cloud-key.json
GCS_BUCKET_NAME: dietician-qa-audio-2026-07-02
GEMINI_API_KEY: SET
```

---

## Step 10: Restart Server (Important!)

1. Stop the current server (Ctrl+C in PowerShell)
2. Restart it:
   ```bash
   cd C:\Users\muskan.rao\Documents\claude\dietician-qa
   python -m uvicorn app.main:app --reload --port 8001
   ```

---

## Test Full Processing

Now that processing is enabled, test end-to-end:

1. Open http://localhost:8001
2. Click **"Upload"** tab
3. Download the Excel template (or create your own with 3 columns):
   - `dietician_name` (e.g., "Dr. Sharma")
   - `appointment_id` (e.g., "APT001")
   - `recording_url` (publicly accessible audio URL)

4. Upload the file
5. Watch the **progress panel** update in real-time:
   - Downloading audio
   - Transcribing speech
   - Computing metrics
   - Running LLM analysis
   - Generating scores and feedback
6. Once complete (status changes to "completed"), click the call in **"Scorecard"** tab
7. View the full analysis:
   - Transcript with speaker diarization
   - 6 dimension scores (0-10 scale)
   - 8 QA flags with details
   - Personalized coaching feedback
   - Retraining recommendations

---

## Troubleshooting

### "GOOGLE_APPLICATION_CREDENTIALS not found"
- Verify the JSON file path is correct in `.env`
- Use forward slashes or double backslashes: `C:\\path\\to\\file.json`
- Path must be absolute (from C: drive)

### "Invalid Gemini API Key"
- Check you copied the entire key from Google AI Studio
- Verify no extra spaces or quotes around the key

### "GCS bucket not found or access denied"
- Verify service account has "Storage Object Creator" role
- Check bucket name matches exactly in `.env`
- Ensure bucket exists in Google Cloud Console

### "Audio transcription failed"
- Check recording_url is publicly accessible (not behind authentication)
- Verify audio format is supported: WAV, MP3, OGG, FLAC, WEBM
- Ensure audio is under 1 GB (Google STT limit)

### Processing doesn't start after upload
1. Check server logs for errors
2. Verify `.env` file was updated and saved
3. Restart server: `python -m uvicorn app.main:app --reload --port 8001`
4. Try uploading again

---

## Cost Information

**Free Tier:**
- $300 cloud credits (expires after 12 months)
- Covers approximately:
  - Speech-to-Text: ~600,000 minutes (at $0.006/min for premium)
  - Gemini API: ~1,000,000 token pairs (at $0.001/1000 tokens input)
  - Cloud Storage: 5 GB free, then $0.020/GB

**Estimated Cost per Call:**
- Speech-to-Text: $0.05-0.10 (depending on duration)
- Gemini Analysis: $0.001-0.005
- Storage: $0.0001 (minimal)
- **Total per call:** ~$0.10

For 1,000 calls/month: ~$100

---

## Next Steps

1. ✅ Set up Google Cloud project (Steps 1-8)
2. ✅ Verify setup (Step 9)
3. ✅ Restart server (Step 10)
4. ✅ Upload test file with audio URLs (see "Test Full Processing")
5. ✅ View results in Scorecard and Dashboard tabs

---

## Support

If you encounter issues:
1. Check server logs: open PowerShell where server is running
2. Enable debug logging in `.env`: `LOG_LEVEL=DEBUG`
3. Review error messages in the portal (red error boxes)
4. Check Google Cloud Console for API errors: **"APIs & Services"** → **"Quotas"**

---

**You're now ready for full end-to-end audio processing!**

Once credentials are set up and server is restarted, the system will automatically:
- Download audio from URLs
- Transcribe with speaker diarization
- Extract conversation metrics
- Analyze call quality using AI
- Generate coaching feedback
- Store everything in the database

All visible in real-time through the portal dashboard.
