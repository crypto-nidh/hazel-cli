"""
security.py — Dangerous Command Detection Module
-------------------------------------------------
Scans commands against regex patterns from rules.json.
Warns user and requires explicit confirmation for dangerous commands.
"""

import re
import json
import os
from typing import Optional

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')

RED    = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

SEVERITY_COLORS = {
    "CRITICAL": RED,
    "HIGH":     ORANGE,
    "MEDIUM":   YELLOW,
}


def _load_rules() -> list:
    try:
        with open(RULES_PATH, 'r') as f:
            data = json.load(f)
        return data.get("dangerous_commands", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{YELLOW}[hazel] Warning: Could not load security rules: {e}{RESET}")
        return []


def check_command(command: str) -> Optional[dict]:
    """
    Check command against dangerous patterns.
    Returns matching rule dict if dangerous, None if safe.
    """
    rules = _load_rules()
    for rule in rules:
        try:
            if re.search(rule["pattern"], command, re.IGNORECASE):
                return rule
        except re.error:
            continue
    return None


def display_warning(command: str, rule: dict):
    severity = rule.get("severity", "UNKNOWN")
    color = SEVERITY_COLORS.get(severity, YELLOW)
    description = rule.get("description", "This command may be dangerous.")

    print()
    print(f"{color}{BOLD}{'━' * 55}{RESET}")
    print(f"{color}{BOLD}  ⚠  SECURITY WARNING — {severity}{RESET}")
    print(f"{color}{BOLD}{'━' * 55}{RESET}")
    print(f"{BOLD}  Command  :{RESET} {command}")
    print(f"{BOLD}  Risk     :{RESET} {description}")
    print(f"{color}{BOLD}{'━' * 55}{RESET}")
    print()


def prompt_confirmation(command: str) -> bool:
    rule = check_command(command) or {"severity": "HIGH", "description": "Potentially dangerous."}
    display_warning(command, rule)
    try:
        answer = input(
            f"  {YELLOW}Do you still want to run this command? "
            f"Type 'yes' to confirm, anything else to abort:{RESET} "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if answer != "yes":
        print(f"  {YELLOW}[hazel] Command aborted.{RESET}\n")
        return False
    return True


def is_safe_to_run(command: str) -> bool:
    """
    Returns True if command is safe or user confirmed despite warning.
    Returns False if dangerous and user aborted.
    """
    rule = check_command(command)
    if rule is None:
        return True
    return prompt_confirmation(command)