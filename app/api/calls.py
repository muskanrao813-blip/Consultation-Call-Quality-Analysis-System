from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.call import ValidationReport, CallDetailResponse
from app.services.ingestion import IngestService
from app.utils.template import generate_excel_template
from app.db import models
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/template")
async def download_template():
    """Download blank Excel template for call metadata."""
    try:
        template_bytes = generate_excel_template()
        return StreamingResponse(
            iter([template_bytes.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=dietician_calls_template.xlsx"},
        )
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calls/bulk-upload", response_model=ValidationReport)
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload Excel file with call metadata for processing."""
    try:
        ingest = IngestService(db)
        validation_report = await ingest.validate_and_ingest_excel(file)
        return validation_report
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calls/audio-upload")
async def audio_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a single audio file for transcription and QA analysis."""
    try:
        ingest = IngestService(db)
        result = await ingest.validate_and_ingest_audio(file)
        return result
    except Exception as e:
        logger.error(f"Error in audio upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calls", response_model=dict)
async def create_call(call_data: dict, db: Session = Depends(get_db)):
    """Create a single call record."""
    try:
        ingest = IngestService(db)
        call = await ingest.create_single_call(call_data)
        return {"id": str(call.id), "status": "queued"}
    except Exception as e:
        logger.error(f"Error creating call: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calls", response_model=list)
async def list_calls(db: Session = Depends(get_db)):
    """List all completed calls with summary info."""
    try:
        calls = db.query(models.Call).filter(
            models.Call.status.in_(["completed", "processing", "pending"])
        ).order_by(models.Call.created_at.desc()).all()

        result = []
        for call in calls:
            metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
            rubric_scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()

            overall_score = None
            if rubric_scores:
                overall_score = rubric_scores[0].overall_weighted_score

            result.append({
                "id": str(call.id),
                "dietician_name": call.dietician.name if call.dietician else "Unknown",
                "patient_name": call.patient_name,
                "call_datetime": call.call_datetime,
                "call_duration_seconds": call.call_duration_seconds,
                "status": call.status,
                "overall_weighted_score": overall_score,
                "dietician_talk_ratio_pct": metrics.dietician_talk_ratio_pct if metrics else None,
            })

        return result
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}", response_model=CallDetailResponse)
async def get_call(call_id: str, db: Session = Depends(get_db)):
    """Get full call result with transcript, scorecard, and flags."""
    try:
        import uuid
        try:
            call_uuid = uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        call = db.query(models.Call).filter(models.Call.id == call_uuid).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
        metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
        rubric_scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
        qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
        feedback = db.query(models.FeedbackNote).filter(models.FeedbackNote.call_id == call.id).first()

        overall_weighted_score = None
        if rubric_scores:
            overall_weighted_score = rubric_scores[0].overall_weighted_score

        feedback_bullets = []
        retraining_recommended = False
        if feedback:
            feedback_bullets = [b.strip() for b in feedback.bullet.split("|")]
            retraining_recommended = feedback.retraining_recommended

        return {
            "id": call.id,
            "dietician_id": call.dietician_id,
            "patient_id": call.patient_id,
            "patient_name": call.patient_name,
            "appointment_id": call.appointment_id,
            "call_datetime": call.call_datetime,
            "recording_url": call.recording_url,
            "call_duration_seconds": call.call_duration_seconds,
            "status": call.status,
            "created_at": call.created_at,
            "processed_at": call.processed_at,
            "error_message": call.error_message,
            "transcript": {
                "segments": transcript.diarized_segments if transcript else []
            },
            "metrics": {
                "duration_seconds": metrics.duration_seconds if metrics else None,
                "dietician_talk_ratio_pct": metrics.dietician_talk_ratio_pct if metrics else None,
                "patient_talk_ratio_pct": metrics.patient_talk_ratio_pct if metrics else None,
                "interruption_count": metrics.interruption_count if metrics else None,
                "avg_response_latency_seconds": metrics.avg_response_latency_seconds if metrics else None,
                "time_to_first_plan_mention_seconds": metrics.time_to_first_plan_mention_seconds if metrics else None,
                "silence_pct": metrics.silence_pct if metrics else None,
                "off_topic_time_pct": metrics.off_topic_time_pct if metrics else None,
            },
            "rubric_scores": [
                {
                    "dimension": rs.dimension,
                    "score": rs.score,
                    "evidence": rs.evidence,
                    "sub_criteria": rs.sub_criteria
                }
                for rs in rubric_scores
            ],
            "qa_flags": [
                {
                    "flag_type": f.flag_type,
                    "triggered": f.triggered,
                    "detail": f.detail
                }
                for f in qa_flags
            ],
            "feedback_notes": {
                "bullets": feedback_bullets,
                "retraining_recommended": retraining_recommended
            },
            "overall_weighted_score": overall_weighted_score,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/transcript")
async def get_transcript(call_id: str, db: Session = Depends(get_db)):
    """Get diarized transcript only."""
    try:
        import uuid
        try:
            call_uuid = uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call_uuid).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        return {"segments": transcript.diarized_segments}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    """Get batch upload status."""
    try:
        import uuid
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid batch ID format")

        batch = db.query(models.UploadBatch).filter(models.UploadBatch.id == batch_uuid).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        calls = db.query(models.Call).filter(models.Call.batch_id == batch_uuid).all()
        call_statuses = {}
        for call in calls:
            call_statuses[str(call.id)] = call.status

        return {
            "batch_id": str(batch.id),
            "uploaded_at": batch.uploaded_at,
            "total_rows": batch.total_rows,
            "valid_rows": batch.valid_rows,
            "invalid_rows": batch.invalid_rows,
            "call_statuses": call_statuses,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}/progress")
async def get_batch_progress(batch_id: str, db: Session = Depends(get_db)):
    """Get batch processing progress with live call status and detailed step info."""
    try:
        import uuid
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid batch ID format")

        batch = db.query(models.UploadBatch).filter(models.UploadBatch.id == batch_uuid).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        calls = db.query(models.Call).filter(models.Call.batch_id == batch_uuid).all()

        completed = 0
        failed = 0
        pending = 0
        processing = 0
        call_details = []

        for call in calls:
            if call.status == models.CallStatus.completed:
                completed += 1
                current_step = "Completed"
                step_number = 6
            elif call.status == models.CallStatus.failed:
                failed += 1
                current_step = f"Failed: {call.error_message}"
                step_number = 0
            elif call.status == models.CallStatus.processing:
                processing += 1
                # Determine step based on what data exists
                if db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first():
                    if db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).first():
                        current_step = "Analyzing with AI..."
                        step_number = 4
                    else:
                        current_step = "Extracting metrics..."
                        step_number = 3
                else:
                    current_step = "Transcribing audio..."
                    step_number = 2
            else:  # pending
                pending += 1
                current_step = "Waiting to start..."
                step_number = 1

            # Get overall score for completed calls
            overall_score = None
            if call.status == models.CallStatus.completed:
                rubric_scores = db.query(models.RubricScore).filter(
                    models.RubricScore.call_id == call.id
                ).first()
                if rubric_scores:
                    overall_score = rubric_scores.overall_weighted_score

            try:
                dietician_name = call.dietician.name if (call.dietician and hasattr(call.dietician, 'name')) else None
            except:
                dietician_name = None

            call_details.append({
                "id": str(call.id),
                "status": call.status.value,
                "dietician_name": dietician_name,
                "patient_name": call.patient_name,
                "appointment_id": call.appointment_id,
                "overall_score": overall_score,
                "current_step": current_step,
                "step_number": step_number,
                "error_message": call.error_message,
            })

        total = len(calls)
        pct_complete = int((completed / total * 100)) if total > 0 else 0

        return {
            "batch_id": str(batch.id),
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": processing,
            "pct_complete": pct_complete,
            "status_text": f"{completed} completed, {processing} processing, {pending} pending, {failed} failed",
            "calls": call_details,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
