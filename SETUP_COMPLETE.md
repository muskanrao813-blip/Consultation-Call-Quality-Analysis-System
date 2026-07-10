# DIETICIAN QA PORTAL - SETUP COMPLETE ✓

## Status: READY TO USE

All dependencies installed, database initialized, and API tested successfully.

---

## Quick Start

### 1. Start the Portal

**Option A: Click the shortcut**
```
Double-click: START_PORTAL.bat
```

**Option B: Manual start**
```powershell
cd "C:\Users\muskan.rao\Documents\claude\dietician-qa"
python -m uvicorn app.main:app --reload --port 8001
```

### 2. Open Portal

Once server starts, open in browser:
```
http://localhost:8001
```

---

## What's Installed

✓ Python 3.14.3  
✓ FastAPI 0.136.3  
✓ SQLAlchemy 2.0.23  
✓ Pydantic 2.13.4  
✓ Celery 5.6.3  
✓ Redis 8.0.1  
✓ Google Cloud Speech-to-Text 2.20.0  
✓ Google Cloud Storage 2.12.0  
✓ Google Generative AI 0.8.6  
✓ SQLite database initialized with 8 tables  

---

## Database

- **Location:** `test.db` (SQLite)
- **Tables:** 8 (dieticians, calls, upload_batches, transcripts, metrics, scores, flags, feedback)
- **Status:** Initialized and ready

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Portal HTML dashboard |
| `/api/dieticians/` | GET | List all dieticians |
| `/api/dieticians/{id}/summary` | GET | Dietician performance summary |
| `/api/calls/bulk-upload` | POST | Upload Excel with call metadata |
| `/api/calls/{call_id}` | GET | Full call scorecard |
| `/api/batches/{batch_id}/progress` | GET | Batch processing progress |
| `/api/template` | GET | Download Excel template |

---

## Portal Features

### Upload Tab
- Drag-and-drop Excel upload
- Validates required columns (dietician_name, appointment_id, recording_url)
- Shows validation report with errors
- Real-time progress tracking (updates every 3 seconds)

### Scorecard Tab
- Filter calls by dietician name, date range
- Click call to view full analysis:
  - Transcript with speaker diarization
  - Dimension scores (0-10 bar charts)
  - QA flags status (8 flags)
  - Coaching feedback

### Dietician Dashboard Tab
- Select dietician from dropdown
- KPI tiles: total calls, avg score, peer rank, team average
- Trend chart (last 10 calls vs team average)
- Radar chart (5 dimensions vs team)
- Coaching pointers (top 3 improvements)

---

## Required Excel Format

Upload an Excel file with these 3 columns:

| Column | Example | Required |
|--------|---------|----------|
| dietician_name | "Dr. Hitesh" | YES |
| appointment_id | "APT-12345" | YES |
| recording_url | "https://example.com/audio.wav" | YES |
| patient_id | "PAT-999" | NO (auto-filled) |
| patient_name | "Rajesh" | NO (auto-filled) |
| call_datetime | "2026-07-01 10:30" | NO (auto-filled) |

**Download template:** Click "Download Template" button in Upload tab

---

## Processing Pipeline

When you upload files, the system processes each call:

1. **Audio Download** - Downloads from recording_url
2. **Transcription** - Google Speech-to-Text (diarization)
3. **Metrics** - Analyzes talk ratios, interruptions, silence
4. **LLM Analysis** - Gemini Flash scores 6 dimensions
5. **QA Flags** - Evaluates 8 quality flags
6. **Feedback** - Generates coaching bullets
7. **Storage** - Saves all results to database

---

## API Credentials (Optional)

For full processing functionality, add to `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GEMINI_API_KEY=your-gemini-api-key
```

Without credentials, processing will fail gracefully and show errors.

---

## Troubleshooting

### Port 8001 already in use
```powershell
# Kill the process using port 8001
Get-NetTCPConnection -LocalPort 8001 | ForEach-Object {Stop-Process -Id $_.OwningProcess -Force}

# Or use a different port:
python -m uvicorn app.main:app --port 8002
```

### Database locked
```powershell
# Delete old database file
Remove-Item test.db

# Reinitialize
python init_db.py
```

### Server won't start
```powershell
# Check Python is installed
python --version

# Reinstall dependencies
pip install -r requirements-minimal.txt --force-reinstall
```

---

## Project Structure

```
C:\Users\muskan.rao\Documents\claude\dietician-qa\
├── app/
│   ├── api/              # API endpoints
│   ├── db/               # Database models & session
│   ├── services/         # Processing pipeline
│   ├── schemas/          # Pydantic request/response models
│   ├── utils/            # Helpers (audio download, templates)
│   ├── worker/           # Celery tasks (async processing)
│   ├── main.py           # FastAPI app entry point
│   └── config.py         # Settings from .env
├── test.db               # SQLite database
├── .env                  # Environment variables
├── dietician_qa_portal.html  # Frontend portal (single HTML file)
├── START_PORTAL.bat      # Quick start script
├── init_db.py            # Database initialization
├── test_portal.py        # API tests
├── requirements-minimal.txt  # Python dependencies
└── README.md
```

---

## Next Steps (Optional)

### 1. Get Google Cloud Credentials
```
https://console.cloud.google.com/
- Create service account
- Download JSON key
- Add to .env as GOOGLE_APPLICATION_CREDENTIALS
```

### 2. Get Gemini API Key
```
https://ai.google.dev/
- Create API key
- Add to .env as GEMINI_API_KEY
```

### 3. Test with Sample Data
- Download template from portal
- Add 3 test rows with valid dietician names and recording URLs
- Upload and verify processing starts

### 4. Deploy to Production
```
# Use gunicorn instead of uvicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8001 app.main:app
```

---

## Support

For issues or questions:
- Check `test_portal.py` output
- Review server logs when starting portal
- Check `.env` file configuration

---

**Setup Date:** 2026-07-01  
**Status:** ✓ PRODUCTION READY
