from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from app.db.session import get_db, engine
from app.db.models import Base
from app.api import calls, dieticians, clinical_calls

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dietician Call QA & Analysis Agent", version="0.1.0")

@app.on_event("startup")
def startup_event():
    """Create all database tables on startup"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

# Add CORS middleware - allow development & production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development (localhost)
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        # Production (Netlify)
        "https://consultation-call-quality-analysis.netlify.app",
        "https://rainbow-biscotti-eb81b0.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls.router, prefix="/api", tags=["calls"])
app.include_router(dieticians.router, prefix="/api", tags=["dieticians"])
app.include_router(clinical_calls.router, prefix="/api", tags=["clinical"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/debug/logs")
def get_logs():
    """Get the last 100 lines of server logs for debugging"""
    import subprocess
    try:
        # Read the last 100 lines of the server log
        result = subprocess.run(
            ["powershell", "-Command", "Get-Content $env:TEMP\\server.log -Tail 100"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout if result.stdout else "No logs yet"
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}", "status": "error"}


@app.get("/api/debug/calls")
def get_processing_status():
    """Get status of all calls for debugging"""
    from app.db.session import SessionLocal
    from app.db import models
    import json

    db = SessionLocal()
    calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(10).all()

    result = []
    for call in calls:
        trans = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
        metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
        scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).first()

        result.append({
            "id": str(call.id),
            "status": str(call.status),
            "created": str(call.created_at),
            "patient_name": call.patient_name,
            "appointment_id": call.appointment_id,
            "recording_url": call.recording_url[:50] + "..." if call.recording_url and len(call.recording_url) > 50 else call.recording_url,
            "transcript_exists": trans is not None,
            "transcript_provider": trans.provider if trans else "None",
            "transcript_text_length": len(trans.raw_transcript) if trans and trans.raw_transcript else 0,
            "metrics_exists": metrics is not None,
            "scores_exists": scores is not None,
            "overall_score": scores.overall_weighted_score if scores else None,
            "error": call.error_message
        })

    db.close()
    return {"calls": result, "total_calls": len(calls)}


@app.get("/api/debug/test-gemini")
def test_gemini():
    """Test if Gemini API is working"""
    import os
    api_key = os.getenv("GEMINI_API_KEY", "NOT_SET")

    if api_key == "NOT_SET":
        return {"status": "error", "message": "GEMINI_API_KEY environment variable not set"}

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Simple test
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents="Say 'Gemini is working' in one sentence"
        )
        return {
            "status": "success",
            "message": response.text[:100],
            "api_key_set": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "api_key_set": api_key != "NOT_SET"
        }


@app.get("/api/debug/test-claude")
def test_claude():
    """Test if Claude CLI is available and working"""
    import subprocess
    import shutil
    import os

    claude_path = shutil.which("claude")

    if not claude_path:
        return {
            "status": "error",
            "message": "Claude CLI not found in PATH",
            "claude_available": False,
            "current_path": os.environ.get("PATH", "NOT SET")[:300],
            "hint": "Claude CLI must be installed. Build output should show 'claude --version' success."
        }

    try:
        result = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {
                "status": "success",
                "message": result.stdout.strip(),
                "claude_available": True,
                "claude_path": claude_path
            }
        else:
            return {
                "status": "error",
                "message": f"Claude CLI returned exit code {result.returncode}: {result.stderr}",
                "claude_available": False,
                "claude_path": claude_path
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "claude_available": False,
            "claude_path": claude_path
        }


@app.get("/")
def root():
    return {
        "name": "Dietician Call QA & Analysis Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "note": "Frontend available at http://localhost:3001"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
