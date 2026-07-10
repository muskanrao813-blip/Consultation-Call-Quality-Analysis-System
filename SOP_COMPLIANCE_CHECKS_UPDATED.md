# Updated SOP Compliance Checks

## ❌ Removed Checks
- ❌ HIPAA ID Verification (handled separately, not SOP for this system)
- ❌ HIPAA Privacy Compliance

## ✅ New Critical SOP Checks

### 1. **Health Understanding First** [CRITICAL]
**Definition:** Dietician explores patient's complete health context BEFORE providing any diet recommendations.

**What to Check:**
- [ ] Medical history explored (existing conditions, past medical events)
- [ ] Current medications discussed (affects nutrition absorption, interactions)
- [ ] Allergies identified and documented
- [ ] Lifestyle factors understood (work schedule, family situation, activity level)
- [ ] Dietary preferences and restrictions asked

**Violation Example:**
> At [2:15s]: "Based on what you told me, here's a 1200-calorie diet plan" - without asking about medications, allergies, or lifestyle. Patient might be on medications that contraindicate certain foods!

**Alert Severity:** CRITICAL ⚠️

---

### 2. **Personalized Plan** [CRITICAL]
**Definition:** Diet recommendations are customized to patient's specific health context, NOT a generic template.

**What to Check:**
- [ ] Recommendations specific to patient's conditions
- [ ] Considers medication-nutrient interactions
- [ ] Accounts for patient's schedule/lifestyle
- [ ] Includes cultural/preference considerations
- [ ] Not a one-size-fits-all plan

**Violation Example:**
> At [3:45s]: Dietician gives same 7-day meal plan template to every patient. Should be: "For your {condition} and because you work nights, here's a modified plan..."

**Alert Severity:** CRITICAL ⚠️

---

### 3. **No Self-Promotion** [CRITICAL]
**Definition:** Dietician provides unbiased advice focused on patient benefit, not promoting own products/supplements/entity.

**What to Check:**
- [ ] Recommendations based on patient need, not product availability
- [ ] No mention of dietician's own product line
- [ ] No affiliate products promoted unnecessarily
- [ ] Unbiased supplement recommendations (if needed)
- [ ] Evidence-based guidance not marketing

**Violation Example:**
> At [5:22s]: "I recommend my own brand of protein powder - it's the best" instead of "For your condition, consider any quality protein powder like..."

**Alert Severity:** CRITICAL ⚠️

---

### 4. **Informed Consent** [HIGH]
**Definition:** Patient explicitly understands and agrees with recommendations provided.

**What to Check:**
- [ ] Recommendations explained clearly
- [ ] Patient confirms understanding
- [ ] Patient given opportunity to ask questions
- [ ] Patient agrees to proposed plan
- [ ] Teach-back method used (patient explains plan back)

**Violation Example:**
> At [6:30s]: Dietician finishes consultation without confirming: "Does this plan work for you?" Patient might not understand or disagree!

**Alert Severity:** WARNING ⚠️

---

### 5. **Barrier Assessment** [HIGH]
**Definition:** Dietician explores and addresses patient's real constraints (cost, time, adherence, preferences).

**What to Check:**
- [ ] Affordability barriers discussed
- [ ] Time/schedule constraints explored
- [ ] Adherence challenges identified
- [ ] Food preferences considered
- [ ] Family/cultural factors acknowledged
- [ ] Solutions offered for identified barriers

**Violation Example:**
> Patient: "I work 12-hour shifts, when do I meal prep?"
> Dietician: "Just prepare all meals on Sunday" - didn't address shift worker's reality!

**Alert Severity:** WARNING ⚠️

---

### 6. **Patient Education** [MEDIUM]
**Definition:** Dietician explains WHY (nutritional science) not just WHAT (diet plan).

**What to Check:**
- [ ] Explains nutritional science behind recommendations
- [ ] Patient learns "why" not just "what to eat"
- [ ] Educational value for future decisions
- [ ] Empowers patient with knowledge
- [ ] References medical guidelines when appropriate

