#!/usr/bin/env python3
"""
Tests for security functions.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
from pathlib import Path

from mac_cleaner.security import validate_finder_path


def test_validate_finder_path_rejects_missing_path(tmp_path):
    allowed = [str(tmp_path)]
    ok, message, safe_path = validate_finder_path("", allowed)
    assert ok is False
    assert message
    assert safe_path == ""


def test_validate_finder_path_allows_within_root(tmp_path):
    file_path = tmp_path / "example.txt"
    file_path.write_text("ok")
    ok, message, safe_path = validate_finder_path(str(file_path), [str(tmp_path)])
    assert ok is True
    assert message == ""
    assert safe_path == str(file_path.resolve())


def test_validate_finder_path_blocks_outside_root(tmp_path):
    outside = Path(os.sep) / "tmp"
    outside.mkdir(exist_ok=True)
    ok, message, safe_path = validate_finder_path(str(outside), [str(tmp_path)])
    assert ok is False
    assert "allowed" in message.lower()
    assert safe_path == ""
