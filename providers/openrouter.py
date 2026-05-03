"""
providers/openrouter.py — OpenRouter API Provider
--------------------------------------------------
OpenRouter gives access to many models (including free ones)
via a single OpenAI-compatible API.

Free models: meta-llama/llama-3-8b-instruct:free
             mistralai/mistral-7b-instruct:free
Get key    : https://openrouter.ai/keys
"""

import urllib.request
import urllib.error
import json

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL      = "google/gemma-3-4b-it:free"

# Current working free models on OpenRouter (2025)
FALLBACK_MODELS = [
    "google/gemma-3-4b-it:free",
    "google/gemma-3-1b-it:free",
    "meta-llama/llama-4-scout:free",
    "deepseek/deepseek-r1-0528:free",
    "microsoft/mai-ds-r1:free",
]


def query(prompt: str, api_key: str, system: str = None,
          model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to OpenRouter and return the text response.
    Tries fallback free models if primary is unavailable.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

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
            OPENROUTER_API_URL,
            data=payload,
            headers={
                "Authorization":  f"Bearer {api_key}",
                "Content-Type":   "application/json",
                "HTTP-Referer":   "https://github.com/hazel-cli",
                "X-Title":        "Hazel CLI",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if content is None:
                    # Free model returned null content (rate-limited or filtered)
                    last_error = f"Model '{try_model}' returned null content"
                    continue
                return content.strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if e.code == 404:
                last_error = f"Model '{try_model}' not available"
                continue
            raise RuntimeError(f"OpenRouter API error {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"OpenRouter connection failed: {e.reason}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"OpenRouter unexpected response format: {e}")

    raise RuntimeError(f"All OpenRouter free models failed. Last: {last_error}")