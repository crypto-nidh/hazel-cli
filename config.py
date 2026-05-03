"""
config.py — API Key & Provider Configuration Manager
------------------------------------------------------
Handles:
  - Storing API keys securely in a local .env file
  - Reading/writing the active AI provider
  - Masking keys when displayed (gsk_****abcd)
  - set-api and ai-provider CLI commands

Files created:
  .env              → stores API keys (never commit this)
  hazel_config.json → stores active provider and settings
"""

import os
import getpass
import json

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ENV_FILE    = os.path.join(BASE_DIR, '.env')
CONFIG_FILE = os.path.join(BASE_DIR, 'hazel_config.json')

SUPPORTED_PROVIDERS = ["groq", "gemini", "openrouter", "ollama"]

# Provider info shown to users
PROVIDER_INFO = {
    "groq": {
        "name":     "Groq (Llama3-70b)",
        "free":     "14,400 req/day — completely free",
        "url":      "https://console.groq.com",
        "key_hint": "Starts with: gsk_"
    },
    "gemini": {
        "name":     "Google Gemini",
        "free":     "15 req/min, 1500/day — free tier",
        "url":      "https://aistudio.google.com/app/apikey",
        "key_hint": "Starts with: AIza"
    },
    "openrouter": {
        "name":     "OpenRouter (Multi-model)",
        "free":     "Free models available",
        "url":      "https://openrouter.ai/keys",
        "key_hint": "Starts with: sk-or-"
    },
    "ollama": {
        "name":     "Ollama (Local — no key needed)",
        "free":     "100% free, runs locally",
        "url":      "https://ollama.ai",
        "key_hint": "No API key required"
    }
}

# ANSI colors
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


# ── .env file helpers ─────────────────────────────────────────────────────────

def _read_env() -> dict:
    """Read all key=value pairs from .env file."""
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                env[key.strip()] = val.strip()
    return env


def _write_env(env: dict):
    """Write all key=value pairs back to .env file."""
    lines = ["# Hazel CLI — API Keys", "# DO NOT commit this file to git", ""]
    for key, val in env.items():
        lines.append(f"{key}={val}")
    with open(ENV_FILE, 'w') as f:
        f.write("\n".join(lines) + "\n")
    # Restrict file permissions to owner only
    os.chmod(ENV_FILE, 0o600)


def _env_key_name(provider: str) -> str:
    """Convert provider name to env var name. e.g. groq → HAZEL_GROQ_API_KEY"""
    return f"HAZEL_{provider.upper()}_API_KEY"


# ── Config JSON helpers ───────────────────────────────────────────────────────

def _read_config() -> dict:
    """Read hazel_config.json, return empty dict if missing."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _write_config(cfg: dict):
    """Write config dict to hazel_config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def get_api_key(provider: str) -> str:
    """
    Return the stored API key for a provider, or empty string if not set.
    Checks .env file first, then environment variables.
    """
    env_name = _env_key_name(provider)

    # Check .env file
    env = _read_env()
    if env_name in env and env[env_name]:
        return env[env_name]

    # Fallback: check actual environment variables
    return os.environ.get(env_name, "")


def set_api_key(provider: str, key: str):
    """Store an API key for a provider in the .env file."""
    env = _read_env()
    env[_env_key_name(provider)] = key
    _write_env(env)


def get_active_provider() -> str:
    """Return the currently selected AI provider, default 'groq'."""
    cfg = _read_config()
    return cfg.get("active_provider", "none")


def set_active_provider(provider: str):
    """Save the active provider to config."""
    cfg = _read_config()
    cfg["active_provider"] = provider
    _write_config(cfg)


def get_configured_providers() -> list:
    """Return list of providers that have API keys stored.

    Ollama is only included if the user has explicitly selected it as
    a provider (stored in config), so we don't blindly time-out waiting
    for a local server that may not be running.
    """
    configured = []
    active = _read_config().get("active_provider", "none")
    for p in SUPPORTED_PROVIDERS:
        if p == "ollama":
            # Include Ollama only when it is the explicitly active provider
            if active == "ollama":
                configured.append(p)
        elif get_api_key(p):
            configured.append(p)
    return configured


def mask_key(key: str) -> str:
    """
    Mask an API key for safe display.
    e.g. gsk_abcdefghijklmnop → gsk_****mnop
    """
    if not key or len(key) < 8:
        return "****"
    prefix = key[:4]
    suffix = key[-4:]
    return f"{prefix}****{suffix}"


