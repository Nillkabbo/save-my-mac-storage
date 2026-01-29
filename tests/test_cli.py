#!/usr/bin/env python3
"""
Tests for CLI interface.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import json

from click.testing import CliRunner

from mac_cleaner.cli import main


def test_cli_clean_unknown_category_json():
    runner = CliRunner()
    result = runner.invoke(main, ["clean", "--category", "unknown", "--json"])
    # Click now validates choices automatically, so we get exit code 2 and help message
    assert result.exit_code == 2
    assert "Invalid value for '--category'" in result.output
    assert "is not one of" in result.output


def test_cli_clean_dry_run_json():
    runner = CliRunner()
    result = runner.invoke(
        main, ["clean", "--dry-run", "--category", "cache", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["category"] == "cache"
    assert "total_files" in payload
    assert "total_space" in payload
