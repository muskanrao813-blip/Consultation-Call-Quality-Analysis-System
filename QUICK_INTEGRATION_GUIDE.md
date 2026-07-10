# Quick Integration Guide - Clinical System

## 🎯 Goal
Integrate improved clinical analysis with FE portal

## 📋 Checklist

### Priority 1: Core Integration (1-2 hours)

- [ ] **Update Pipeline to Use ClinicalAnalyzer**
  ```python
  # In app/services/pipeline.py, line 381
  # Change: LLMProvider = _get_llm_provider()
  # To:
  from app.services.llm.clinical_analyzer import ClinicalAnalyzer
  LLMProvider = ClinicalAnalyzer
  
  # Pass patient condition:
  patient_condition = "Diabetes"  # Extract from Excel or default
  llm_provider.analyze_all_dimensions(..., patient_condition=patient_condition)
  ```

- [ ] **Extract Patient Medical Condition from Excel**
  ```python
  # In app/services/ingestion.py
  # Add to Excel template columns: "patient_condition" or "medical_condition"
  # Read and store in Call model
  ```

- [ ] **Generate QA Flags from Claude Violations**
  ```python
  # In app/services/pipeline.py, after Claude analysis
  for violation in response['sop_compliance']['violations']:
      if violation['violated']:
          flag = models.QAFlag(
              call_id=call.id,
              flag_type=violation['check'],
              triggered=True,
              detail=violation['evidence']
          )
          db.add(flag)
  ```

- [ ] **Test Clinical Endpoints**
  ```bash
  # Test new endpoints
  curl http://localhost:3000/api/clinical/calls
  curl http://localhost:3000/api/clinical/calls/{id}
  curl http://localhost:3000/api/clinical/dashboard/stats
  ```

### Priority 2: Scoring Realignment (1-2 hours)

- [ ] **Map Old Dimensions to New Scoring Model**
  ```python
  # In scoring logic, map:
  # greeting ← discovery_assessment + greeting quality (0-100)
  # empathy ← empathy_communication + patient engagement (0-100)
  # compliance ← SOP compliance + safety (0-100)
  # technical ← technical quality + completeness (0-100)
  ```

- [ ] **Update Weights**
  ```python
  weights = {
      "greeting": 0.25,
      "empathy": 0.25,
      "compliance": 0.20,
      "technical": 0.30  # Most important: clinical guidance
  }
  overall_score = sum(scores[dim] * weight for dim, weight in weights.items())
  ```

### Priority 3: FE Integration (30 minutes)

- [ ] **Update FE API Calls**
  ```typescript
  // In clinical-intelligence-system/src/App.tsx or components
  // Change:
  // const response = await fetch('/api/calls');
  // To:
  // const response = await fetch('/api/clinical/calls');
  ```

- [ ] **Verify Response Schema Matches**
  ```typescript
  // FE expects:
  Recording {
    scores: {
      greeting: number,
      empathy: number,
      compliance: number,
      technical: number
    },
    sopCompliant: boolean,
    sopComplianceScore: number,
    qaAlerts: QAAlert[],
    insights: {
      whatWentWell: string[],
      areasForImprovement: string[]
    }
  }
  ```

### Priority 4: Testing & Validation (1 hour)

- [ ] **Upload Test File**
  ```bash
  # With patient_condition column
  # Expected: Proper clinical analysis with 4 scores
  ```

- [ ] **Verify All 4 Scores Populated**
  - greeting (0-100)
  - empathy (0-100)
  - compliance (0-100)
  - technical (0-100)

- [ ] **Check QA Alerts Generated**
  - At least critical alerts for SOP violations
  - Proper severity levels

- [ ] **Validate FE Portal Displays**
  - Clinical dashboard stats
  - 4-dimension score visualization
  - QA alerts with severity badges
  - Insights with specific examples

## 🔧 Code Examples

### 1. Update Pipeline Provider Selection
**File:** `app/services/pipeline.py` (around line 350-390)

