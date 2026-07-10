# API Reference

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### 1. Download Excel Template

**GET** `/template`

Download a blank Excel template with instructions for call metadata.

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Body: Binary Excel file

**Example:**
```bash
curl http://localhost:8000/api/template -o calls_template.xlsx
```

---

### 2. Bulk Upload Calls

**POST** `/calls/bulk-upload`

Upload an Excel/CSV file with call metadata. Returns validation report before processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (Excel or CSV)

**Response:**
```json
{
  "total_rows": 10,
  "valid_rows": 8,
  "invalid_rows": 2,
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "rows": [
    {
      "row_num": 2,
      "status": "valid",
      "reason": null
    },
    {
      "row_num": 3,
      "status": "invalid",
      "reason": "Invalid recording URL format"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/calls/bulk-upload \
  -F "file=@calls_template.xlsx"
```

---

### 3. Create Single Call

**POST** `/calls`

Ingest a single call programmatically.

**Request:**
```json
{
  "dietician_name": "Dr. Rajesh Kumar",
  "dietician_id": "DTN001",
  "patient_id": "PAT001",
  "patient_name": "Rajiv Singh",
  "appointment_id": "APT001",
  "call_datetime": "2024-01-15T09:30:00",
  "recording_url": "https://example.com/call1.wav",
  "call_duration_seconds": 1245
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### 4. Get Call Details

**GET** `/calls/{call_id}`

Retrieve full call result including transcript, metrics, scores, and flags.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "dietician_id": "550e8400-e29b-41d4-a716-446655440001",
  "dietician_name": "Dr. Rajesh Kumar",
  "patient_id": "PAT001",
  "patient_name": "Rajiv Singh",
  "appointment_id": "APT001",
  "call_datetime": "2024-01-15T09:30:00",
  "recording_url": "https://example.com/call1.wav",
  "call_duration_seconds": 1245,
  "status": "completed",
  "created_at": "2024-01-15T09:30:00",
  "processed_at": "2024-01-15T09:45:00",
  "error_message": null,
  "transcript": {
    "segments": [
      {
        "speaker": "speaker_0",
        "text": "Hello, how are you?",
        "start_s": 0,
        "end_s": 3
      }
    ]
  },
  "metrics": {
    "dietician_talk_ratio_pct": 45.5,
    "patient_talk_ratio_pct": 54.5,
    "interruption_count": 2,
    "avg_response_latency_seconds": 1.8,
    "time_to_first_plan_mention_seconds": 280.5,
    "silence_pct": 3.2,
    "off_topic_time_pct": 0.0
  },
  "rubric_scores": [
    {
      "dimension": "discovery_assessment",
      "score": 8.5,
      "evidence": [
        {
          "quote": "Tell me about your medical history.",
          "timestamp_s": 15.5
        }
      ],
      "sub_criteria_met": {
        "medical_history": true,
        "lifestyle_activity": true,
        "dietary_habits": true,
        "goal_alignment": false,
        "allergy_screening": false
      }
    }
  ],
  "qa_flags": [
    {
      "flag_type": "Missing Discovery",
      "triggered": true,
      "detail": "Only 3/5 discovery sub-criteria met"
    },
    {
      "flag_type": "Low Engagement",
      "triggered": false,
      "detail": null
    }
  ],
  "feedback_notes": "Improve discovery questioning | Good communication",
  "overall_weighted_score": 7.2,
  "retraining_recommended": false
}
```

**Example:**
```bash
curl http://localhost:8000/api/calls/550e8400-e29b-41d4-a716-446655440000
```

---

### 5. Get Transcript Only

**GET** `/calls/{call_id}/transcript`

Get just the diarized transcript without full analysis results.

**Response:**
```json
{
  "segments": [
    {
      "speaker": "speaker_0",
      "text": "Hello, how are you today?",
      "start_s": 0,
      "end_s": 3
    },
    {
      "speaker": "speaker_1",
      "text": "I'm doing well, thank you.",
      "start_s": 4,
      "end_s": 7
    }
  ]
}
```

---

### 6. Get Dietician Score History

**GET** `/dieticians/{dietician_id}/history`

Get trend of scores over the last 10 calls for a dietician.

**Response:**
```json
{
  "dietician": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Dr. Rajesh Kumar",
    "external_id": "DTN001",
    "created_at": "2024-01-15T09:30:00",
    "needs_admin_confirmation": false
  },
  "last_10_calls": [
    {
      "call_id": "550e8400-e29b-41d4-a716-446655440000",
      "call_datetime": "2024-01-15T09:30:00",
      "overall_weighted_score": 7.2,
      "status": "completed"
    },
    {
      "call_id": "550e8400-e29b-41d4-a716-446655440002",
      "call_datetime": "2024-01-14T14:00:00",
      "overall_weighted_score": 6.8,
      "status": "completed"
    }
  ],
  "average_score": 7.0,
  "call_count": 10
}
```

---

### 7. Get Dietician QA Flags Summary

**GET** `/dieticians/{dietician_id}/flags`

Get all QA flags for a dietician (rolling 10-call window) with trigger counts and instances.

