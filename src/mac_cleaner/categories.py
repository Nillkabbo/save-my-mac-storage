#!/usr/bin/env python3
"""
Shared category mapping for macOS Cleaner interfaces.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

CATEGORY_MAP = {
    "cache": ["user_cache", "system_cache"],
    "temp": ["temp_files"],
    "logs": ["logs"],
    "trash": ["trash"],
    "browser_cache": ["browser_cache"],
}

CATEGORY_CHOICES = ["all"] + list(CATEGORY_MAP.keys())
