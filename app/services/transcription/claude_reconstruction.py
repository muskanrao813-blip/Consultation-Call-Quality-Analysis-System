"""
Claude CLI-Based Intelligent Transcript Reconstruction
Uses Claude to fix phonetic degradation and extract entities from degraded transcripts
"""

import subprocess
import json
import logging
import tempfile
import os
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ClaudeReconstructor:
    """
    Uses Claude CLI to intelligently reconstruct degraded transcripts
    Fixes phonetic errors, adds context, extracts entities
    """

    def __init__(self):
        self.claude_path = None
        self.claude_available = self._check_claude_available()

    def _check_claude_available(self) -> bool:
        """Check if Claude CLI is available"""
        import pathlib

        # Try multiple ways to find Claude
        possible_paths = [
            "claude",  # Direct command
            str(pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude"),
            str(pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"),
        ]

        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.claude_path = path
                    logger.info(f"Claude CLI available at: {path}")
                    return True
            except Exception:
                pass

        logger.warning("Claude CLI not found in any expected location")
        return False

    def reconstruct_transcript(
        self,
        raw_transcript: str,
        language: str = "ENGLISH"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Reconstruct degraded transcript using Claude CLI

        Args:
            raw_transcript: Raw transcript from Whisper/Groq (potentially degraded)
            language: Detected language (ENGLISH or HINDI)

        Returns:
            Tuple of (reconstructed_transcript, entities)
        """
        if not self.claude_available:
            logger.warning("Claude CLI not available, returning raw transcript")
            return raw_transcript, {}

        if not raw_transcript or len(raw_transcript.strip()) == 0:
            logger.warning("Empty transcript provided")
            return "", {}

        # Create prompt based on language
        if language == "HINDI":
            prompt = self._create_hindi_prompt(raw_transcript)
        else:
            prompt = self._create_english_prompt(raw_transcript)

        try:
            # Call Claude CLI via stdin (no file permission needed)
            # Use explicit UTF-8 encoding to handle multilingual text (Hindi, English, etc.)
            result = subprocess.run(
                [self.claude_path],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"Claude CLI error: {result.stderr}")
                return raw_transcript, {}

            # Parse Claude's response
            response_text = result.stdout.strip()
            reconstructed, entities = self._parse_claude_response(
                response_text,
                language
            )

            logger.info(f"Reconstruction complete: {len(reconstructed)} chars")
            logger.info(f"Entities extracted: {list(entities.keys())}")

            return reconstructed, entities

        except subprocess.TimeoutExpired:
            logger.error("Claude CLI request timed out")
            return raw_transcript, {}
        except Exception as e:
            logger.error(f"Reconstruction failed: {e}")
            return raw_transcript, {}

    def _create_english_prompt(self, raw_transcript: str) -> str:
        """Create prompt for English transcript reconstruction"""
        return f"""You are a speech-to-text error correction specialist for healthcare calls.

TASK: Fix transcription errors in this degraded English healthcare transcript while preserving the exact conversation.

COMMON STT ERRORS TO FIX (examples):
- "TBS Bayai" → "TVS Bajaj" (similar phonetics)
- "Beep beep beep" → silence or noise markers
- "the book of" → "the telehealth"
- Repeated fragments (stuttering artifacts)
- Missing punctuation despite clear sentence boundaries

RULES:
1. Fix obvious phonetic confusions using healthcare domain knowledge
2. Remove duplicate/repeated words (except natural repetition for emphasis)
3. Correct obvious letter/number confusions
4. Add natural punctuation where sentence boundaries are clear
5. Preserve exact speaking order and all topics covered
6. DO NOT add words, explanations, or context not in the original
7. DO NOT remove any medical information or health mentions

TRANSCRIPT TO FIX:
{raw_transcript}

Respond with ONLY valid JSON (no markdown, no extra text):
{{
    "reconstructed_transcript": "The fixed transcript with all corrections applied",
    "entities": {{"patient_name": "exact name if stated", "organization": "exact org if stated"}},
    "confidence": "high/medium/low based on how confident you are"
}}"""

    def _create_hindi_prompt(self, raw_transcript: str) -> str:
        """Create prompt for Hindi transcript reconstruction"""
        return f"""आप एक speech-to-text त्रुटि सुधार विशेषज्ञ हैं जो स्वास्थ्य सेवा कॉल्स के लिए काम करते हैं।

कार्य: इस degraded Hindi transcript में transcription errors को ठीक करें, लेकिन बातचीत को पूरी तरह बचाएं।

आम STT त्रुटियों के उदाहरण (ये ठीक करें):
- "बीड़ी अग्याज" → "benefits" (फोनेटिक भ्रम)
- "हलो हलो" → "नमस्ते" (greeting confusion)
- "विक्त" → "विकल्प" (partial word)
- "चेवियरस" → "service/benefit" (severe distortion)
- दोहराए गए fragments (स्टटरिंग artifacts)
- लापता विराम चिह्न

नियम:
1. Healthcare domain knowledge से obvious phonetic confusions को ठीक करें
2. बिना प्राकृतिक जोर के दोहराए गए शब्दों को हटाएं
3. स्पष्ट sentence boundaries पर विराम चिह्न जोड़ें
4. बोलने का सही क्रम बचाएं
5. सभी medical information/health mentions बचाएं
6. Original में नहीं है ऐसे शब्द/context न जोड़ें
7. कोई जानकारी न हटाएं

ठीक करने के लिए TRANSCRIPT:
{raw_transcript}

केवल valid JSON respond करें (markdown नहीं, कोई extra text नहीं):
{{
    "reconstructed_transcript": "सभी corrections के साथ ठीक किया गया transcript",
    "entities": {{"patient_name": "exact नाम अगर कहा गया", "organization": "exact organization अगर कहा गया"}},
    "confidence": "high/medium/low"
}}"""

    def _parse_claude_response(
        self,
        response_text: str,
        language: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Parse Claude's JSON response (handles markdown-wrapped JSON and incomplete responses)"""
        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]  # Remove ```json
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]  # Remove ```
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]  # Remove closing ```

            cleaned = cleaned.strip()

            # Try to extract JSON object if incomplete
            # Find the opening { and try to parse from there
            json_start = cleaned.find('{')
            if json_start != -1:
                # Work backwards from end to find the last }
                json_end = cleaned.rfind('}')
                if json_end > json_start:
                    json_str = cleaned[json_start:json_end + 1]
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If that fails, try the original
                        data = json.loads(cleaned)
                else:
                    data = json.loads(cleaned)
            else:
                data = json.loads(cleaned)

            reconstructed = data.get("reconstructed_transcript", "")
            entities = data.get("entities", {})
            confidence = data.get("confidence", "Unknown")

            logger.info(f"Reconstruction confidence: {confidence}")
            return reconstructed, entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response preview: {response_text[:300]}")
            return "", {}
        except Exception as e:
            logger.error(f"Error parsing Claude response: {e}")
            return "", {}
