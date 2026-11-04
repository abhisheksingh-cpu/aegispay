"""The only file that talks to the LLM provider (Groq, OpenAI-compatible). Swap providers here."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


def call_llm(system: str, user: str) -> tuple[str, int]:
    """Returns (reply_text, total_tokens). Raises on any failure; callers must handle it."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_completion_tokens": 1200,  # reasoning models spend part of this on hidden thinking
    }
    if "gpt-oss" in model:
        body["reasoning_effort"] = "low"  # less thinking = fewer tokens and faster
    r = httpx.post(URL, headers={"Authorization": f"Bearer {key}"}, timeout=30, json=body)
    if not r.is_success:  # keep the provider's reason: it is usually a wrong model name or key
        raise RuntimeError(f"Groq HTTP {r.status_code}: {r.text[:150]}")
    data = r.json()
    return data["choices"][0]["message"]["content"], data["usage"]["total_tokens"]