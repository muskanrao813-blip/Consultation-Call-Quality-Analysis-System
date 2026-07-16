#!/usr/bin/env python3
import sys, io, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"
calls = requests.get(f"{BASE}/api/calls").json()

print("="*70)
print("1. LIST API — qaAlerts check")
print("="*70)
for c in calls:
    alerts = c.get('qaAlerts') or []
    bad = [a for a in alerts if not a.get('title')]
    print(f"  {c['id'][:8]} | alerts={len(alerts)} | alerts_missing_title={len(bad)} | score={c.get('overall_weighted_score')}")

print("\n" + "="*70)
print("2. TRANSCRIPT SPEAKER LABELS in diarized_lines (DB)")
print("="*70)
for c in calls:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    lines = d.get('transcript', {}).get('diarized_lines') or []
    speakers = set(l.get('speaker','?') for l in lines)
    sample = lines[:3] if lines else []
    print(f"\n  {c['id'][:8]} | {c['patient_name']:22} | lines={len(lines)} | speakers={speakers}")
    for l in sample:
        print(f"    [{l.get('speaker')}]: {str(l.get('text',''))[:60]}")

print("\n" + "="*70)
print("3. ENTITIES — call_purpose check (no diabetes inference)")
print("="*70)
for c in calls:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    ents = d.get('entities') or {}
    print(f"  {c['patient_name']:22} | purpose: {str(ents.get('call_purpose',''))[:60]}")
    print(f"  {'':22} | health_topics: {ents.get('health_topics','')}")

print("\n" + "="*70)
print("4. INSIGHTS — diabetes in text check")
print("="*70)
for c in calls:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    ins = d.get('insights') or {}
    summary = ins.get('summary','')
    improvements = ins.get('areasForImprovement',[])
    # Check for diabetes in transcript
    lines = d.get('transcript', {}).get('diarized_lines') or []
    tr_text = ' '.join(l.get('text','') for l in lines).lower()
    diabet_in_transcript = 'diabet' in tr_text or 'sugar' in tr_text
    diabet_in_summary = 'diabet' in summary.lower()
    diabet_in_improvements = any('diabet' in i.lower() for i in improvements)
    print(f"  {c['patient_name']:22} | diabet_in_transcript={diabet_in_transcript} | diabet_in_summary={diabet_in_summary} | diabet_in_improvements={diabet_in_improvements}")
