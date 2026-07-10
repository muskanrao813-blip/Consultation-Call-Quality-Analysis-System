"""Integration tests for the full processing pipeline."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.db import models
from app.services import metrics
from app.services.scoring import (
    compute_weighted_score,
    evaluate_flags,
    generate_retraining_recommendation,
    generate_feedback_bullets,
)


class TestMetricsIntegration:
    def test_full_metrics_computation(self, sample_segments):
        """Test computing all metrics from a sample transcript."""
        total_duration = sample_segments[-1]["end_s"]

        talk_ratios = metrics.compute_talk_ratios(sample_segments)
        interruptions = metrics.compute_interruptions(sample_segments)
        latency = metrics.compute_response_latency(sample_segments)
        silence_pct = metrics.compute_silence_pct(sample_segments, total_duration)
        time_to_plan = metrics.compute_time_to_first_plan(sample_segments)
        off_topic = metrics.compute_off_topic_pct(sample_segments)
        patient_words = metrics.count_patient_words(sample_segments)

        # All should return sensible values
        assert 0 <= talk_ratios["dietician_pct"] <= 100
        assert 0 <= talk_ratios["patient_pct"] <= 100
        assert talk_ratios["dietician_pct"] + talk_ratios["patient_pct"] == 100.0
        assert interruptions >= 0
        assert latency >= 0
        assert 0 <= silence_pct <= 100
        assert time_to_plan is not None and time_to_plan >= 0
        assert 0 <= off_topic <= 100
        assert patient_words > 0

    def test_talk_ratio_calculation(self, sample_segments):
        """Verify talk ratio calculation logic."""
        ratios = metrics.compute_talk_ratios(sample_segments)

        # speaker_0 = dietician, speaker_1 = patient
        # Total time: 0-29s = 29s
        # Dietician: 0-3, 8-12, 19-26 = 3+4+7 = 14s
        # Patient: 4-7, 13-18, 27-29 = 3+5+2 = 10s
        # Dietician: 14/24 ≈ 58%, Patient: 10/24 ≈ 42%

        assert ratios["dietician_pct"] > 50
        assert ratios["patient_pct"] < 50


class TestScoringIntegration:
    def test_weighted_score_calculation(self):
        """Test weighted score computation with realistic dimensions."""
        dimension_scores = {
            "discovery_assessment": 7.0,
            "empathy_communication": 8.5,
            "rushed_forced_detection": 2.0,  # Low risk (good)
            "adherence_counselling": 6.0,
            "consultation_completeness": 7.5,
        }

        score = compute_weighted_score(dimension_scores, clinical_safety_triggered=False)

        # Should be weighted average with inverse rushed score
        # 0.20*7 + 0.20*8.5 + 0.15*(10-2) + 0.20*6 + 0.25*7.5
        # = 1.4 + 1.7 + 1.2 + 1.2 + 1.875 = 7.375

        assert 7.0 <= score <= 8.0

    def test_clinical_safety_gate(self):
        """Test that clinical safety gate caps score at 4.0."""
        high_dimension_scores = {
            "discovery_assessment": 10.0,
            "empathy_communication": 10.0,
            "rushed_forced_detection": 0.0,
            "adherence_counselling": 10.0,
            "consultation_completeness": 10.0,
        }

        score_without_safety = compute_weighted_score(high_dimension_scores, clinical_safety_triggered=False)
        score_with_safety = compute_weighted_score(high_dimension_scores, clinical_safety_triggered=True)

        assert score_without_safety > 8.0
        assert score_with_safety <= 4.0

    def test_flag_evaluation_good_call(self, test_db):
        """Test flag evaluation on a good quality call."""
        metrics_dict = {
            "duration_seconds": 900,
            "dietician_talk_ratio_pct": 45,
            "patient_talk_ratio_pct": 55,
            "interruption_count": 1,
            "avg_response_latency_seconds": 1.5,
            "time_to_first_plan_mention_seconds": 300,
            "silence_pct": 3,
            "off_topic_time_pct": 5,
        }

        dimension_scores = {
            "discovery_assessment": 8.5,
            "empathy_communication": 8.0,
            "rushed_forced_detection": 2.0,  # Low risk
            "adherence_counselling": 7.5,
            "consultation_completeness": 8.0,
        }

        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 8.5,
                    "sub_criteria_met": {
                        "medical_history": True,
                        "lifestyle_activity": True,
                        "dietary_habits": True,
                        "goal_alignment": True,
                        "allergy_screening": False,
                    },
                },
                "empathy_communication": {
                    "score": 8.0,
                    "sub_criteria_met": {
                        "empathy_tone": True,
                        "conversation_balance": True,
                        "active_listening": True,
                        "patient_engagement": True,
                        "sentiment": "positive",
                    },
                },
                "adherence_counselling": {
                    "score": 7.5,
                    "sub_criteria_met": {
                        "motivation": True,
                        "importance_explained": True,
                        "practical_implementation": True,
                        "barriers_addressed": True,
                    },
                },
                "consultation_completeness": {
                    "score": 8.0,
                    "sub_criteria_met": {
                        "goals_documented": True,
                        "bmi_reviewed": True,
                        "conditions_incorporated": True,
                        "followup_shared": True,
                    },
                },
                "rushed_forced_detection": {
                    "is_forced": False,
                    "is_missing_discovery": False,
                },
                "clinical_safety": {
                    "red_flag_detected": False,
                    "handled_appropriately": None,
                },
            },
        }

        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return []

        flags = evaluate_flags(metrics_dict, dimension_scores, rubric_data, MockDB(), None)

        # Good call should have no triggered flags
        triggered_flags = [f for f in flags if f["triggered"]]
        assert len(triggered_flags) == 0

    def test_flag_evaluation_poor_call(self):
        """Test flag evaluation on a poor quality call."""
        metrics_dict = {
            "duration_seconds": 300,
            "dietician_talk_ratio_pct": 80,
            "patient_talk_ratio_pct": 20,  # Low engagement
            "interruption_count": 5,
            "avg_response_latency_seconds": 0.5,
            "time_to_first_plan_mention_seconds": 60,  # Early plan mention
            "silence_pct": 10,
            "off_topic_time_pct": 0,
        }

        dimension_scores = {
            "discovery_assessment": 2.0,  # Poor discovery
            "empathy_communication": 3.0,
            "rushed_forced_detection": 8.0,  # High risk
            "adherence_counselling": 1.0,
            "consultation_completeness": 2.0,
        }

        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 2.0,
                    "sub_criteria_met": {
                        "medical_history": False,
                        "lifestyle_activity": False,
                        "dietary_habits": False,
                        "goal_alignment": False,
                        "allergy_screening": False,
                    },
                },
                "adherence_counselling": {
                    "score": 1.0,
                    "sub_criteria_met": {
                        "motivation": False,
                        "importance_explained": False,
                        "practical_implementation": False,
                        "barriers_addressed": False,
                    },
                },
                "rushed_forced_detection": {
                    "is_forced": True,
                    "is_missing_discovery": True,
                },
                "clinical_safety": {
                    "red_flag_detected": False,
                },
            },
        }

        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return []

        flags = evaluate_flags(metrics_dict, dimension_scores, rubric_data, MockDB(), None)

        # Poor call should have multiple triggered flags
        triggered_flags = [f for f in flags if f["triggered"]]
        assert len(triggered_flags) >= 3

        flag_types = [f["flag_type"] for f in triggered_flags]
        assert "Forced Consultation" in flag_types
        assert "Missing Discovery" in flag_types
        assert "Poor Adherence Counselling" in flag_types
        assert "Low Engagement" in flag_types

    def test_feedback_generation(self, mock_rubric_response):
        """Test natural-language feedback generation."""
        dimension_scores = {
            "discovery_assessment": 7.5,
            "empathy_communication": 8.0,
            "rushed_forced_detection": 3.0,
            "adherence_counselling": 5.0,
            "consultation_completeness": 6.5,
        }

        flags = [
            {"flag_type": "Forced Consultation", "triggered": False},
            {"flag_type": "Missing Discovery", "triggered": True},
            {"flag_type": "Low Engagement", "triggered": False},
            {"flag_type": "Poor Adherence Counselling", "triggered": True},
            {"flag_type": "Off-Topic/Non-Consultative Time", "triggered": False},
            {"flag_type": "Appointment Not Delivered", "triggered": False},
            {"flag_type": "Clinical Safety Concern", "triggered": False},
            {"flag_type": "Templated/Generic Plan Suspected", "triggered": False},
        ]

        bullets = generate_feedback_bullets(dimension_scores, mock_rubric_response, flags)

        assert len(bullets) > 0
        assert all(isinstance(b, str) for b in bullets)
        assert any("discovery" in b.lower() for b in bullets)

    def test_retraining_recommendation_low_score(self, test_db):
        """Test that low overall score triggers retraining."""
        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return []

        flags = [
            {"flag_type": "Missing Discovery", "triggered": True},
            {"flag_type": "Low Engagement", "triggered": True},
        ]

        retraining, reason = generate_retraining_recommendation(
            overall_score=4.5,
            flags=flags,
            dietician_id="test_dietician_id",
            db=MockDB()
        )

        assert retraining is True
        assert "score" in reason.lower() or "threshold" in reason.lower()

    def test_retraining_recommendation_clinical_safety(self, test_db):
        """Test that clinical safety concern triggers retraining."""
        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return []

        flags = [
            {"flag_type": "Clinical Safety Concern", "triggered": True},
        ]

        retraining, reason = generate_retraining_recommendation(
            overall_score=7.0,  # Good score but safety issue
            flags=flags,
            dietician_id="test_dietician_id",
            db=MockDB()
        )

        assert retraining is True
        assert "safety" in reason.lower()
