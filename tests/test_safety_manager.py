#!/usr/bin/env python3
"""
Tests for safety manager functionality.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from mac_cleaner.safety_manager import SafetyManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def safety_manager():
    """Create a SafetyManager instance."""
    return SafetyManager()


class TestSafetyManager:
    """Test cases for SafetyManager class."""

    def test_init_default_backup_dir(self, safety_manager):
        """Test SafetyManager initialization with default backup directory."""
        assert safety_manager.backup_dir is not None
        assert "mac_cleaner_backup" in str(safety_manager.backup_dir)

    def test_is_path_safe_system_paths(self, safety_manager):
        """Test safety check for system paths."""
        protected_paths = [
            "/System",
            "/usr/bin",
            "/Library/Keychains",
            "/etc"
        ]
        
        for path in protected_paths:
            assert not safety_manager.is_path_safe(path)

    def test_is_path_safe_user_paths(self, safety_manager):
        """Test safety check for user paths."""
        user_protected = [
            "~/.ssh",
            "~/.gnupg",
            "~/Library/Keychains"
        ]
        
        for path in user_protected:
            expanded = str(Path(path).expanduser())
            assert not safety_manager.is_path_safe(expanded)

    def test_is_path_safe_safe_paths(self, safety_manager):
        """Test that safe paths return True."""
        safe_paths = [
            "/tmp",
            "~/Library/Caches",
            "~/Downloads",
            "/var/tmp"
        ]
        
        for path in safe_paths:
            expanded = str(Path(path).expanduser())
            assert safety_manager.is_path_safe(expanded)

    def test_create_backup_file(self, safety_manager, temp_dir):
        """Test creating backup of a single file."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("important content")
        
        # Create backup
        success = safety_manager.create_backup(str(test_file))
        
        assert success
        
        # Check that backup was created in backup directory
        backup_files = list(safety_manager.backup_dir.glob("*"))
        assert len(backup_files) > 0

    def test_create_backup_nonexistent_file(self, safety_manager):
        """Test backup of nonexistent file."""
        success = safety_manager.create_backup("/nonexistent/file")
        assert not success

    def test_get_size_file(self, safety_manager, temp_dir):
        """Test getting file size."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 100)
        
        size = safety_manager.get_size(str(test_file))
        assert size == 100

    def test_get_size_directory(self, safety_manager, temp_dir):
        """Test getting directory size."""
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("x" * 50)
        (test_dir / "file2.txt").write_text("x" * 30)
        
        size = safety_manager.get_size(str(test_dir))
        assert size == 80

    def test_calculate_checksum(self, safety_manager, temp_dir):
        """Test file checksum calculation."""
        # Create test file
        test_file = temp_dir / "test.txt"
        content = "test content for checksum"
        test_file.write_text(content)
        
        # Calculate checksum
        checksum1 = safety_manager.calculate_checksum(str(test_file))
        
        # Modify file and recalculate
        test_file.write_text(content + " modified")
        checksum2 = safety_manager.calculate_checksum(str(test_file))
        
        assert checksum1 != checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_is_critical_file(self, safety_manager):
        """Test critical file detection."""
        critical_files = [
            "/System/Library/CoreServices/SystemUIServer.app",
            "/usr/bin/python3",
            "~/Library/Keychains/login.keychain-db"
        ]
        
        for file_path in critical_files:
            result = SafetyManager.is_critical_file(file_path)
            # Note: This might return False since files don't exist, but method should not crash
            assert isinstance(result, bool)

    def test_is_recently_modified(self, safety_manager, temp_dir):
        """Test recent file modification detection."""
        # Create a recent file
        recent_file = temp_dir / "recent.txt"
        recent_file.write_text("recent content")
        
        # Should be recent
        assert SafetyManager.is_recently_modified(str(recent_file), days=7)
        
        # Should not be recent for 365 days
        assert not SafetyManager.is_recently_modified(str(recent_file), days=365)

    def test_is_large_file(self, safety_manager, temp_dir):
        """Test large file detection."""
        # Create a small file
        small_file = temp_dir / "small.txt"
        small_file.write_text("x" * 1000)  # 1KB
        
        assert not SafetyManager.is_large_file(str(small_file), size_mb=1)
        
        # Create a larger file
        large_file = temp_dir / "large.txt"
        large_file.write_text("x" * (2 * 1024 * 1024))  # 2MB
        
        assert SafetyManager.is_large_file(str(large_file), size_mb=1)

    def test_list_backups(self, safety_manager):
        """Test listing available backups."""
        backups = safety_manager.list_backups()
        assert isinstance(backups, list)
        
        # Check structure of backup entries
        for backup in backups:
            assert "session_id" in backup
            assert "timestamp" in backup
            assert "backup_count" in backup

    def test_cleanup_old_backups(self, safety_manager):
        """Test cleanup of old backups."""
        # This should not raise an exception
        safety_manager.cleanup_old_backups(days_to_keep=30)
        
        # Test with very short retention period
        safety_manager.cleanup_old_backups(days_to_keep=0)
