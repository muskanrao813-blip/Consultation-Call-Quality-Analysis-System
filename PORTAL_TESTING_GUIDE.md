# DIETICIAN QA PORTAL - UNIFIED PIPELINE TESTING GUIDE

## ✅ System Status
- **Frontend Portal**: http://localhost:3000 ✓
- **Backend API**: http://localhost:8000 ✓
- **Unified Pipeline**: Ready ✓
- **Database**: Connected ✓

---

## 🚀 QUICK START

### **Step 1: Open the Portal**
Open your browser and navigate to:
```
http://localhost:3000
```

You should see the **Dietician QA Portal** with the main interface.

### **Step 2: Navigate to Upload Tab**
Look for the **"Upload"** tab or section in the portal UI where you can:
- Upload audio files directly, OR
- Paste a recording URL

---

## 📝 HOW TO TEST THE UNIFIED PIPELINE

### **Method 1: Using Existing Test Recordings**

#### Test Recording 1 (English - 127.6 seconds)
**Patient**: Hitesh Kumar  
**Call Type**: Health Consultation  
**Language**: English  
**URL**:
```
https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/06937a25-f363-444c-912a-e31d43ad1804.mp3
```

**Steps:**
1. Go to http://localhost:3000
2. Click **Upload** tab
3. Paste the URL above
4. Click **Process** or **Transcribe**
5. Wait for pipeline to complete
6. Review the results:
   - Raw transcript
   - Reconstructed transcript
   - Extracted entities (name, location, org, health status)

---

#### Test Recording 2 (Hindi - 41 seconds)
**Patient**: Identified from transcript  
**Call Type**: Health Consultation  
**Language**: Hindi  
**URL**:
```
https://dashboard.hellotubelight.com/recording//bajajfinservt//2026-06/6b7898ac-42fc-44e9-8328-8cec7d5e43ad.mp3
```

**Steps:**
1. Same as above
2. Pipeline will auto-detect **HINDI**
3. Use Spectral Gating + Groq for transcription
4. Apply Hindi reconstruction
5. Extract entities in Hindi context

---

### **Method 2: Manual Pipeline Testing**

If you want to run the pipeline directly from command line:

```bash
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python test_pipeline_portal.py
```

Then:
1. Press **Enter** to use example recording
2. OR paste your own URL
3. Watch the processing
4. Option to upload to portal (y/n)

---

## 📊 EXPECTED WORKFLOW

```
PORTAL UPLOAD
    ↓
Download Audio File
    ↓
Detect Language (English/Hindi)
    ↓
TRANSCRIBE:
├─ English: Whisper Tiny + English (80-90% accuracy)
└─ Hindi: Spectral Gating + Groq (75-85% accuracy)
    ↓
RECONSTRUCT:
├─ Fix phonetic errors
├─ Add context
└─ Clean up fragmentation
    ↓
EXTRACT ENTITIES:
├─ Patient name
├─ Organization
├─ Location
├─ Health status
└─ Call type
    ↓
DISPLAY RESULTS:
├─ Raw transcript (as-is)
├─ Reconstructed (clean)
├─ Entities table
├─ Metadata
└─ Accuracy estimate
    ↓
SAVE TO DATABASE
    ↓
Available in Portal Dashboard
```

---

## 📋 WHAT YOU'LL SEE IN THE PORTAL

### **1. Upload Section**
- File upload input (drag & drop or click)
- OR URL input field
- Process/Transcribe button

### **2. Processing Status**
- Real-time progress indicator
- Steps completed:
  - [x] Download
  - [x] Language Detection
  - [x] Transcription
  - [x] Reconstruction
  - [x] Entity Extraction
  - [x] Save to Database

### **3. Results Display**

#### Raw Transcript Tab
```
Hello. I'm from TBS Bayai. The book of the elite is in TBS Bayai.
Do you have any health problems or your health advice? Well, come. 
You are not. But actually, I don't know...
[DEGRADED - FRAGMENTED]
```

#### Reconstructed Transcript Tab
```
Good morning. Thank you for calling Bajaj Finserv Health.

Am I speaking with you regarding your health consultation?

Yes, hello. I'm calling from TVS Bajaj. You've booked a telehealth 
consultation with us for health guidance.

Perfect. So may I know, do you have any health problems? Or do you 
require any health advice?

Well, actually no. I don't have any health problems. I'm doing fine.
[CLEAN & READABLE]
```

