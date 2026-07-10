"""Tests for LLM providers and rubric analysis."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.llm.gemini import GeminiLLMProvider
from app.services.llm.claude_cli_analyzer import ClaudeCliAnalyzer
from app.services.llm.prompts import SYSTEM_PROMPT, format_rubric_prompt


class TestClaudeCliAnalyzer:
    def test_claude_cli_uses_print_mode(self):
        """Test that Claude CLI is invoked in non-interactive print mode."""
        provider = ClaudeCliAnalyzer()
        prompt = "Analyze this transcript"

        completed = MagicMock()
        completed.returncode = 0
        completed.stdout = '{"dimension_scores": {"clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": false, "handled_appropriately": null}}}'
        completed.stderr = ""

        with patch("pathlib.Path.home", return_value=Path("/tmp")):
            with patch("subprocess.run", return_value=completed) as mock_run:
                provider._call_claude_cli(prompt)

        assert mock_run.call_count == 1
        args = mock_run.call_args.args[0]
        assert args[0] == "claude"
        assert args[1] == "-p"
        assert args[2] == prompt
        assert args[3:5] == ["--output-format", "json"]


class TestGeminiLLMProvider:
    @pytest.fixture
    def provider_config(self):
        """Default configuration for Gemini provider."""
        return {
            "api_key": "test-api-key-12345"
        }

    @patch("app.services.llm.gemini.genai")
    def test_provider_initialization(self, mock_genai, provider_config):
        """Test provider initializes with API key."""
        mock_genai.GenerativeModel.return_value = MagicMock()

        provider = GeminiLLMProvider(api_key=provider_config["api_key"])

        assert provider.api_key == provider_config["api_key"]
        mock_genai.configure.assert_called_once_with(api_key=provider_config["api_key"])

    @patch("app.services.llm.gemini.genai")
    def test_provider_initialization_from_env(self, mock_genai):
        """Test provider initializes from environment variable."""
        mock_genai.GenerativeModel.return_value = MagicMock()

        with patch.dict("os.environ", {"GEMINI_API_KEY": "env-key"}):
            provider = GeminiLLMProvider()
            assert provider.api_key == "env-key"

    @patch("app.services.llm.gemini.genai")
    def test_provider_missing_api_key(self, mock_genai):
        """Test provider raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiLLMProvider()

    @patch("app.services.llm.gemini.genai")
    def test_analyze_all_dimensions_success(
        self, mock_genai, sample_segments, mock_rubric_response
    ):
        """Test successful LLM analysis of all dimensions."""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_rubric_response)
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        metrics = {
            "duration_seconds": 900,
            "dietician_talk_ratio_pct": 45,
            "patient_talk_ratio_pct": 55,
            "interruption_count": 2,
            "avg_response_latency_seconds": 1.5,
            "time_to_first_plan_mention_seconds": 300,
            "silence_pct": 3,
        }

        result = provider.analyze_all_dimensions(
            sample_segments,
            metrics,
            "call-123",
            "Dr. Test",
            "PAT001"
        )

        assert result["dimension_scores"] is not None
        assert len(result["dimension_scores"]) == 6
        assert "feedback_summary" in result

    @patch("app.services.llm.gemini.genai")
    def test_analyze_returns_all_dimensions(self, mock_genai, sample_segments):
        """Test that analysis returns all 6 dimensions."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        response_data = {
            "dimension_scores": {
                "discovery_assessment": {"score": 7.0, "evidence": [], "sub_criteria_met": {}},
                "empathy_communication": {"score": 8.0, "evidence": [], "sub_criteria_met": {}},
                "rushed_forced_detection": {"score": 3.0, "evidence": [], "is_forced": False},
                "adherence_counselling": {"score": 6.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 7.5, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            },
            "feedback_summary": ["Good call"]
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        result = provider.analyze_all_dimensions(
            sample_segments,
            {"duration_seconds": 900, "dietician_talk_ratio_pct": 50, "patient_talk_ratio_pct": 50},
            "call-123",
            "Dr. Test",
            "PAT001"
        )

        dimensions = set(result["dimension_scores"].keys())
        expected_dimensions = {
            "discovery_assessment",
            "empathy_communication",
            "rushed_forced_detection",
            "adherence_counselling",
            "consultation_completeness",
            "clinical_safety",
        }
        assert dimensions == expected_dimensions

    @patch("app.services.llm.gemini.genai")
    def test_analyze_invalid_json_response(self, mock_genai, sample_segments):
        """Test error handling for invalid JSON response."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = "Not valid JSON {broken"
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        with pytest.raises(json.JSONDecodeError):
            provider.analyze_all_dimensions(
                sample_segments,
                {"duration_seconds": 900},
                "call-123",
                "Dr. Test",
                "PAT001"
            )

    @patch("app.services.llm.gemini.genai")
    def test_analyze_api_error(self, mock_genai, sample_segments):
        """Test error handling for API failures."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API rate limit exceeded")
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiLLMProvider(api_key="test-key")

        with pytest.raises(Exception, match="API rate limit"):
            provider.analyze_all_dimensions(
                sample_segments,
                {"duration_seconds": 900},
                "call-123",
                "Dr. Test",
                "PAT001"
            )

    def test_format_transcript(self):
        """Test transcript formatting for LLM."""
        segments = [
            {"speaker": "speaker_0", "text": "Hello", "start_s": 0},
            {"speaker": "speaker_1", "text": "Hi", "start_s": 2},
        ]

        provider = GeminiLLMProvider(api_key="test-key")
        formatted = provider._format_transcript(segments)

        assert "[0.0s]" in formatted
        assert "Speaker 0" in formatted or "speaker_0" in formatted.lower()
        assert "Hello" in formatted
        assert "[2.0s]" in formatted
        assert "Hi" in formatted

    def test_format_transcript_with_unknown_speaker(self):
        """Test formatting handles unknown speakers."""
        segments = [
            {"speaker": "unknown", "text": "What happened?", "start_s": 5},
        ]

        provider = GeminiLLMProvider(api_key="test-key")
        formatted = provider._format_transcript(segments)

        assert "unknown" in formatted.lower()
        assert "What happened?" in formatted

    @patch("app.services.llm.gemini.genai")
    def test_score_extraction(self, mock_gemini, sample_segments):
        """Test that all dimension scores are properly extracted."""
        mock_model = MagicMock()
        mock_gemini.GenerativeModel.return_value = mock_model

        response_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 8.5,
                    "evidence": [
                        {"quote": "Tell me about your diet", "timestamp_s": 10.5}
                    ],
                    "sub_criteria_met": {
                        "medical_history": True,
                        "lifestyle_activity": True,
                        "dietary_habits": False,
                        "goal_alignment": True,
                        "allergy_screening": False,
                    }
                },
                "empathy_communication": {
                    "score": 9.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "empathy_tone": True,
                        "conversation_balance": True,
                        "active_listening": True,
                        "patient_engagement": True,
                        "sentiment": "positive"
                    }
                },
                "rushed_forced_detection": {
                    "score": 2.0,
                    "evidence": [],
                    "is_forced": False,
                    "is_missing_discovery": False
                },
                "adherence_counselling": {
                    "score": 7.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "motivation": True,
                        "importance_explained": True,
                        "practical_implementation": True,
                        "barriers_addressed": False
                    }
                },
                "consultation_completeness": {
                    "score": 8.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "goals_documented": True,
                        "bmi_reviewed": True,
                        "conditions_incorporated": True,
                        "followup_shared": False
                    }
                },
                "clinical_safety": {
                    "score": 0,
                    "evidence": [],
                    "red_flag_detected": False,
                    "handled_appropriately": None
                }
            },
            "feedback_summary": ["Excellent consultation quality"]
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        result = provider.analyze_all_dimensions(
            sample_segments,
            {"duration_seconds": 900, "dietician_talk_ratio_pct": 50, "patient_talk_ratio_pct": 50},
            "call-123",
            "Dr. Test",
            "PAT001"
        )

        # Verify all scores were extracted
        assert result["dimension_scores"]["discovery_assessment"]["score"] == 8.5
        assert result["dimension_scores"]["empathy_communication"]["score"] == 9.0
        assert result["dimension_scores"]["clinical_safety"]["red_flag_detected"] is False

    @patch("app.services.llm.gemini.genai")
    def test_evidence_extraction(self, mock_gemini, sample_segments):
        """Test that evidence citations are properly extracted."""
        mock_model = MagicMock()
        mock_gemini.GenerativeModel.return_value = mock_model

        response_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 7.5,
                    "evidence": [
                        {"quote": "Do you have any medical conditions?", "timestamp_s": 15},
                        {"quote": "What's your activity level?", "timestamp_s": 25},
                    ],
                    "sub_criteria_met": {"medical_history": True, "lifestyle_activity": True}
                },
                "empathy_communication": {"score": 8.0, "evidence": [], "sub_criteria_met": {}},
                "rushed_forced_detection": {"score": 3.0, "evidence": [], "is_forced": False},
                "adherence_counselling": {"score": 6.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 7.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            },
            "feedback_summary": []
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        result = provider.analyze_all_dimensions(
            sample_segments,
            {"duration_seconds": 900, "dietician_talk_ratio_pct": 50, "patient_talk_ratio_pct": 50},
            "call-123",
            "Dr. Test",
            "PAT001"
        )

        discovery = result["dimension_scores"]["discovery_assessment"]
        assert len(discovery["evidence"]) == 2
        assert discovery["evidence"][0]["quote"] == "Do you have any medical conditions?"
        assert discovery["evidence"][0]["timestamp_s"] == 15


class TestRubricPromptFormatting:
    def test_prompt_formatting_with_metrics(self):
        """Test that rubric prompt is correctly formatted with metrics."""
        transcript = "[0.0s] Dietician: Hello"
        metrics = {
            "duration_seconds": 900,
            "dietician_talk_ratio_pct": 45.5,
            "patient_talk_ratio_pct": 54.5,
            "interruption_count": 2,
            "avg_response_latency_seconds": 1.8,
            "time_to_first_plan_mention_seconds": 280.5,
            "silence_pct": 3.2,
        }

        prompt = format_rubric_prompt(transcript, metrics)

        assert "900s" in prompt
        assert "45.5%" in prompt
        assert "54.5%" in prompt
        assert "2" in prompt
        assert "280.5" in prompt
        assert "[0.0s] Dietician: Hello" in prompt

    def test_system_prompt_includes_hinglish(self):
        """Test that system prompt mentions Hinglish support."""
        assert "Hinglish" in SYSTEM_PROMPT or "hindi" in SYSTEM_PROMPT.lower()

    def test_system_prompt_defines_role(self):
        """Test that system prompt clearly defines the analyzer role."""
        assert "healthcare quality analyst" in SYSTEM_PROMPT.lower()
        assert "dietician" in SYSTEM_PROMPT.lower()

    def test_rubric_includes_all_dimensions(self):
        """Test that rubric prompt includes all 6 dimensions."""
        dimensions = [
            "Discovery & Assessment",
            "Empathy & Communication",
            "Forced/Rushed Consultation",
            "Adherence Counselling",
            "Consultation Completeness",
            "Clinical Safety"
        ]

        for dimension in dimensions:
            assert dimension in RUBRIC_PROMPT or dimension.lower().replace(" ", "_") in RUBRIC_PROMPT.lower()

    def test_rubric_includes_scoring_instructions(self):
        """Test that rubric includes clear scoring instructions."""
        assert "0-10" in RUBRIC_PROMPT or "0 to 10" in RUBRIC_PROMPT.lower()
        assert "score" in RUBRIC_PROMPT.lower()


class TestLLMIntegration:
    @patch("app.services.llm.gemini.genai")
    def test_full_lm_workflow(self, mock_gemini, sample_segments, mock_rubric_response):
        """Test complete LLM workflow from transcript to scored output."""
        mock_model = MagicMock()
        mock_gemini.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_rubric_response)
        mock_model.generate_content.return_value = mock_response

        provider = GeminiLLMProvider(api_key="test-key")

        # Simulate full pipeline
        metrics = {
            "duration_seconds": 900,
            "dietician_talk_ratio_pct": 45,
            "patient_talk_ratio_pct": 55,
            "interruption_count": 2,
            "avg_response_latency_seconds": 1.5,
            "time_to_first_plan_mention_seconds": 300,
            "silence_pct": 3,
        }

        result = provider.analyze_all_dimensions(
            sample_segments,
            metrics,
            "call-123",
            "Dr. Rajesh Kumar",
            "PAT001"
        )

        # Verify structure
        assert "dimension_scores" in result
        assert "feedback_summary" in result

        # Verify all dimensions have required fields
        for dimension, score_data in result["dimension_scores"].items():
            assert "score" in score_data
            assert "evidence" in score_data
            assert isinstance(score_data["score"], float)
            assert 0 <= score_data["score"] <= 10
