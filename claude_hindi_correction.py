"""
Use Claude API to correct and reconstruct phonetically degraded Hindi transcripts
"""

import anthropic
import json
import os

raw_degraded_transcript = """कर दो तो आप दिलिगे अटे लिगाइब जब कर दो दो हलो हैंग हैंग अब
बेदेशा जरिया को इस वे लिए झाले प्रिवाज़ एपी जुब्रिये कर्या है, यह व्यूंट उपकि एल्यूराइब
रौटरित, प्रिशलिश देन रिजिएब आगेशर एपको। प्रफ्ट्राइब बजाज ना, पर हैंगा? यह तो मैं आइनो,
और यह रखना प्रफ्लमा और यह रिवार नहीं रहांगा जावाज़ आप्टावाज रहाज़ रहाज़ रहाज़ आप्टारिवाज।
but actually I told her absolutely आप प्सेड़ा जाता है झाल जाता है नहीं जाता है बेहाँ जेल खाल गाल
खौर तक वाल से अटुटें तेम प्रेश खाल शाल खाल खाल गाल है खाल खाल खाल खाल वाट ने ने ने सुट?
इटिएटिएन हीटेश कुमार वायों जी एसने, नका है आवे में की संग, जो जो जो जो जो जो जो करते हैं"""

# Create correction prompt
correction_prompt = f"""You are a Hindi language expert correcting degraded speech-to-text output from a medical consultation call.

CONTEXT:
- Original audio: 127.6 seconds, 8kHz 16kbps (heavily compressed)
- Call type: Dietician/Health consultation with Bajaj Finserv Health
- Participants: Dietician and patient discussing health issues
- Expected topics: Health advice, doctor consultation, general guidelines, lifestyle suggestions
- Key identifiable content: Patient name (Hitesh Kumar), Organization (Bajaj Finserv)

DEGRADED TRANSCRIPT (phonetically corrupted):
{raw_degraded_transcript}

YOUR TASK:
1. Identify corrupted words and map to likely correct Hindi words based on context
2. Reconstruct sentence structure to be meaningful
3. Infer missing content from medical consultation context
4. Preserve actual English fragments (like "but actually I told her")
5. Output ONLY the corrected Hindi transcript, nothing else

CORRECTION HINTS:
- "कर दो" = likely "करो" or action verb
- "दिलिगे/लिगाइब" = phonetic garbage, likely health-related term
- "हैंग" = "हाँ" (yes)
- "प्रफ्ट्राइब बजाज" = "प्रतिनिधि बजाज" or reference to Bajaj organization
- "हीटेश कुमार" = Patient name (Hitesh Kumar) - KEEP THIS
- Repeated words = Often indicates emphasis or filler words
- Medical context = Guidelines, health advice, consultation booking are likely topics

Output the best-effort reconstructed meaningful Hindi transcript:"""

try:
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": correction_prompt}
        ]
    )

    corrected_transcript = message.content[0].text

    # Extract entities
    entity_extraction_prompt = f"""Extract key information from this corrected Hindi transcript of a dietician consultation:

TRANSCRIPT:
{corrected_transcript}

Extract and list:
1. Patient name
2. Organization/Company
3. Main health topics discussed
4. Key advice given
5. Follow-up actions
6. Any locations mentioned
7. Professional name/title mentioned

Format as simple bullet-point list."""

    entity_message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": entity_extraction_prompt}
        ]
    )

    entities = entity_message.content[0].text

    # Save results to JSON
    results = {
        "status": "SUCCESS",
        "raw_degraded": raw_degraded_transcript,
        "raw_length": len(raw_degraded_transcript),
        "corrected_by_claude": corrected_transcript,
        "corrected_length": len(corrected_transcript),
        "approach": "Claude API Post-processing",
        "methodology": "Hindi language understanding + medical context + phonetic error correction",
        "model_used": "claude-opus-4-8",
        "extracted_entities": entities,
        "improvement": f"{len(corrected_transcript) - len(raw_degraded_transcript):+d} chars"
    }

    output_file = os.path.join(tempfile.gettempdir(), 'claude_corrected_transcript.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("SUCCESS")

except Exception as e:
    error_results = {
        "status": "FAILED",
        "error": str(e),
        "error_type": type(e).__name__
    }

    import tempfile
    output_file = os.path.join(tempfile.gettempdir(), 'claude_corrected_transcript.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(error_results, f, ensure_ascii=False, indent=2)

    print(f"ERROR: {str(e)[:100]}")
