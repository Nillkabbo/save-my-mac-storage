#!/usr/bin/env python3
"""
Tests for plugin architecture.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from mac_cleaner.interfaces import CleanerPlugin, PluginManager
from mac_cleaner.plugins import (
    BrowserCacheCleaner,
    SystemCacheCleaner,
    LogFileCleaner,
    TempFileCleaner,
    XcodeCleaner,
    DockerCleaner,
    DownloadsCleaner,
    register_builtin_plugins,
)


class TestPluginManager:
    """Test the plugin manager"""

    def test_register_plugin(self):
        """Test plugin registration"""
        manager = PluginManager()
        plugin = Mock(spec=CleanerPlugin)
        plugin.name = "Test Plugin"
        plugin.category = "test"

        manager.register_plugin(plugin)

        assert "Test Plugin" in manager.plugins
        assert plugin in manager.get_plugins_by_category("test")

    def test_get_plugin(self):
        """Test getting plugin by name"""
        manager = PluginManager()
        plugin = Mock(spec=CleanerPlugin)
        plugin.name = "Test Plugin"
        plugin.category = "test"

        manager.register_plugin(plugin)

        retrieved = manager.get_plugin("Test Plugin")
        assert retrieved == plugin

        nonexistent = manager.get_plugin("Nonexistent")
        assert nonexistent is None

    def test_get_categories(self):
        """Test getting all categories"""
        manager = PluginManager()

        plugin1 = Mock(spec=CleanerPlugin)
        plugin1.name = "Plugin 1"
        plugin1.category = "category1"

        plugin2 = Mock(spec=CleanerPlugin)
        plugin2.name = "Plugin 2"
        plugin2.category = "category2"

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        categories = manager.get_categories()
        assert "category1" in categories
        assert "category2" in categories
        assert len(categories) == 2


class TestBrowserCacheCleaner:
    """Test browser cache cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = BrowserCacheCleaner()

        assert plugin.name == "Browser Cache Cleaner"
        assert plugin.category == "cache"
        assert "cache" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = BrowserCacheCleaner()
        assert plugin.is_safe_to_clean("/any/path") is True

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.home")
    def test_get_cleanable_paths(self, mock_home, mock_exists):
        """Test getting browser cache paths"""
        mock_home.return_value = Path("/Users/test")
        mock_exists.return_value = True

        plugin = BrowserCacheCleaner()
        paths = plugin.get_cleanable_paths()

        # Should contain browser cache paths
        assert any("Chrome" in path for path in paths)
        assert any("Firefox" in path for path in paths)
        assert any("Safari" in path for path in paths)


class TestSystemCacheCleaner:
    """Test system cache cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = SystemCacheCleaner()

        assert plugin.name == "System Cache Cleaner"
        assert plugin.category == "cache"
        assert "system cache" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = SystemCacheCleaner()

        # User cache should be safe
        assert plugin.is_safe_to_clean("/Users/test/Library/Caches") is True

        # System cache should not be safe by default
        assert plugin.is_safe_to_clean("/System/Library/Caches") is False


class TestLogFileCleaner:
    """Test log file cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = LogFileCleaner()

        assert plugin.name == "Log File Cleaner"
        assert plugin.category == "logs"
        assert "log files" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = LogFileCleaner()

        # User logs should be safe
        assert plugin.is_safe_to_clean("/Users/test/Library/Logs") is True

        # System logs should not be safe by default
        assert plugin.is_safe_to_clean("/var/log") is False
        assert plugin.is_safe_to_clean("/Library/Logs") is False


