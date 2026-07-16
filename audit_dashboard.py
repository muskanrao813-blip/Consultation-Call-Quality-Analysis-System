#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"

print("="*70)
print("DASHBOARD AUDIT — ALL FIELDS")
print("="*70)

# ── LIST VIEW ──────────────────────────────────────────────────────────────
calls = requests.get(f"{BASE}/api/calls").json()
print(f"\n[LIST /api/calls]  {len(calls)} calls")
print(f"{'ID':10} {'Patient':22} {'Dietician':12} {'Status':12} {'Score':8} {'Scores(G/E/C/T)':20} {'Alerts':8} {'Duration':10}")
print("-"*100)
for c in calls:
    s = c.get('scores') or {}
    score_str = f"{s.get('greeting',0)}/{s.get('empathy',0)}/{s.get('compliance',0)}/{s.get('technical',0)}"
    print(f"{str(c['id'])[:8]:10} {str(c.get('patient_name',''))[:22]:22} {str(c.get('dietician_name',''))[:12]:12} {c.get('status',''):12} {str(c.get('overall_weighted_score','NULL')):8} {score_str:20} {len(c.get('qaAlerts',[])):8} {str(c.get('call_duration_seconds','NULL')):10}")

# ── DETAIL VIEW ────────────────────────────────────────────────────────────
print(f"\n\n[DETAIL /api/calls/:id]  Checking each completed call")
print("="*70)

for c in calls:
    if c['status'] != 'completed':
        continue
    d = requests.get(f"{BASE}/api/calls/{c['id']}").json()
    s = d.get('scores') or {}
    ins = d.get('insights') or {}
    ents = d.get('entities') or {}
    alerts = d.get('qaAlerts') or []
    lines = (d.get('transcript') or {}).get('diarized_lines') or []
    rubric = d.get('rubric_scores') or []

    print(f"\nCall {c['id'][:8]}... | Patient: {d.get('patient_name')} | Dietician: {d.get('dietician_name')}")
    print(f"  overall_weighted_score : {d.get('overall_weighted_score')}")
    print(f"  scores                 : greeting={s.get('greeting')} empathy={s.get('empathy')} compliance={s.get('compliance')} technical={s.get('technical')}")
    print(f"  rubric_scores          : {len(rubric)} dims → {[r.get('dimension') for r in rubric]}")
    print(f"  qaAlerts               : {len(alerts)} total | critical={sum(1 for a in alerts if a.get('severity')=='critical')}")

    # Check for duplicate alerts
    titles = [a.get('title','') for a in alerts]
    dupes = [t for t in titles if titles.count(t) > 1]
    if dupes:
        print(f"  DUPLICATE ALERTS       : {set(dupes)}")

    print(f"  insights.summary       : {len(ins.get('summary',''))} chars")
    print(f"  insights.whatWentWell  : {len(ins.get('whatWentWell',[]))} items")
    print(f"  insights.areasForImp   : {len(ins.get('areasForImprovement',[]))} items")
    print(f"  transcript lines       : {len(lines)} | speakers: {set(l.get('speaker') for l in lines)}")
    print(f"  entities               : customer_name={ents.get('customer_name')} | outcome={ents.get('call_outcome')} | language={ents.get('call_language')}")
    print(f"  recording_url          : {'set' if d.get('recording_url') else 'MISSING'}")
    print(f"  call_duration_seconds  : {d.get('call_duration_seconds')}")

    # Check blank fields
    blank = []
    if not d.get('patient_name') or d['patient_name'] in ('Unknown Patient', ''):
        blank.append('patient_name')
    if not d.get('dietician_name'):
        blank.append('dietician_name')
    if not s.get('greeting') and not s.get('empathy'):
        blank.append('scores')
    if not ins.get('summary'):
        blank.append('insights.summary')
    if not lines:
        blank.append('transcript')
    if blank:
        print(f"  BLANK FIELDS           : {blank}")

# ── DIETICIAN REPORTS ──────────────────────────────────────────────────────
print(f"\n\n[DIETICIAN REPORTS /api/dieticians]")
print("="*70)
dieticians_data = requests.get(f"{BASE}/api/dieticians").json()
print(f"Dieticians: {len(dieticians_data)}")
for d in dieticians_data:
    det = d['dietician']
    gaps = d['trainingGaps']
    print(f"\n  Name      : {det['name']}")
    print(f"  avgScore  : {det['avgScore']}")
    print(f"  breaches  : {det['sopBreaches']}")
    print(f"  aiStatus  : {det['aiStatus']}")
    print(f"  trend     : {det['trend']} ({det['trendDirection']})")
    print(f"  trendVals : {det['trendValues']}")
    print(f"  gaps      : {len(gaps)}")

    # Check duplicate gaps
    gap_titles = [g['title'] for g in gaps]
    dup_gaps = [t for t in gap_titles if gap_titles.count(t) > 1]
    if dup_gaps:
        print(f"  DUPLICATE GAPS: {set(dup_gaps)}")

    # Gap category breakdown
    cats = {}
    for g in gaps:
        cats[g['urgency']] = cats.get(g['urgency'], 0) + 1
    print(f"  urgency breakdown: {cats}")

print("\n" + "="*70)
print("AUDIT COMPLETE")
