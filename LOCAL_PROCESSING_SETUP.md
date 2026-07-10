# Local Processing Setup (No Credit Card Needed)

**Status:** Your portal is ready for local audio processing using Whisper + Ollama.

**Cost:** ₹0 (completely free)  
**Setup Time:** 20-30 minutes  
**Processing Speed:** 10-20 seconds per minute of audio

---

## What You Get

✅ Audio transcription (speech-to-text)  
✅ Speaker diarization (who is talking)  
✅ Quality scoring on 6 dimensions  
✅ QA flag detection  
✅ Coaching feedback generation  
✅ No internet required after setup  
✅ Data stays on your computer  

---

## Architecture

```
Your Computer
    │
    ├─ Whisper (local model) → Transcription
    │
    └─ Ollama (local LLM) → Quality Analysis
         └─ Uses: Mistral or Llama2 model
```

---

## Prerequisites

- Windows 11 Pro (you have this ✓)
- Python 3.14 (you have this ✓)
- ~4GB free disk space for models
- ~2GB free RAM during processing

---

## Step 1: Install Ollama

1. Go to [ollama.ai](https://ollama.ai)
2. Click "Download"
3. Download **Ollama for Windows**
4. Run the installer
5. Follow the installation wizard
6. **Restart your computer** (important!)

**Verify installation:**
```powershell
ollama --version
# Expected: ollama version X.X.X
```

---

## Step 2: Download a Model

Open PowerShell and run:

```powershell
ollama pull mistral
```

This downloads the Mistral model (~4GB). Options:

| Model | Size | Speed | Quality | Recommendation |
|-------|------|-------|---------|-----------------|
| **mistral** | 4GB | Fast | Good | ✅ Recommended |
| neural-chat | 4GB | Fast | Good | ✅ Good alternative |
| llama2 | 3.5GB | Slower | Fair | For low RAM |
| dolphin-mixtral | 26GB | Slow | Excellent | If you have time/space |

**Use this command (recommended):**
```powershell
ollama pull mistral
```

Wait for download to complete (~5-10 minutes).

---

## Step 3: Start Ollama Server

Open a **new PowerShell window** and run:

```powershell
ollama serve
```

You should see:
```
pulling manifest
pulling 975c58153fc6
pulling e8816e318710
pulling de071a6fa3f1
pulling d01c5b4ab39a
pulling cc2ba3346e65
pulling 3567fdde87f6
pulling cdc6ba6f5540
pulling 3f119e2e6330
pulling c8ffe33a2737
pulling a0d66932eacd
pulling cc4ba6f5540b
pulling 9b09f511d5d0
pulling 9c99a6c0c40e
pulling f176b079a6c8
INFO [blas] AVX = 1
...
Listening on 127.0.0.1:11434
```

**Keep this window open** — it's the Ollama server running in the background.

---

## Step 4: Test Ollama Connection

In a **different PowerShell window**, test the connection:

```powershell
curl http://localhost:11434/api/tags
```

Expected response: JSON with model list including "mistral"

If you get "Connection refused", Ollama server is not running. Go back to Step 3.

---

## Step 5: Verify Whisper Installation

The Whisper package should already be installed. Verify:

```powershell
python -c "import whisper; print('Whisper installed successfully')"
```

If it fails, install it:
```powershell
pip install openai-whisper
```

---

## Step 6: Test the Full Setup

Test that both Whisper and Ollama work together:

```powershell
cd C:\Users\muskan.rao\Documents\claude\dietician-qa

python -c "
from app.services.transcription.local_whisper import LocalWhisperProvider
from app.services.llm.ollama_local import OllamaLocalProvider

print('Testing Whisper...')
whisper_provider = LocalWhisperProvider()
print('✓ Whisper provider loaded')

print('Testing Ollama...')
ollama_provider = OllamaLocalProvider()
print('✓ Ollama provider loaded')

print('All providers ready!')
"
```

Expected output:
```
Testing Whisper...
Loading Whisper model (base)...
Whisper model loaded successfully
✓ Whisper provider loaded
Testing Ollama...
✓ Ollama provider loaded
All providers ready!
```

---

## Step 7: Restart the Portal Server

Stop the current server (Ctrl+C in the PowerShell where it's running), then restart:

```powershell
cd C:\Users\muskan.rao\Documents\claude\dietician-qa
python -m uvicorn app.main:app --reload --port 8001
```

The server should start and log:
```
INFO:     Application startup complete
```

---

## Step 8: Test End-to-End Processing

Now test the complete pipeline:

### A. Create a Test Audio File

You need an audio URL (publicly accessible) or create a test file:

```powershell
# Example: Download a free audio sample
curl -o test_audio.wav "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
```

### B. Create Excel File

1. Go to http://localhost:8001
2. Click "Upload" tab
3. Download the template
4. Add this row:
   ```
   dietician_name,appointment_id,recording_url
   Dr. Test,APT-TEST-001,file:///C:/Users/muskan.rao/Documents/claude/dietician-qa/test_audio.wav
   ```
   
   OR use a public URL:
   ```
   dietician_name,appointment_id,recording_url
   Dr. Test,APT-TEST-001,https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3
   ```

5. Save as `test_upload.xlsx`
6. Upload the file

### C. Monitor Progress

Watch the progress bar update with stages:
- ✓ Downloading audio
- ✓ Transcribing
- ✓ Computing metrics
- ✓ Running LLM analysis
- ✓ Storing results

Once complete, click the call in "Scorecard" tab to see results.

---

## Troubleshooting

### "Connection refused" when testing Ollama

**Problem:** Ollama server not running or on wrong port

**Solution:**
1. Make sure PowerShell window with `ollama serve` is still open
2. Check port: 11434 (default)
3. Restart: `ollama serve`

---

### "Model not found" error

**Problem:** Mistral model not downloaded

**Solution:**
```powershell
ollama pull mistral
# Wait for download to complete
ollama serve
```

---

### "Whisper not found" error

**Problem:** Whisper package not installed

**Solution:**
```powershell
pip install openai-whisper
```

---

### Transcription is very slow

**Problem:** Whisper is using CPU (slow)

**Solution:** Unfortunately, Whisper on CPU is slow. Options:
1. **Use smaller model** (less accurate but faster):
   ```python
   # In local_whisper.py, change:
   whisper.load_model("base")  # Change to "tiny" or "small"
   ```

2. **Upgrade to CUDA** (if you have NVIDIA GPU):
   - Install CUDA Toolkit
   - Install: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
   - Whisper will use GPU automatically

---

### LLM Analysis is very slow

**Problem:** Mistral model is running on CPU

**Solution:** 
1. Install more RAM (if possible)
2. Use smaller/faster model:
   ```python
   # In ollama_local.py __init__, change:
   OllamaLocalProvider("neural-chat")  # Faster variant
   ```

3. Or upgrade to NVIDIA GPU for faster processing

---

### "Pipeline dependencies not installed"

**Problem:** Missing packages

**Solution:**
```powershell
pip install openai-whisper ollama requests
```

---

## Performance Expectations

| Phase | Time | Notes |
|-------|------|-------|
| Download audio | 5-10s | Depends on file size |
| Transcription | 20-60s per minute | Whisper on CPU is slow |
| Metrics | <1s | Quick computation |
| LLM analysis | 30-120s | Depends on transcript length |
| Storage | <1s | Database write |
| **Total per call** | **2-3 minutes** | Can vary widely |

Typical call (15 min audio): 8-10 minutes processing time

---

## Keeping Ollama Running

You have two options:

### Option A: Manual (what we did above)
- Open PowerShell → run `ollama serve`
- Keep window open while processing
- Close when done

### Option B: Background Service
Install Ollama as Windows service:
```powershell
# Ollama installer sets this up automatically
# Service name: Ollama
# It auto-starts with Windows
```

Check if service is running:
```powershell
Get-Service Ollama
```

---

## System Requirements Check

Run this to verify your system is ready:

```powershell
python -c "
import platform
import psutil

print(f'OS: {platform.system()} {platform.release()}')
print(f'Python: {platform.python_version()}')
print(f'RAM: {psutil.virtual_memory().total / (1024**3):.1f}GB')
print(f'Disk: {psutil.disk_usage(\"C:\").free / (1024**3):.1f}GB free')
"
```

Minimum requirements:
- ✅ Windows 10 or later
- ✅ Python 3.8+
- ✅ 4GB RAM
- ✅ 5GB free disk space

---

## Next Steps

1. ✅ Install Ollama (Step 1)
2. ✅ Download Mistral model (Step 2)
3. ✅ Start Ollama server (Step 3)
4. ✅ Verify connection (Step 4)
5. ✅ Test providers (Step 6)
6. ✅ Restart portal server (Step 7)
7. ✅ Upload test file (Step 8)

Once complete, your portal will automatically process all calls!

---

## Switching Models

Want a different model? Easy:

```powershell
# Download alternative
ollama pull neural-chat

# Use in portal by changing config in portal .env:
# Or in code: OllamaLocalProvider("neural-chat")
```

Available models:
- `mistral` — Fast, good quality (recommended)
- `neural-chat` — Optimized for chat
- `llama2` — Slower, decent quality
- `dolphin-mixtral` — Excellent but very slow

---

## Important Notes

⚠️ **Keep Ollama running** while processing files. The server must be accessible at `http://localhost:11434`

⚠️ **First model load is slow** (~30 seconds to load Mistral into memory). Subsequent calls are faster.

⚠️ **CPU processing is slow** for Whisper. If you have an NVIDIA GPU, CUDA can speed this up 10x.

---

## Support

If stuck:
1. Check server logs (look at PowerShell windows)
2. Verify `ollama serve` window is open and shows "Listening on 127.0.0.1:11434"
3. Test connection: `curl http://localhost:11434/api/tags`
4. Check .env file has no Google Cloud credentials blocking local fallback

---

## Cost Summary

| Item | Cost |
|------|------|
| Ollama | FREE |
| Mistral model | FREE |
| Whisper | FREE |
| Portal | FREE |
| **Total** | **₹0** |

No credit card required. Everything runs locally on your computer.

---

**You're ready for full end-to-end processing with zero cost!**

Start here: http://localhost:8001

Then follow Steps 1-8 above to enable local processing.
