"""
providers/groq.py — Groq API Provider
--------------------------------------
Uses Groq's OpenAI-compatible REST API (pure urllib, no extra deps).

Free tier : 14,400 requests/day, 30 req/min
Get key   : https://console.groq.com

Available free models (2025):
  llama-3.3-70b-versatile     ← best quality
  llama-3.1-8b-instant        ← fastest
  mixtral-8x7b-32768          ← good for long context
  gemma2-9b-it                ← Google's Gemma 2
"""

import urllib.request
import urllib.error
import json

GROQ_API_URL  = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Fallback models tried in order if default is unavailable
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


def query(prompt: str, api_key: str, system: str = None,
          model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to Groq and return the text response.
    Automatically tries fallback models if the primary is unavailable.

    Args:
        prompt:  The user message.
        api_key: Your Groq API key (starts with gsk_).
        system:  Optional system prompt.
        model:   Groq model name.

    Returns:
        Response text string.

    Raises:
        RuntimeError on API or network error.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # Try primary model first, then fallbacks automatically
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = None

    for try_model in models_to_try:
        payload = json.dumps({
            "model":       try_model,
            "messages":    messages,
            "max_tokens":  1024,
            "temperature": 0.3,
        }).encode("utf-8")

        req = urllib.request.Request(
            GROQ_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
                "User-Agent":    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept":        "application/json",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if e.code == 404:
                # Model not found — silently try next fallback
                last_error = f"Model '{try_model}' not available"
                continue
            # Auth / rate limit / server errors — raise immediately
            raise RuntimeError(f"Groq API error {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Groq connection failed: {e.reason}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Groq unexpected response format: {e}")

    raise RuntimeError(f"All Groq models failed. Last: {last_error}")
