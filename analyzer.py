"""
analyzer.py — Typo Detection & Correction Module
-------------------------------------------------
Compares user input against known commands using:
  1. Static typo_corrections dict (fast path)
  2. Fuzzy matching via difflib.get_close_matches()
"""

import difflib
import json
import os
from typing import Optional

# Rules file lives in the same directory as this script
RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')

CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
YELLOW = "\033[93m"


def _load_data() -> tuple:
    try:
        with open(RULES_PATH, 'r') as f:
            data = json.load(f)
        return (
            data.get("known_commands", []),
            data.get("typo_corrections", {})
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{YELLOW}[hazel] Warning: Could not load analyzer rules: {e}{RESET}")
        return [], {}


def extract_base_command(command: str) -> str:
    """Extract the first word of a command string."""
    return command.strip().split()[0] if command.strip() else ""


def find_correction(command: str) -> Optional[str]:
    """
    Look for a typo correction for the given command.
    Returns corrected command string, or None if no correction found.
    """
    known_commands, typo_corrections = _load_data()
    base = extract_base_command(command)

    if not base:
        return None

    # Strategy 1: static lookup
    if base in typo_corrections:
        corrected_base = typo_corrections[base]
        rest = command.strip()[len(base):]
        return corrected_base + rest

    # Strategy 2: fuzzy match
    matches = difflib.get_close_matches(base, known_commands, n=1, cutoff=0.6)
    if matches and matches[0] != base:
        corrected_base = matches[0]
        rest = command.strip()[len(base):]
        return corrected_base + rest

    return None


def display_suggestion(original: str, corrected: str):
    print()
    print(f"{CYAN}{BOLD}  ✏  Did you mean?{RESET}")
    print(f"  {BOLD}You typed:{RESET}  {original}")
    print(f"  {BOLD}Suggested:{RESET}  {CYAN}{corrected}{RESET}")
    print()


def prompt_correction(original: str, corrected: str) -> str:
    """Ask user whether to run corrected or original command."""
    display_suggestion(original, corrected)
    try:
        answer = input(f"  {CYAN}Run corrected command? [Y/n]: {RESET}").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return original

    if answer in ("", "y", "yes"):
        print(f"  {CYAN}[hazel] Running: {corrected}{RESET}\n")
        return corrected
    else:
        print(f"  {CYAN}[hazel] Running original: {original}{RESET}\n")
        return original


def analyze(command: str) -> str:
    """
    Main entry point. Returns the command to execute
    (may be corrected based on user choice).
    """
    correction = find_correction(command)
    if correction and correction != command:
        return prompt_correction(command, correction)
    return command