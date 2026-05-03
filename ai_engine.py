"""
ai_engine.py — Multi-Provider AI Routing Engine
------------------------------------------------
Central AI brain for Hazel CLI.

Features:
  - Routes to the configured provider (groq/gemini/openrouter/ollama)
  - Multi-provider fallback chain if primary fails
  - Falls back to rule-based system if ALL providers fail
  - Cybersecurity-focused system prompt
  - Safe command flow: AI suggests → user confirms → safety checks → execute

Commands handled:
  ask <question>     → free-form AI question
  ai explain <cmd>   → AI-powered command explanation
  ai suggest         → AI next-step suggestions based on history
  ai writeup         → AI-generated pentest narrative
"""

import os
import sys
import re

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROVIDERS_DIR = os.path.join(BASE_DIR, "providers")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, PROVIDERS_DIR)

import config
import security
import analyzer

import providers.groq       as _groq
import providers.gemini     as _gemini
import providers.openrouter as _openrouter
import providers.ollama     as _ollama

# ANSI colors
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# Maps provider name → query function
PROVIDER_MAP = {
    "groq":       _groq.query,
    "gemini":     _gemini.query,
    "openrouter": _openrouter.query,
    "ollama":     _ollama.query,
}

# Cybersecurity system prompt sent with every AI request
SYSTEM_PROMPT = """You are Hazel, an expert cybersecurity and penetration testing assistant embedded in a Linux terminal.

Rules you must always follow:
1. NEVER execute commands yourself — only SUGGEST them to the user.
2. When suggesting a command, ALWAYS wrap it in <cmd> tags: <cmd>nmap -sS -sV 10.10.10.1</cmd>
3. Keep responses concise and terminal-friendly. No markdown headers. Plain text only.
4. Always explain WHY you are suggesting a command in one sentence.
5. Add a one-line risk warning for any potentially dangerous command.
6. Only help with ethical hacking, CTF challenges, and authorized penetration testing.
7. If asked about illegal activities, refuse politely and explain why.

Format for command suggestions:
  Suggestion: [what to do]
  Reason: [why]
  <cmd>actual command here</cmd>
  Risk: [one line risk note, or 'Low risk' if safe]"""


# ── Core AI call with fallback ────────────────────────────────────────────────

def _call_provider(provider: str, prompt: str) -> str:
    """
    Call a specific provider. Returns response text or raises RuntimeError.
    """
    fn = PROVIDER_MAP.get(provider)
    if not fn:
        raise RuntimeError(f"Unknown provider: {provider}")

    key = config.get_api_key(provider)
    if not key and provider != "ollama":
        raise RuntimeError(
            f"No API key configured for '{provider}'. "
            f"Run: set-api {provider}"
        )

    return fn(prompt=prompt, api_key=key, system=SYSTEM_PROMPT)


def call_ai(prompt: str) -> tuple:
    """
    Main AI call with multi-provider fallback.

    Order:
      1. Try active provider
      2. Try other configured providers
      3. Return (None, error_message) if all fail

    Returns:
        Tuple of (response_text, provider_used) on success
        Tuple of (None, error_message) on total failure
    """
    active   = config.get_active_provider()
    all_configured = config.get_configured_providers()

    # Build fallback order: active first, then others
    order = []
    if active and active != "none":
        order.append(active)
    for p in all_configured:
        if p not in order:
            order.append(p)

    if not order:
        return None, "no_provider"

    errors = []
    for provider in order:
        try:
            print(f"  {DIM}[hazel AI] Calling {provider}...{RESET}", flush=True)
            response = _call_provider(provider, prompt)
            return response, provider
        except RuntimeError as e:
            errors.append(f"{provider}: {e}")
            if len(order) > 1:
                print(f"  {YELLOW}[hazel] {provider} failed, trying next...{RESET}")
            continue

    return None, "\n".join(errors)


# ── Command extraction from AI response ──────────────────────────────────────

def extract_commands(text: str) -> list:
    """
    Extract all <cmd>...</cmd> tagged commands from AI response.
    Returns list of command strings.
    """
    return re.findall(r'<cmd>(.*?)</cmd>', text, re.DOTALL)


