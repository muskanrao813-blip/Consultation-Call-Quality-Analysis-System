# Updated Analysis Examples - New SOP Compliance Focus

## Example 1: ❌ POOR Consultation (Generic Plan Without Assessment)

### Transcript
```
[0:00] Dietician: "Good morning, I'm Priya, your dietician. Let's talk about your diet."
[0:15] Patient: "Hi, I have diabetes and I'm trying to lose weight."
[0:30] Dietician: "Great! Here's my standard 1500-calorie diabetes diet plan. Follow this for 2 weeks."
[1:45] Patient: "What about my work schedule? I work nights..."
[2:00] Dietician: "Just adjust the times. This plan works for everyone."
[2:30] Patient: "Okay... I guess."
[2:45] Dietician: "Great! Call me in a month."
```

### Analysis Output (OLD System)
```
Compliance Score: 60/100
Feedback: "Ensure all consultation elements are covered"
Status: Not specific enough to fix
```

### Analysis Output (NEW System - Updated SOP)
```
Compliance Score: 35/100 ⚠️ CRITICAL

VIOLATIONS:
1. ❌ Health Understanding First [CRITICAL]
   Violated at [0:30s]
   Evidence: "No exploration of medical history, current medications, or lifestyle 
   before providing diet plan. Jumped straight to generic plan."
   Impact: Patient might be on medications that contraindicate certain foods. 
   Night shift work fundamentally changes meal timing.

2. ❌ Personalized Plan [CRITICAL]
   Violated at [2:00s]
   Evidence: "Dietician dismissed patient's work schedule concern: 'This plan works 
   for everyone.' Generic plan not tailored to night shift worker."
   Impact: Patient will likely not adhere because plan doesn't fit reality.

3. ⚠️ Barrier Assessment [WARNING]
   Violated at [1:45s-2:00s]
   Evidence: "Patient mentioned night shifts, dietician didn't explore impact on 
   meal prep time, sleep schedule, food availability during shifts."
   Impact: Missed opportunity to address adherence barrier.

4. ⚠️ Informed Consent [WARNING]
   Violated at [2:30s]
   Evidence: "Patient's 'Okay... I guess' shows uncertainty, not clear agreement. 
   Dietician didn't verify understanding or confirm commitment."
   Impact: Weak commitment increases failure risk.

QA ALERTS:
[CRITICAL] Generic Diet Plan Without Health Assessment
- At 0:30s: Provided standard plan without understanding patient's:
  - Medications (which could affect nutrient needs)
  - Work schedule (night shift = different meal timing)
  - Family situation
  - Lifestyle constraints
- Recommendation: Always assess FIRST, then personalize

[CRITICAL] Dismissing Patient's Real Barriers
- At 2:00s: Patient mentioned night shifts, dietician said "plan works for everyone"
- This is a red flag for non-personalized care
- Recommendation: Explore constraints, offer solutions

[WARNING] Weak Informed Consent
- At 2:30s: Patient's hesitant "Okay... I guess" indicates uncertainty
- Recommendation: Confirm: "Does this plan work for you? Do you have questions?"

COACHING RECOMMENDATIONS:
1. HEALTH ASSESSMENT FIRST
   Current: Jumps to generic plan immediately
   Target: Explore patient's health context BEFORE recommending anything
   Action: Ask in order:
     - What conditions/medications do you take?
     - What's your current schedule like?
     - What have you tried before?
     - What are your barriers?
   Then: Create personalized plan based on answers

2. PERSONALIZATION SKILLS
   Current: Uses same template for all patients
   Target: Every recommendation should reference patient's specific situation
   Example: "Given you work nights AND have diabetes, here's a modified plan..."

3. BARRIER EXPLORATION
   Current: Dismissed patient's concerns
   Target: Explore and address barriers
   Action: When patient raises constraint, say:
     - "Tell me more about your schedule"
     - "What challenges do you face?"
     - "How can we make this work for YOUR life?"
```

---

