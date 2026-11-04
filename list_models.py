"""Lists the model IDs your Groq key can use. Pick a chat model and put it in .env as GROQ_MODEL."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
    timeout=20,
)
if not r.is_success:
    raise SystemExit(f"Groq HTTP {r.status_code}: {r.text[:150]}")
for model_id in sorted(m["id"] for m in r.json()["data"]):
    print(model_id)