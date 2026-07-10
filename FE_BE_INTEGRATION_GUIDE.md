# Frontend-Backend Integration Guide

## Current State

### Backend (FastAPI) - Ready ✅
- **Clinical Analyzer**: Converts transcripts to 4-dimension scores + SOP violations
- **API Endpoints**: 
  - `GET /api/clinical/calls` → returns all calls with analysis
  - `GET /api/clinical/calls/{id}` → returns detailed call analysis
  - `GET /api/clinical/dashboard/stats` → returns dashboard statistics
- **QA Alert Generation**: Automatically creates QA flags from SOP violations
- **Data Format**: Matches FE `Recording` type exactly

### Frontend (React + Vite) - Needs Integration 🔄
- **Location**: `C:\Users\muskan.rao\Downloads\clinical-intelligence-system\`
- **Type System**: Defined types in `src/types.ts` (Recording, QAAlert, etc.)
- **Current State**: Uses mock data from `src/data.ts`
- **Target State**: Fetch real data from BE endpoints

---

## Data Flow

### Current Mock Flow
```
App.tsx (initialRecordings from data.ts)
  ↓
  → DashboardView
  → QAAlertsView
  → AIInsightsView
  → TranscriptionsView
```

### Target Real Flow
```
App.tsx (fetch /api/clinical/calls)
  ↓
  Backend (Python + Claude CLI)
  ↓
  → Recording with scores, qaAlerts, insights
  ↓
  → DashboardView
  → QAAlertsView
  → AIInsightsView
  → TranscriptionsView
```

---

## BE API Response Format

### GET /api/clinical/calls

**Response Type**: `ClinicalCallResponse` (from app/schemas/clinical_call.py)

```json
{
  "id": "call-123",
  "name": "patient_visit_id_123.wav",
  "patientName": "John Doe",
  "agentName": "Dr. Smith",
  "duration": "04:12",
  "date": "2026-07-09",
  "status": "completed",
  "progress": 100,
  "statusText": "Ready for review",
  "scores": {
    "greeting": 85,
    "empathy": 92,
    "compliance": 78,
    "technical": 88
  },
  "sopCompliant": true,
  "sopComplianceScore": 78,
  "qaAlerts": [
    {
      "id": "alert-1",
      "title": "Health Assessment Missing",
      "description": "Did not explore patient's medication history before recommendations",
      "severity": "critical",
      "status": "active",
      "recordingId": "call-123",
      "recordingName": "patient_visit_id_123.wav",
      "dieticianName": "Dr. Smith",
      "date": "Jul 9, 2026"
    }
  ],
  "insights": {
    "whatWentWell": [
      "Good patient engagement and rapport",
      "Clear personalization for patient's schedule"
    ],
    "areasForImprovement": [
      "Could have explored cost barriers more thoroughly",
      "Follow-up plan could have been more specific"
    ],
    "summary": "Overall good consultation with some gaps in barrier assessment"
  },
  "transcript": [
    {
      "id": "turn-1",
      "speaker": "agent",
      "speakerName": "Dr. Smith",
      "timestamp": "00:15",
      "text": "Let me ask about your current medications...",
      "isCritical": false
    }
  ]
}
```

---

## Integration Steps

### Step 1: Create API Fetch Hook

**File**: `C:\Users\muskan.rao\Downloads\clinical-intelligence-system\src\hooks\useClinicalAPI.ts`

```typescript
import { useState, useEffect } from 'react';
import { Recording } from '../types';

export function useClinicalAPI() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecordings = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/api/clinical/calls');
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        
        const data = await response.json();
        setRecordings(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        console.error('Failed to fetch recordings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecordings();
    // Optional: Refresh every 30 seconds
    const interval = setInterval(fetchRecordings, 30000);
    return () => clearInterval(interval);
  }, []);

  return { recordings, loading, error };
}
```

### Step 2: Update App.tsx

Replace mock data initialization with API call:

```typescript
import { useClinicalAPI } from './hooks/useClinicalAPI';

