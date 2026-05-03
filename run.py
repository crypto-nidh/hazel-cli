#!/usr/bin/env python3
"""
run.py — Hazel CLI Launcher
----------------------------
Run this file directly when all .py files are in the same folder:

    python3 run.py

This avoids needing a hazel/ package subfolder.
"""

import sys
import os

# Add current directory to path so all modules can import each other
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the CLI
from cli import main

if __name__ == "__main__":
    main()