**Response:**
```json
{
  "dietician_id": "550e8400-e29b-41d4-a716-446655440001",
  "dietician_name": "Dr. Rajesh Kumar",
  "flags": {
    "Missing Discovery": {
      "count": 3,
      "instances": [
        {
          "call_id": "550e8400-e29b-41d4-a716-446655440000",
          "call_datetime": "2024-01-15T09:30:00",
          "detail": "Only 3/5 discovery sub-criteria met"
        }
      ]
    },
    "Low Engagement": {
      "count": 1,
      "instances": [
        {
          "call_id": "550e8400-e29b-41d4-a716-446655440002",
          "call_datetime": "2024-01-14T14:00:00",
          "detail": "Patient talk ratio 18% (threshold: <20%)"
        }
      ]
    },
    "Clinical Safety Concern": {
      "count": 0,
      "instances": []
    }
  }
}
```

---

### 8. Get Batch Upload Status

**GET** `/batches/{batch_id}`

Check the processing status of a bulk upload batch.

**Response:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "uploaded_at": "2024-01-15T09:30:00",
  "total_rows": 10,
  "valid_rows": 8,
  "invalid_rows": 2,
  "call_statuses": {
    "550e8400-e29b-41d4-a716-446655440001": "completed",
    "550e8400-e29b-41d4-a716-446655440002": "processing",
    "550e8400-e29b-41d4-a716-446655440003": "pending",
    "550e8400-e29b-41d4-a716-446655440004": "failed"
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK` — Successful request
- `400 Bad Request` — Invalid input (missing fields, malformed data)
- `404 Not Found` — Resource doesn't exist (call_id, batch_id, etc.)
- `500 Internal Server Error` — Server-side error (transcription failure, LLM error, etc.)

---

## Example Workflow

### 1. Download template
```bash
curl http://localhost:8000/api/template -o calls.xlsx
```

### 2. Fill in Excel with call data and upload
```bash
curl -X POST http://localhost:8000/api/calls/bulk-upload \
  -F "file=@calls.xlsx"
```

Response:
```json
{
  "total_rows": 5,
  "valid_rows": 5,
  "invalid_rows": 0,
  "batch_id": "abc-123"
}
```

### 3. Check batch status
```bash
curl http://localhost:8000/api/batches/abc-123
```

### 4. Once processing is done, view call
```bash
curl http://localhost:8000/api/calls/{first_call_id}
```

### 5. View dietician trends
```bash
curl http://localhost:8000/api/dieticians/{dietician_id}/history
```

### 6. Check flags for pattern detection
```bash
curl http://localhost:8000/api/dieticians/{dietician_id}/flags
```

---

## Rate Limiting & Throttling

- **Gemini Flash API**: 15 requests/min (free tier)
- **Celery Workers**: 10 concurrent tasks per batch (configurable)
- **Database**: Connection pool of 5-20 (configurable)

Jobs are queued and processed asynchronously. Check batch status to monitor progress.

---

## Metrics Reference

All computed metrics per call:

| Metric | Type | Range | Description |
|--------|------|-------|-------------|
| `dietician_talk_ratio_pct` | float | 0-100 | % of call time dietician speaks |
| `patient_talk_ratio_pct` | float | 0-100 | % of call time patient speaks |
| `interruption_count` | int | 0+ | Number of overlapping speech turns |
| `avg_response_latency_seconds` | float | 0+ | Avg gap between speaker turns |
| `time_to_first_plan_mention_seconds` | float | 0+ | Timestamp of first plan/diet mention |
| `silence_pct` | float | 0-100 | % of call with no speech |
| `off_topic_time_pct` | float | 0-100 | % of non-clinical talk |

---

## Scoring Reference

Scores are on a 0-10 scale per dimension:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Discovery & Assessment | 20% | Medical history, lifestyle, dietary habits, goals, allergies |
| Empathy & Communication | 20% | Warmth, balance, active listening, engagement, sentiment |
| Forced/Rushed Detection | 15% | (Inverse) Early plan mention, low discovery, high monologue |
| Adherence Counselling | 20% | Motivation, importance, practicality, barrier handling |
| Consultation Completeness | 25% | Goals, BMI review, condition incorporation, follow-up |
| **Overall Weighted Score** | - | Sum of (dimension_score × weight) |

**Clinical Safety Gate**: If a red flag is detected and not handled, overall score is capped at 4.0 regardless of dimension scores.

---

## QA Flags Reference

| Flag Type | Trigger | Action |
|-----------|---------|--------|
| Forced Consultation | Plan mentioned < 2 min AND discovery < 3/5 | Coach on discovery first |
| Missing Discovery | < 3 of 5 discovery criteria met | Review discovery script |
| Low Engagement | Patient talk ratio < 20% | Improve listening skills |
| Poor Adherence | 0 of 4 adherence criteria met | Train adherence counselling |
| Off-Topic Content | > 25% non-clinical time | Refocus on patient needs |
| Appointment Not Delivered | Minimal patient participation | Review call completion |
| Clinical Safety Concern | Red flag detected and unhandled | Mandatory escalation |
| Templated Plan | High similarity to prior calls (v2) | Personalization coaching |

---

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Queued, not yet processing |
| `processing` | Transcription/analysis in progress |
| `completed` | Successfully processed and scored |
| `failed` | Processing failed (see error_message) |

---

## Timestamps

All timestamps are in ISO 8601 format (UTC):
```
2024-01-15T09:30:00
```

---

## Support

For issues or questions:
1. Check QUICKSTART.md for setup help
2. Review logs in Docker containers: `docker-compose logs -f api`
3. Check Celery worker logs: (running in terminal)
4. File an issue with error details and call_id
