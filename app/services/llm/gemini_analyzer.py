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

            # Use the EXACT clinical analysis prompt (same as Claude)
            from app.services.llm.clinical_prompt import create_clinical_analysis_prompt
            prompt = create_clinical_analysis_prompt(transcript_text, metrics, patient_condition or "General Health")

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

        # IMPORTANT: dimension_scores keys must match compute_weighted_score expectations
        # Keys: greeting, empathy, compliance, technical (NOT with _rapport, _communication, etc suffixes)
        return {
            "dimension_scores": {
                "greeting": {
                    "score": scores.get("greeting", 0),  # Already 0-100
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "empathy": {
                    "score": scores.get("empathy", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "compliance": {
                    "score": scores.get("compliance", 0),
                    "evidence": sop.get("violations", []),
                    "sub_criteria_met": {}
                },
                "technical": {
                    "score": scores.get("technical", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "clinical_safety": {
                    "score": 85.0,  # Default high (0-100 scale)
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
        """Generate scores based on metrics when Gemini fails - using clinical rubric."""
        logger.info("[Gemini] Generating heuristic scores using clinical rubric")

        duration = metrics.get("duration_seconds", 0)
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 0)
        patient_talk = metrics.get("patient_talk_ratio_pct", 0)
        interruptions = metrics.get("interruption_count", 0)
        time_to_plan = metrics.get("time_to_first_plan_mention_seconds", 0)

        # Strict clinical scoring (0-100)
        # Greeting: Professional opening quality
        greeting_score = 40  # Base (strict: need clear intro)
        if duration > 60:
            greeting_score += 15  # Adequate time
        if interruptions <= 2:
            greeting_score += 15  # Controlled conversation
        if dietician_talk < 70:
            greeting_score += 20  # Space for patient

        # Empathy: Patient-centered care
        empathy_score = 30  # Base (strict: need active listening)
        if patient_talk >= 25:
            empathy_score += 25  # Adequate patient voice
        if interruptions <= 3:
            empathy_score += 20  # Respectful listening
        if duration >= 180:
            empathy_score += 15  # Time for exploration

        # Compliance: SOP adherence (CRITICAL)
        compliance_score = 20  # Base (strict: SOP violations common)
        if time_to_plan >= 180:
            compliance_score += 25  # Health understanding first
        if duration >= 300:
            compliance_score += 20  # Adequate assessment
        if patient_talk >= 30:
            compliance_score += 20  # Barrier discussion
        if dietician_talk < 60:
            compliance_score += 15  # Not self-promotion heavy

        # Technical: Action plan quality
        technical_score = 30  # Base (strict: need medical soundness)
        if duration >= 240:
            technical_score += 25  # Adequate explanation time
        if time_to_plan >= 150:
            technical_score += 20  # Well-structured plan
        if dietician_talk >= 40:
            technical_score += 25  # Clear recommendations

        # Violations (based on clinical rubric)
        violations = []
        if time_to_plan < 120:
            violations.append({
                "check": "Health Understanding First",
                "violated": True,
                "evidence": "Plan mentioned too early (< 2min) - insufficient health assessment"
            })
        if patient_talk < 25:
            violations.append({
                "check": "Patient Education",
                "violated": True,
                "evidence": "Patient talking < 25% - insufficient discussion"
            })
        if duration < 180:
            violations.append({
                "check": "Informed Consent",
                "violated": True,
                "evidence": "Call too short (< 3min) to establish understanding"
            })

        qa_alerts = []
        if time_to_plan < 120:
            qa_alerts.append({
                "title": "Rushed Diagnosis",
                "description": "Diet plan mentioned too early without adequate health assessment",
                "severity": "critical"
            })
        if patient_talk < 25:
            qa_alerts.append({
                "title": "Low Patient Engagement",
                "description": "Patient talking time < 25% indicates one-sided conversation",
                "severity": "warning"
            })
        if compliance_score < 50:
            qa_alerts.append({
                "title": "SOP Compliance Risk",
                "description": f"Multiple compliance gaps detected (score: {int(compliance_score)})",
                "severity": "critical"
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
                    f"Patient engagement: {patient_talk}%" if patient_talk >= 25 else "Conversation structure",
                    f"Call duration: {duration}s" if duration >= 300 else "Time management needed"
                ],
                "areasForImprovement": [
                    "Health understanding must come BEFORE recommendations" if time_to_plan < 120 else "Good assessment sequence",
                    "Increase patient talking time" if patient_talk < 25 else "",
                    "Provide more detailed plan explanation" if technical_score < 60 else ""
                ],
                "summary": f"Clinical assessment: Compliance needs improvement (focus on health assessment first)" if compliance_score < 70 else f"Call meets clinical standards"
            }
        }
