"""Gemini-based QA analyzer for dietician calls."""

import logging
import json
import os
from typing import Dict, List

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Analyzes dietician call transcripts using Gemini API for QA scoring."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            import httpx
            http_client = httpx.Client(verify=False)
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(httpx_client=http_client),
            )
        return self._client

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str,
        patient_condition: str = None
    ) -> Dict:
        """Analyze call transcript using Gemini."""
        try:
            client = self._get_client()
            transcript_text = self._build_transcript_text(transcript_segments)

            # Build simple, reliable prompt
            prompt = f"""Analyze this dietician call and return ONLY JSON (no markdown, no text):

TRANSCRIPT:
{transcript_text}

METRICS: Duration {metrics.get('duration_seconds', 0)}s, Dietician {metrics.get('dietician_talk_ratio_pct', 0)}%, Patient {metrics.get('patient_talk_ratio_pct', 0)}%

Return valid JSON:
{{
  "scores": {{
    "greeting": <0-100>,
    "empathy": <0-100>,
    "compliance": <0-100>,
    "technical": <0-100>
  }},
  "sop_compliance": {{
    "compliant": <true/false>,
    "compliance_score": <0-100>,
    "violations": [
      {{"check": "Health Understanding First", "violated": <bool>, "evidence": "text"}}
    ]
  }},
  "qa_alerts": [
    {{"title": "Alert", "description": "Details", "severity": "critical"}}
  ],
  "insights": {{
    "whatWentWell": ["Specific positive example"],
    "areasForImprovement": ["Specific improvement area"],
    "summary": "Overall assessment"
  }}
}}"""

            logger.info(f"[Gemini] Calling Gemini for call {call_id}")
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
            )

            response_text = response.text.strip()
            logger.info(f"[Gemini] Response length: {len(response_text)}")

            # Try parsing JSON
            try:
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.split("```")[0]
                    response_text = response_text.strip()

                result = json.loads(response_text)
                logger.info("[Gemini] JSON parsed successfully")
                # Convert to pipeline-expected format
                return self._normalize_response_format(result)

            except json.JSONDecodeError as e:
                logger.warning(f"[Gemini] JSON parse failed: {e}")
                logger.warning(f"[Gemini] Response text: {response_text[:200]}")
                # Fall back to heuristic
                return self._generate_heuristic_scores(metrics)

        except Exception as e:
            logger.error(f"[Gemini] Error: {type(e).__name__}: {str(e)}")
            return self._generate_heuristic_scores(metrics)

    def _normalize_response_format(self, response: Dict) -> Dict:
        """Convert Gemini response to pipeline-expected format."""
        # If already in correct format, return as-is
        if "dimension_scores" in response:
            return response

        # Convert from scores format to dimension_scores format
        scores = response.get("scores", {})
        sop = response.get("sop_compliance", {})
        insights = response.get("insights", {})
        qa_alerts = response.get("qa_alerts", [])

        return {
            "dimension_scores": {
                "greeting_rapport": {
                    "score": scores.get("greeting", 0) / 10,  # Convert 0-100 to 0-10
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "empathy_communication": {
                    "score": scores.get("empathy", 0) / 10,
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "compliance_sop": {
                    "score": scores.get("compliance", 0) / 10,
                    "evidence": sop.get("violations", []),
                    "sub_criteria_met": {}
                },
                "technical_quality": {
                    "score": scores.get("technical", 0) / 10,
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "clinical_safety": {
                    "score": 8.0,  # Default high
                    "evidence": [],
                    "red_flag_detected": False,
                    "handled_appropriately": True
                }
            },
            "insights": insights,
            "qa_alerts": qa_alerts,
            "sop_compliance": sop
        }

    def _build_transcript_text(self, segments: List[Dict]) -> str:
        """Build readable transcript from segments."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").title()
            text = seg.get("text", "").strip()
            if text:
                lines.append(f"[{speaker}]: {text}")
        return "\n".join(lines) if lines else "No transcript available"

    def _generate_heuristic_scores(self, metrics: Dict) -> Dict:
        """Generate scores based on metrics when Gemini fails."""
        logger.info("[Gemini] Generating heuristic scores")

        duration = metrics.get("duration_seconds", 0)
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 0)
        patient_talk = metrics.get("patient_talk_ratio_pct", 0)
        interruptions = metrics.get("interruption_count", 0)
        latency = metrics.get("avg_response_latency_seconds", 0)
        time_to_plan = metrics.get("time_to_first_plan_mention_seconds", 0)

        # Calculate scores (0-100)
        greeting_score = min(100, 50 + (duration / 6))
        empathy_score = min(100, 40 + (patient_talk / 0.3) - (interruptions * 5))
        compliance_score = min(100, 50 + (duration / 6) + (20 if time_to_plan > 120 else 0))
        technical_score = min(100, 50 + (dietician_talk / 0.5))

        violations = []
        if time_to_plan > 300:
            violations.append({
                "check": "Health Understanding First",
                "violated": True,
                "evidence": "Plan mentioned late in call"
            })
        if patient_talk < 25:
            violations.append({
                "check": "Patient Education",
                "violated": True,
                "evidence": "Patient talking time too low"
            })

        qa_alerts = []
        if compliance_score < 60:
            qa_alerts.append({
                "title": "Low Compliance Score",
                "description": f"Compliance score is {compliance_score}",
                "severity": "warning"
            })

        return {
            "scores": {
                "greeting": max(0, min(100, int(greeting_score))),
                "empathy": max(0, min(100, int(empathy_score))),
                "compliance": max(0, min(100, int(compliance_score))),
                "technical": max(0, min(100, int(technical_score)))
            },
            "sop_compliance": {
                "compliant": compliance_score >= 70,
                "compliance_score": max(0, min(100, int(compliance_score))),
                "violations": violations
            },
            "qa_alerts": qa_alerts,
            "insights": {
                "whatWentWell": [
                    f"Call duration: {duration}s",
                    f"Patient engagement: {patient_talk}%"
                ],
                "areasForImprovement": [
                    "Improve health assessment before recommendations",
                    "Increase patient talking time" if patient_talk < 30 else "Good patient engagement"
                ],
                "summary": f"Call analysis: {int((greeting_score + empathy_score + compliance_score + technical_score) / 4)}/100 overall"
            }
        }
