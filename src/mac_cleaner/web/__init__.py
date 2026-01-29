#!/usr/bin/env python3
"""
Web package for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from .web_gui import main as web_main, app

__all__ = [
    'web_main',
    'app',
]