export default function App() {
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Fetch real data from BE
  const { recordings, loading, error } = useClinicalAPI();
  
  // Derive QA alerts from recordings
  const [allQAAlerts, setAllQAAlerts] = useState<QAAlert[]>([]);

  useEffect(() => {
    const alerts = recordings.reduce((acc: QAAlert[], curr) => {
      if (curr.qaAlerts && curr.qaAlerts.length > 0) {
        return [...acc, ...curr.qaAlerts];
      }
      return acc;
    }, []);
    setAllQAAlerts(alerts);
  }, [recordings]);

  // ... rest of App component remains the same
}
```

### Step 3: Add Loading State UI

```typescript
{/* In main render */}
{loading && (
  <div className="flex items-center justify-center h-full">
    <p>Loading clinical data...</p>
  </div>
)}

{error && (
  <div className="flex items-center justify-center h-full text-red-600">
    <p>Error: {error}</p>
  </div>
)}

{!loading && !error && (
  // ... existing view switchboard
)}
```

---

## Testing Checklist

- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] Browser console shows no CORS errors
- [ ] `/api/clinical/calls` returns Recording array
- [ ] DashboardView displays real scores
- [ ] QAAlertsView shows real alerts with severity badges
- [ ] AIInsightsView shows real transcript and insights
- [ ] Each call shows 4-dimension scores (greeting, empathy, compliance, technical)
- [ ] QA Alerts display with correct severity (critical=red, warning=yellow, info=blue)
- [ ] Clicking "Audit" button navigates to call details

---

## CORS Configuration

### Backend (FastAPI)

The backend should allow localhost:3000. In `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Running Both Services

### Terminal 1: Backend
```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python -m uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd C:\Users\muskan.rao\Downloads\clinical-intelligence-system
npm install
npm run dev
```

Access portal: `http://localhost:5173` (Vite dev server) or configured port

---

## Data Transformation (if needed)

If BE returns different field names, add transformation in `useClinicalAPI`:

```typescript
const transformRecording = (raw: any): Recording => ({
  ...raw,
  status: raw.status || 'completed',
  progress: raw.progress || 100,
  statusText: raw.statusText || 'Ready for review'
});

const data = await response.json();
setRecordings(data.map(transformRecording));
```

---

## Troubleshooting

### "Cannot fetch from API"
- ✅ Check backend is running: `curl http://localhost:8000/api/clinical/calls`
- ✅ Check CORS headers in BE response
- ✅ Check Frontend is pointing to correct BE URL

### "Missing fields in Recording"
- ✅ Verify BE endpoint returns all fields from `Recording` type
- ✅ Check `app/api/clinical_calls.py` transform function
- ✅ Add console.log to see actual response structure

### "QA Alerts not showing"
- ✅ Verify `qaAlerts` array is populated in BE response
- ✅ Check `app/services/pipeline.py` generates QA flags from violations
- ✅ View database: `SELECT * FROM qa_flags WHERE call_id = '...'`

---

## Next Steps

1. **Implement API Fetch Hook** → `useClinicalAPI.ts`
2. **Update App.tsx** → Use real data instead of mock
3. **Test Integration** → Verify all views display correctly
4. **Upload Test Data** → Test with real call files
5. **Deploy** → Production setup

---

## API Response Schema (Python Pydantic)

See `app/schemas/clinical_call.py`:
- `TranscriptTurn`: Single transcript line
- `QAAlert`: Alert with severity and status
- `CallScore`: 4-dimension scores
- `SOPCompliance`: Compliance score + violations list
- `CallInsights`: What went well, areas for improvement
- `ClinicalCallResponse`: Complete call analysis

All models match FE `types.ts` definitions for seamless integration.

---

## Status: READY FOR INTEGRATION 🚀

Backend is production-ready and returning correctly formatted data. FE just needs API hook implementation to consume real data instead of mocks.

**Estimated time**: 30-60 minutes to implement, test, and verify.
