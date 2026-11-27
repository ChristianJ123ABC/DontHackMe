import os, time, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")  

models = [
    "baidu/ernie-5.5-flash-preview:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

for model in models:
    start = time.time()
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer " + key},
            json={"model": model,
                  "messages": [{"role": "user", "content": "Reply with the word OK."}],
                  "max_tokens": 20},
            timeout=30)
        print(model, r.status_code, round(time.time() - start, 1), r.text[:150])
    except Exception as e:
        print(model, "error", type(e).__name__, round(time.time() - start, 1))