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
    calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(5).all()

    result = []
    for call in calls:
        trans = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
        result.append({
            "id": str(call.id),
            "status": str(call.status),
            "created": str(call.created_at),
            "transcript_provider": trans.provider if trans else "None",
            "transcript_segments": len(trans.diarized_segments) if trans and trans.diarized_segments else 0,
            "error": call.error_message
        })

    db.close()
    return {"calls": result}


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
