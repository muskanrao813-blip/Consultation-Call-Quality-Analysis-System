# Start server with Gemini API key from .env
$env:GEMINI_API_KEY = "AQ.Ab8RN6KbD0l45n3lNaeopSVQcCNDsOHpB4YFax-WfbK11uFQ8w"
$ffmpegBin = "C:\Users\muskan.rao\Downloads\ffmpeg_extracted\ffmpeg-master-latest-win64-gpl\bin"
$env:Path = "$ffmpegBin;$env:Path"

cd "C:\Users\muskan.rao\Documents\claude\dietician-qa\"

# Kill any existing servers
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
