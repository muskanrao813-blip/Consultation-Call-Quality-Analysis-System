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
            # Disable SSL verification for corporate proxy
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
        """Analyze call transcript against 6 rubric dimensions using Gemini."""
        try:
            client = self._get_client()

            # Build transcript text from segments
            transcript_text = self._build_transcript_text(transcript_segments)

            # Build analysis prompt
            prompt = self._build_analysis_prompt(
                transcript_text,
                metrics,
                dietician_name,
                patient_condition
            )

            logger.info(f"[Gemini QA] Analyzing call {call_id} with Gemini...")

            # Call Gemini with JSON response mode
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
            )

            # Parse response as JSON
            response_text = response.text.strip()
            logger.info(f"[Gemini QA] Response length: {len(response_text)} chars")
            logger.info(f"[Gemini QA] First 500 chars: {response_text[:500]}")

            # Try to extract JSON from response
            try:
                # Try parsing as JSON directly
                analysis_result = json.loads(response_text)
                logger.info(f"[Gemini QA] Successfully parsed JSON response")
            except json.JSONDecodeError as parse_err:
                logger.warning(f"[Gemini QA] JSON parse error: {parse_err}")
                # Try extracting JSON from markdown code block
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                    try:
                        analysis_result = json.loads(json_str)
                        logger.info(f"[Gemini QA] Extracted JSON from markdown block")
                    except json.JSONDecodeError as md_err:
                        logger.warning(f"[Gemini QA] Markdown JSON parse error: {md_err}, using fallback")
                        analysis_result = self._generate_fallback_scores(metrics)
                else:
                    logger.warning(f"[Gemini QA] No JSON found in response, using fallback")
                    logger.warning(f"[Gemini QA] Full response: {response_text}")
                    analysis_result = self._generate_fallback_scores(metrics)

            logger.info("[Gemini QA] Analysis complete")
            return analysis_result

        except Exception as e:
            logger.error(f"[Gemini QA] Error: {type(e).__name__}: {str(e)}")
            logger.info("Falling back to heuristic scores")
            return self._generate_fallback_scores(metrics)

    def _build_transcript_text(self, segments: List[Dict]) -> str:
        """Build readable transcript from segments."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").title()
            text = seg.get("text", "").strip()
            if text:
                lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    def _build_analysis_prompt(
        self,
        transcript: str,
        metrics: Dict,
        dietician_name: str,
        patient_condition: str
    ) -> str:
        """Build the analysis prompt for Gemini using clinical SOP framework."""
        from app.services.llm.clinical_prompt import create_clinical_analysis_prompt

        # Use the exact same prompt that Claude uses
        prompt = create_clinical_analysis_prompt(transcript, metrics, patient_condition)
        logger.info(f"[Gemini QA] Using clinical analysis prompt (same as Claude)")
        return prompt

{{
  "dimension_scores": {{
    "discovery_assessment": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<exact quote from transcript>", "timestamp_s": <number>}}
      ],
      "sub_criteria_met": {{
        "medical_history": <boolean>,
        "lifestyle_activity": <boolean>,
        "dietary_habits": <boolean>,
        "goal_alignment": <boolean>,
        "allergy_screening": <boolean>
      }}
    }},
    "empathy_communication": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<exact quote>", "timestamp_s": <number>}}
      ],
      "sub_criteria_met": {{
        "empathy_tone": <boolean>,
        "conversation_balance": <boolean>,
        "active_listening": <boolean>,
        "patient_engagement": <boolean>,
        "sentiment": "<positive|neutral|negative>"
      }}
    }},
    "rushed_forced_detection": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<quote>", "timestamp_s": <number>}}
      ],
      "is_forced": <boolean>,
      "is_missing_discovery": <boolean>
    }},
    "adherence_counselling": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<quote>", "timestamp_s": <number>}}
      ],
      "sub_criteria_met": {{
        "motivation": <boolean>,
        "importance_explained": <boolean>,
        "practical_implementation": <boolean>,
        "barriers_addressed": <boolean>
      }}
    }},
    "consultation_completeness": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<quote>", "timestamp_s": <number>}}
      ],
      "sub_criteria_met": {{
        "goals_documented": <boolean>,
        "bmi_reviewed": <boolean>,
        "conditions_incorporated": <boolean>,
        "followup_shared": <boolean>
      }}
    }},
    "clinical_safety": {{
      "score": <float 0-10>,
      "evidence": [
        {{"quote": "<quote>", "timestamp_s": <number>}}
      ],
      "red_flag_detected": <boolean>,
      "handled_appropriately": <boolean|null>
    }}
  }},
  "feedback_summary": [
    "<actionable feedback point 1>",
    "<actionable feedback point 2>",
    "<actionable feedback point 3>"
  ],
  "qa_alerts": [
    {{"title": "Alert Title", "severity": "<critical|warning|info>", "description": "Details"}}
  ]
}}

Score based on actual evidence from transcript. Be fair but rigorous."""

    def _generate_fallback_scores(self, metrics: Dict) -> Dict:
        """Generate fallback scores if Gemini analysis fails."""
        logger.info("[Gemini QA] Using fallback heuristic analyzer")
        from app.services.llm.heuristic_analyzer import HeuristicAnalyzer
        analyzer = HeuristicAnalyzer()
        result = analyzer.analyze_all_dimensions(
            [],
            metrics,
            "fallback",
            "Unknown",
            "Unknown"
        )
        # Ensure all required fields are present
        result.setdefault("qa_alerts", [])
        result.setdefault("insights", {
            "whatWentWell": ["Consultation completed"],
            "areasForImprovement": ["Continue to refine consultation approach"],
            "summary": "Consultation analysis completed using heuristic scoring"
        })
        logger.info("[Gemini QA] Fallback scores generated with feedback")
        return result
