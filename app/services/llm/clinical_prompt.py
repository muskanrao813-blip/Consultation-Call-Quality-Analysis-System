"""Clinical-specific analysis prompt for dietary consultation calls."""

def create_clinical_analysis_prompt(transcript: str, metrics: dict, patient_condition: str = "Diabetes") -> str:
    """
    Create a clinical-focused analysis prompt for dietician-patient calls.

    Args:
        transcript: Formatted transcript with speaker turns
        metrics: Call metrics (duration, talk ratios, etc.)
        patient_condition: Medical condition (Diabetes, Hypertension, Obesity, etc.)

    Returns:
        Formatted prompt for Claude CLI analysis
    """

    return f"""You are a clinical quality assurance specialist reviewing a dietician-patient consultation call for {patient_condition} management.

PATIENT CONDITION: {patient_condition} Management
CALL METRICS:
- Duration: {metrics.get('duration_seconds', 0)}s
- Dietician Talk Ratio: {metrics.get('dietician_talk_ratio_pct', 0)}%
- Patient Talk Ratio: {metrics.get('patient_talk_ratio_pct', 0)}%
- Interruptions: {metrics.get('interruption_count', 0)}
- Response Latency: {metrics.get('avg_response_latency_seconds', 0)}s

TRANSCRIPT:
{transcript}

EVALUATION FRAMEWORK:

Score these 4 clinical dimensions (0-100):

1. **GREETING & RAPPORT (Professional Opening)**
   - Clear introduction and purpose of consultation?
   - Warm, professional tone established?
   - Patient comfort and readiness assessed?
   - Explanation of call structure and duration?
   Score based on: Clarity, professionalism, warmth, patient comfort.

2. **EMPATHY & PATIENT-CENTERED CARE**
   - Acknowledgment of patient concerns and barriers?
   - Active listening demonstrated (reflections, validations)?
   - Personalized approach (NOT generic/templated advice)?
   - Cultural sensitivity shown (if applicable)?
   - Patient talking time adequate (>25%)?
   Score based on: Patient engagement, validation, personalization, listening quality.

3. **COMPLIANCE WITH SOP & CLINICAL STANDARDS**
   Score based on:
   - **Health Understanding FIRST**: Did dietician explore medical history, current conditions, medications, allergies BEFORE giving diet plan? (CRITICAL)
   - **Personalized Recommendations**: Diet plan customized to patient's specific health conditions, NOT generic template? (CRITICAL)
   - **No Self-Promotion**: Did dietician give unbiased advice without promoting their own entity/products/supplements? (CRITICAL)
   - **Informed Consent**: Patient understands and agrees with recommendations?
   - **Barrier Assessment**: Affordability, adherence, lifestyle barriers explored?
   - **Follow-up Plan**: Clear next steps, timeline, and contact process communicated?

4. **TECHNICAL QUALITY & ACTION PLAN CLARITY**
   - Clear, actionable dietary recommendations provided?
   - Recommendations based on {patient_condition} medical guidelines?
   - SMART goals established (Specific, Measurable, Achievable, Relevant, Time-bound)?
   - Patient education: Explains WHY (nutrition science) not just WHAT (diet plan)?
   - Patient understanding verified (teach-back method or confirmation)?
   Score based on: Clarity, specificity, guideline alignment, patient comprehension.

CRITICAL SOP COMPLIANCE CHECKS (Generate QA Alerts if violated):
1. Health Understanding First: Explored medical history, current conditions, medications, allergies BEFORE recommendations
2. Personalized Plan: Diet plan customized to patient's health context, NOT generic template
3. No Self-Promotion: Unbiased advice given, no promotion of own entity/products/supplements
4. Informed Consent: Patient explicitly agrees with recommendations provided
5. Barrier Assessment: Discussed affordability, adherence barriers, lifestyle constraints
6. Patient Education: Explained nutritional science and WHY recommendations matter
7. Follow-up Plan: Clear next steps, timeline, and follow-up communication plan

GENERATE SOP VIOLATIONS:
For each compliance check violated, create an alert with:
- severity: "critical" (SOP violation - patient safety/quality risk), "warning" (process gap), "info" (improvement opportunity)
- description: Specific evidence from transcript with timestamp

Return ONLY valid JSON (no markdown, no explanation, pure JSON):
{{
  "scores": {{
    "greeting": <number 0-100>,
    "empathy": <number 0-100>,
    "compliance": <number 0-100>,
    "technical": <number 0-100>
  }},
  "sop_compliance": {{
    "compliant": <bool>,
    "compliance_score": <number 0-100>,
    "violations": [
      {{"check": "Health Understanding First", "violated": <bool>, "evidence": "quoted text from transcript with timestamp"}},
      {{"check": "Personalized Plan", "violated": <bool>, "evidence": "..."}},
      {{"check": "No Self-Promotion", "violated": <bool>, "evidence": "..."}},
      {{"check": "Informed Consent", "violated": <bool>, "evidence": "..."}},
      {{"check": "Barrier Assessment", "violated": <bool>, "evidence": "..."}},
      {{"check": "Patient Education", "violated": <bool>, "evidence": "..."}},
      {{"check": "Follow-up Plan", "violated": <bool>, "evidence": "..."}}
    ]
  }},
  "qa_alerts": [
    {{
      "title": "Alert Title (e.g., Generic Diet Plan Without Health Assessment)",
      "description": "Specific evidence from transcript with timestamp showing the violation",
      "severity": "critical|warning|info"
    }}
  ],
  "transcript_tags": {{
    "turn_id": ["critical", "positive", "concern", "generic", "personalized"],
    "turn_id2": ["positive", "rapport", "health-assessment"]
  }},
  "insights": {{
    "whatWentWell": [
      "Specific positive example with timestamp (e.g., 'At 3:22s, excellent empathy when patient mentioned struggles')"
    ],
    "areasForImprovement": [
      "Specific improvement with evidence (e.g., 'At 2:15s, gave diet plan without understanding patient works shifts - need to ask about schedule first')"
    ],
    "trainingGapRecs": [
      {{
        "type": "compliance|soft_skills",
        "title": "Training Gap Title",
        "description": "Specific recommendation with evidence from transcript",
        "urgency": "Urgent|Mid-term|Low-priority"
      }}
    ],
    "summary": "Overall assessment of consultation quality - focus on whether health assessment preceded recommendations and if advice was personalized"
  }}
}}"""