def clean_response(text: str) -> str:
    """Remove <cmd> tags from display text (commands shown separately)."""
    return re.sub(r'<cmd>.*?</cmd>', '', text, flags=re.DOTALL).strip()


# ── Safe command execution flow ───────────────────────────────────────────────

def prompt_and_execute(commands: list, session_id: str):
    """
    Show AI-suggested commands and ask user to confirm each one.
    Each confirmed command goes through full safety checks before execution.

    Args:
        commands:   List of command strings extracted from AI response.
        session_id: Current session ID for history logging.
    """
    if not commands:
        return

    import interceptor  # imported here to avoid circular import

    print()
    print(f"{CYAN}{BOLD}{'━' * 50}{RESET}")
    print(f"{CYAN}{BOLD}  🤖  AI Suggested Commands{RESET}")
    print(f"{CYAN}{BOLD}{'━' * 50}{RESET}")

    for i, cmd in enumerate(commands, 1):
        cmd = cmd.strip()
        print(f"\n  {BOLD}[{i}]{RESET} {CYAN}{cmd}{RESET}")

    print(f"\n{CYAN}{'━' * 50}{RESET}")
    print(f"  {YELLOW}⚠  AI-generated commands — review before running{RESET}")
    print()

    for cmd in commands:
        cmd = cmd.strip()
        try:
            answer = input(
                f"  Run {CYAN}{cmd[:60]}{'...' if len(cmd)>60 else ''}{RESET} ? [y/N]: "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if answer in ("y", "yes"):
            # Run through full Hazel pipeline (typo check + security check)
            interceptor.execute(cmd, session_id)
        else:
            print(f"  {DIM}Skipped.{RESET}")

    print()


# ── AI Feature Handlers ───────────────────────────────────────────────────────

def cmd_ask(question: str, session_id: str):
    """
    Handler for: hazel> ask <question>
    Free-form AI cybersecurity Q&A.
    """
    if not question.strip():
        print(f"  {YELLOW}Usage: ask <your question>{RESET}")
        print(f"  Example: ask how do i enumerate smb shares\n")
        return

    response, provider = call_ai(question)

    if response is None:
        _show_ai_unavailable(provider)
        return

    _print_ai_response(response, provider)

    # Extract and offer to run any suggested commands
    commands = extract_commands(response)
    if commands:
        prompt_and_execute(commands, session_id)


def cmd_ai_explain(command: str, session_id: str):
    """
    Handler for: hazel> ai explain <command>
    AI-powered command explanation (richer than rule-based explain).
    """
    if not command.strip():
        print(f"  {YELLOW}Usage: ai explain <command>{RESET}")
        print(f"  Example: ai explain nmap -sS -sV -A 10.10.10.1\n")
        return

    prompt = (
        f"Explain this command in detail for a penetration tester:\n"
        f"  {command}\n\n"
        f"Cover: what it does, what each flag means, what output to expect, "
        f"and any security/legal risks. Be concise."
    )

    response, provider = call_ai(prompt)

    if response is None:
        # Graceful fallback to rule-based explain
        print(f"  {YELLOW}[hazel] AI unavailable — using built-in explainer{RESET}\n")
        import explain
        explain.explain_command(command)
        return

    _print_ai_response(response, provider)


def cmd_ai_suggest(session_id: str):
    """
    Handler for: hazel> ai suggest
    AI analyzes recent session history and suggests next steps.
    """
    import history

    recent = history.get_session_commands(session_id)
    if not recent:
        print(f"  {YELLOW}No commands in this session yet. Run some scans first!{RESET}\n")
        return

    # Build a context summary from last 10 commands
    cmd_list = "\n".join(
        f"  {c['command']}" for c in recent[-10:]
    )

    prompt = (
        f"I am doing a penetration test. Here are the commands I have run so far:\n\n"
        f"{cmd_list}\n\n"
        f"Based on these commands, what should I do next? "
        f"Suggest 2-3 specific next steps with exact commands."
    )

    response, provider = call_ai(prompt)

    if response is None:
        print(f"  {YELLOW}[hazel] AI unavailable — using rule-based suggestions{RESET}\n")
        import suggestions
        # Show frequent tools as fallback
        tools = history.get_frequent_tools(3)
        if tools:
            print(f"  {BOLD}Recently used tools:{RESET}")
            for t in tools:
                print(f"  • {t['tool']} ({t['count']}x)")
        return

    _print_ai_response(response, provider)
    commands = extract_commands(response)
    if commands:
        prompt_and_execute(commands, session_id)


def cmd_ai_writeup(session_id: str):
    """
    Handler for: hazel> ai writeup
    AI generates a professional pentest narrative from session history.
    """
    import history

    cmds = history.get_session_commands(session_id)
    if not cmds:
        print(f"  {YELLOW}No commands recorded in this session yet.{RESET}\n")
        return

    # Build session summary for AI
    cmd_list = "\n".join(
        f"  [{c['timestamp'][11:19]}] {c['command']}"
        for c in cmds if not c.get('was_blocked')
    )

    prompt = (
        f"Generate a professional penetration testing writeup based on these commands:\n\n"
        f"{cmd_list}\n\n"
        f"Format it as:\n"
        f"1. Executive Summary (2 sentences)\n"
        f"2. Methodology (phases used)\n"
        f"3. Findings (what was discovered)\n"
        f"4. Recommendations\n\n"
        f"Be professional, concise, and suitable for a client report."
    )

    response, provider = call_ai(prompt)

    if response is None:
        print(f"  {YELLOW}[hazel] AI unavailable — using rule-based writeup{RESET}\n")
        import writeup
        writeup.print_writeup(session_id, cmds)
        return

    print()
    print(f"{GREEN}{BOLD}{'━' * 55}{RESET}")
    print(f"{GREEN}{BOLD}  📝  AI WRITEUP  [{provider}]{RESET}")
    print(f"{GREEN}{BOLD}{'━' * 55}{RESET}")
    print()

    for line in response.splitlines():
        print(f"  {line}")

    print()
    print(f"{GREEN}{BOLD}{'━' * 55}{RESET}")

    # Ask to save
    try:
        save = input(f"\n  Save as .md file? [y/N]: ").strip().lower()
        if save in ("y", "yes"):
            import writeup
            writeup.save_writeup(session_id, cmds)
    except (KeyboardInterrupt, EOFError):
        print()


# ── Display helpers ───────────────────────────────────────────────────────────

def _print_ai_response(response: str, provider: str):
    """Pretty-print an AI response with provider badge."""
    clean = clean_response(response)

    print()
    print(f"{BLUE}{BOLD}{'━' * 55}{RESET}")
    print(f"{BLUE}{BOLD}  🤖  HAZEL AI  [{provider}]{RESET}")
    print(f"{BLUE}{BOLD}{'━' * 55}{RESET}")
    print()

    for line in clean.splitlines():
        if line.strip().startswith("Suggestion:"):
            print(f"  {CYAN}{BOLD}{line}{RESET}")
        elif line.strip().startswith("Risk:"):
            print(f"  {YELLOW}{line}{RESET}")
        elif line.strip().startswith("Reason:"):
            print(f"  {DIM}{line}{RESET}")
        else:
            print(f"  {line}")

    print()
    print(f"{BLUE}{'━' * 55}{RESET}")
    print()


def _show_ai_unavailable(error: str):
    """Show a helpful message when no AI provider is available."""
    print()
    print(f"{YELLOW}{BOLD}{'━' * 50}{RESET}")
    print(f"{YELLOW}{BOLD}  ⚠  AI Not Available{RESET}")
    print(f"{YELLOW}{BOLD}{'━' * 50}{RESET}")

    if error == "no_provider":
        print(f"\n  No AI provider configured yet.")
        print(f"\n  Quick setup:")
        print(f"  {CYAN}1. set-api groq{RESET}       ← get free key at console.groq.com")
        print(f"  {CYAN}2. ai-provider groq{RESET}   ← set as active")
        print(f"  {CYAN}3. ask <question>{RESET}     ← start using AI")
    else:
        print(f"\n  All providers failed:")
        for line in error.splitlines():
            print(f"  {DIM}{line}{RESET}")
        print(f"\n  Hazel's rule-based system is still active.")

    print(f"\n{YELLOW}{'━' * 50}{RESET}\n")


def is_ai_available() -> bool:
    """Return True if at least one provider is configured."""
    return bool(config.get_configured_providers())