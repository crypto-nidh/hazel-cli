"""
explain.py — Command Explanation Engine
----------------------------------------
Triggered by: explain <command> [flags]
Looks up command info from rules.json and prints a structured breakdown.
"""

import json
import os
from typing import Optional

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')

BLUE   = "\033[94m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def _load_explanations() -> dict:
    try:
        with open(RULES_PATH, 'r') as f:
            data = json.load(f)
        return data.get("command_explanations", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{YELLOW}[hazel] Warning: Could not load explanations: {e}{RESET}")
        return {}


def parse_explain_input(user_input: str) -> tuple:
    """
    Parse 'explain nmap -sS -A ...' into (tool, [flags]).
    """
    parts = user_input.strip().split()
    if not parts:
        return "", []
    tool = parts[0].lower()
    flags = [p for p in parts[1:] if p.startswith('-')]
    return tool, flags


def explain_command(user_input: str):
    """Parse input and print the explanation."""
    explanations = _load_explanations()
    tool, flags = parse_explain_input(user_input)

    if not tool:
        print(f"  {YELLOW}Usage: explain <command> [flags]{RESET}")
        print(f"  {YELLOW}Example: explain nmap -sS -A{RESET}")
        return

    print()
    print(f"{BLUE}{BOLD}{'━' * 55}{RESET}")
    print(f"{BLUE}{BOLD}  📖  HAZEL EXPLAIN — {tool.upper()}{RESET}")
    print(f"{BLUE}{BOLD}{'━' * 55}{RESET}")

    if tool not in explanations:
        _show_unknown_tool(tool)
        return

    info = explanations[tool]

    print(f"\n  {BOLD}What it does:{RESET}")
    print(f"  {info.get('description', 'No description available.')}")

    all_flags = info.get("flags", {})

    if flags:
        print(f"\n  {BOLD}Flags you used:{RESET}")
        for flag in flags:
            explanation = all_flags.get(flag) or all_flags.get(flag.lstrip('-'))
            if explanation:
                print(f"  {CYAN}{flag:<10}{RESET} {explanation}")
            else:
                print(f"  {CYAN}{flag:<10}{RESET} {DIM}(no description available){RESET}")
    else:
        if all_flags:
            print(f"\n  {BOLD}Available flags:{RESET}")
            for flag, desc in all_flags.items():
                print(f"  {CYAN}{flag:<10}{RESET} {desc}")

    risks = info.get("risks", "")
    if risks and risks.lower() != "none.":
        print(f"\n  {BOLD}⚠  Risks & Notes:{RESET}")
        print(f"  {YELLOW}{risks}{RESET}")

    print(f"\n{BLUE}{BOLD}{'━' * 55}{RESET}")
    print()


def _show_unknown_tool(tool: str):
    print(f"\n  {YELLOW}No explanation found for '{tool}' in Hazel's knowledge base.{RESET}")
    print(f"\n  {DIM}Try:{RESET}  man {tool}   OR   {tool} --help")
    print(f"  {DIM}Add it to rules.json under 'command_explanations' to contribute!{RESET}")
    print(f"\n{BLUE}{BOLD}{'━' * 55}{RESET}")
    print()


def is_explain_command(user_input: str) -> bool:
    return user_input.strip().lower().startswith("explain ")


def get_explain_target(user_input: str) -> str:
    stripped = user_input.strip()
    if stripped.lower().startswith("explain "):
        return stripped[8:].strip()
    return stripped