def create_enhanced_feedback_prompt(scores: dict, violations: list, medical_condition: str) -> str:
    """
    Create a prompt for generating enhanced coaching feedback.

    Args:
        scores: Dictionary with greeting, empathy, compliance, technical scores
        violations: List of SOP violations found
        medical_condition: Patient's medical condition

    Returns:
        Prompt for generating targeted coaching recommendations
    """

    return f"""Generate specific, actionable coaching recommendations for a dietician based on this clinical call analysis for {medical_condition} management.

CALL SCORES:
- Greeting: {scores.get('greeting', 0)}/100
- Empathy: {scores.get('empathy', 0)}/100
- Compliance: {scores.get('compliance', 0)}/100
- Technical: {scores.get('technical', 0)}/100

SOP VIOLATIONS FOUND:
{chr(10).join([f"- {v.get('check')}: {v.get('evidence')}" for v in violations if v.get('violated')])}

KEY COACHING AREAS:
- Health Understanding First: Always assess patient's complete health picture BEFORE recommending diet
- Personalization: Customize recommendations to patient's specific conditions (not generic templates)
- No Self-Promotion: Give unbiased advice focused on patient benefit, not product/entity promotion
- Patient Education: Explain nutritional science and WHY recommendations matter
- Barrier Assessment: Understand patient's real constraints (cost, schedule, preferences)

Generate 2-3 specific, actionable coaching points:
- If compliance low: Focus on health assessment order, personalization, avoiding self-promotion
- If empathy low: Focus on patient listening and barrier understanding
- If technical low: Focus on clinical guidance quality and patient education
- If greeting low: Focus on professional opening and patient comfort

IMPORTANT: Each coaching point MUST reference specific timestamps from the transcript showing the gap.

Return as JSON with this structure:
{{
  "coachingPoints": [
    {{
      "area": "Health Assessment Order|Personalization|Unbiased Recommendations|Patient Education|Barrier Understanding",
      "current": "What was actually observed (with timestamp)",
      "target": "What should happen instead",
      "specificExample": "Quote from transcript at [timestamp] showing the gap",
      "action": "Exact action to improve (step-by-step)",
      "resource": "Training module, reference guide, or SOP section"
    }}
  ]
}}"""
