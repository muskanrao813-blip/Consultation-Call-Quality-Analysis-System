# Quick Start Guide

## Local Development Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 12+ (or use Docker)
- Redis (or use Docker)
- Google Cloud account with:
  - Speech-to-Text API enabled
  - Service account JSON key
  - GCS bucket created
- Gemini API key

### 2. Clone & Setup

```bash
cd dietician-qa
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your actual values:
# - DATABASE_URL (default: postgresql://dietician_qa_user:password123@localhost:5432/dietician_qa)
# - GOOGLE_APPLICATION_CREDENTIALS (path to GCP service account JSON)
# - GCS_BUCKET_NAME
# - GEMINI_API_KEY
```

### 4. Start Docker Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)

Wait for services to be healthy:
```bash
docker-compose ps
```

### 5. Initialize Database

```bash
alembic upgrade head
```

### 6. Run Tests

```bash
pytest tests/ -v

# Run specific test file
pytest tests/test_metrics.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### 7. Start the API Server

In one terminal:
```bash
uvicorn app.main:app --reload --port 8000
```

### 8. Start Celery Worker (in another terminal)

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### 9. Test the Workflow

#### Download Template
```bash
curl http://localhost:8000/api/template -o calls_template.xlsx
```

#### Fill in template with call metadata and upload:
```bash
curl -X POST http://localhost:8000/api/calls/bulk-upload \
  -F "file=@calls_template.xlsx"
```

This will return a validation report with batch_id.

#### Check batch status:
```bash
curl http://localhost:8000/api/batches/{batch_id}
```

#### Once processing is done, view call details:
```bash
curl http://localhost:8000/api/calls/{call_id}
```

#### View dietician history:
```bash
curl http://localhost:8000/api/dieticians/{dietician_id}/history
```

## Troubleshooting

### "Connection refused" for PostgreSQL
- Ensure Docker is running: `docker-compose ps`
- Restart services: `docker-compose restart`

### "Connection refused" for Redis
- Same as above

### Alembic migration fails
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running and accessible
- Try dropping the database and re-running: `alembic downgrade base && alembic upgrade head`

### Celery tasks not processing
- Ensure Redis is running
- Check Celery worker logs for errors
- Verify REDIS_URL in .env

### Google STT transcription fails
- Verify GCP service account JSON path is correct
- Ensure Speech-to-Text API is enabled in GCP project
- Check that GCS bucket exists and is accessible
- Audio file must be reachable via the URL provided

### Gemini API errors
- Verify GEMINI_API_KEY is set and valid
- Check rate limits (free tier: 15 RPM)
- Ensure prompt is well-formed JSON

## Development Workflow

1. **Make code changes**
2. **Run tests**: `pytest tests/ -v`
3. **Start API**: `uvicorn app.main:app --reload`
4. **Test endpoints** manually or with integration tests
5. **Commit changes** with descriptive message

## File Structure Reference

- `app/main.py` — FastAPI entry point
- `app/api/` — REST endpoints
- `app/services/` — Business logic (ingestion, transcription, LLM, scoring)
- `app/db/` — Database models and session management
- `tests/` — Unit and integration tests
- `alembic/` — Database migrations

## Next Steps

- [ ] Set up IDE debugger (VS Code, PyCharm)
- [ ] Configure pre-commit hooks
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to staging environment
- [ ] Load test with 100+ concurrent calls
- [ ] Integrate with Managed Care pipeline
