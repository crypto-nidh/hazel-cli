"""
providers/gemini.py — Google Gemini API Provider
-------------------------------------------------
Uses Google's Gemini REST API (pure urllib, no google-generativeai SDK needed).

Free tier : 15 req/min, 1,500 req/day
Model     : gemini-1.5-flash (fast + free)
Get key   : https://aistudio.google.com/app/apikey
"""

import urllib.request
import urllib.error
import json

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
DEFAULT_MODEL  = "gemini-2.0-flash"

# Fallback models if primary hits quota or is unavailable
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
]


def query(prompt: str, api_key: str, system: str = None,
          model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to Google Gemini and return the text response.
    Tries fallback models on 429 (quota) or 404 (not found).
    """
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = None

    for try_model in models_to_try:
        payload = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature":     0.3,
            }
        }).encode("utf-8")

        url = GEMINI_API_URL.format(model=try_model, key=api_key)
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if e.code in (404, 429):
                # 404 = model not found, 429 = quota — try next model
                last_error = f"Model '{try_model}' error {e.code}"
                continue
            raise RuntimeError(f"Gemini API error {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini connection failed: {e.reason}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Gemini unexpected response format: {e}")

    raise RuntimeError(f"All Gemini models failed. Last: {last_error}")