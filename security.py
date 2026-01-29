#!/usr/bin/env python3
"""
Security helpers for macOS Cleaner.
"""

import os
import shlex
from pathlib import Path
from typing import Iterable, Tuple


def sanitize_shell_input(value: str) -> str:
    """Sanitize a string for safe shell usage."""
    return shlex.quote(value or "")


def _resolve_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def is_path_within(path: str, allowed_roots: Iterable[str]) -> bool:
    """Check whether path resolves within one of allowed roots."""
    resolved_path = _resolve_path(path)
    for root in allowed_roots:
        resolved_root = _resolve_path(root)
        try:
            common = os.path.commonpath([resolved_path, resolved_root])
        except ValueError:
            continue
        if common == resolved_root:
            return True
    return False


def validate_finder_path(
    path: str, allowed_roots: Iterable[str]
) -> Tuple[bool, str, str]:
    """Validate path for Finder access and return normalized path."""
    if not path:
        return False, "No path provided", ""

    try:
        resolved_path = _resolve_path(path)
    except (OSError, RuntimeError, ValueError):
        return False, "Invalid path", ""

    if not os.path.exists(resolved_path):
        return False, "Path does not exist", ""

    if not is_path_within(resolved_path, allowed_roots):
        return False, "Path is not allowed", ""

    return True, "", resolved_path
