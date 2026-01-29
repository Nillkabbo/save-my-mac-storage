#!/usr/bin/env python3
"""
Basic error handling tests for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mac_cleaner.cli import main
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.safety_manager import SafetyManager


class TestBasicErrorHandling:
    """Test basic error handling scenarios."""

    def test_cli_help_command(self, capsys):
        """Test that help command works without errors."""
        with patch('sys.argv', ['mac-cleaner', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_version_command(self, capsys):
        """Test that version command works without errors."""
        with patch('sys.argv', ['mac-cleaner', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_info_command(self):
        """Test that info command works without errors."""
        with patch('sys.argv', ['mac-cleaner', 'info']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_analyze_command(self):
        """Test that analyze command works without errors."""
        with patch('sys.argv', ['mac-cleaner', 'analyze']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_plugins_command(self):
        """Test that plugins command works without errors."""
        with patch('sys.argv', ['mac-cleaner', 'plugins']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_space_analyzer_init(self):
        """Test SpaceAnalyzer initialization."""
        analyzer = SpaceAnalyzer()
        assert analyzer is not None

    def test_space_analyzer_basic_report(self):
        """Test basic report generation."""
        analyzer = SpaceAnalyzer()
        report = analyzer.generate_report()
        assert report is not None
        assert isinstance(report, dict)

    def test_safety_manager_init(self):
        """Test SafetyManager initialization."""
        safety = SafetyManager()
        assert safety is not None
        assert safety.backup_dir.exists()

    def test_safety_manager_protected_paths(self):
        """Test protected paths functionality."""
        safety = SafetyManager()
        protected = safety.get_protected_paths()
        assert isinstance(protected, set)
        assert len(protected) > 0
        assert "/System" in protected

    def test_format_bytes_function(self):
        """Test format_bytes utility function."""
        from mac_cleaner.cli import format_bytes
        
        assert format_bytes(0) == "0.00 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024*1024) == "1.00 MB"
        assert format_bytes(1024*1024*1024) == "1.00 GB"

    def test_invalid_category_handling(self):
        """Test handling of invalid categories."""
        with patch('sys.argv', ['mac-cleaner', 'clean', '--category', 'invalid']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with error code for invalid category
            assert exc_info.value.code != 0

    def test_invalid_plugin_handling(self):
        """Test handling of invalid plugins."""
        with patch('sys.argv', ['mac-cleaner', 'clean', '--plugin', 'nonexistent']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with error code for invalid plugin
            assert exc_info.value.code != 0

    def test_backup_invalid_path(self):
        """Test backup with invalid path."""
        with patch('sys.argv', ['mac-cleaner', 'backup', '--path', '']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with error code for invalid path
            assert exc_info.value.code != 0


class TestImportErrorHandling:
    """Test import error handling."""

    def test_missing_dependency_handling(self):
        """Test graceful handling of missing dependencies."""
        # This test ensures the application handles missing imports gracefully
        try:
            import psutil
            import flask
            import click
        except ImportError as e:
            pytest.fail(f"Required dependency missing: {e}")

    def test_core_module_imports(self):
        """Test that core modules can be imported."""
        try:
            from mac_cleaner import cli, space_analyzer, safety_manager
            from mac_cleaner.mac_cleaner import MacCleaner
        except ImportError as e:
            pytest.fail(f"Core module import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
