"""End-to-end pipeline tests with mocked external services."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Dietician, Call, Transcript, CallMetrics, RubricScore, QAFlag, FeedbackNote
from app.services.pipeline import process_call


@pytest.fixture
def test_db_e2e():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


class TestPipelineEndToEnd:
    @pytest.fixture
    def sample_call(self, test_db_e2e):
        """Create a sample call in the database."""
        dietician = Dietician(
            name="Dr. Test Dietician",
            external_id="TEST001",
            needs_admin_confirmation=False,
        )
        test_db_e2e.add(dietician)
        test_db_e2e.flush()

        call = Call(
            dietician_id=dietician.id,
            patient_id="PAT001",
            patient_name="Test Patient",
            appointment_id="APT001",
            call_datetime=datetime.utcnow(),
            recording_url="https://example.com/test_call.wav",
            status="pending",
        )
        test_db_e2e.add(call)
        test_db_e2e.commit()

        return call

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.GeminiLLMProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_full_workflow(
        self,
        mock_cleanup,
        mock_gemini,
        mock_stt,
        mock_download,
        test_db_e2e,
        sample_call,
        sample_segments,
        mock_rubric_response,
    ):
        """Test complete pipeline from download to scoring."""
        # Mock audio download
        mock_download.return_value = "/tmp/test_audio.wav"

        # Mock transcription provider
        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = sample_segments
        mock_stt_instance.get_raw_response.return_value = {"test": "response"}
        mock_stt.return_value = mock_stt_instance

        # Mock LLM provider
        mock_gemini_instance = MagicMock()
        mock_gemini_instance.analyze_all_dimensions.return_value = mock_rubric_response
        mock_gemini.return_value = mock_gemini_instance

        # Patch the SessionLocal to use our test DB
        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            process_call(str(sample_call.id))

        # Verify call was updated
        updated_call = test_db_e2e.query(Call).filter(Call.id == sample_call.id).first()
        assert updated_call.status.value == "completed"
        assert updated_call.processed_at is not None
        assert updated_call.call_duration_seconds is not None

        # Verify transcript was stored
        transcript = test_db_e2e.query(Transcript).filter(Transcript.call_id == sample_call.id).first()
        assert transcript is not None
        assert transcript.diarized_segments == sample_segments

        # Verify metrics were computed
        metrics = test_db_e2e.query(CallMetrics).filter(CallMetrics.call_id == sample_call.id).first()
        assert metrics is not None
        assert metrics.dietician_talk_ratio_pct > 0
        assert metrics.patient_talk_ratio_pct > 0
        assert metrics.duration_seconds > 0

        # Verify rubric scores were stored
        rubric_scores = test_db_e2e.query(RubricScore).filter(RubricScore.call_id == sample_call.id).all()
        assert len(rubric_scores) == 6  # All 6 dimensions

        # Verify QA flags were evaluated
        qa_flags = test_db_e2e.query(QAFlag).filter(QAFlag.call_id == sample_call.id).all()
        assert len(qa_flags) == 8  # All 8 flag types

        # Verify feedback notes were generated
        feedback = test_db_e2e.query(FeedbackNote).filter(FeedbackNote.call_id == sample_call.id).first()
        assert feedback is not None
        assert len(feedback.bullet) > 0

        # Verify cleanup was called
        mock_cleanup.assert_called_once_with("/tmp/test_audio.wav")

    @patch("app.services.pipeline.download_audio")
    def test_pipeline_download_failure(self, mock_download, test_db_e2e, sample_call):
        """Test pipeline handles download failures gracefully."""
        mock_download.side_effect = Exception("Network error")

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            with pytest.raises(Exception, match="Network error"):
                process_call(str(sample_call.id))

        # Call should be marked as failed
        updated_call = test_db_e2e.query(Call).filter(Call.id == sample_call.id).first()
        assert updated_call.status.value == "failed"
        assert updated_call.error_message is not None

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_transcription_failure(
        self, mock_cleanup, mock_stt, mock_download, test_db_e2e, sample_call
    ):
        """Test pipeline handles transcription failures."""
        mock_download.return_value = "/tmp/test_audio.wav"

        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.side_effect = Exception("STT API error")
        mock_stt.return_value = mock_stt_instance

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            with pytest.raises(Exception, match="STT API error"):
                process_call(str(sample_call.id))

        updated_call = test_db_e2e.query(Call).filter(Call.id == sample_call.id).first()
        assert updated_call.status.value == "failed"

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.GeminiLLMProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_llm_failure_fallback(
        self,
        mock_cleanup,
        mock_gemini,
        mock_stt,
        mock_download,
        test_db_e2e,
        sample_call,
        sample_segments,
    ):
        """Test pipeline handles LLM failures gracefully."""
        mock_download.return_value = "/tmp/test_audio.wav"

        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = sample_segments
        mock_stt_instance.get_raw_response.return_value = {}
        mock_stt.return_value = mock_stt_instance

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.analyze_all_dimensions.side_effect = Exception("LLM API error")
        mock_gemini.return_value = mock_gemini_instance

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            with pytest.raises(Exception, match="LLM API error"):
                process_call(str(sample_call.id))

        updated_call = test_db_e2e.query(Call).filter(Call.id == sample_call.id).first()
        assert updated_call.status.value == "failed"

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.GeminiLLMProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_stores_all_scores(
        self,
        mock_cleanup,
        mock_gemini,
        mock_stt,
        mock_download,
        test_db_e2e,
        sample_call,
        sample_segments,
        mock_rubric_response,
    ):
        """Test pipeline stores all rubric dimension scores."""
        mock_download.return_value = "/tmp/test_audio.wav"

        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = sample_segments
        mock_stt_instance.get_raw_response.return_value = {}
        mock_stt.return_value = mock_stt_instance

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.analyze_all_dimensions.return_value = mock_rubric_response
        mock_gemini.return_value = mock_gemini_instance

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            process_call(str(sample_call.id))

        # Verify all 6 dimensions were stored
        scores = test_db_e2e.query(RubricScore).filter(RubricScore.call_id == sample_call.id).all()
        dimensions = {s.dimension for s in scores}

        expected_dimensions = {
            "discovery_assessment",
            "empathy_communication",
            "rushed_forced_detection",
            "adherence_counselling",
            "consultation_completeness",
            "clinical_safety",
        }

        assert dimensions == expected_dimensions

        # Verify each score has evidence
        for score in scores:
            assert score.raw_llm_response is not None
            assert isinstance(score.sub_criteria, dict)

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.GeminiLLMProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_clinical_safety_gate(
        self,
        mock_cleanup,
        mock_gemini,
        mock_stt,
        mock_download,
        test_db_e2e,
        sample_call,
        sample_segments,
        mock_rubric_response,
    ):
        """Test that clinical safety concerns trigger appropriate flags."""
        mock_download.return_value = "/tmp/test_audio.wav"

        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = sample_segments
        mock_stt_instance.get_raw_response.return_value = {}
        mock_stt.return_value = mock_stt_instance

        # Modify response to trigger safety concern
        safety_response = mock_rubric_response.copy()
        safety_response["dimension_scores"]["clinical_safety"] = {
            "score": 0,
            "evidence": [{"quote": "Patient mentioned chest pain", "timestamp_s": 120}],
            "red_flag_detected": True,
            "handled_appropriately": False,  # Not handled properly
        }

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.analyze_all_dimensions.return_value = safety_response
        mock_gemini.return_value = mock_gemini_instance

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            process_call(str(sample_call.id))

        # Verify clinical safety flag was triggered
        flags = test_db_e2e.query(QAFlag).filter(
            QAFlag.call_id == sample_call.id,
            QAFlag.flag_type == "Clinical Safety Concern",
        ).all()

        assert len(flags) > 0
        assert flags[0].triggered is True

        # Verify overall score was capped due to safety gate
        scores = test_db_e2e.query(RubricScore).filter(RubricScore.call_id == sample_call.id).all()
        overall_scores = [s.overall_weighted_score for s in scores if s.overall_weighted_score is not None]
        assert any(score <= 4.0 for score in overall_scores)

    @patch("app.services.pipeline.download_audio")
    @patch("app.services.pipeline.GoogleSTTProvider")
    @patch("app.services.pipeline.GeminiLLMProvider")
    @patch("app.services.pipeline.cleanup_audio")
    def test_pipeline_retraining_flag_low_score(
        self,
        mock_cleanup,
        mock_gemini,
        mock_stt,
        mock_download,
        test_db_e2e,
        sample_call,
        sample_segments,
    ):
        """Test pipeline flags for retraining when score is low."""
        mock_download.return_value = "/tmp/test_audio.wav"

        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = sample_segments
        mock_stt_instance.get_raw_response.return_value = {}
        mock_stt.return_value = mock_stt_instance

        # Create response with low scores
        low_score_response = {
            "dimension_scores": {
                "discovery_assessment": {"score": 2.0, "evidence": [], "sub_criteria_met": {}},
                "empathy_communication": {"score": 3.0, "evidence": [], "sub_criteria_met": {}},
                "rushed_forced_detection": {"score": 8.0, "evidence": [], "is_forced": True},
                "adherence_counselling": {"score": 1.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 2.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            },
            "feedback_summary": ["Poor quality call"],
        }

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.analyze_all_dimensions.return_value = low_score_response
        mock_gemini.return_value = mock_gemini_instance

        with patch("app.services.pipeline.SessionLocal", return_value=test_db_e2e):
            process_call(str(sample_call.id))

        # Verify retraining was recommended
        feedback = test_db_e2e.query(FeedbackNote).filter(FeedbackNote.call_id == sample_call.id).first()
        assert feedback is not None
        assert feedback.retraining_recommended is True