## Example 2: ✅ GOOD Consultation (Health-First, Personalized)

### Transcript
```
[0:00] Dietician: "Hi, I'm Dr. Sharma. Let's create a plan that works for YOUR life."
[0:15] Patient: "Thanks, I have diabetes and work night shifts."
[0:30] Dietician: "Night shifts are tricky. Are you on any medications?"
[0:45] Patient: "Yes, metformin and a blood pressure medication."
[1:00] Dietician: "Good to know. Metformin affects B12 absorption, so we need to 
                    include B12-rich foods. What does a typical night shift day look like?"
[1:30] Patient: "I wake at 6pm, work 8pm-8am, sleep during day."
[1:45] Dietician: "So you need energy for night work but stable blood sugar. 
                   Let's look at meal times around your schedule. What foods do you like?"
[2:15] Patient: "I like rice, dal, vegetables..."
[2:30] Dietician: "Perfect. Here's your personalized plan:
                   - Pre-work meal at 7:30pm (complex carbs + protein)
                   - Work snacks at 2am (nuts, yogurt - no sugar crash)
                   - Post-work at 8:30am (B12-rich foods)
                   This keeps blood sugar stable through your 12-hour shift.
                   Does this fit your life?"
[3:15] Patient: "Yes! This makes sense. But what if I'm still hungry at night?"
[3:30] Dietician: "Good question. Add vegetables to snacks - more volume, 
                   lower calories. Try cucumber with hummus. Any allergies?"
[3:45] Patient: "No allergies. What about cost? Some of this might be expensive."
[4:00] Dietician: "Valid point. You can get B12 from eggs instead of expensive 
                   supplements - much cheaper. Seasonal vegetables also cost less. 
                   Here's an affordable version. Ready?"
[4:30] Patient: "Yes, I understand the plan and it works for me."
[4:45] Dietician: "Great! Call me in 2 weeks. We'll check your blood sugar logs 
                   and adjust if needed. My number is [phone]. Any final questions?"
[5:00] Patient: "No, I feel confident about this!"
```

### Analysis Output (NEW System - Updated SOP)
```
Compliance Score: 94/100 ✅

SCORES:
- Greeting: 92/100 (Professional, explained approach)
- Empathy: 95/100 (Acknowledged work schedule challenges)
- Compliance: 94/100 (All SOP checks passed)
- Technical: 95/100 (Evidence-based, personalized recommendations)

VIOLATIONS: None

QA ALERTS: None

INSIGHTS:
✅ What Went Well:
1. At [1:00s]: Excellent health understanding - asked about medications and 
   understood metformin-B12 interaction
2. At [1:45s]: Strong personalization - adapted timing to night shift schedule
3. At [3:30s]: Patient education - explained WHY certain foods (prevents blood 
   sugar crashes during 12-hour shift)
4. At [4:00s]: Barrier assessment - addressed cost concerns with affordable alternatives
5. At [4:30s]: Clear follow-up - specific timeline, phone number, next steps

⚠️ Areas for Enhancement:
- Could have discussed exercise/activity during day sleep (minor improvement)
- Could have provided written plan summary

TRAINING GAP RECOMMENDATIONS: None - this is exemplary consultation

COACHING NOTES:
"This is an excellent consultation model. Use this as training example for team:
1. Health assessment FIRST (medications → schedule → preferences)
2. Personalization throughout (reference patient's specific life at each step)
3. Patient education (explain the 'why')
4. Barrier solving (affordability, scheduling, adherence challenges)
5. Clear follow-up (date, contact, progress measures)"
```

---

## Example 3: ⚠️ MEDIUM Consultation (Good Care, Process Gaps)