```python
# Add at top:
from app.services.llm.clinical_analyzer import ClinicalAnalyzer

# In process_call function:
def _get_clinical_llm_provider(patient_condition: str = "Diabetes"):
    """Get LLM provider for clinical analysis."""
    return ClinicalAnalyzer()

# In the pipeline:
LLMProvider = _get_clinical_llm_provider(patient_condition)
llm_provider.analyze_all_dimensions(
    segments,
    metrics_dict,
    str(call.id),
    call.dietician.name,
    call.patient_id,
    patient_condition=patient_condition  # NEW
)
```

### 2. Generate QA Flags from Violations
**File:** `app/services/pipeline.py` (around line 430)

```python
# After getting rubric_response from LLM:
if 'sop_compliance' in rubric_response:
    sop_data = rubric_response['sop_compliance']
    for violation in sop_data.get('violations', []):
        if violation.get('violated'):
            qa_flag = models.QAFlag(
                call_id=call.id,
                flag_type=violation.get('check'),
                triggered=True,
                detail=violation.get('evidence')
            )
            db.add(qa_flag)
```

### 3. Update Score Mapping
**File:** `app/services/scoring.py` or `app/services/pipeline.py`

```python
# Map Claude's 4 scores directly or aggregate from rubric:
clinical_scores = rubric_response.get('scores', {})

# Overall score calculation:
overall = (
    clinical_scores.get('greeting', 0) * 0.25 +
    clinical_scores.get('empathy', 0) * 0.25 +
    clinical_scores.get('compliance', 0) * 0.20 +
    clinical_scores.get('technical', 0) * 0.30
)

call.overall_score = round(overall, 2)
```

## 🧪 Testing Commands

```bash
# 1. Restart server
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
# Kill existing process and restart on 3000

# 2. Upload test file with patient_condition
curl -X POST http://localhost:3000/api/calls/bulk-upload \
  -F "file=@test_calls_with_condition.xlsx"

# 3. Check clinical calls
curl http://localhost:3000/api/clinical/calls | jq

# 4. Get specific call detail
curl http://localhost:3000/api/clinical/calls/{call_id} | jq

# 5. Verify all 4 scores present
curl http://localhost:3000/api/clinical/calls | \
  jq '.[] | {id: .id, scores: .scores}'

# 6. Check QA alerts
curl http://localhost:3000/api/clinical/calls | \
  jq '.[] | {id: .id, alerts: .qa_alerts}'
```

## 📊 Expected Output After Integration

```json
{
  "id": "call-123",
  "patient_name": "Patient Name",
  "dietician_name": "Dr. Smith",
  "scores": {
    "greeting": 85,
    "empathy": 78,
    "compliance": 42,
    "technical": 92
  },
  "overall_weighted_score": 80.3,
  "sop_compliant": false,
  "sop_compliance_score": 42,
  "qa_alerts": [
    {
      "title": "HIPAA Violation: Missing Patient ID Verification",
      "description": "At 0:15s, agent skipped patient ID verification",
      "severity": "critical",
      "status": "active"
    }
  ],
  "insights": {
    "what_went_well": [
      "Excellent rapport with patient",
      "Strong clinical knowledge demonstrated"
    ],
    "areas_for_improvement": [
      "CRITICAL: HIPAA compliance - always verify ID",
      "Add closing question: 'Any other health concerns?'"
    ],
    "summary": "Good clinical content but SOP gaps need immediate attention"
  }
}
```

## ✅ Success Criteria

- [x] Clinical prompt created with SOP checks
- [x] ClinicalAnalyzer implemented and integrated
- [x] 4-dimension scoring model defined
- [x] Clinical API endpoints ready
- [ ] Pipeline updated to use ClinicalAnalyzer
- [ ] Patient condition extraction from Excel
- [ ] QA flags generated from violations
- [ ] Score mapping complete
- [ ] FE portal updated to use clinical endpoints
- [ ] All tests passing
- [ ] Portal displays clinical data correctly

## 🎯 Timeline

- **Day 1**: Complete Priority 1 & 2 (3-4 hours)
- **Day 1**: Testing & validation (1-2 hours)
- **Day 2**: FE integration & final testing (1-2 hours)

**Total Effort:** 5-8 hours of development

## 🚀 Go Live

Once all steps complete, the clinical system will:
- Analyze with medical condition context ✓
- Generate SOP compliance alerts ✓
- Provide specific, actionable feedback ✓
- Track training gaps ✓
- Support dietician development ✓
