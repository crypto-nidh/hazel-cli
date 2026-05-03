"""
suggestions.py — Context-Aware Pentesting Suggestion Engine
------------------------------------------------------------
After a pentesting tool runs, inspects output and suggests next steps.
All logic is rule-based via rules.json.
"""

import json
import os
import re

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')

GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def _load_suggestions() -> dict:
    try:
        with open(RULES_PATH, 'r') as f:
            data = json.load(f)
        return data.get("pentest_suggestions", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _extract_target(command: str) -> str:
    """Extract IP or URL from command, fallback to placeholder."""
    ip_match = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', command)
    if ip_match:
        return ip_match.group(1)
    url_match = re.search(r'https?://[\w./:-]+', command)
    if url_match:
        return url_match.group(0)
    return "{target}"


def get_suggestions(tool: str, command: str, output: str) -> list:
    """
    Generate next-step suggestions based on tool output.
    Returns list of dicts with 'suggestion' and 'command' keys.
    """
    rules = _load_suggestions()
    tool_rules = rules.get(tool.lower(), [])

    if not tool_rules:
        return []

    target = _extract_target(command)
    matched = []

    for rule in tool_rules:
        keywords = rule.get("keywords", [])
        if any(kw.lower() in output.lower() for kw in keywords):
            suggested_cmd = rule["command"].replace("{target}", target)
            matched.append({
                "suggestion": rule["suggestion"],
                "command": suggested_cmd,
                "condition": rule.get("condition", "")
            })

    return matched


def display_suggestions(suggestions: list):
    if not suggestions:
        return

    print()
    print(f"{GREEN}{BOLD}{'━' * 55}{RESET}")
    print(f"{GREEN}{BOLD}  💡  HAZEL SUGGESTS — Next Steps{RESET}")
    print(f"{GREEN}{BOLD}{'━' * 55}{RESET}")

    for i, item in enumerate(suggestions, 1):
        print(f"\n  {BOLD}[{i}] {item['suggestion']}{RESET}")
        print(f"  {DIM}$ {item['command']}{RESET}")

    print(f"\n{GREEN}{BOLD}{'━' * 55}{RESET}")
    print()


def analyze_and_suggest(tool: str, command: str, output: str):
    """Main entry: get suggestions and display them."""
    suggestions = get_suggestions(tool, command, output)
    if suggestions:
        display_suggestions(suggestions)


# Pentesting tool detection
PENTEST_TOOLS = {
    "nmap", "gobuster", "ffuf", "nikto", "sqlmap",
    "hydra", "metasploit", "msfconsole", "dirb",
    "wfuzz", "enum4linux", "smbclient", "wpscan"
}


def is_pentest_tool(command: str) -> bool:
    base = command.strip().split()[0].lower() if command.strip() else ""
    return base in PENTEST_TOOLS


def extract_tool_name(command: str) -> str:
    return command.strip().split()[0].lower() if command.strip() else ""