"""Clinical-focused LLM analyzer using Claude CLI with improved prompts."""

import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, List
from app.services.llm.base import LLMProvider
from app.services.llm.clinical_prompt import create_clinical_analysis_prompt

logger = logging.getLogger(__name__)


class ClinicalAnalyzer(LLMProvider):
    """Uses Claude CLI for clinical-specific call analysis."""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str,
        patient_condition: str = "Diabetes"
    ) -> Dict:
        """Analyze using Claude CLI with clinical prompts."""
        try:
            logger.info(f"[Clinical] Analyzing call {call_id} for {patient_condition}...")

            # Format transcript
            transcript_text = self._format_transcript(transcript_segments)

            # Create clinical analysis prompt
            prompt = create_clinical_analysis_prompt(transcript_text, metrics, patient_condition)

            # Call Claude CLI
            result = self._call_claude_cli(prompt)

            logger.info(f"[Clinical] Analysis complete for {call_id}")

            # Transform Claude response to match our schema
            return self._transform_to_schema(result)

        except Exception as e:
            logger.error(f"[Clinical] Error: {e}")
            raise

    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format segments into readable transcript."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").replace("_", " ").title()
            text = seg.get("text", "")
            timestamp = seg.get("start_s", 0)
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")
        return "\n".join(lines)

    def _call_claude_cli(self, prompt: str) -> Dict:
        """Call Claude CLI using its non-interactive print mode."""
        try:
            import pathlib

            claude_npm = pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
            claude_cmd = str(claude_npm) if claude_npm.exists() else "claude"

            logger.info("[Clinical] Calling Claude CLI with clinical prompt")

            cmd = [
                claude_cmd,
                "-p",
                prompt,
                "--output-format",
                "json",
                "--permission-mode",
                "bypassPermissions",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )

            output = (result.stdout or result.stderr or "").strip()
            if not output:
                raise RuntimeError("Claude CLI returned empty output")

            logger.info(f"[Clinical] Got response ({len(output)} chars)")

            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                import re
                json_pattern = r'\{[\s\S]*"scores"[\s\S]*\}'
                match = re.search(json_pattern, output)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    match = re.search(r'\{[\s\S]*\}', output)
                    if match:
                        parsed = json.loads(match.group(0))
                    else:
                        raise ValueError("No JSON found in response")

            if isinstance(parsed, dict) and parsed.get("is_error"):
                detail = parsed.get("result") or parsed.get("message") or output
                raise RuntimeError(f"Claude CLI rejected the request: {detail}")

            if isinstance(parsed, dict) and "result" in parsed and isinstance(parsed["result"], str):
                result_text = parsed["result"].strip()
                if result_text.startswith("{"):
                    return json.loads(result_text)
                if result_text:
                    return {"text": result_text}

            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI failed with code {result.returncode}: {output[:1000]}")

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[Clinical] JSON parse error: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("[Clinical] Timeout after 5 minutes")
            raise
        except Exception as e:
            logger.error(f"[Clinical] Error: {e}")
            raise

    def _transform_to_schema(self, claude_response: Dict) -> Dict:
        """Transform Claude response to match FE schema."""
        scores = claude_response.get("scores", {})
        sop = claude_response.get("sop_compliance", {})
        alerts = claude_response.get("qa_alerts", [])
        insights = claude_response.get("insights", {})

        # Calculate overall compliance score
        compliance_score = sop.get("compliance_score", 0)
        sop_compliant = sop.get("compliant", True)

        # Transform SOP violations to QA alerts if not already done
        qa_alerts = []
        for alert in alerts:
            qa_alerts.append({
                "title": alert.get("title"),
                "description": alert.get("description"),
                "severity": alert.get("severity", "info"),
                "status": "active"
            })

        # Add violation-based alerts
        for violation in sop.get("violations", []):
            if violation.get("violated"):
                qa_alerts.append({
                    "title": f"SOP Violation: {violation.get('check')}",
                    "description": violation.get("evidence", ""),
                    "severity": "critical",
                    "status": "active"
                })

        return {
            "dimension_scores": {
                "greeting": {
                    "score": scores.get("greeting", 0),
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
                    "evidence": [],
                    "sub_criteria_met": sop.get("violations", [])
                },
                "technical": {
                    "score": scores.get("technical", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                }
            },
            "scores": scores,  # Include raw scores for convenience
            "sop_compliance": {
                "compliant": sop_compliant,
                "score": compliance_score,
                "violations": sop.get("violations", [])
            },
            "qa_alerts": qa_alerts,
            "transcript_tags": claude_response.get("transcript_tags", {}),
            "insights": {
                "whatWentWell": insights.get("whatWentWell", []),
                "areasForImprovement": insights.get("areasForImprovement", []),
                "summary": insights.get("summary", ""),
                "trainingGaps": insights.get("trainingGapRecs", [])
            },
            "feedback_summary": insights.get("areasForImprovement", [])
        }