# ── CLI Command Handlers ──────────────────────────────────────────────────────

def cmd_set_api(provider: str = None):
    """
    Interactive handler for: hazel> set-api <provider>
    Prompts user for their API key securely (no echo).
    """
    if not provider:
        print(f"\n  {YELLOW}Usage: set-api <provider>{RESET}")
        print(f"  Supported: {', '.join(SUPPORTED_PROVIDERS)}\n")
        return

    provider = provider.lower().strip()

    if provider not in SUPPORTED_PROVIDERS:
        print(f"\n  {RED}Unknown provider: '{provider}'{RESET}")
        print(f"  Supported: {', '.join(SUPPORTED_PROVIDERS)}\n")
        return

    if provider == "ollama":
        print(f"\n  {GREEN}Ollama runs locally — no API key needed!{RESET}")
        print(f"  Just install Ollama: https://ollama.ai")
        print(f"  Then run: {DIM}ollama pull llama3{RESET}\n")
        return

    info = PROVIDER_INFO[provider]

    print()
    print(f"{CYAN}{BOLD}{'━' * 50}{RESET}")
    print(f"{CYAN}{BOLD}  🔑  Set API Key — {info['name']}{RESET}")
    print(f"{CYAN}{BOLD}{'━' * 50}{RESET}")
    print(f"  {BOLD}Free tier:{RESET} {info['free']}")
    print(f"  {BOLD}Get key  :{RESET} {info['url']}")
    print(f"  {BOLD}Key hint :{RESET} {info['key_hint']}")
    print(f"{CYAN}{'━' * 50}{RESET}")
    print()

    try:
        key = getpass.getpass(f"  Paste your {provider} API key (hidden): ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n  {YELLOW}Cancelled.{RESET}\n")
        return

    if not key:
        print(f"  {YELLOW}No key entered — cancelled.{RESET}\n")
        return

    set_api_key(provider, key)

    print(f"\n  {GREEN}{BOLD}✓  Key saved: {mask_key(key)}{RESET}")
    print(f"  {DIM}Stored in: {ENV_FILE}{RESET}")
    print(f"\n  Now set as active: {CYAN}ai-provider {provider}{RESET}\n")


def cmd_set_provider(provider: str = None):
    """
    Interactive handler for: hazel> ai-provider <provider>
    Sets the active AI provider.
    """
    if not provider:
        _show_provider_status()
        return

    provider = provider.lower().strip()

    if provider not in SUPPORTED_PROVIDERS:
        print(f"\n  {RED}Unknown provider: '{provider}'{RESET}")
        print(f"  Supported: {', '.join(SUPPORTED_PROVIDERS)}\n")
        return

    # Check key exists (except ollama)
    if provider != "ollama" and not get_api_key(provider):
        print(f"\n  {YELLOW}No API key found for '{provider}'.{RESET}")
        print(f"  Set it first: {CYAN}set-api {provider}{RESET}\n")
        return

    set_active_provider(provider)
    info = PROVIDER_INFO[provider]
    print(f"\n  {GREEN}{BOLD}✓  Active provider set to: {info['name']}{RESET}\n")


def _show_provider_status():
    """Print a table of all providers and their status."""
    active = get_active_provider()

    print()
    print(f"{CYAN}{BOLD}{'━' * 55}{RESET}")
    print(f"{CYAN}{BOLD}  🤖  AI Provider Status{RESET}")
    print(f"{CYAN}{BOLD}{'━' * 55}{RESET}")

    for p in SUPPORTED_PROVIDERS:
        info   = PROVIDER_INFO[p]
        key    = get_api_key(p)
        is_act = (p == active)

        if p == "ollama":
            status = f"{GREEN}local{RESET}"
            key_display = "no key needed"
        elif key:
            status = f"{GREEN}✓ configured{RESET}"
            key_display = mask_key(key)
        else:
            status = f"{YELLOW}✗ no key{RESET}"
            key_display = f"run: set-api {p}"

        active_marker = f" {GREEN}{BOLD}← ACTIVE{RESET}" if is_act else ""
        print(f"\n  {BOLD}{info['name']}{RESET}{active_marker}")
        print(f"  Status : {status}")
        print(f"  Key    : {DIM}{key_display}{RESET}")
        print(f"  Free   : {DIM}{info['free']}{RESET}")

    print(f"\n{CYAN}{'━' * 55}{RESET}")
    print(f"  Change provider: {CYAN}ai-provider <name>{RESET}")
    print(f"  Add key        : {CYAN}set-api <name>{RESET}")
    print()