#!/usr/bin/env python3
import sys, io, json, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = "http://localhost:8000"

calls = requests.get(f"{BASE}/api/calls").json()
print("=== SOP COMPLIANCE CHECK ===")
for c in calls:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    # Get sop_compliance from rubric raw_llm_response
    rubric = d.get('rubric_scores', [])
    sop_compliant_claude = None
    sop_score_claude = None
    for r in rubric:
        raw = r.get('raw_llm_response') or {}
        if isinstance(raw, dict) and 'sop_compliance' in raw:
            sop_compliant_claude = raw['sop_compliance'].get('compliant')
            sop_score_claude = raw['sop_compliance'].get('score')
            break
        if isinstance(raw, dict) and 'insights' in raw:
            # first rubric score has insights - check if sop_compliance also present
            pass
    alerts = d.get('qaAlerts') or []
    critical = sum(1 for a in alerts if a.get('severity') == 'critical')
    print(f"  {c['id'][:8]} | score={d.get('overall_weighted_score')} | sop_claude_compliant={sop_compliant_claude} | sop_claude_score={sop_score_claude} | critical_alerts={critical}")

print("\n=== QA ALERTS ACROSS CALLS ===")
# Aggregate all alert titles across all calls
from collections import defaultdict
alert_map = defaultdict(list)  # title -> [call_id, ...]
for c in calls:
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    for a in (d.get('qaAlerts') or []):
        alert_map[a.get('title','')].append(c['id'][:8])

print(f"Unique alert types: {len(alert_map)}")
print(f"Total alerts across all calls: {sum(len(v) for v in alert_map.values())}")
print("\nTop 10 recurring alerts:")
for title, call_ids in sorted(alert_map.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  ({len(call_ids)}/6 calls) {title[:70]}")
