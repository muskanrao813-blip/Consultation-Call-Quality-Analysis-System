"""Tests for complete scoring workflows with realistic call scenarios."""

import pytest
from sqlalchemy.orm import Session
from app.db import models
from app.services.scoring import (
    compute_weighted_score,
    evaluate_flags,
    generate_feedback_bullets,
    generate_retraining_recommendation,
)


class TestScoringWorkflows:
    """Test realistic scoring scenarios end-to-end."""

    def get_mock_db(self):
        """Create a mock database for testing."""
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
        return MockDB()

    def test_excellent_consultation_workflow(self):
        """Test scoring for an excellent quality consultation."""
        # High scores across all dimensions
        dimension_scores = {
            "discovery_assessment": 9.0,
            "empathy_communication": 9.5,
            "rushed_forced_detection": 1.5,  # Very low risk
            "adherence_counselling": 8.5,
            "consultation_completeness": 9.0,
        }

        # Excellent metrics
        metrics = {
            "duration_seconds": 1200,
            "dietician_talk_ratio_pct": 40.0,
            "patient_talk_ratio_pct": 60.0,
            "interruption_count": 0,
            "avg_response_latency_seconds": 1.2,
            "time_to_first_plan_mention_seconds": 600,
            "silence_pct": 1.0,
            "off_topic_time_pct": 0.0,
        }

        # Perfect rubric response
        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 9.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "medical_history": True,
                        "lifestyle_activity": True,
                        "dietary_habits": True,
                        "goal_alignment": True,
                        "allergy_screening": True,
                    }
                },
                "empathy_communication": {
                    "score": 9.5,
                    "evidence": [],
                    "sub_criteria_met": {
                        "empathy_tone": True,
                        "conversation_balance": True,
                        "active_listening": True,
                        "patient_engagement": True,
                        "sentiment": "positive"
                    }
                },
                "adherence_counselling": {
                    "score": 8.5,
                    "evidence": [],
                    "sub_criteria_met": {
                        "motivation": True,
                        "importance_explained": True,
                        "practical_implementation": True,
                        "barriers_addressed": True,
                    }
                },
                "consultation_completeness": {
                    "score": 9.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "goals_documented": True,
                        "bmi_reviewed": True,
                        "conditions_incorporated": True,
                        "followup_shared": True,
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

        # Compute weighted score
        weighted_score = compute_weighted_score(dimension_scores, clinical_safety_triggered=False)
        assert weighted_score > 8.0, "Excellent call should score > 8.0"

        # Evaluate flags
        flags = evaluate_flags(metrics, dimension_scores, rubric_data, self.get_mock_db(), None)
        triggered_flags = [f for f in flags if f["triggered"]]
        assert len(triggered_flags) == 0, "Excellent call should have no triggered flags"

        # Check retraining
        retraining, reason = generate_retraining_recommendation(
            weighted_score, flags, "dietician-1", self.get_mock_db()
        )
        assert retraining is False, "Excellent call should not trigger retraining"

    def test_poor_quality_consultation_workflow(self):
        """Test scoring for a poor quality consultation."""
        # Low scores across all dimensions
        dimension_scores = {
            "discovery_assessment": 2.0,
            "empathy_communication": 2.5,
            "rushed_forced_detection": 8.5,  # Very high risk
            "adherence_counselling": 1.0,
            "consultation_completeness": 2.0,
        }

        # Poor metrics
        metrics = {
            "duration_seconds": 180,
            "dietician_talk_ratio_pct": 85.0,
            "patient_talk_ratio_pct": 15.0,
            "interruption_count": 8,
            "avg_response_latency_seconds": 0.3,
            "time_to_first_plan_mention_seconds": 30,
            "silence_pct": 10.0,
            "off_topic_time_pct": 35.0,
        }

        # Poor rubric response
        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 2.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "medical_history": False,
                        "lifestyle_activity": False,
                        "dietary_habits": False,
                        "goal_alignment": False,
                        "allergy_screening": False,
                    }
                },
                "empathy_communication": {
                    "score": 2.5,
                    "evidence": [],
                    "sub_criteria_met": {
                        "empathy_tone": False,
                        "conversation_balance": False,
                        "active_listening": False,
                        "patient_engagement": False,
                        "sentiment": "negative"
                    }
                },
                "adherence_counselling": {
                    "score": 1.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "motivation": False,
                        "importance_explained": False,
                        "practical_implementation": False,
                        "barriers_addressed": False,
                    }
                },
                "consultation_completeness": {
                    "score": 2.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "goals_documented": False,
                        "bmi_reviewed": False,
                        "conditions_incorporated": False,
                        "followup_shared": False,
                    }
                },
                "rushed_forced_detection": {
                    "is_forced": True,
                    "is_missing_discovery": True,
                },
                "clinical_safety": {
                    "red_flag_detected": False,
                    "handled_appropriately": None,
                },
            }
        }

        # Compute weighted score
        weighted_score = compute_weighted_score(dimension_scores, clinical_safety_triggered=False)
        assert weighted_score < 4.0, "Poor call should score < 4.0"

        # Evaluate flags
        flags = evaluate_flags(metrics, dimension_scores, rubric_data, self.get_mock_db(), None)
        triggered_flags = [f for f in flags if f["triggered"]]
        assert len(triggered_flags) >= 5, "Poor call should trigger multiple flags"

        flag_types = [f["flag_type"] for f in triggered_flags]
        assert "Forced Consultation" in flag_types
        assert "Missing Discovery" in flag_types
        assert "Low Engagement" in flag_types

        # Check retraining (low score)
        retraining, reason = generate_retraining_recommendation(
            weighted_score, flags, "dietician-1", self.get_mock_db()
        )
        assert retraining is True, "Poor score should trigger retraining"

    def test_clinical_safety_gate_workflow(self):
        """Test that clinical safety gate caps score."""
        # High scores but with unhandled red flag
        dimension_scores = {
            "discovery_assessment": 9.0,
            "empathy_communication": 9.0,
            "rushed_forced_detection": 2.0,
            "adherence_counselling": 8.0,
            "consultation_completeness": 9.0,
        }

        metrics = {
            "duration_seconds": 900,
            "dietician_talk_ratio_pct": 40,
            "patient_talk_ratio_pct": 60,
            "interruption_count": 1,
            "avg_response_latency_seconds": 1.5,
            "time_to_first_plan_mention_seconds": 400,
            "silence_pct": 2.0,
            "off_topic_time_pct": 0.0,
        }

        # Red flag detected and NOT handled
        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {"score": 9.0, "evidence": [], "sub_criteria_met": {}},
                "empathy_communication": {"score": 9.0, "evidence": [], "sub_criteria_met": {}},
                "rushed_forced_detection": {"score": 2.0, "evidence": [], "is_forced": False},
                "adherence_counselling": {"score": 8.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 9.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {
                    "score": 0,
                    "evidence": [
                        {"quote": "Patient mentioned chest pain", "timestamp_s": 150}
                    ],
                    "red_flag_detected": True,
                    "handled_appropriately": False,  # NOT HANDLED - triggers gate
                },
            }
        }

        # Without gate: would be high score
        score_without_gate = compute_weighted_score(dimension_scores, clinical_safety_triggered=False)
        assert score_without_gate > 7.0

        # With gate: capped at 4.0
        score_with_gate = compute_weighted_score(dimension_scores, clinical_safety_triggered=True)
        assert score_with_gate <= 4.0, "Clinical safety gate should cap score at 4.0"

        # Verify flag is triggered
        flags = evaluate_flags(metrics, dimension_scores, rubric_data, self.get_mock_db(), None)
        safety_flags = [f for f in flags if f["flag_type"] == "Clinical Safety Concern"]
        assert len(safety_flags) > 0
        assert safety_flags[0]["triggered"] is True

        # Should trigger retraining
        retraining, reason = generate_retraining_recommendation(
            score_with_gate, flags, "dietician-1", self.get_mock_db()
        )
        assert retraining is True
        assert "safety" in reason.lower()

    def test_forced_consultation_detection_workflow(self):
        """Test detection of forced/rushed consultations."""
        dimension_scores = {
            "discovery_assessment": 3.0,  # Very low discovery
            "empathy_communication": 4.0,
            "rushed_forced_detection": 8.0,  # High risk
            "adherence_counselling": 3.0,
            "consultation_completeness": 2.0,
        }

        # Forced: plan mentioned very early with little discovery
        metrics = {
            "duration_seconds": 240,  # 4 minutes - short
            "dietician_talk_ratio_pct": 75.0,  # Dietician talks too much
            "patient_talk_ratio_pct": 25.0,
            "interruption_count": 3,
            "avg_response_latency_seconds": 0.8,
            "time_to_first_plan_mention_seconds": 60,  # Plan within 1 minute
            "silence_pct": 5.0,
            "off_topic_time_pct": 0.0,
        }

        rubric_data = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 3.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "medical_history": False,
                        "lifestyle_activity": False,
                        "dietary_habits": True,
                        "goal_alignment": False,
                        "allergy_screening": False,
                    }
                },
                "empathy_communication": {"score": 4.0, "evidence": [], "sub_criteria_met": {}},
                "rushed_forced_detection": {
                    "score": 8.0,
                    "evidence": [],
                    "is_forced": True,  # Marked as forced
                    "is_missing_discovery": True,
                },
                "adherence_counselling": {"score": 3.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 2.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            }
        }

        flags = evaluate_flags(metrics, dimension_scores, rubric_data, self.get_mock_db(), None)

        # Verify forced consultation flag
        forced_flags = [f for f in flags if f["flag_type"] == "Forced Consultation"]
        assert len(forced_flags) > 0
        assert forced_flags[0]["triggered"] is True

        # Verify missing discovery flag
        discovery_flags = [f for f in flags if f["flag_type"] == "Missing Discovery"]
        assert len(discovery_flags) > 0
        assert discovery_flags[0]["triggered"] is True

        # Verify low engagement flag
        engagement_flags = [f for f in flags if f["flag_type"] == "Low Engagement"]
        assert engagement_flags[0]["triggered"] is True

    def test_feedback_generation_workflow(self):
        """Test feedback generation for different scenarios."""
        # Scenario 1: Low discovery
        dimension_scores_1 = {
            "discovery_assessment": 3.0,
            "empathy_communication": 7.0,
            "rushed_forced_detection": 6.0,
            "adherence_counselling": 5.0,
            "consultation_completeness": 4.0,
        }

        rubric_data_1 = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 3.0,
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "empathy_communication": {
                    "score": 7.0,
                    "evidence": [],
                    "sub_criteria_met": {"sentiment": "neutral"}
                },
                "rushed_forced_detection": {"score": 6.0, "evidence": [], "is_forced": False},
                "adherence_counselling": {"score": 5.0, "evidence": [], "sub_criteria_met": {}},
                "consultation_completeness": {"score": 4.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            }
        }

        flags_1 = evaluate_flags(
            {"duration_seconds": 600, "dietician_talk_ratio_pct": 50, "patient_talk_ratio_pct": 50},
            dimension_scores_1,
            rubric_data_1,
            self.get_mock_db(),
            None
        )

        bullets_1 = generate_feedback_bullets(dimension_scores_1, rubric_data_1, flags_1)
        assert len(bullets_1) > 0
        assert any("discovery" in b.lower() for b in bullets_1)

        # Scenario 2: Good communication but poor adherence
        dimension_scores_2 = {
            "discovery_assessment": 7.0,
            "empathy_communication": 8.5,
            "rushed_forced_detection": 3.0,
            "adherence_counselling": 2.0,  # Low adherence
            "consultation_completeness": 6.0,
        }

        rubric_data_2 = {
            "dimension_scores": {
                "discovery_assessment": {"score": 7.0, "evidence": [], "sub_criteria_met": {}},
                "empathy_communication": {
                    "score": 8.5,
                    "evidence": [],
                    "sub_criteria_met": {"sentiment": "positive"}
                },
                "rushed_forced_detection": {"score": 3.0, "evidence": [], "is_forced": False},
                "adherence_counselling": {
                    "score": 2.0,
                    "evidence": [],
                    "sub_criteria_met": {
                        "motivation": False,
                        "importance_explained": False,
                        "practical_implementation": False,
                        "barriers_addressed": False,
                    }
                },
                "consultation_completeness": {"score": 6.0, "evidence": [], "sub_criteria_met": {}},
                "clinical_safety": {"score": 0, "evidence": [], "red_flag_detected": False},
            }
        }

        flags_2 = evaluate_flags(
            {"duration_seconds": 600, "dietician_talk_ratio_pct": 50, "patient_talk_ratio_pct": 50},
            dimension_scores_2,
            rubric_data_2,
            self.get_mock_db(),
            None
        )

        bullets_2 = generate_feedback_bullets(dimension_scores_2, rubric_data_2, flags_2)
        assert any("adherence" in b.lower() for b in bullets_2)
