# Dietician QA Portal — Setup & Run Guide

## Quick Start (3 Steps)

### Step 1: Install Dependencies (Run Once)
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
pip install -r requirements-dev.txt
```

**Wait for completion.** You should see: `Successfully installed ...`

### Step 2: Start FastAPI Server (Terminal 1)
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python -m uvicorn app.main:app --reload --port 8001
```

**Keep this terminal open.** You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete
```

### Step 3: Start Celery Worker (Terminal 2)
Open a **new terminal/PowerShell** and run:
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
celery -A app.worker.celery_app worker -c 2 -l info
```

**Keep this terminal open.** You should see:
```
celery@... ready. Waiting for tasks.
```

### Step 4: Open Browser
```
http://localhost:8001
```

---

## One-Click Startup (Windows Batch Scripts)

We've created two batch scripts for easy startup:

### For FastAPI Server:
Double-click: **`START_PORTAL.bat`**

This will:
- Install dependencies automatically
- Set up SQLite database
- Start FastAPI on port 8001

### For Celery Worker:
Double-click: **`START_CELERY.bat`**

This will:
- Start the Celery worker for background job processing

---

## Full Setup (First Time Only)

### 1. Install Python Dependencies
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
pip install -r requirements-dev.txt
```

### 2. Set Up Environment (.env)
The startup scripts create `.env` automatically with SQLite.

**If you need PostgreSQL instead** (production), edit `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/dietician_qa
REDIS_URL=redis://localhost:6379/0
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
GCS_BUCKET_NAME=dietician-qa-audio
GEMINI_API_KEY=your-gemini-api-key
CELERY_CONCURRENCY=2
```

### 3. Set Up Database
```bash
alembic upgrade head
```

---

## Running the Portal

### Method 1: Manual (Recommended for Development)

**Terminal 1:**
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2:**
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
celery -A app.worker.celery_app worker -c 2 -l info
```

**Browser:**
```
http://localhost:8001
```

### Method 2: Batch Scripts (Easiest)

**Double-click these files:**
1. `START_PORTAL.bat` (FastAPI server)
2. `START_CELERY.bat` (Celery worker)

Then open: `http://localhost:8001`

---

## Verify Everything Works

### Check FastAPI is running:
```bash
curl http://localhost:8001/health
```

Should return:
```json
{"status": "ok"}
```

### Check API endpoints:
```bash
curl http://localhost:8001/api/dieticians/
```

Should return:
```json
[]
```

(Empty because no calls uploaded yet)

---

## Troubleshooting

### "uvicorn: The term is not recognized"
**Fix:** Run `pip install -r requirements-dev.txt` first

### "Port 8001 already in use"
**Option 1:** Use different port:
```bash
python -m uvicorn app.main:app --reload --port 8002
```
Then access: `http://localhost:8002`

**Option 2:** Kill process using port 8001:
```powershell
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### "Database is locked" or SQLite errors
**Fix:** Delete `test.db` and restart:
```bash
del test.db
python -m uvicorn app.main:app --reload --port 8001
```

### "Celery worker won't start"
**Check Redis is running:**
```bash
redis-cli ping
```

Should return: `PONG`

If not installed, install Redis:
```bash
choco install redis-64  # or use chocolatey
```

Then start Redis:
```bash
redis-server
```

### "No module named 'app'"
**Fix:** Make sure you're in the correct directory:
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
ls  # Should show app/, alembic/, requirements-dev.txt, etc.
```

---

## Portal Features

### Tab 1: Upload
- Download Excel template
- Upload call recordings
- Real-time progress tracking
- Validation report

### Tab 2: Scorecard
- View all calls
- Click to see full analysis
- Transcript, dimension scores, flags, feedback

### Tab 3: Dietician Dashboard
- Select dietician
- See performance metrics
- Peer ranking
- Coaching pointers
- Trend charts

---

## File Structure

```
dietician-qa/
├── START_PORTAL.bat             <-- Double-click to start FastAPI
├── START_CELERY.bat             <-- Double-click to start Celery
├── requirements-dev.txt         <-- Dependencies (SQLite, no PostgreSQL)
├── .env                         <-- Auto-created (edit if needed)
├── app/
│   ├── main.py                 <-- FastAPI app
│   ├── api/
│   │   ├── calls.py           <-- Call endpoints
│   │   └── dieticians.py       <-- Dietician endpoints
│   └── ...
├── dietician_qa_portal.html     <-- Frontend portal
└── alembic/                     <-- Database migrations
```

---

## Development vs Production

### Development (SQLite) — Default
```
DATABASE_URL=sqlite:///./test.db
```

✅ No external database needed  
✅ Perfect for testing  
❌ Not suitable for production  

### Production (PostgreSQL)
```
DATABASE_URL=postgresql://user:password@localhost/dietician_qa
```

✅ Full production setup  
✅ Handles concurrent users  
❌ Requires PostgreSQL installed  

---

## Next Steps

1. **Run `START_PORTAL.bat`** (or `python -m uvicorn app.main:app --reload --port 8001`)
2. **Run `START_CELERY.bat`** (or `celery -A app.worker.celery_app worker -c 2 -l info`)
3. **Open** `http://localhost:8001`
4. **Upload test data** using the Upload tab
5. **Verify it works** — see scorecard and dashboard

---

## Support

- **FastAPI Docs:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health
- **Error Log:** Check Terminal 1 output for FastAPI errors
- **Celery Log:** Check Terminal 2 output for worker errors

---

**You're all set! Start the services and enjoy the portal 🚀**
