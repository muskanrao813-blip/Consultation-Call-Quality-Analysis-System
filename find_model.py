import httpx, json, time

key = "AQ.Ab8RN6K_ouw6DSjTmSI5ZtBAfnSthGXV_M6FuiV7XYu9f5FiXw"
models = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-pro-latest",
]

for model in models:
    body = {"contents": [{"parts": [{"text": "Say hello in one word"}]}]}
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        json=body, verify=False, timeout=15
    )
    data = r.json()
    if r.status_code == 200:
        text = data["candidates"][0]["content"]["parts"][0]["text"][:50]
        print(f"OK  {model}: {text}")
    else:
        err = data.get("error", {})
        print(f"ERR {model}: {err.get('status','')} - {err.get('message','')[:80]}")
    time.sleep(2)
