# Clinical Intelligence System - Implementation Guide

## Overview
Integration of FE (React/Vite) portal design with BE (Python/FastAPI) clinical analysis system.

## ✅ Completed Implementations

### 1. **Clinical Analysis Prompt** (`app/services/llm/clinical_prompt.py`)
**Purpose:** Replace generic prompt with clinical-specific analysis
- Medical condition context (Diabetes, Hypertension, Obesity, etc.)
- 4-dimension clinical scoring:
  - **Greeting & Rapport** (0-100): HIPAA compliance, patient verification
  - **Empathy & Patient Care** (0-100): Active listening, personalization
  - **SOP Compliance** (0-100): Critical checks (HIPAA, closing scripts, medical screening)
  - **Technical Quality** (0-100): Action plan clarity, guideline alignment
- SOP violation detection with severity levels
- QA alert generation
- Training gap recommendations

**Key Features:**
- HIPAA compliance verification
- Mandatory script element checking
- Clinical contraindication screening
- SMART goal assessment
- Barrier/adherence discussion evaluation

### 2. **Clinical Analyzer** (`app/services/llm/clinical_analyzer.py`)
**Purpose:** Use Claude CLI with clinical prompts for analysis
- Integrates with improved clinical_prompt
- Transforms Claude response to match FE schema
- Generates SOP compliance scores
- Creates QA alerts from violations
- Produces actionable insights

### 3. **Clinical Call Schemas** (`app/schemas/clinical_call.py`)
**Purpose:** Define FE-compatible data structures
- `ClinicalCallResponse`: Complete call analysis
- `CallScore`: 4-dimension scores (greeting, empathy, compliance, technical)
- `SOPCompliance`: Compliance tracking with violations
- `QAAlert`: Alert data with severity levels
- `CallInsights`: Insights with specific examples

### 4. **Clinical API Endpoints** (`app/api/clinical_calls.py`)
**Purpose:** Serve clinical data to FE portal
Endpoints:
- `GET /api/clinical/calls` - List all calls with clinical analysis
- `GET /api/clinical/calls/{call_id}` - Detailed analysis for single call
- `GET /api/clinical/dashboard/stats` - Dashboard statistics

## 📋 Next Steps Required

### 1. **Update Pipeline to Use ClinicalAnalyzer**
File: `app/services/pipeline.py`
- Replace `_get_llm_provider()` to prioritize ClinicalAnalyzer
- Pass `patient_condition` to analyzer
- Update response transformation to use clinical schema

### 2. **Extract Patient Condition from Uploaded Data**
File: `app/services/ingestion.py`
- Extract medical condition from Excel (add column: "patient_condition" or similar)
- Pass to pipeline for context-aware analysis

### 3. **Generate QA Flags in Pipeline**
File: `app/services/pipeline.py`
- Convert Claude's SOP violations to QA Flag DB records
- Set severity levels (critical, warning, info)
- Populate QA Flag table for each violation

### 4. **Update Scoring Logic**
File: `app/services/scoring.py`
- Align rubric_scores to 4 dimensions (instead of current 6)
- Map old dimensions to new:
  - greeting ← discovery_assessment + greeting quality
  - empathy ← empathy_communication + patient engagement
  - compliance ← SOP compliance score + safety
  - technical ← technical quality + action plan clarity
- Calculate weighted overall score (suggested: greeting 25%, empathy 25%, compliance 20%, technical 30%)

### 5. **Update Database Models (Optional)**
File: `app/db/models.py`
Consider adding columns to Call model:
- `patient_condition` - Medical condition
- `medical_history` - Key conditions/allergies
- `consultation_goals` - Patient's stated goals

### 6. **Update FE Portal to Use Clinical Endpoints**
File: `clinical-intelligence-system/src/App.tsx`
- Change API calls to use `/api/clinical/calls` instead of `/api/calls`
- Ensure response schema matches FE types (CallScore, SOPCompliance, etc.)

### 7. **Add Transcript Segment Tags**
Generate during analysis:
- `["critical"]` - HIPAA violation, safety concern
- `["positive"]` - Good patient engagement, empathy shown
- `["concern"]` - Process gap, compliance issue

## 🧪 Testing Checklist

### Unit Tests
- [ ] Clinical prompt generates valid JSON
- [ ] Claude CLI analyzer handles responses correctly
- [ ] SOP compliance calculations accurate
- [ ] QA alert severity levels correct
- [ ] Score mapping from 6 dimensions to 4 dimensions correct

### Integration Tests
- [ ] Upload → Transcription → Clinical Analysis complete pipeline
- [ ] Claude CLI processes with new clinical prompt
- [ ] Response matches FE ClinicalCallResponse schema
- [ ] All 4 scores populated (greeting, empathy, compliance, technical)
- [ ] SOP compliance score calculated correctly
- [ ] QA alerts generated and stored in DB
- [ ] Clinical endpoints return correctly formatted data

### Portal Tests
- [ ] Dashboard loads with clinical stats
- [ ] Call list shows clinical call data
- [ ] Call detail view shows 4-dimension scores
- [ ] QA alerts display with severity badges
- [ ] Transcript segments tagged appropriately
- [ ] Insights show specific examples from transcript

## 🔧 Configuration Examples

### Medical Condition Context
Update prompt for different conditions:
```python
# For Diabetes
create_clinical_analysis_prompt(transcript, metrics, patient_condition="Diabetes Management")

# For Hypertension
create_clinical_analysis_prompt(transcript, metrics, patient_condition="Blood Pressure Management")

# For Obesity/Weight Loss
create_clinical_analysis_prompt(transcript, metrics, patient_condition="Weight Management")
```

### Score Weights (Suggested)
```python
weights = {
    "greeting": 0.25,      # Opening quality & HIPAA compliance
    "empathy": 0.25,       # Patient engagement & soft skills
    "compliance": 0.20,    # SOP adherence (critical)
    "technical": 0.30      # Clinical guidance quality (most important)
}

overall_score = sum(scores[dim] * weight for dim, weight in weights.items())
```

### SOP Compliance Checks
Critical checks (must pass):
- HIPAA ID verification
- Closing disclosure script
- Informed consent
- Medical contraindication screening
- Barrier assessment
- Follow-up plan clarity

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Clinical Prompt | ✅ Complete | Comprehensive SOP + clinical checks |
| Clinical Analyzer | ✅ Complete | Integrated with Claude CLI |
| Clinical Schemas | ✅ Complete | FE-compatible structures |
| Clinical API | ✅ Complete | Endpoints ready |
| Pipeline Integration | ⏳ Pending | Need to switch to ClinicalAnalyzer |
| QA Flag Generation | ⏳ Pending | Convert Claude violations to DB records |
| Scoring Remapping | ⏳ Pending | Align 6 dims → 4 dims |
| FE Integration | ⏳ Pending | Update portal to use new endpoints |

## 🚀 Quick Start

Once completed, test with:
```bash
# Upload test call
curl -X POST http://localhost:3000/api/calls/bulk-upload \
  -F "file=@test_calls.xlsx"

# Get clinical calls
curl http://localhost:3000/api/clinical/calls

# Get call detail
curl http://localhost:3000/api/clinical/calls/{call_id}

# Get dashboard stats
curl http://localhost:3000/api/clinical/dashboard/stats
```

## 📝 Notes

- Claude CLI is working with improved clinical prompt
- Whisper transcription ready (using mock provider)
- Portal running on localhost:3000
- All infrastructure in place for clinical analysis
- Just need to wire up the pieces!