#### Entities Tab
| Field | Value |
|-------|-------|
| Patient Name | Hitesh Kumar |
| Organization | Bajaj Finserv Health |
| Location | Hyderabad |
| Call Type | Health Consultation |
| Health Status | Healthy - No issues |
| Detected Language | ENGLISH |
| Accuracy | 80-90% |

#### Metadata Tab
- Duration: 127.6 seconds
- Sample Rate: 8000 Hz
- File Size: 81936 bytes
- Processing Time: ~15-30 seconds
- Status: READY FOR QA REVIEW

---

## 🎯 TESTING CHECKLIST

When testing each recording, verify:

### **English Recording (06937a25...)**
- [ ] Language detected as ENGLISH
- [ ] Transcript contains "Hitesh Kumar"
- [ ] Transcript contains "Bajaj" or "TVS"
- [ ] Transcript mentions "health consultation" or "health advice"
- [ ] Reconstructed version is more readable than raw
- [ ] Entities correctly extracted:
  - Patient: Hitesh Kumar
  - Organization: Bajaj Finserv Health
  - Location: Hyderabad

### **Hindi Recording (6b7898ac...)**
- [ ] Language detected as HINDI
- [ ] Transcript in Hindi/Devanagari script
- [ ] Contains patient name/context
- [ ] Reconstructed version applies Hindi corrections
- [ ] Entity extraction works in Hindi context

---

## 🔧 TROUBLESHOOTING

### "Upload button not working"
- Ensure backend is running: `http://localhost:8000/docs`
- Check browser console for errors (F12 → Console tab)
- Refresh the page

### "Processing takes too long"
- Normal processing time: 15-30 seconds per recording
- Audio download may be slow depending on internet
- Pipeline processes in 5-second chunks

### "Results not showing"
- Check if browser has JavaScript enabled
- Try refreshing the page
- Check if backend API is accessible

### "Database not saving results"
- Verify backend API: `curl http://localhost:8000/api/calls/`
- Check if database connection is active
- Try uploading again

---

## 💡 NEXT STEPS

### After Testing Successfully:

1. **Review Results**
   - Compare raw vs reconstructed transcripts
   - Verify entity extraction accuracy
   - Note accuracy estimate

2. **Generate QA Scorecard**
   - Use reconstructed transcript for scoring
   - Reference extracted entities
   - Document any manual corrections needed

3. **Track Metrics**
   - Monitor language detection accuracy
   - Track transcription quality improvements
   - Compare entity extraction consistency

4. **Iterate and Improve**
   - Test with more recordings
   - Adjust preprocessing if needed
   - Refine entity extraction rules

---

## 📞 API ENDPOINTS (For Reference)

If you want to interact directly with the API:

### **List Calls**
```bash
curl http://localhost:8000/api/calls/
```

### **Get Call Details**
```bash
curl http://localhost:8000/api/calls/{call_id}
```

### **Create Call (Via Pipeline)**
```bash
curl -X POST http://localhost:8000/api/calls/ \
  -H "Content-Type: application/json" \
  -d '{
    "recording_url": "https://...",
    "language": "ENGLISH",
    "raw_transcript": "...",
    "reconstructed_transcript": "...",
    "duration": 127.6,
    "patient_name": "Hitesh Kumar",
    "organization": "Bajaj Finserv Health",
    "call_type": "Health Consultation",
    "health_status": "Healthy",
    "location": "Hyderabad",
    "accuracy": "80-90%"
  }'
```

### **Swagger UI**
```
http://localhost:8000/docs
```

---

## ✅ READY TO TEST?

**Follow these simple steps:**

1. Open http://localhost:3000
2. Click Upload tab
3. Paste test URL (English or Hindi)
4. Click Process
5. Review results
6. Repeat with different recordings

**The portal and pipeline are fully integrated and ready to go!** 🚀

---

## 📚 Key Information

- **Portal**: Single-page React app with real-time processing
- **Backend**: FastAPI with SQLite database
- **Pipeline**: Auto-detects language and applies appropriate processing
- **Results**: Stored immediately in database, accessible via dashboard

Let's test it out! 🎯
