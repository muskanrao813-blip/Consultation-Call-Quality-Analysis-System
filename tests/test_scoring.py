"""Tests for scoring and flagging logic."""

import pytest
from app.services.scoring import compute_weighted_score, evaluate_flags


def test_compute_weighted_score():
    """Test weighted score calculation."""
    dimension_scores = {
        "discovery_assessment": 8.0,
        "empathy_communication": 7.0,
        "rushed_forced_detection": 3.0,  # Lower is better (inverse-scored)
        "adherence_counselling": 6.0,
        "consultation_completeness": 9.0,
    }

    score = compute_weighted_score(dimension_scores, clinical_safety_triggered=False)

    assert isinstance(score, float)
    assert 0 <= score <= 10
    assert score > 5  # Should be decent score with these inputs


def test_weighted_score_with_clinical_safety_gate():
    """Test that clinical safety gate caps score at 4.0."""
    dimension_scores = {
        "discovery_assessment": 10.0,
        "empathy_communication": 10.0,
        "rushed_forced_detection": 2.0,
        "adherence_counselling": 10.0,
        "consultation_completeness": 10.0,
    }

    score = compute_weighted_score(dimension_scores, clinical_safety_triggered=True)

    assert score <= 4.0


def test_evaluate_flags():
    """Test flag evaluation logic."""
    metrics_dict = {
        "duration_seconds": 600,
        "dietician_talk_ratio_pct": 60,
        "patient_talk_ratio_pct": 40,
        "interruption_count": 2,
        "avg_response_latency_seconds": 2.5,
        "time_to_first_plan_mention_seconds": 120,
        "silence_pct": 5,
        "off_topic_time_pct": 10,
    }

    dimension_scores = {
        "discovery_assessment": 7.0,
        "empathy_communication": 8.0,
        "rushed_forced_detection": 3.0,
        "adherence_counselling": 6.0,
        "consultation_completeness": 8.0,
    }

    rubric_data = {
        "dimension_scores": {
            "discovery_assessment": {
                "sub_criteria_met": {
                    "medical_history": True,
                    "lifestyle_activity": True,
                    "dietary_habits": True,
                    "goal_alignment": False,
                    "allergy_screening": False,
                }
            },
            "adherence_counselling": {
                "sub_criteria_met": {
                    "motivation": True,
                    "importance_explained": True,
                    "practical_implementation": False,
                    "barriers_addressed": False,
                }
            },
            "rushed_forced_detection": {
                "is_forced": False,
                "is_missing_discovery": False,
            },
            "clinical_safety": {
                "red_flag_detected": False,
                "handled_appropriately": None,
            },
        }
    }

    # Mock DB and call
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

    class MockCall:
        pass

    flags = evaluate_flags(metrics_dict, dimension_scores, rubric_data, MockDB(), MockCall())

    assert isinstance(flags, list)
    assert len(flags) == 8  # All 8 flag types
    assert all("flag_type" in f and "triggered" in f for f in flags)


def test_flags_forced_consultation():
    """Test that forced consultation flag triggers correctly."""
    metrics_dict = {
        "duration_seconds": 300,
        "dietician_talk_ratio_pct": 70,
        "patient_talk_ratio_pct": 30,
        "time_to_first_plan_mention_seconds": 60,  # Plan mentioned early
    }

    dimension_scores = {
        "discovery_assessment": 3.0,  # Low discovery
        "empathy_communication": 6.0,
        "rushed_forced_detection": 7.0,
        "adherence_counselling": 5.0,
        "consultation_completeness": 5.0,
    }

    rubric_data = {
        "dimension_scores": {
            "discovery_assessment": {
                "sub_criteria_met": {
                    "medical_history": False,
                    "lifestyle_activity": False,
                    "dietary_habits": True,
                    "goal_alignment": False,
                    "allergy_screening": False,
                }
            },
            "adherence_counselling": {"sub_criteria_met": {}},
            "rushed_forced_detection": {"is_forced": True, "is_missing_discovery": True},
            "clinical_safety": {"red_flag_detected": False},
        }
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
    forced_flag = [f for f in flags if f["flag_type"] == "Forced Consultation"][0]

    assert forced_flag["triggered"] is True


def test_flags_low_engagement():
    """Test low engagement flag."""
    metrics_dict = {
        "duration_seconds": 600,
        "dietician_talk_ratio_pct": 85,  # High dietician talk
        "patient_talk_ratio_pct": 15,   # Low patient talk (<20%)
        "time_to_first_plan_mention_seconds": 300,
    }

    dimension_scores = {
        "discovery_assessment": 5.0,
        "empathy_communication": 4.0,
        "rushed_forced_detection": 6.0,
        "adherence_counselling": 5.0,
        "consultation_completeness": 5.0,
    }

    rubric_data = {
        "dimension_scores": {
            "discovery_assessment": {"sub_criteria_met": {}},
            "adherence_counselling": {"sub_criteria_met": {}},
            "rushed_forced_detection": {"is_forced": False},
            "clinical_safety": {"red_flag_detected": False},
        }
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
    engagement_flag = [f for f in flags if f["flag_type"] == "Low Engagement"][0]

    assert engagement_flag["triggered"] is True
