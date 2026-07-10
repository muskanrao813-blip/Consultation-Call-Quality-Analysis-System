"""Tests for Excel ingestion and validation."""

import pytest
import io
import pandas as pd
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Dietician, UploadBatch, Call
from app.services.ingestion import IngestService


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
def ingest_service(test_db):
    """Create IngestService with test database."""
    return IngestService(test_db)


def create_test_excel_file(rows_data: list[dict]) -> io.BytesIO:
    """Create a test Excel file from row data."""
    df = pd.DataFrame(rows_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Calls", index=False)
    output.seek(0)
    return output


class TestExcelParsing:
    @pytest.mark.asyncio
    async def test_valid_excel_upload(self, ingest_service):
        """Test uploading valid Excel with multiple calls."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                "dietician_id": "DTN001",
                "patient_id": "PAT001",
                "patient_name": "Rajiv Singh",
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "https://example.com/call1.wav",
                "call_duration_seconds": 1245,
            },
            {
                "dietician_name": "Dr. Priya Sharma",
                "dietician_id": "DTN002",
                "patient_id": "PAT002",
                "patient_name": "Priya Desai",
                "appointment_id": "APT002",
                "call_datetime": "2024-01-15 10:30:00",
                "recording_url": "https://example.com/call2.wav",
            },
        ]

        excel_file = create_test_excel_file(rows)

        file = UploadFile(filename="test_calls.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        assert report.total_rows == 2
        assert report.valid_rows == 2
        assert report.invalid_rows == 0
        assert report.batch_id is not None
        assert len(report.rows) == 2
        assert all(r.status == "valid" for r in report.rows)

        # Verify calls were created
        calls = ingest_service.db.query(Call).all()
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_missing_required_columns(self, ingest_service):
        """Test validation fails when required columns missing."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                "patient_id": "PAT001",
                # Missing: appointment_id, call_datetime, recording_url
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_invalid.xlsx", file=excel_file)

        with pytest.raises(ValueError, match="Missing required columns"):
            await ingest_service.validate_and_ingest_excel(file)

    @pytest.mark.asyncio
    async def test_missing_required_values(self, ingest_service):
        """Test row validation fails when required values missing."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                "dietician_id": "DTN001",
                "patient_id": None,  # Missing value
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "https://example.com/call1.wav",
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_missing_values.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        assert report.invalid_rows == 1
        assert report.rows[0].status == "invalid"
        assert "Missing required" in report.rows[0].reason

    @pytest.mark.asyncio
    async def test_invalid_url_format(self, ingest_service):
        """Test validation fails for invalid recording URLs."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                "patient_id": "PAT001",
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "not-a-url.wav",  # Invalid URL
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_bad_url.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        assert report.invalid_rows == 1
        assert report.rows[0].status == "invalid"
        assert "URL" in report.rows[0].reason or "url" in report.rows[0].reason

    @pytest.mark.asyncio
    async def test_duplicate_appointment_id(self, ingest_service):
        """Test that duplicate appointment IDs are rejected."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                "patient_id": "PAT001",
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "https://example.com/call1.wav",
            },
        ]

        excel_file1 = create_test_excel_file(rows)
        file1 = UploadFile(filename="test_calls_1.xlsx", file=excel_file1)

        # Upload first batch
        report1 = await ingest_service.validate_and_ingest_excel(file1)
        assert report1.valid_rows == 1

        # Try to upload duplicate appointment_id
        rows[0]["call_datetime"] = "2024-01-15 11:30:00"  # Different time
        excel_file2 = create_test_excel_file(rows)
        file2 = UploadFile(filename="test_calls_2.xlsx", file=excel_file2)

        report2 = await ingest_service.validate_and_ingest_excel(file2)
        assert report2.invalid_rows >= 1
        assert any("already processed" in r.reason for r in report2.rows if r.status == "invalid")

    @pytest.mark.asyncio
    async def test_flexible_column_names(self, ingest_service):
        """Test that flexible column names are normalized."""
        rows = [
            {
                "Dietician Name": "Dr. Rajesh Kumar",  # Flexible name
                "Patient ID": "PAT001",
                "Appointment ID": "APT001",
                "Call DateTime": "2024-01-15 09:30:00",
                "Recording URL": "https://example.com/call1.wav",
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_flexible.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        assert report.total_rows == 1
        assert report.valid_rows == 1
        assert report.rows[0].status == "valid"

    @pytest.mark.asyncio
    async def test_auto_dietician_creation(self, ingest_service):
        """Test that new dieticians are auto-created and flagged for confirmation."""
        rows = [
            {
                "dietician_name": "Dr. New Dietician",
                "patient_id": "PAT001",
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "https://example.com/call1.wav",
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_new_dietician.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        # Verify dietician was created
        dietician = ingest_service.db.query(Dietician).filter(
            Dietician.name == "Dr. New Dietician"
        ).first()

        assert dietician is not None
        assert dietician.needs_admin_confirmation is True

    @pytest.mark.asyncio
    async def test_optional_fields(self, ingest_service):
        """Test that optional fields (patient_name, call_duration, dietician_id) are handled."""
        rows = [
            {
                "dietician_name": "Dr. Rajesh Kumar",
                # dietician_id omitted
                "patient_id": "PAT001",
                # patient_name omitted
                "appointment_id": "APT001",
                "call_datetime": "2024-01-15 09:30:00",
                "recording_url": "https://example.com/call1.wav",
                # call_duration_seconds omitted
            },
        ]

        excel_file = create_test_excel_file(rows)
        file = UploadFile(filename="test_optional.xlsx", file=excel_file)

        report = await ingest_service.validate_and_ingest_excel(file)

        assert report.valid_rows == 1

        call = ingest_service.db.query(Call).first()
        assert call.patient_name is None
        assert call.call_duration_seconds is None

    def test_column_normalization(self, ingest_service):
        """Test flexible column name mapping."""
        df = pd.DataFrame({
            "Dietician": "Dr. Rajesh",
            "Patient Code": "PAT001",
            "Appointment": "APT001",
            "Call Date Time": "2024-01-15",
            "Recording": "https://example.com/call.wav",
        })

        normalized = ingest_service._normalize_column_names(df)

        assert "dietician_name" in normalized.columns
        assert "patient_id" in normalized.columns
        assert "appointment_id" in normalized.columns
        assert "call_datetime" in normalized.columns
        assert "recording_url" in normalized.columns
