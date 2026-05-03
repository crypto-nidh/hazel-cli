#!/usr/bin/env python3
"""
cli.py — Main Entry Point for Hazel CLI
-----------------------------------------
Starts the interactive REPL loop using prompt_toolkit.
Run via: python3 run.py  OR  hazel (alias)
"""

import sys
import uuid
import os
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

import history
import interceptor
import config

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".hazel_history")

GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

PROMPT_STYLE = Style.from_dict({
    "prompt.bracket": "#666666",
    "prompt.name":    "#00d7af bold",
    "prompt.arrow":   "#444444",
    "prompt.cwd":     "#888888",
})

COMPLETION_WORDS = [
    # AI commands
    "ask", "ai explain", "ai suggest", "ai writeup", "ai status",
    "set-api groq", "set-api gemini", "set-api openrouter", "set-api ollama",
    "ai-provider groq", "ai-provider gemini", "ai-provider openrouter", "ai-provider ollama",
    # Hazel built-ins
    "explain", "writeup", "writeup save",
    "history", "history search",
    "hazel help", "hazel freq",
    "exit", "quit",
    # Shell commands
    "ls", "cd", "pwd", "cat", "grep", "find", "chmod", "chown",
    "ps", "kill", "top", "df", "du", "tar", "ssh", "scp",
    "curl", "wget", "ping", "netstat", "ifconfig", "ip",
    # Pentest tools
    "nmap", "gobuster", "ffuf", "nikto", "sqlmap", "hydra",
    "msfconsole", "john", "hashcat", "dirb", "wfuzz",
    "smbclient", "enum4linux", "wpscan", "nc", "netcat",
]


def _print_banner():
    active   = config.get_active_provider()
    if active and active != "none":
        ai_line = f"  {DIM}AI Provider :{RESET} {GREEN}{active}{RESET}"
    else:
        ai_line = f"  {DIM}AI Provider :{RESET} {YELLOW}not set — run: set-api groq{RESET}"

    print(f"""
{CYAN}{BOLD}  ╔══════════════════════════════════════╗
  ║   🌿  Hazel CLI  v2.0.0              ║
  ║   AI-Powered Cybersecurity Terminal  ║
  ╚══════════════════════════════════════╝{RESET}

{ai_line}
  {DIM}Type {RESET}{GREEN}hazel help{RESET}{DIM} for all commands.
  Type {RESET}{GREEN}ask <question>{RESET}{DIM} to use AI.
  Type {RESET}{GREEN}exit{RESET}{DIM} to quit.{RESET}
""")


def _get_prompt_text(session_id: str) -> HTML:
    cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
    return HTML(
        f'<prompt.bracket>[</prompt.bracket>'
        f'<prompt.name>hazel</prompt.name>'
        f'<prompt.bracket>]</prompt.bracket>'
        f' <prompt.cwd>{cwd}</prompt.cwd>'
        f' <prompt.arrow>❯</prompt.arrow> '
    )


def _handle_cd(command: str):
    parts = command.strip().split(maxsplit=1)
    target = os.path.expanduser(parts[1]) if len(parts) > 1 else os.path.expanduser("~")
    try:
        os.chdir(target)
    except FileNotFoundError:
        print(f"  {YELLOW}hazel: cd: {target}: No such file or directory{RESET}")
    except PermissionError:
        print(f"  {YELLOW}hazel: cd: {target}: Permission denied{RESET}")


def main():
    history.init_db()
    session_id = str(uuid.uuid4())
    history.start_session(session_id)

    _print_banner()

    completer = WordCompleter(COMPLETION_WORDS, ignore_case=True)
    session   = PromptSession(
        history=FileHistory(HISTORY_FILE),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        complete_while_typing=True,
        style=PROMPT_STYLE,
    )

    while True:
        try:
            user_input = session.prompt(
                lambda: _get_prompt_text(session_id),
                style=PROMPT_STYLE,
            )
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print(f"\n  {DIM}Session ended. Goodbye!{RESET}\n")
            break

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit", "q"):
            print(f"\n  {DIM}Session ended. Goodbye!{RESET}\n")
            break

        if user_input.strip().startswith("cd"):
            _handle_cd(user_input.strip())
            continue

        interceptor.execute(user_input, session_id)

    history.end_session(session_id)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()