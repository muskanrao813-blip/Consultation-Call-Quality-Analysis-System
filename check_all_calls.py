#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"

calls = requests.get(f"{BASE}/api/calls").json()
completed = [c for c in calls if c["status"] == "completed"]
pending = [c for c in calls if c["status"] in ("pending", "processing")]

print(f"{'='*60}")
print(f"TOTAL: {len(calls)}  COMPLETED: {len(completed)}  IN QUEUE: {len(pending)}")
print(f"{'='*60}\n")

all_ok = True
for c in completed:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    s = d.get("scores") or {}
    ins = d.get("insights") or {}
    entities = d.get("entities") or {}
    alerts = d.get("qaAlerts") or []
    lines = (d.get("transcript") or {}).get("diarized_lines") or []

    checks = {
        "patient_name":    bool(d.get("patient_name") and d["patient_name"] not in ("Unknown Patient","Unknown","")),
        "dietician_name":  bool(d.get("dietician_name")),
        "scores non-zero": any(v > 0 for v in s.values()),
        "overall score":   bool(d.get("overall_weighted_score")),
        "qa alerts":       len(alerts) > 0,
        "summary":         bool(ins.get("summary")),
        "whatWentWell":    len(ins.get("whatWentWell", [])) > 0,
        "improvements":    len(ins.get("areasForImprovement", [])) > 0,
        "transcript turns":len(lines) > 0,
        "entities":        bool(entities.get("customer_name")),
    }

    passed = sum(checks.values())
    total = len(checks)
    status = "ALL OK" if passed == total else f"PARTIAL {passed}/{total}"
    if passed < total:
        all_ok = False

    print(f"[{status}] {c['id'][:8]}...  Patient: {d.get('patient_name')}  Score: {d.get('overall_weighted_score')}")
    print(f"  Scores: greeting={s.get('greeting')} empathy={s.get('empathy')} compliance={s.get('compliance')} technical={s.get('technical')}")
    print(f"  QA Alerts: {len(alerts)}  Transcript turns: {len(lines)}  Outcome: {entities.get('call_outcome')}")
    missing = [k for k, v in checks.items() if not v]
    if missing:
        print(f"  MISSING: {', '.join(missing)}")
    print()

print("="*60)
print("RESULT:", "ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED - see MISSING above")
print("="*60)
