#!/usr/bin/env python3
"""
Shared configuration defaults for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from pathlib import Path
from typing import List


def get_allowed_finder_roots() -> List[str]:
    """Roots allowed for Finder access in the web interface."""
    home = str(Path.home())
    return [
        home,
        "/Library",
        "/System/Library",
        "/tmp",
        "/var/tmp",
        "/private/var",
        "/var",
    ]


def get_allowed_backup_roots() -> List[str]:
    """Roots allowed for on-demand backups via the web interface."""
    return [str(Path.home())]
