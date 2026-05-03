"""
interceptor.py — Command Interceptor & Execution Engine
---------------------------------------------------------
Full pipeline every command passes through:

  1. Check Hazel built-ins (explain, writeup, history, AI commands)
  2. Typo detection via analyzer.py
  3. Dangerous command check via security.py
  4. Execute via subprocess / os.system
  5. Capture output → suggestions engine
  6. Save to SQLite history
"""

import subprocess
import os
import sys

import analyzer
import security
import suggestions
import history
import explain
import writeup
import config
import ai_engine

# ANSI colors
GRAY   = "\033[90m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# Commands that need a real interactive TTY
INTERACTIVE_COMMANDS = {
    "vim", "vi", "nano", "emacs", "htop", "top", "less", "more",
    "ssh", "telnet", "ftp", "mysql", "psql", "python", "python3",
    "irb", "node", "bash", "sh", "zsh", "fish", "gdb", "pdb",
    "msfconsole", "metasploit"
}


def _is_interactive(command: str) -> bool:
    base = command.strip().split()[0].lower() if command.strip() else ""
    return base in INTERACTIVE_COMMANDS


def _run_interactive(command: str):
    os.system(command)


def _run_captured(command: str) -> tuple:
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "[hazel] Command timed out after 300 seconds.", 1
    except Exception as e:
        return "", f"[hazel] Execution error: {str(e)}", 1


def handle_builtin(user_input: str, session_id: str) -> bool:
    """
    Handle all Hazel built-in commands.
    Returns True if handled (don't pass to shell), False otherwise.
    """
    raw     = user_input.strip()
    lowered = raw.lower()

    # ── AI commands ─────────────────────────────────────────────────────────

    # ask <question>  — free-form AI Q&A
    # Match "ask" with or without a trailing argument (handles no-arg case too)
    if lowered == "ask" or lowered.startswith("ask "):
        question = raw[4:].strip()
        ai_engine.cmd_ask(question, session_id)
        return True

    # ai explain <command>
    # "ai explain" is 10 chars; require the prefix then slice the rest
    if lowered == "ai explain" or lowered.startswith("ai explain "):
        command = raw[10:].strip()
        ai_engine.cmd_ai_explain(command, session_id)
        return True

    # ai suggest
    if lowered == "ai suggest":
        ai_engine.cmd_ai_suggest(session_id)
        return True

    # ai writeup
    if lowered == "ai writeup":
        ai_engine.cmd_ai_writeup(session_id)
        return True

    # ai status — show which provider is active
    if lowered in ("ai status", "ai"):
        config.cmd_set_provider()
        return True

    # ── API key management ───────────────────────────────────────────────────

    # set-api <provider>
    if lowered.startswith("set-api"):
        parts = raw.split(maxsplit=1)
        provider = parts[1].strip() if len(parts) > 1 else None
        config.cmd_set_api(provider)
        return True

    # ai-provider <provider>
    if lowered.startswith("ai-provider"):
        parts = raw.split(maxsplit=1)
        provider = parts[1].strip() if len(parts) > 1 else None
        config.cmd_set_provider(provider)
        return True

    # ── explain (rule-based) ─────────────────────────────────────────────────
    if explain.is_explain_command(user_input):
        target = explain.get_explain_target(user_input)
        explain.explain_command(target)
        return True

    # ── writeup ──────────────────────────────────────────────────────────────
    if lowered == "writeup":
        cmds = history.get_session_commands(session_id)
        writeup.print_writeup(session_id, cmds)
        return True

    if lowered == "writeup save":
        cmds = history.get_session_commands(session_id)
        writeup.save_writeup(session_id, cmds)
        return True

    # ── history ──────────────────────────────────────────────────────────────
    if lowered == "history":
        _show_recent_history()
        return True

    if lowered.startswith("history search "):
        keyword = raw[15:].strip()
        _search_history(keyword)
        return True

    # ── misc ─────────────────────────────────────────────────────────────────
    if lowered in ("hazel help", "hazel --help", "hazel -h"):
        _show_help()
        return True

    if lowered in ("hazel freq", "hazel frequent"):
        _show_frequent()
        return True

    return False


