#!/usr/bin/env python3
"""
Tests for space analyzer functionality.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from mac_cleaner.space_analyzer import SpaceAnalyzer


@pytest.fixture
def analyzer():
    """Create a SpaceAnalyzer instance."""
    return SpaceAnalyzer()


class TestSpaceAnalyzer:
    """Test cases for SpaceAnalyzer class."""

    def test_generate_report_structure(self, analyzer):
        """Test that generate_report returns proper structure."""
        report = analyzer.generate_report()
        
        # Check required fields
        assert "timestamp" in report
        assert "disk_usage" in report
        assert "user_directories" in report
        assert "large_files" in report
        assert "old_files" in report
        assert "total_cache_size" in report
        
        # Check disk usage structure
        disk_usage = report["disk_usage"]
        assert "total" in disk_usage
        assert "free" in disk_usage
        assert "used" in disk_usage
        assert "total_human" in disk_usage
        assert "free_human" in disk_usage
        assert "used_human" in disk_usage

    def test_format_bytes(self, analyzer):
        """Test byte formatting."""
        # Test various sizes
        assert analyzer.format_bytes(0) == "0.00 B"
        assert analyzer.format_bytes(1023) == "1023.00 B"
        assert analyzer.format_bytes(1024) == "1.00 KB"
        assert analyzer.format_bytes(1024 * 1024) == "1.00 MB"
        assert analyzer.format_bytes(1024 * 1024 * 1024) == "1.00 GB"

    def test_get_folder_size(self, analyzer, temp_dir):
        """Test folder size calculation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("x" * 100)
        (temp_dir / "file2.txt").write_text("x" * 200)
        
        # Create nested directory
        nested = temp_dir / "nested"
        nested.mkdir()
        (nested / "file3.txt").write_text("x" * 50)
        
        size = analyzer.get_folder_size(temp_dir)
        assert size == 350  # 100 + 200 + 50

    def test_get_file_age_days(self, analyzer, temp_dir):
        """Test file age calculation."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Should be very recent (0 days old)
        age = analyzer.get_file_age_days(test_file)
        assert age == 0

    def test_is_safe_to_delete(self, analyzer, temp_dir):
        """Test safe to delete detection."""
        # Test safe patterns
        safe_paths = [
            ("Caches", temp_dir / "Caches"),
            ("cache", temp_dir / "cache"),
            ("tmp", temp_dir / "tmp")
        ]
        
        for name, path in safe_paths:
            path.mkdir(exist_ok=True)
            assert analyzer.is_safe_to_delete(name, path)
        
        # Test unsafe patterns
        unsafe_paths = [
            ("Documents", temp_dir / "Documents"),
            ("Desktop", temp_dir / "Desktop"),
            ("Applications", temp_dir / "Applications")
        ]
        
        for name, path in unsafe_paths:
            path.mkdir(exist_ok=True)
            assert not analyzer.is_safe_to_delete(name, path)

    def test_get_recommendation(self, analyzer, temp_dir):
        """Test recommendation generation."""
        # Test cache recommendation
        cache_path = temp_dir / "Caches"
        cache_path.mkdir()
        rec = analyzer.get_recommendation("Caches", cache_path, 1024*1024)
        assert "Safe to delete" in rec
        
        # Test large directory recommendation
        large_path = temp_dir / "LargeDir"
        large_path.mkdir()
        rec = analyzer.get_recommendation("LargeDir", large_path, 1024*1024*1024)  # 1GB
        assert "High priority" in rec

    def test_find_large_files(self, analyzer, temp_dir):
        """Test finding large files."""
        # Create files of different sizes
        (temp_dir / "small.txt").write_text("x" * 1000)  # 1KB
        (temp_dir / "large.txt").write_text("x" * (200 * 1024))  # 200KB
        
        # Mock the home directory to use our temp dir
        analyzer.home = temp_dir
        
        large_files = analyzer.find_large_files(min_size_mb=0)  # Very low threshold
        
        # Should find the large file
        assert len(large_files) >= 1
        large_file = next(f for f in large_files if "large.txt" in f["path"])
        assert large_file["size"] == 200 * 1024

    def test_find_old_files(self, analyzer, temp_dir):
        """Test finding old files."""
        # Create an old file by modifying its timestamp
        old_file = temp_dir / "old.txt"
        old_file.write_text("old content")
        
        # Set file to be very old (365 days ago)
        import time
        old_time = time.time() - (365 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))
        
        # Mock the home directory
        analyzer.home = temp_dir
        
        old_files = analyzer.find_old_files(days_old=300)
        
        # Should find the old file
        assert len(old_files) >= 1
        old_file_result = next(f for f in old_files if "old.txt" in f["path"])
        assert old_file_result["age_days"] >= 300

    def test_save_report(self, analyzer, temp_dir):
        """Test saving report to file."""
        # Create a simple report
        report = {
            "timestamp": "2024-01-01 12:00:00",
            "disk_usage": {
                "total": 1000000000,
                "used": 500000000,
                "free": 500000000
            }
        }
        
        # Mock home directory
        analyzer.home = temp_dir
        
        # Save report
        saved_path = analyzer.save_report(report, filename="test_report.json")
        
        assert saved_path.exists()
        content = saved_path.read_text()
        assert "timestamp" in content
        assert "disk_usage" in content
