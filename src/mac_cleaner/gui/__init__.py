#!/usr/bin/env python3
"""
GUI package for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from .gui import main as gui_main
from .detailed_gui import main as detailed_gui_main

__all__ = [
    'gui_main',
    'detailed_gui_main',
]
