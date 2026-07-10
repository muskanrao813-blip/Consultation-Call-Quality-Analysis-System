"""Tests for metrics computation."""

import pytest
from app.services import metrics


@pytest.fixture
def sample_segments():
    """Sample diarized segments for testing."""
    return [
        {"speaker": "dietician", "text": "Hello, how are you?", "start_s": 0, "end_s": 3},
        {"speaker": "patient", "text": "I'm good.", "start_s": 4, "end_s": 6},
        {"speaker": "dietician", "text": "Let me check your diet history.", "start_s": 7, "end_s": 12},
        {"speaker": "patient", "text": "I usually eat rice and dal.", "start_s": 13, "end_s": 18},
        {"speaker": "dietician", "text": "Good. I recommend a balanced diet plan with more vegetables.", "start_s": 19, "end_s": 28},
    ]


def test_compute_talk_ratios(sample_segments):
    """Test talk ratio calculation."""
    ratios = metrics.compute_talk_ratios(sample_segments)

    assert "dietician_pct" in ratios
    assert "patient_pct" in ratios
    assert ratios["dietician_pct"] + ratios["patient_pct"] == 100.0 or abs(ratios["dietician_pct"] + ratios["patient_pct"] - 100.0) < 1


def test_compute_interruptions(sample_segments):
    """Test interruption detection."""
    interruptions = metrics.compute_interruptions(sample_segments)
    assert isinstance(interruptions, int)
    assert interruptions >= 0


def test_compute_response_latency(sample_segments):
    """Test response latency calculation."""
    latency = metrics.compute_response_latency(sample_segments)
    assert isinstance(latency, float)
    assert latency >= 0


def test_compute_silence_pct(sample_segments):
    """Test silence percentage calculation."""
    total_duration = 30.0
    silence_pct = metrics.compute_silence_pct(sample_segments, total_duration)

    assert isinstance(silence_pct, float)
    assert 0 <= silence_pct <= 100


def test_compute_time_to_first_plan(sample_segments):
    """Test time to first plan mention detection."""
    time_to_plan = metrics.compute_time_to_first_plan(sample_segments)
    assert time_to_plan is not None
    assert time_to_plan >= 0


def test_count_patient_words(sample_segments):
    """Test patient word count."""
    word_count = metrics.count_patient_words(sample_segments)
    assert isinstance(word_count, int)
    assert word_count > 0


def test_empty_segments():
    """Test with empty segment list."""
    assert metrics.compute_talk_ratios([]) == {"dietician_pct": 0.0, "patient_pct": 0.0}
    assert metrics.compute_interruptions([]) == 0
    assert metrics.compute_response_latency([]) == 0.0
    assert metrics.compute_silence_pct([], 100) == 100.0
