#!/usr/bin/env python3
"""
Detailed GUI entry point for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gui_cleaner import main

if __name__ == "__main__":
    main()