**Violation Example:**
> WEAK: "Eat more fiber"
> STRONG: "Your diabetes means your body processes sugar differently. Soluble fiber slows sugar absorption, preventing spikes. That's why I recommend oats, beans, and vegetables in each meal."

**Alert Severity:** INFO ℹ️

---

### 7. **Follow-up Plan** [HIGH]
**Definition:** Clear next steps, timeline, and communication plan provided.

**What to Check:**
- [ ] Follow-up appointment scheduled or timeline given
- [ ] How patient contacts dietician with questions
- [ ] Progress measurement points identified
- [ ] When to re-assess and adjust plan
- [ ] Emergency contacts or urgent care guidance

**Violation Example:**
> Missing: "Call me in 2 weeks, and we'll adjust based on your progress. You can reach me at [number]"

**Alert Severity:** WARNING ⚠️

---

## 📊 Severity Levels

| Severity | Meaning | Examples |
|----------|---------|----------|
| **CRITICAL** ⚠️ | Patient safety/quality risk | Generic plan without health assessment, self-promotion bias, no personalization |
| **WARNING** ⚠️ | Process gap | Missing informed consent, no barrier assessment, no follow-up plan |
| **INFO** ℹ️ | Improvement opportunity | Limited patient education, could explain science better |

---

## 🎯 Example Analysis

### Test Case: Diabetes Patient Consultation

**Patient Context:** 45yo, Type 2 diabetes, works night shifts, on metformin

**POOR Consultation:**
```
Dietician: "Here's a standard 1500-calorie diabetes diet plan"
Score: compliance = 35/100
Violations:
- ❌ Health Understanding First: Didn't discuss medications (metformin affects B12)
- ❌ Personalized Plan: Generic template, doesn't address night shift eating
- ⚠️ Barrier Assessment: Didn't explore schedule constraints
- ⚠️ Patient Education: Just gave plan, no explanation of why

CRITICAL ALERTS:
1. Generic diet plan provided without understanding night shift schedule
2. No discussion of medication-nutrient interactions (metformin + B12)
```

**GOOD Consultation:**
```
Dietician: "I see you're on metformin, which affects B12 absorption.
You work nights, so eating patterns are different.
For your diabetes, we need to prevent blood sugar spikes.
Here's a personalized night-shift plan with B12-rich foods:
[Customized plan based on patient's schedule and medication]
Do you have questions? Does this work with your lifestyle?"

Score: compliance = 92/100
No critical violations
Alerts: None
```

---

## 💡 Key Differences from Old System

| Old SOP Checks | New SOP Checks |
|---|---|
| HIPAA verification | Health understanding FIRST |
| Generic compliance | Personalization required |
| Closing scripts | Barrier assessment |
| Medical screening (generic) | No self-promotion focus |
| | Patient education quality |
| | Informed consent verification |
| | Follow-up plan clarity |

---

## 🚀 Claude Will Now Detect

✅ Consultations that jump to diet plan without health assessment  
✅ Generic plans applied to all patients  
✅ Dietician promoting own products  
✅ Patients not understanding why recommendations matter  
✅ Missing follow-up communication  
✅ Unaddressed patient barriers (cost, schedule, preferences)  

---

## 📝 Training Focus Areas

When compliance score is LOW, training should focus on:

1. **Health Assessment Order** - Always: explore → understand → personalize → educate → confirm
2. **Personalization Skills** - Adapt recommendations to patient's real life
3. **Bias Awareness** - Recognize when promoting own products vs patient benefit
4. **Patient Engagement** - Understand barriers, not just give advice
5. **Communication** - Explain science, ensure understanding, confirm agreement

---

## ✨ Result

Portal will now flag consultations that:
- Skip health assessment and jump to generic diet plans
- Give one-size-fits-all recommendations
- Promote dietician's own products/entity
- Don't explore or address patient barriers
- Lack clear follow-up communication
- Don't educate patient on nutritional science

**This directly addresses patient care quality and consultant accountability!**
