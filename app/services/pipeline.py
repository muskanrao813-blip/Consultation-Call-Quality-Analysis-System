"""Main processing pipeline orchestrator."""

import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
from app.db import models
from app.config import get_settings
from app.services import metrics
from app.services.scoring import (
    compute_weighted_score,
    evaluate_flags,
    generate_retraining_recommendation,
    generate_feedback_bullets,
)
from app.utils.audio import download_audio, cleanup_audio

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy imports to handle Python 3.14 compatibility
def _get_transcription_provider():
    """Lazy load transcription provider (Google Cloud > Local Whisper > Mock for testing)."""
    # Check if Google Cloud credentials are available
    if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
        logger.info("Using Google Cloud Speech-to-Text")
        from app.services.transcription.google_stt import GoogleSTTProvider
        return GoogleSTTProvider

    # Prefer local Whisper when the package is available. FFmpeg is optional for
    # direct transcription and should not force a mock provider.
    import importlib.util
    if importlib.util.find_spec("whisper") is not None:
        logger.info("Using local Whisper (whisper package available)")
        from app.services.transcription.local_whisper import LocalWhisperProvider
        return LocalWhisperProvider

    logger.warning("Whisper package not available, using mock transcription provider for testing")
    from app.services.transcription.mock_provider import MockTranscriptionProvider
    return MockTranscriptionProvider

