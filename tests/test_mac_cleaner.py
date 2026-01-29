#!/usr/bin/env python3
"""
Tests for MacCleaner core functionality.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mac_cleaner.mac_cleaner import MacCleaner


class TestMacCleaner:
    """Test the MacCleaner class"""

    def test_initialization(self):
        """Test MacCleaner initialization"""
        cleaner = MacCleaner()
        assert cleaner.system_info is not None
        assert cleaner.cleanable_paths is not None
        assert cleaner.stats == {"files_deleted": 0, "space_freed": 0, "errors": []}
        assert cleaner.logger is not None

    def test_get_system_info(self):
        """Test system info collection"""
        cleaner = MacCleaner()
        info = cleaner.get_system_info()

        # Check required fields
        required_fields = [
            "platform",
            "macos_version",
            "python_version",
            "total_memory",
            "total_memory_human",
            "total_space",
            "total_space_human",
            "used_space",
            "used_space_human",
            "free_space",
            "free_space_human",
            "disk_usage_percent",
        ]

        for field in required_fields:
            assert field in info
            assert info[field] is not None

    def test_get_cleanable_paths(self):
        """Test cleanable paths configuration"""
        cleaner = MacCleaner()
        paths = cleaner.get_cleanable_paths()

        # Check required categories
        required_categories = [
            "user_cache",
            "system_cache",
            "temp_files",
            "logs",
            "trash",
            "browser_cache",
        ]

        for category in required_categories:
            assert category in paths
            assert isinstance(paths[category], list)
            assert len(paths[category]) > 0

    def test_format_bytes(self):
        """Test byte formatting"""
        cleaner = MacCleaner()

        # Test various sizes
        assert cleaner.format_bytes(0) == "0.00 B"
        assert cleaner.format_bytes(1024) == "1.00 KB"
        assert cleaner.format_bytes(1024 * 1024) == "1.00 MB"
        assert cleaner.format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert cleaner.format_bytes(1024 * 1024 * 1024 * 1024) == "1.00 TB"

    def test_get_directory_size_nonexistent(self):
        """Test directory size with non-existent path"""
        cleaner = MacCleaner()
        size = cleaner.get_directory_size("/non/existent/path")
        assert size == 0

    def test_get_directory_size_with_permission_error(self, tmp_path):
        """Test directory size with permission error"""
        cleaner = MacCleaner()

        # Create a directory and file
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Mock os.walk to raise PermissionError
        with patch("os.walk") as mock_walk:
            mock_walk.side_effect = PermissionError("Permission denied")
            size = cleaner.get_directory_size(str(test_dir))
            assert size == 0

    def test_clean_category_readonly_mode(self, tmp_path):
        """Test category cleaning in read-only mode"""
        cleaner = MacCleaner()

        # Create a temporary cache directory
        cache_dir = tmp_path / "Library" / "Caches"
        cache_dir.mkdir(parents=True)

        # Add some test files
        (cache_dir / "test1.txt").write_text("test1")
        (cache_dir / "test2.txt").write_text("test2")

        # Mock the cleanable_paths to use our test directory
        cleaner.cleanable_paths["user_cache"] = [str(cache_dir)]

        # Test in dry-run mode (should always be read-only)
        result = cleaner.clean_category("user_cache", dry_run=True)

        assert result["category"] == "user_cache"
        assert result["files_deleted"] == 0  # Should never delete in read-only mode
        assert result["space_freed"] == 0
        assert result["space_freed_human"] == "0 B"
        assert result["mode"] == "read_only_analysis"
        assert result["files_analyzed"] >= 0
        assert result["space_analyzed"] >= 0

    def test_clean_category_nonexistent_category(self):
        """Test cleaning non-existent category"""
        cleaner = MacCleaner()
        result = cleaner.clean_category("nonexistent_category", dry_run=True)

        assert result["files_deleted"] == 0
        assert "error" in result
        assert "Category not found" in result["error"]

    def test_clean_all_readonly_mode(self):
        """Test cleaning all categories in read-only mode"""
        cleaner = MacCleaner()
        result = cleaner.clean_all(dry_run=True)

        assert result["mode"] == "read_only_analysis"
        assert result["files_analyzed"] >= 0
        assert result["space_analyzed"] >= 0
        assert "categories" in result
        assert result["total_files"] == 0  # Should never delete in read-only mode
        assert result["total_space"] == 0
        assert result["total_space_human"] == "0 B"

    def test_analyze_cleanable_space(self):
        """Test cleanable space analysis"""
        cleaner = MacCleaner()
        analysis = cleaner.analyze_cleanable_space()

        # Check structure
        for category, info in analysis.items():
            assert "total_size" in info
            assert "total_size_human" in info
            assert "details" in info
            assert isinstance(info["details"], list)

    def test_get_disk_usage(self):
        """Test disk usage information"""
        cleaner = MacCleaner()
        usage = cleaner.get_disk_usage()

        assert "total_gb" in usage
        assert "used_gb" in usage
        assert "free_gb" in usage
        assert "usage_percent" in usage

        # Check that values are reasonable
        assert usage["total_gb"] > 0
        assert usage["used_gb"] >= 0
        assert usage["free_gb"] >= 0
        assert 0 <= usage["usage_percent"] <= 100

    @patch("psutil.disk_usage")
    def test_get_system_info_with_mock(self, mock_disk_usage):
        """Test system info with mocked psutil"""
        # Mock disk usage
        mock_disk_usage.return_value.total = 1000000000000  # 1TB
        mock_disk_usage.return_value.used = 500000000000  # 500GB
        mock_disk_usage.return_value.free = 500000000000  # 500GB

        cleaner = MacCleaner()
        info = cleaner.get_system_info()

        assert info["total_space"] == 1000000000000
        assert info["used_space"] == 500000000000
        assert info["free_space"] == 500000000000
        assert info["disk_usage_percent"] == 50.0
