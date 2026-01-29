#!/usr/bin/env python3
"""
Tests for file analyzer functionality.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from mac_cleaner.file_analyzer import FileAnalyzer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def analyzer():
    """Create a FileAnalyzer instance."""
    return FileAnalyzer()


class TestFileAnalyzer:
    """Test cases for FileAnalyzer class."""

    def test_analyze_empty_directory(self, analyzer, temp_dir):
        """Test analyzing an empty directory."""
        results = analyzer.scan_directory(str(temp_dir))
        assert isinstance(results, list)
        assert len(results) == 0

    def test_analyze_directory_with_files(self, analyzer, temp_dir):
        """Test analyzing a directory with various file types."""
        # Create test files
        (temp_dir / "test.txt").write_text("test content")
        (temp_dir / "cache.tmp").write_text("cache data")
        (temp_dir / "old.log").write_text("log content")
        
        # Set different modification times
        old_time = datetime.now() - timedelta(days=60)
        (temp_dir / "old.log").touch()
        
        results = analyzer.scan_directory(str(temp_dir))
        assert len(results) == 3
        
        # Check that all required fields are present
        for result in results:
            assert "path" in result
            assert "size" in result
            assert "modified" in result
            assert "importance_score" in result
            assert "safety_level" in result
            assert "recommendation" in result

    def test_importance_score_calculation(self, analyzer, temp_dir):
        """Test importance score calculation for different file types."""
        # Create a cache file (should have low importance)
        cache_file = temp_dir / "cache.tmp"
        cache_file.write_text("cache content")
        
        results = analyzer.scan_directory(str(temp_dir))
        cache_result = next(r for r in results if r["path"].endswith("cache.tmp"))
        
        # Cache files should have low importance scores
        assert cache_result["importance_score"] <= 30
        assert cache_result["safety_level"] in ["safe", "very_safe"]
        assert cache_result["recommendation"] in ["delete", "review"]

    def test_safety_level_classification(self, analyzer, temp_dir):
        """Test safety level classification."""
        # Create different file types
        (temp_dir / "document.txt").write_text("important document")
        (temp_dir / "cache.tmp").write_text("temporary cache")
        (temp_dir / "system.log").write_text("system log")
        
        results = analyzer.scan_directory(str(temp_dir))
        
        # Find results by file type
        cache_result = next(r for r in results if r["path"].endswith("cache.tmp"))
        doc_result = next(r for r in results if r["path"].endswith("document.txt"))
        
        # Cache should be safer to delete than documents
        assert cache_result["importance_score"] < doc_result["importance_score"]

    def test_recommendation_logic(self, analyzer, temp_dir):
        """Test deletion recommendations."""
        # Create very old cache file
        old_cache = temp_dir / "old_cache.tmp"
        old_cache.write_text("old cache")
        old_time = datetime.now() - timedelta(days=100)
        old_cache.touch()
        
        results = analyzer.scan_directory(str(temp_dir))
        old_cache_result = next(r for r in results if r["path"].endswith("old_cache.tmp"))
        
        # Old cache files should be recommended for deletion
        assert old_cache_result["recommendation"] == "delete"
        assert old_cache_result["safety_level"] in ["safe", "very_safe"]

    def test_file_size_calculation(self, analyzer, temp_dir):
        """Test file size calculation."""
        # Create files with different sizes
        (temp_dir / "small.txt").write_text("x" * 100)
        (temp_dir / "large.txt").write_text("x" * 10000)
        
        results = analyzer.scan_directory(str(temp_dir))
        
        small_result = next(r for r in results if r["path"].endswith("small.txt"))
        large_result = next(r for r in results if r["path"].endswith("large.txt"))
        
        assert small_result["size"] == 100
        assert large_result["size"] == 10000
        assert large_result["size"] > small_result["size"]

    def test_nested_directory_analysis(self, analyzer, temp_dir):
        """Test analyzing nested directories."""
        # Create nested structure
        nested = temp_dir / "nested"
        nested.mkdir()
        (nested / "deep_file.tmp").write_text("deep content")
        
        results = analyzer.scan_directory(str(temp_dir))
        
        # Should find files in nested directories
        assert len(results) == 1
        assert any("deep_file.tmp" in r["path"] for r in results)

    def test_analyze_nonexistent_directory(self, analyzer):
        """Test analyzing a directory that doesn't exist."""
        results = analyzer.scan_directory("/nonexistent/directory")
        assert isinstance(results, list)

    def test_export_analysis_to_json(self, analyzer, temp_dir):
        """Test exporting analysis results to JSON."""
        # Create test files
        (temp_dir / "test.txt").write_text("test content")
        
        results = analyzer.scan_directory(str(temp_dir))
        
        # Test export functionality
        json_file = temp_dir / "analysis.json"
        success = analyzer.export_analysis(results, str(json_file))
        
        assert success
        assert json_file.exists()
        content = json_file.read_text()
        assert "test.txt" in content
        assert "importance_score" in content