class TestTempFileCleaner:
    """Test temporary file cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = TempFileCleaner()

        assert plugin.name == "Temporary File Cleaner"
        assert plugin.category == "temp"
        assert "temporary files" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = TempFileCleaner()

        # User temp files should be safe
        assert plugin.is_safe_to_clean("/Users/test/.Trash") is True

        # System temp should not be safe by default
        assert plugin.is_safe_to_clean("/tmp") is False
        assert plugin.is_safe_to_clean("/var/tmp") is False


class TestXcodeCleaner:
    """Test Xcode cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = XcodeCleaner()

        assert plugin.name == "Xcode Cleaner"
        assert plugin.category == "development"
        assert "xcode" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = XcodeCleaner()
        assert plugin.is_safe_to_clean("/any/path") is True


class TestDockerCleaner:
    """Test Docker cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = DockerCleaner()

        assert plugin.name == "Docker Cleaner"
        assert plugin.category == "development"
        assert "docker" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = DockerCleaner()
        assert plugin.is_safe_to_clean("/any/path") is True


class TestDownloadsCleaner:
    """Test downloads cleaner plugin"""

    def test_plugin_properties(self):
        """Test plugin metadata"""
        plugin = DownloadsCleaner()

        assert plugin.name == "Downloads Cleaner"
        assert plugin.category == "user"
        assert "downloads" in plugin.description.lower()

    def test_is_safe_to_clean(self):
        """Test safety check"""
        plugin = DownloadsCleaner()
        assert plugin.is_safe_to_clean("/any/path") is False


class TestRegisterBuiltinPlugins:
    """Test builtin plugin registration"""

    def test_register_builtin_plugins(self):
        """Test registering all builtin plugins"""
        manager = register_builtin_plugins(PluginManager())

        # Should have multiple plugins registered
        assert len(manager.get_all_plugins()) > 0

        # Should have multiple categories
        categories = manager.get_categories()
        assert "cache" in categories
        assert "development" in categories

        # Should have specific plugins
        assert manager.get_plugin("Browser Cache Cleaner") is not None
        assert manager.get_plugin("Xcode Cleaner") is not None


class TestPluginIntegration:
    """Test plugin integration with real filesystem"""

    def test_analyze_paths_with_real_directory(self):
        """Test analyzing paths with a real directory"""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            (temp_path / "file1.txt").write_text("test content 1")
            (temp_path / "file2.txt").write_text("test content 2")

            # Create subdirectory with file
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("test content 3")

            # Create a mock plugin that returns our temp directory
            class MockPlugin(CleanerPlugin):
                @property
                def name(self) -> str:
                    return "Mock Plugin"

                @property
                def category(self) -> str:
                    return "test"

                @property
                def description(self) -> str:
                    return "Test plugin"

                def get_cleanable_paths(self) -> list:
                    return [str(temp_path)]

                def is_safe_to_clean(self, path: str) -> bool:
                    return True

            plugin = MockPlugin()
            results = plugin.analyze_paths()

            # Should analyze the directory correctly
            assert len(results["paths"]) == 1
            assert results["paths"][0]["path"] == str(temp_path)
            assert results["paths"][0]["file_count"] == 3
            assert results["paths"][0]["size"] > 0
            assert results["file_count"] == 3
            assert results["total_size"] > 0
            assert results["safe_to_clean"] is True

    def test_clean_paths_dry_run(self):
        """Test cleaning paths in dry run mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.txt").write_text("test content")

            class MockPlugin(CleanerPlugin):
                @property
                def name(self) -> str:
                    return "Mock Plugin"

                @property
                def category(self) -> str:
                    return "test"

                @property
                def description(self) -> str:
                    return "Test plugin"

                def get_cleanable_paths(self) -> list:
                    return [str(temp_path)]

                def is_safe_to_clean(self, path: str) -> bool:
                    return True

            plugin = MockPlugin()
            results = plugin.clean_paths(dry_run=True)

            # Should simulate analysis without actually deleting
            assert len(results["analyzed"]) == 1
            assert results["analyzed"][0]["path"] == str(temp_path)
            assert results["analyzed"][0]["action"] == "analyzed_only"
            assert results["total_analyzed"] > 0
            assert results["mode"] == "read_only_analysis"

            # Directory should still exist
            assert temp_path.exists()