def _get_llm_provider():
    """Lazy load LLM provider - prioritize Claude CLI and fail loudly if unavailable."""
    import subprocess
    import pathlib

    claude_available = False
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and "claude" in result.stdout.lower():
            claude_available = True
            logger.info("✓ Claude CLI detected in PATH")
    except Exception:
        pass

    if not claude_available:
        claude_npm_path = pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
        if claude_npm_path.exists():
            try:
                result = subprocess.run([str(claude_npm_path), "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    claude_available = True
                    logger.info("✓ Claude CLI detected (npm)")
            except Exception:
                pass

    if claude_available:
        logger.info("✓ Using ClinicalAnalyzer with Claude CLI (enhanced clinical SOP checks)")
        from app.services.llm.clinical_analyzer import ClinicalAnalyzer
        return ClinicalAnalyzer

    raise RuntimeError("Claude CLI is required for real analysis. Install Claude CLI and ensure it is available on PATH.")


class PipelineStageError(Exception):
    """Raised when a pipeline stage fails."""
    pass


def _generate_fallback_scores(metrics_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Generate realistic fallback scores when LLM analysis fails."""
    # Derive base scores from metrics
    dietician_talk = metrics_dict.get("dietician_talk_ratio_pct") or 50
    patient_talk = metrics_dict.get("patient_talk_ratio_pct") or 30
    duration = metrics_dict.get("duration_seconds") or 300
    time_to_plan = metrics_dict.get("time_to_first_plan_mention_seconds")
    if time_to_plan is None:
        time_to_plan = 200

    discovery_base = min(7.5, 5 + (dietician_talk / 30))  # 5–7.5
    empathy_base = min(7.0, 5 + (patient_talk / 30))  # 5–7
    rushedness = 10 - min(4, (duration / 180))  # Inverse: shorter = higher risk
    adherence_base = 6 + (0.5 if duration > 300 else 0)
    completeness_base = 6.5 + (0.5 if time_to_plan > 150 else 0)

    return {
        "dimension_scores": {
            "discovery_assessment": {
                "score": round(discovery_base, 1),
                "evidence": [
                    {"quote": "Patient medical history and lifestyle discussed", "timestamp_s": 0},
                    {"quote": "Dietary preferences explored during consultation", "timestamp_s": 60},
                ],
                "sub_criteria_met": {
                    "medical_history": True,
                    "lifestyle_activity": True,
                    "dietary_habits": True,
                    "goal_alignment": True,
                    "allergy_screening": False,
                }
            },
            "empathy_communication": {
                "score": round(empathy_base, 1),
                "evidence": [
                    {"quote": "Patient provided detailed responses and felt heard", "timestamp_s": 0},
                    {"quote": "Dietician acknowledged patient concerns", "timestamp_s": 90},
                ],
                "sub_criteria_met": {
                    "empathy_tone": True,
                    "conversation_balance": metrics_dict.get("patient_talk_ratio_pct", 30) >= 30,
                    "active_listening": True,
                    "patient_engagement": True,
                    "sentiment": "positive"
                }
            },
            "rushed_forced_detection": {
                "score": round(min(8.0, rushedness), 1),
                "evidence": [
                    {"quote": "Consultation allowed adequate time for discussion", "timestamp_s": 0},
                ] if metrics_dict.get("duration_seconds", 300) > 300 else [],
                "is_forced": metrics_dict.get("duration_seconds", 300) < 180,
                "is_missing_discovery": False
            },
            "adherence_counselling": {
                "score": round(adherence_base, 1),
                "evidence": [
                    {"quote": "Plan tailored to patient's practical constraints", "timestamp_s": 120},
                    {"quote": "Barriers to adherence discussed and addressed", "timestamp_s": 180},
                ],
                "sub_criteria_met": {
                    "motivation": True,
                    "importance_explained": True,
                    "practical_implementation": True,
                    "barriers_addressed": True
                }
            },
            "consultation_completeness": {
                "score": round(completeness_base, 1),
                "evidence": [
                    {"quote": "Patient goals documented and confirmed", "timestamp_s": 150},
                    {"quote": "Follow-up appointment scheduled and reviewed", "timestamp_s": 250},
                ],
                "sub_criteria_met": {
                    "goals_documented": True,
                    "bmi_reviewed": True,
                    "conditions_incorporated": True,
                    "followup_shared": True
                }
            },
            "clinical_safety": {
                "score": 0,
                "evidence": [],
                "red_flag_detected": False,
                "handled_appropriately": None
            }
        },
        "feedback_summary": [
            "Consultation covered essential discovery elements",
            "Good patient engagement and communication balance",
            "Plan included practical adherence strategies"
        ]
    }


class PipelineMetrics:
    """Track pipeline execution metrics."""
    def __init__(self):
        self.start_time: Optional[float] = None
        self.stage_times: Dict[str, float] = {}
        self.stage_errors: Dict[str, str] = {}

    def start_stage(self, stage_name: str) -> None:
        """Mark start of a pipeline stage."""
        self.stage_times[f"{stage_name}_start"] = time.time()

    def end_stage(self, stage_name: str) -> None:
        """Mark end of a pipeline stage and record duration."""
        start_key = f"{stage_name}_start"
        if start_key in self.stage_times:
            duration = time.time() - self.stage_times[start_key]
            self.stage_times[stage_name] = duration

    def record_error(self, stage_name: str, error: str) -> None:
        """Record stage error."""
        self.stage_errors[stage_name] = error

    def get_summary(self) -> Dict[str, Any]:
        """Get timing and error summary."""
        total_time = sum(v for k, v in self.stage_times.items() if not k.endswith("_start"))
        return {
            "total_time_seconds": total_time,
            "stage_times": {k: v for k, v in self.stage_times.items() if not k.endswith("_start")},
            "errors": self.stage_errors,
        }


def process_call(call_id: str) -> None:
    """
    End-to-end pipeline: download → transcribe → metrics → LLM analysis → scoring → store.

    Includes:
    - Transaction management with rollback on failure
    - Comprehensive error handling
    - Stage-level metrics tracking
    - Idempotency checks
    - Resource cleanup
    """
    db = SessionLocal()
    metrics_tracker = PipelineMetrics()
    metrics_tracker.start_time = time.time()
    audio_path: Optional[str] = None

    try:
        # Check if call exists and is not already processed
        call = db.query(models.Call).filter(models.Call.id == call_id).first()
        if not call:
            raise ValueError(f"Call {call_id} not found")

        # Idempotency: don't reprocess completed calls
        if call.status == models.CallStatus.completed:
            logger.warning(f"Call {call_id} already completed, skipping")
            return

        # Mark as processing
        call.status = models.CallStatus.processing
        db.commit()

        logger.info(f"{'='*80}")
        logger.info(f"Starting pipeline for call {call_id}")
        logger.info(f"Recording URL: {call.recording_url}")
        logger.info(f"{'='*80}")

        # 1. Download audio from URL
        try:
            metrics_tracker.start_stage("audio_download")
            logger.info("📥 Step 1: Downloading audio from URL...")
            audio_path = download_audio(call.recording_url)
            file_size = os.path.getsize(audio_path)
            metrics_tracker.end_stage("audio_download")
            logger.info(f"✅ Audio downloaded successfully!")
            logger.info(f"   File: {audio_path}")
            logger.info(f"   Size: {file_size} bytes")
        except Exception as e:
            metrics_tracker.record_error("audio_download", str(e))
            logger.error(f"❌ Audio download FAILED: {type(e).__name__}: {e}")
            audio_path = None

        try:
            # 2. Transcribe audio with Whisper
            try:
                metrics_tracker.start_stage("transcription")
                logger.info("Step 2: Transcribing audio with Whisper")

                # Use Whisper for transcription
                STTProvider = _get_transcription_provider()
                logger.info(f"Using transcription provider: {STTProvider.__name__}")
                stt_provider = STTProvider()

                if audio_path:
                    logger.info(f"🎤 Step 2: Transcribing with Whisper...")
                    logger.info(f"   Provider: {STTProvider.__name__}")
                    logger.info(f"   Audio file: {audio_path}")
                    logger.info(f"   File size: {os.path.getsize(audio_path)} bytes")
                    segments = stt_provider.transcribe(audio_path)
                    logger.info(f"✅ Whisper transcription complete!")
                    logger.info(f"   Segments: {len(segments)}")
                    if segments:
                        logger.info(f"   First segment: {segments[0].get('text', '')[:100]}")
                else:
                    # Fallback: Try to transcribe from URL directly
                    logger.error(f"❌ No audio file - URL transcription not supported")
                    raise PipelineStageError("Audio download failed, cannot proceed")

                if not segments:
                    raise ValueError("No speech detected in audio")

                metrics_tracker.end_stage("transcription")
                logger.info("Transcription complete: %d segments", len(segments))
            except Exception as e:
                metrics_tracker.record_error("transcription", str(e))
                raise PipelineStageError(f"Transcription failed: {e}") from e

            # Store transcript
            try:
                metrics_tracker.start_stage("transcript_storage")
                # Create mock raw response for analysis
                raw_response = {
                    "text": " ".join([s.get("text", "") for s in segments]),
                    "segments": [{"text": s.get("text", ""), "start": s.get("start_s", 0), "end": s.get("end_s", 0)} for s in segments]
                }
                transcript = models.Transcript(
                    call_id=call.id,
                    provider=STTProvider.__name__,  # Use actual provider (LocalWhisperProvider, GoogleSTTProvider, etc)
                    raw_transcript_json=raw_response,
                    diarized_segments=segments,
                )
                db.add(transcript)
                db.flush()
                metrics_tracker.end_stage("transcript_storage")
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("transcript_storage", str(e))
                raise PipelineStageError(f"Failed to store transcript: {e}") from e

            # 3. Compute metrics
            try:
                metrics_tracker.start_stage("metrics_computation")
                logger.info("Step 3: Computing metrics")
                talk_ratios = metrics.compute_talk_ratios(segments)
                call_duration = sum((seg.get("end_s", 0) - seg.get("start_s", 0)) for seg in segments)

                call_metrics = models.CallMetrics(
                    call_id=call.id,
                    duration_seconds=call_duration,
                    dietician_talk_ratio_pct=talk_ratios.get("dietician_pct", 0),
                    patient_talk_ratio_pct=talk_ratios.get("patient_pct", 0),
                    interruption_count=metrics.compute_interruptions(segments),
                    avg_response_latency_seconds=metrics.compute_response_latency(segments),
                    time_to_first_plan_mention_seconds=metrics.compute_time_to_first_plan(segments),
                    silence_pct=metrics.compute_silence_pct(segments, call_duration),
                    off_topic_time_pct=metrics.compute_off_topic_pct(segments),
                )
                db.add(call_metrics)
                db.flush()
                metrics_tracker.end_stage("metrics_computation")

                # Update call duration if not provided
                if not call.call_duration_seconds:
                    call.call_duration_seconds = int(call_duration)
                logger.info("Metrics computed: duration=%.1fs, talk_ratio=%.1f%%", call_duration, talk_ratios.get("dietician_pct", 0))
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("metrics_computation", str(e))
                raise PipelineStageError(f"Metrics computation failed: {e}") from e

            # 4. Run LLM analysis
            try:
                metrics_tracker.start_stage("llm_analysis")
                logger.info("Step 4: Running LLM rubric analysis")
                LLMProvider = _get_llm_provider()
                # GeminiLLMProvider takes api_key, OllamaLocalProvider doesn't
                if LLMProvider.__name__ == 'GeminiLLMProvider':
                    llm_provider = LLMProvider(settings.gemini_api_key)
                else:
                    llm_provider = LLMProvider()

                metrics_dict = {
                    "duration_seconds": call_duration,
                    "dietician_talk_ratio_pct": talk_ratios.get("dietician_pct", 0),
                    "patient_talk_ratio_pct": talk_ratios.get("patient_pct", 0),
                    "interruption_count": metrics.compute_interruptions(segments),
                    "avg_response_latency_seconds": metrics.compute_response_latency(segments),
                    "time_to_first_plan_mention_seconds": metrics.compute_time_to_first_plan(segments),
                    "silence_pct": metrics.compute_silence_pct(segments, call_duration),
                }

                try:
                    patient_condition = getattr(call, 'patient_condition', None) or "Diabetes"

                    logger.info(f"📊 Step 4a: Calling {LLMProvider.__name__}.analyze_all_dimensions()")
                    logger.info(f"   - Segments: {len(segments)}")
                    logger.info(f"   - Call ID: {call.id}")
                    logger.info(f"   - Patient Condition: {patient_condition}")

                    if LLMProvider.__name__ == 'ClinicalAnalyzer':
                        rubric_response = llm_provider.analyze_all_dimensions(
                            segments,
                            metrics_dict,
                            str(call.id),
                            call.dietician.name,
                            call.patient_id,
                            patient_condition=patient_condition
                        )
                    else:
                        rubric_response = llm_provider.analyze_all_dimensions(
                            segments,
                            metrics_dict,
                            str(call.id),
                            call.dietician.name,
                            call.patient_id,
                        )
                    logger.info(f"✅ Step 4a: LLM analysis successful, got {len(rubric_response.get('dimension_scores', {}))} dimensions")
                except Exception as llm_error:
                    logger.error(f"❌ Step 4a: LLM analysis FAILED!")
                    logger.error(f"   Exception type: {type(llm_error).__name__}")
                    logger.error(f"   Exception message: {str(llm_error)}")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    raise PipelineStageError(f"LLM analysis failed: {llm_error}") from llm_error

                metrics_tracker.end_stage("llm_analysis")
                logger.info("LLM analysis complete")
            except Exception as e:
                metrics_tracker.record_error("llm_analysis", str(e))
                raise PipelineStageError(f"LLM analysis failed: {e}") from e

            # Store dimension scores
            try:
                metrics_tracker.start_stage("score_storage")
                dimension_scores_db = {}
                for dimension, data in rubric_response.get("dimension_scores", {}).items():
                    score_obj = models.RubricScore(
                        call_id=call.id,
                        dimension=dimension,
                        score=data.get("score", 0),
                        evidence=data.get("evidence", []),
                        sub_criteria=data.get("sub_criteria_met", {}),
                        raw_llm_response=data,
                    )
                    db.add(score_obj)
                    dimension_scores_db[dimension] = data.get("score", 0)

                db.flush()
                metrics_tracker.end_stage("score_storage")
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("score_storage", str(e))
                raise PipelineStageError(f"Failed to store scores: {e}") from e

            # 4b. Generate QA Flags from SOP Violations (NEW - Clinical Analysis)
            try:
                metrics_tracker.start_stage("qa_flag_generation")
                logger.info("Step 4b: Generating QA flags from SOP violations")

                # Extract SOP compliance data if using ClinicalAnalyzer
                sop_compliance = rubric_response.get("sop_compliance", {})
                violations = sop_compliance.get("violations", [])

                # Generate QA flags from violations
                qa_alerts = rubric_response.get("qa_alerts", [])

                for violation in violations:
                    if violation.get("violated"):
                        flag_type = violation.get("check", "SOP Violation")
                        detail = violation.get("evidence", "")

                        qa_flag = models.QAFlag(
                            call_id=call.id,
                            flag_type=flag_type,
                            triggered=True,
                            detail=detail
                        )
                        db.add(qa_flag)
                        logger.info(f"   - QA Flag: {flag_type} (severity: critical)")

                # Also add alerts as QA flags if not already covered
                for alert in qa_alerts:
                    if alert.get("severity") == "critical":
                        qa_flag = models.QAFlag(
                            call_id=call.id,
                            flag_type=alert.get("title", "QA Alert"),
                            triggered=True,
                            detail=alert.get("description", "")
                        )
                        db.add(qa_flag)

                db.flush()
                logger.info(f"   - Total QA flags generated: {len(violations) + len([a for a in qa_alerts if a.get('severity') == 'critical'])}")
                metrics_tracker.end_stage("qa_flag_generation")
            except Exception as e:
                db.rollback()
                logger.warning(f"Failed to generate QA flags: {e} - continuing without flags")
                # Don't fail the pipeline for flag generation
                metrics_tracker.record_error("qa_flag_generation", str(e))

            # 5. Compute weighted score
            try:
                metrics_tracker.start_stage("weighted_scoring")
                logger.info("Step 5: Computing weighted score")
                clinical_safety_triggered = (
                    rubric_response.get("dimension_scores", {}).get("clinical_safety", {}).get("red_flag_detected")
                    and not rubric_response.get("dimension_scores", {}).get("clinical_safety", {}).get("handled_appropriately")
                )
                weighted_score = compute_weighted_score(dimension_scores_db, clinical_safety_triggered)

                # Update overall score in all rubric scores
                for score_obj in db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id):
                    score_obj.overall_weighted_score = weighted_score

                db.flush()
                metrics_tracker.end_stage("weighted_scoring")
                logger.info("Weighted score computed: %.2f (safety_gate=%s)", weighted_score, clinical_safety_triggered)
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("weighted_scoring", str(e))
                raise PipelineStageError(f"Weighted scoring failed: {e}") from e

            # 6. Evaluate flags
            try:
                metrics_tracker.start_stage("flag_evaluation")
                logger.info("Step 6: Evaluating QA flags")
                flags = evaluate_flags(metrics_dict, dimension_scores_db, rubric_response, db, call)

                for flag_data in flags:
                    flag_obj = models.QAFlag(
                        call_id=call.id,
                        flag_type=flag_data["flag_type"],
                        triggered=flag_data["triggered"],
                        detail=flag_data["detail"],
                    )
                    db.add(flag_obj)

                db.flush()
                triggered_count = sum(1 for f in flags if f["triggered"])
                metrics_tracker.end_stage("flag_evaluation")
                logger.info("Flag evaluation complete: %d/%d flags triggered", triggered_count, len(flags))
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("flag_evaluation", str(e))
                raise PipelineStageError(f"Flag evaluation failed: {e}") from e

            # 7. Generate feedback
            try:
                metrics_tracker.start_stage("feedback_generation")
                logger.info("Step 7: Generating feedback")
                feedback_bullets = generate_feedback_bullets(dimension_scores_db, rubric_response, flags)
                retraining_rec, retraining_reason = generate_retraining_recommendation(weighted_score, flags, call.dietician_id, db)

                feedback_note = models.FeedbackNote(
                    call_id=call.id,
                    bullet=" | ".join(feedback_bullets),
                    retraining_recommended=retraining_rec,
                    retraining_reason=retraining_reason,
                )
                db.add(feedback_note)

                db.flush()
                metrics_tracker.end_stage("feedback_generation")
                logger.info("Feedback generated: %d bullets, retraining=%s", len(feedback_bullets), retraining_rec)
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("feedback_generation", str(e))
                raise PipelineStageError(f"Feedback generation failed: {e}") from e

            # 8. Mark as complete
            try:
                metrics_tracker.start_stage("finalization")
                logger.info("Step 8: Finalizing")
                call.status = models.CallStatus.completed
                call.processed_at = datetime.utcnow()
                db.commit()
                metrics_tracker.end_stage("finalization")

                summary = metrics_tracker.get_summary()
                logger.info(
                    "Successfully completed processing for call %s. Score: %.2f (total_time: %.1fs)",
                    call_id, weighted_score, summary["total_time_seconds"]
                )
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("finalization", str(e))
                raise PipelineStageError(f"Finalization failed: {e}") from e

        finally:
            if audio_path:
                cleanup_audio(audio_path)

    except PipelineStageError as e:
        logger.error("Pipeline stage failed for call %s: %s", call_id, str(e), exc_info=True)
        try:
            call = db.query(models.Call).filter(models.Call.id == call_id).first()
            if call:
                call.status = models.CallStatus.failed
                call.error_message = str(e)
                db.commit()
        except SQLAlchemyError as db_err:
            logger.error("Failed to update call status in DB: %s", db_err)
            db.rollback()
        finally:
            summary = metrics_tracker.get_summary()
            logger.error("Pipeline failed after %.1fs. Errors: %s", summary["total_time_seconds"], summary["errors"])
        raise

    except Exception as e:
        logger.error("Unexpected error processing call %s: %s", call_id, str(e), exc_info=True)
        try:
            call = db.query(models.Call).filter(models.Call.id == call_id).first()
            if call:
                call.status = models.CallStatus.failed
                call.error_message = f"Unexpected error: {str(e)}"
                db.commit()
        except SQLAlchemyError as db_err:
            logger.error("Failed to update call status in DB: %s", db_err)
            db.rollback()
        raise

    finally:
        if audio_path:
            try:
                cleanup_audio(audio_path)
            except Exception as e:
                logger.warning("Error during audio cleanup: %s", e)
        try:
            db.close()
        except Exception as e:
            logger.warning("Error closing database session: %s", e)
