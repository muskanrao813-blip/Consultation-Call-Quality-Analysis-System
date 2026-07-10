"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dieticians",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("needs_admin_confirmation", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )

    op.create_table(
        "upload_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", sa.String(255), nullable=True),
        sa.Column("uploaded_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_blob", sa.LargeBinary(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dietician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", sa.String(255), nullable=False),
        sa.Column("patient_name", sa.String(255), nullable=True),
        sa.Column("appointment_id", sa.String(255), nullable=False),
        sa.Column("call_datetime", sa.TIMESTAMP(), nullable=False),
        sa.Column("recording_url", sa.String(2048), nullable=False),
        sa.Column("call_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("pending", "processing", "completed", "failed", name="callstatus"), nullable=False, server_default="pending"),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("processed_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["upload_batches.id"]),
        sa.ForeignKeyConstraint(["dietician_id"], ["dieticians.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id", name="uq_appointment_id"),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("raw_transcript_json", postgresql.JSON(), nullable=False),
        sa.Column("diarized_segments", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "call_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("dietician_talk_ratio_pct", sa.Float(), nullable=False),
        sa.Column("patient_talk_ratio_pct", sa.Float(), nullable=False),
        sa.Column("interruption_count", sa.Integer(), nullable=False),
        sa.Column("avg_response_latency_seconds", sa.Float(), nullable=True),
        sa.Column("time_to_first_plan_mention_seconds", sa.Float(), nullable=True),
        sa.Column("silence_pct", sa.Float(), nullable=False),
        sa.Column("off_topic_time_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rubric_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dimension", sa.String(50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSON(), nullable=False),
        sa.Column("sub_criteria", postgresql.JSON(), nullable=False),
        sa.Column("raw_llm_response", postgresql.JSON(), nullable=False),
        sa.Column("overall_weighted_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "qa_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flag_type", sa.String(100), nullable=False),
        sa.Column("triggered", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "feedback_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bullet", sa.Text(), nullable=False),
        sa.Column("retraining_recommended", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("retraining_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("feedback_notes")
    op.drop_table("qa_flags")
    op.drop_table("rubric_scores")
    op.drop_table("call_metrics")
    op.drop_table("transcripts")
    op.drop_table("calls")
    op.drop_table("upload_batches")
    op.drop_table("dieticians")
