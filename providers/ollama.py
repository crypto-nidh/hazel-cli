"""
providers/ollama.py — Local Ollama Provider
--------------------------------------------
Runs AI models completely locally — no API key, no internet, 100% free.
Requires Ollama to be installed and running.

Install : https://ollama.ai
Setup   : ollama pull llama3
Run     : ollama serve   (auto-starts on most systems)
"""

import urllib.request
import urllib.error
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL  = "llama3"


def query(prompt: str, api_key: str = "", system: str = None,
          model: str = DEFAULT_MODEL) -> str:
    """
    Send a prompt to local Ollama and return the text response.

    Args:
        prompt:  The user message.
        api_key: Not needed for Ollama — ignored.
        system:  Optional system prompt.
        model:   Ollama model name (must be pulled first).

    Returns:
        Response text string.

    Raises:
        RuntimeError if Ollama is not running or model not found.
    """
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    payload = json.dumps({
        "model":  model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": 1024,
            "temperature": 0.3,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama not reachable at localhost:11434. "
            f"Is it running? Try: ollama serve\nError: {e.reason}"
        )
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Ollama unexpected response: {e}")