### Transcript
```
[0:00] Dietician: "Hi, let's create your diet plan for blood pressure management."
[0:20] Patient: "Thanks, I have hypertension and I'm vegetarian."
[0:40] Dietician: "Good, low sodium is key. Are you on blood pressure meds?"
[1:00] Patient: "Yes, lisinopril."
[1:15] Dietician: "Okay, here's a vegetarian plan with low sodium. It includes:
                   - Whole grains
                   - Legumes for protein
                   - Plenty of vegetables
                   Based on your vegetarian preference, this should work well."
[2:00] Patient: "But my kids don't eat all these vegetables..."
[2:15] Dietician: "Just give them the healthier option."
[2:45] Patient: "Okay, I'll try."
[3:00] Dietician: "Good. Call me in 6 weeks if you need adjustments."
```

### Analysis Output (NEW System - Updated SOP)
```
Compliance Score: 72/100 ⚠️ PROCESS GAPS

VIOLATIONS:
1. ⚠️ Barrier Assessment [WARNING]
   Violated at [2:00s]
   Evidence: "Patient mentioned kids won't eat vegetables, dietician dismissed 
   it without exploring family meal planning or practical solutions."
   Impact: Plan might not be adopted because family resistance not addressed.

2. ⚠️ Patient Education [INFO]
   Opportunity at [1:15s]
   Evidence: "Provided plan but didn't explain WHY low sodium, how it helps 
   blood pressure, what to look for in labels."
   Impact: Patient doesn't understand how to make good choices independently.

3. ⚠️ Informed Consent [WARNING]
   Verified at [2:45s]
   Evidence: "Patient's 'I'll try' shows weak commitment - not clear agreement."
   Impact: Lower adherence likelihood.

QA ALERTS:
[WARNING] Family Barrier Not Addressed
- At 2:00s: Patient raised family meal planning concern
- Dietician should have explored: How to cook one meal, picky eaters, budget
- Recommendation: Problem-solve WITH patient, not dismiss concern

[INFO] Limited Patient Education
- Explains WHAT to eat, but not WHY
- Recommendation: "Low sodium helps your kidneys regulate fluid, lowering blood 
  pressure. That's why we avoid processed foods - they're loaded with hidden salt."

COACHING RECOMMENDATIONS:
1. BARRIER EXPLORATION
   When patient raises concern, explore it:
   Current: "Just give them the healthier option"
   Target: "Tell me about meal times with your kids. What do they usually eat?"
   Then: Adapt plan to work with family dynamics

2. PATIENT EDUCATION
   Add 'why' to every recommendation:
   Current: "Low sodium plan"
   Target: "Low sodium helps your body maintain better fluid balance, which 
   reduces blood pressure naturally. Let's avoid processed foods with hidden salt."

OVERALL ASSESSMENT:
Good personalization and health assessment, but missed opportunities to:
- Address family/lifestyle barriers
- Explain nutritional science
- Get strong commitment/confirmation
Recommendation: Follow-up training on barrier assessment and patient education.
```

---

## Key Takeaways

### What Changed
| Old System | New System |
|---|---|
| Checked HIPAA compliance | Checks if health assessed FIRST |
| Generic SOP elements | Personalization is CRITICAL |
| Script-based closing | Barrier-based follow-up |
| Light patient education | Nutritional science emphasis |

### New Red Flags Claude Will Catch
🚨 **CRITICAL:**
- Generic diet plan without health assessment
- Same plan for all patients (not personalized)
- Promoting own products/entity
- Dismissing patient's barriers

⚠️ **WARNING:**
- Weak informed consent ("okay, I guess")
- Missing barrier exploration
- No follow-up plan clarity
- Limited patient education

### Training Impact
Consultations like "Example 1" will be flagged with:
- Specific timestamp evidence
- Exact coaching action to take
- Link to SOP section

Consultations like "Example 2" will be used as:
- Training examples
- Gold standard for new dieticians
- Coaching showcase

---

## 🎯 Result
Portal now provides feedback that dieticians can ACT ON:
- Not "improve compliance" → but "always assess health before recommending"
- Not "better patient engagement" → but "address your barrier about night shifts"
- Not "complete consultation" → but "explain why low sodium matters"

**Specific, actionable, tied to patient care quality!**
