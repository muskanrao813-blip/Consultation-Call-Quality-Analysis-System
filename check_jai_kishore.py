#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d = requests.get('http://localhost:8000/api/calls/a4c17545-4b23-4e34-a5d1-005a99912e4b').json()
print("Patient:", d.get('patient_name'))
print("Recording URL:", d.get('recording_url'))
print("\nFull transcript text:")
print(d.get('transcript', {}).get('text', ''))
print("\nDiarized lines:")
for l in d.get('transcript', {}).get('diarized_lines', []):
    print(f"  [{l['speaker']}]: {l['text']}")