def _show_recent_history():
    cmds = history.get_last_n_commands(20)
    print(f"\n{BOLD}  Recent commands:{RESET}")
    for i, cmd in enumerate(reversed(cmds), 1):
        ts = cmd.get("timestamp", "")[:19].replace("T", " ")
        print(f"  {GRAY}{i:>3}.  {ts}  {RESET}{cmd['command']}")
    print()


def _search_history(keyword: str):
    cmds = history.search_history(keyword)
    if not cmds:
        print(f"\n  {YELLOW}No history found matching '{keyword}'{RESET}\n")
        return
    print(f"\n{BOLD}  History matching '{keyword}':{RESET}")
    for cmd in cmds:
        ts = cmd.get("timestamp", "")[:19].replace("T", " ")
        print(f"  {GRAY}{ts}  {RESET}{cmd['command']}")
    print()


def _show_frequent():
    cmds = history.get_frequent_commands(10)
    if not cmds:
        print(f"\n  {YELLOW}No command history yet.{RESET}\n")
        return
    print(f"\n{BOLD}  Most used commands:{RESET}")
    for item in cmds:
        bar = "█" * min(item["count"], 20)
        print(f"  {GREEN}{item['count']:>4}x{RESET}  {bar}  {item['command']}")
    print()


def _show_help():
    ai_status = config.get_active_provider()
    ai_badge  = f"{GREEN}{ai_status}{RESET}" if ai_status != "none" else f"{YELLOW}not configured{RESET}"

    print(f"""
{BOLD}  Hazel CLI — Command Reference{RESET}
  {'─' * 50}

  {CYAN}{BOLD}AI Commands{RESET}  (provider: {ai_badge})
  {GREEN}ask <question>{RESET}          Free-form AI cybersecurity Q&A
  {GREEN}ai explain <cmd>{RESET}        AI-powered command explanation
  {GREEN}ai suggest{RESET}              AI next-step suggestions
  {GREEN}ai writeup{RESET}              AI-generated pentest report
  {GREEN}ai status{RESET}               Show AI provider status

  {CYAN}{BOLD}API Key Setup{RESET}
  {GREEN}set-api groq{RESET}            Add Groq API key (free)
  {GREEN}set-api gemini{RESET}          Add Google Gemini key (free)
  {GREEN}set-api openrouter{RESET}      Add OpenRouter key (free models)
  {GREEN}set-api ollama{RESET}          Setup local Ollama (no key)
  {GREEN}ai-provider <name>{RESET}      Switch active AI provider

  {CYAN}{BOLD}Built-in Tools{RESET}
  {GREEN}explain <cmd> [flags]{RESET}   Rule-based command explainer
  {GREEN}writeup{RESET}                 Print session writeup
  {GREEN}writeup save{RESET}            Save writeup to .md file
  {GREEN}history{RESET}                 Show recent commands
  {GREEN}history search <kw>{RESET}     Search command history
  {GREEN}hazel freq{RESET}              Most used commands
  {GREEN}exit / quit{RESET}             Exit Hazel
  {'─' * 50}
""")


def execute(user_input: str, session_id: str):
    """
    Main pipeline. Called for every user input from cli.py.
    """
    command = user_input.strip()
    if not command:
        return

    # Step 1: Built-in commands
    if handle_builtin(command, session_id):
        return

    # Step 2: Typo correction
    command = analyzer.analyze(command)

    # Step 3: Dangerous command check
    if not security.is_safe_to_run(command):
        tool = suggestions.extract_tool_name(command)
        history.save_command(session_id, command, tool=tool, was_blocked=True)
        return

    # Step 4: Execute
    tool = suggestions.extract_tool_name(command)

    if _is_interactive(command):
        history.save_command(session_id, command, tool=tool)
        _run_interactive(command)
    else:
        stdout, stderr, returncode = _run_captured(command)

        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)

        snippet = (stdout or stderr or "")[:300]
        history.save_command(session_id, command, tool=tool, output_snippet=snippet)

        # Step 5: Rule-based pentest suggestions
        if suggestions.is_pentest_tool(command):
            output_combined = (stdout or "") + (stderr or "")
            suggestions.analyze_and_suggest(tool, command, output_combined)