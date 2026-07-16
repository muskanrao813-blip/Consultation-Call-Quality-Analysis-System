#!/usr/bin/env python3
import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d = requests.get('http://localhost:8000/api/calls/d63ae442-52be-4f02-807b-b510563818ca').json()
print("Patient:", d.get('patient_name'))
print("Entities call_purpose:", d.get('entities', {}).get('call_purpose'))
print("Entities health_topics:", d.get('entities', {}).get('health_topics'))
print()
print("TRANSCRIPT:")
for l in d.get('transcript', {}).get('diarized_lines', []):
    print(f"  [{l['speaker']}]: {l['text']}")
print()
# check if diabetes in transcript
full_text = d.get('transcript', {}).get('text', '')
print("'diabet' in transcript:", 'diabet' in full_text.lower())
print("'sugar' in transcript:", 'sugar' in full_text.lower())
print()
# show insights to see where diabetes came from
rubric = d.get('rubric_scores', [])
for r in rubric:
    raw = r.get('raw_llm_response') or {}
    if isinstance(raw, dict) and raw.get('insights', {}).get('summary'):
        print("Summary snippet:", raw['insights']['summary'][:300])
        break
