"""Pytest configuration and shared fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_segments():
    """Sample diarized transcript segments."""
    return [
        {"speaker": "speaker_0", "text": "Hello, how are you today?", "start_s": 0, "end_s": 3},
        {"speaker": "speaker_1", "text": "I'm doing well, thank you.", "start_s": 4, "end_s": 7},
        {"speaker": "speaker_0", "text": "Let me ask about your diet history.", "start_s": 8, "end_s": 12},
        {"speaker": "speaker_1", "text": "I usually eat rice and dal every day.", "start_s": 13, "end_s": 18},
        {"speaker": "speaker_0", "text": "Good, I see. Now let me discuss a diet plan for you.", "start_s": 19, "end_s": 26},
        {"speaker": "speaker_1", "text": "Okay, sounds good.", "start_s": 27, "end_s": 29},
    ]


@pytest.fixture
def mock_rubric_response():
    """Mock LLM rubric analysis response."""
    return {
        "dimension_scores": {
            "discovery_assessment": {
                "score": 7.5,
                "evidence": [
                    {"quote": "Let me ask about your diet history.", "timestamp_s": 8},
                ],
                "sub_criteria_met": {
                    "medical_history": False,
                    "lifestyle_activity": False,
                    "dietary_habits": True,
                    "goal_alignment": False,
                    "allergy_screening": False,
                },
            },
            "empathy_communication": {
                "score": 8.0,
                "evidence": [
                    {"quote": "How are you today?", "timestamp_s": 0},
                ],
                "sub_criteria_met": {
                    "empathy_tone": True,
                    "conversation_balance": True,
                    "active_listening": True,
                    "patient_engagement": True,
                    "sentiment": "positive",
                },
            },
            "rushed_forced_detection": {
                "score": 3.0,
                "evidence": [],
                "is_forced": False,
                "is_missing_discovery": True,
            },
            "adherence_counselling": {
                "score": 5.0,
                "evidence": [],
                "sub_criteria_met": {
                    "motivation": False,
                    "importance_explained": False,
                    "practical_implementation": True,
                    "barriers_addressed": False,
                },
            },
            "consultation_completeness": {
                "score": 6.5,
                "evidence": [],
                "sub_criteria_met": {
                    "goals_documented": True,
                    "bmi_reviewed": False,
                    "conditions_incorporated": False,
                    "followup_shared": False,
                },
            },
            "clinical_safety": {
                "score": 0,
                "evidence": [],
                "red_flag_detected": False,
                "handled_appropriately": None,
            },
        },
        "feedback_summary": [
            "Strengthen discovery questioning before prescribing.",
            "Good communication and patient engagement.",
        ],
    }
