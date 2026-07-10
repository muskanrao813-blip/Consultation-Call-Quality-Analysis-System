# Dietician Call QA & Analysis Agent

An AI-powered platform that automatically analyzes dietician consultation calls against a clinical rubric, generating quality scores, feedback, and QA flags.

## Features

- **Bulk Excel Ingestion**: Upload call metadata in batches (Excel/CSV), with validation report before processing
- **Automated Transcription**: Google Cloud Speech-to-Text with speaker diarization (Hinglish support)
- **Metrics Computation**: Talk ratios, interruptions, response latency, silence, and more
- **LLM-Based Rubric Analysis**: Gemini Flash evaluates 6 dimensions (discovery, empathy, adherence, etc.)
- **Deterministic Flagging**: Clinical safety gates, forced consultation detection, pattern-based retraining alerts
- **REST API**: Full queryability (call detail, dietician trends, batch status)
- **Async Job Queue**: Celery + Redis for parallel processing (10 calls/hour on local machine)

## Architecture

```
Excel Upload → Validation → Queued Jobs → [Async Pipeline]
                                          ↓
                                 Download Audio
                                 ↓ Transcribe
                                 ↓ Compute Metrics
                                 ↓ LLM Analysis
                                 ↓ Scoring & Flags
                                 ↓ Store Results
```

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (or SQLite for local dev)
- Redis (for Celery)
- Google Cloud account (Speech-to-Text API, GCS bucket)
- Gemini API key

### Installation

```bash
# Clone and enter
cd dietician-qa

# Create virtualenv
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in values
cp .env.example .env

# Run migrations
alembic upgrade head

# Start services (Docker)
docker-compose up -d

# Run tests
pytest tests/

# Start API server
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.worker.celery_app worker --loglevel=info
```

## API Endpoints

- `POST /api/calls/bulk-upload` — Upload Excel file
- `POST /api/calls` — Single call ingestion
- `GET /api/calls/{call_id}` — Full call result
- `GET /api/calls/{call_id}/transcript` — Diarized transcript
- `GET /api/dieticians/{dietician_id}/history` — Score trend (last 10 calls)
- `GET /api/dieticians/{dietician_id}/flags` — QA flags summary
- `GET /api/batches/{batch_id}` — Batch upload status

## Configuration

See `.env.example` for all available settings:
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis broker for Celery
- `GOOGLE_APPLICATION_CREDENTIALS` — Path to GCP service account JSON
- `GCS_BUCKET_NAME` — GCS bucket for audio storage
- `GEMINI_API_KEY` — Gemini Flash API key
- `LLM_PROVIDER` — `gemini` (primary) or `claude_cli` (local testing)

## Database Schema

- `dieticians` — Practitioner profiles
- `upload_batches` — Bulk upload metadata + original file
- `calls` — Individual call records
- `transcripts` — Raw + diarized transcripts
- `call_metrics` — Computed metrics (talk ratio, interruptions, etc.)
- `rubric_scores` — LLM-generated dimension scores + evidence
- `qa_flags` — Triggered QA flags per call
- `feedback_notes` — Natural-language feedback + retraining recommendation

## Rubric Dimensions

1. **Discovery & Assessment** (20%) — Medical history, lifestyle, dietary habits, goals, allergies
2. **Empathy & Communication** (20%) — Warmth, balance, active listening, engagement, sentiment
3. **Forced/Rushed Consultation** (15%) — Early plan mention, low discovery, high dietician monologue
4. **Adherence Counselling** (20%) — Motivation, importance explanation, practicality, barrier handling
5. **Consultation Completeness** (25%) — Goal confirmation, BMI review, condition incorporation, follow-up
6. **Clinical Safety** (gate) — Red-flag detection and appropriate escalation

## Flags

- **Forced Consultation** — Plan prescribed < 2 min with insufficient discovery
- **Missing Discovery** — < 3 of 5 discovery sub-criteria met
- **Low Engagement** — Patient talk ratio < 20%
- **Poor Adherence Counselling** — Zero adherence counselling criteria met
- **Off-Topic/Non-Consultative** — > 25% non-clinical talk
- **Appointment Not Delivered** — Minimal patient participation or clinical content
- **Clinical Safety Concern** — Red flag detected and not handled appropriately
- **Templated/Generic Plan** — (v2 feature) High similarity to prior calls

## Testing

```bash
pytest tests/test_metrics.py       # Metrics computation
pytest tests/test_scoring.py       # Scoring and flagging logic
pytest tests/test_ingestion.py     # Excel parsing (TODO)
pytest tests/test_pipeline.py      # End-to-end pipeline (TODO)
```

## Performance

- **Throughput**: ~1,400 calls per 14-day batch at 10 concurrent workers × ~3 min/call
- **Rate limits**: Respects Gemini Flash free-tier (15 RPM, 1M TPM)
- **Storage**: ~2-5 KB per call metadata + raw transcript storage

## Build Progress

| Phase | Deliverable | Status | Tests |
|-------|-------------|--------|-------|
| 1 | Repo scaffold, DB schema, migrations | ✅ Complete | — |
| 2 | Excel ingestion + validation + template | ✅ Complete | 8 |
| 3 | Audio download + Google STT | ✅ Complete | 15 |
| 4 | Metrics engine + scoring logic | ✅ Complete | 12 |
| 5 | Gemini Flash LLM + rubric analysis | ✅ Complete | 17 |
| 6 | Pipeline orchestrator + Celery worker | 🚧 Next | — |
| 7 | REST API (all routes) + React dashboard | 🚧 Planned | — |

## Test Coverage

```
Total Tests: 52 (comprehensive coverage)

Test Breakdown:
- test_audio.py (6 tests) — Audio download utilities
- test_transcription.py (8 tests) — Google STT provider
- test_metrics.py (7 tests) — Metrics computation
- test_scoring.py (5 tests) — Scoring + flagging logic
- test_ingestion.py (8 tests) — Excel parsing + validation
- test_pipeline_integration.py (7 tests) — Scoring workflows
- test_pipeline_e2e.py (7 tests) — Full pipeline simulation
- test_llm.py (12 tests) — Gemini LLM provider
- test_scoring_workflows.py (5 tests) — Realistic scenarios
```

Run all tests:
```bash
pytest tests/ -v --tb=short
```

View test count:
```bash
pytest --collect-only -q tests/ | tail -1
```

## Next Steps (v2+)

- [ ] Templated plan detection via historical similarity
- [ ] Off-topic content classifier (LLM or heuristic)
- [ ] Patient word count check for "appointment not delivered"
- [ ] Dashboard UI (React) — call detail, dietician trends, flag drill-down
- [ ] Multi-language support (extend beyond Hinglish)
- [ ] Batch retry/partial re-upload workflow refinement
- [ ] Integration with Managed Care pipeline
- [ ] Performance tuning (optimize for 20K calls/month)

## License

Internal use only.
