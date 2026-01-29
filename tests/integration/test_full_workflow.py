#!/usr/bin/env python3
"""
Integration tests for full workflow scenarios.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import time
import threading
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mac_cleaner.mac_cleaner import MacCleaner
from mac_cleaner.safety_manager import SafetyManager
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.security import SecurityValidator
from mac_cleaner.privilege_manager import PrivilegeManager


class TestFullWorkflow:
    """Test complete cleaning workflows end-to-end"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp(prefix="mac_cleaner_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_cache_files(self, temp_workspace):
        """Create mock cache files for testing"""
        cache_dir = Path(temp_workspace) / "Library" / "Caches" / "test_app"
        cache_dir.mkdir(parents=True)
        
        # Create test cache files
        test_files = []
        for i in range(5):
            file_path = cache_dir / f"cache_{i}.tmp"
            file_path.write_text(f"cache data {i}" * 100)
            test_files.append(str(file_path))
        
        # Create subdirectory with more files
        sub_dir = cache_dir / "subdir"
        sub_dir.mkdir()
        for i in range(3):
            file_path = sub_dir / f"sub_cache_{i}.tmp"
            file_path.write_text(f"sub cache data {i}" * 50)
            test_files.append(str(file_path))
        
        return test_files

    @pytest.fixture
    def mock_log_files(self, temp_workspace):
        """Create mock log files for testing"""
        log_dir = Path(temp_workspace) / "var" / "log"
        log_dir.mkdir(parents=True)
        
        test_files = []
        for i in range(3):
            file_path = log_dir / f"test_{i}.log"
            file_path.write_text(f"log entry {i}\n" * 20)
            test_files.append(str(file_path))
        
        return test_files

    def test_complete_analysis_workflow(self, temp_workspace, mock_cache_files, mock_log_files):
        """Test complete analysis workflow"""
        # Initialize components
        cleaner = MacCleaner()
        analyzer = SpaceAnalyzer()
        
        # Test space analysis
        with patch('mac_cleaner.space_analyzer.Path.home', return_value=Path(temp_workspace)):
            report = analyzer.generate_report()
        
        # Verify report structure
        assert isinstance(report, dict)
        assert 'total_size' in report
        assert 'categories' in report
        assert 'files' in report
        
        # Verify that our test files are detected
        file_paths = [f.get('path', '') for f in report.get('files', [])]
        cache_found = any('cache_' in path for path in file_paths)
        log_found = any('test_' in path and '.log' in path for path in file_paths)
        
        assert cache_found or log_found, "Test files should be detected in analysis"

    def test_dry_run_workflow(self, temp_workspace, mock_cache_files):
        """Test dry-run cleaning workflow"""
        cleaner = MacCleaner()
        
        # Count files before cleaning
        initial_files = list(Path(temp_workspace).rglob("*.tmp"))
        initial_count = len(initial_files)
        
        # Perform dry-run cleaning
        with patch('mac_cleaner.mac_cleaner.Path.home', return_value=Path(temp_workspace)):
            result = cleaner.clean_category("user_cache", dry_run=True)
        
        # Verify dry-run doesn't delete files
        remaining_files = list(Path(temp_workspace).rglob("*.tmp"))
        assert len(remaining_files) == initial_count, "Dry-run should not delete files"
        
        # Verify result contains expected information
        assert isinstance(result, dict)
        assert 'files_processed' in result or 'files_deleted' in result

    def test_safety_manager_workflow(self, temp_workspace, mock_cache_files):
        """Test safety manager integration"""
        safety_manager = SafetyManager()
        
        # Test backup creation
        with patch('mac_cleaner.safety_manager.Path.home', return_value=Path(temp_workspace)):
            backup_path = safety_manager.create_backup(temp_workspace)
        
        assert backup_path is not None
        assert Path(backup_path).exists(), "Backup should be created"
        
        # Test backup verification
        is_valid = safety_manager.verify_backup(backup_path, temp_workspace)
        assert is_valid, "Backup verification should pass"

    def test_security_validation_workflow(self, temp_workspace):
        """Test security validation in workflow"""
        validator = SecurityValidator()
        
        # Test safe paths
        safe_path = str(Path(temp_workspace) / "safe_directory")
        is_valid, error = validator.validate_path(safe_path, [temp_workspace])
        assert is_valid, f"Safe path should be valid: {error}"
        
        # Test dangerous paths
        dangerous_paths = [
            "/System/Library",
            "/etc/passwd",
            "../../../etc/passwd",
            "~/.ssh",
        ]
        
        for dangerous_path in dangerous_paths:
            is_valid, error = validator.validate_path(dangerous_path, [temp_workspace])
            assert not is_valid, f"Dangerous path should be rejected: {dangerous_path}"

    def test_privilege_management_workflow(self, temp_workspace):
        """Test privilege management in workflow"""
        privilege_manager = PrivilegeManager()
        
        # Test privilege checking
        can_write = privilege_manager.can_write_to_path(temp_workspace)
        assert can_write, "Should be able to write to temp workspace"
        
        # Test safe working directory
        safe_dir = privilege_manager.get_safe_working_directory()
        assert Path(safe_dir).exists(), "Safe working directory should exist"

    def test_web_api_integration(self, temp_workspace, mock_cache_files):
        """Test web API integration"""
        # This would require the web server to be running
        # For now, we'll test the components that the API uses
        
        from web_gui import initialize_cleaner
        
        # Test cleaner initialization
        with patch('web_gui.Path.home', return_value=Path(temp_workspace)):
            success = initialize_cleaner()
        
        assert success, "Web GUI should initialize cleaner successfully"

    def test_error_handling_workflow(self, temp_workspace):
        """Test error handling in complete workflow"""
        cleaner = MacCleaner()
        
        # Test with non-existent path
        with patch('mac_cleaner.mac_cleaner.Path.home', return_value=Path("/non/existent/path")):
            result = cleaner.clean_category("user_cache", dry_run=True)
        
        # Should handle errors gracefully
        assert isinstance(result, dict)
        # Should not crash

    def test_concurrent_operations(self, temp_workspace, mock_cache_files):
        """Test concurrent cleaning operations"""
        cleaner = MacCleaner()
        results = []
        
        def clean_operation(category):
            with patch('mac_cleaner.mac_cleaner.Path.home', return_value=Path(temp_workspace)):
                result = cleaner.clean_category(category, dry_run=True)
                results.append(result)
        
        # Run multiple operations concurrently
        threads = []
        categories = ["user_cache", "temp_files"]
        
        for category in categories:
            thread = threading.Thread(target=clean_operation, args=(category,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify all operations completed
        assert len(results) == len(categories), "All operations should complete"

    def test_configuration_integration(self, temp_workspace):
        """Test configuration integration in workflow"""
        from mac_cleaner.config import CleanerConfig
        
        # Test default configuration
        config = CleanerConfig.default()
        assert config is not None
        assert hasattr(config, 'protected_paths')
        
        # Test configuration validation
        assert len(config.protected_paths) > 0, "Should have protected paths"

    def test_logging_integration(self, temp_workspace, mock_cache_files):
        """Test logging integration in workflow"""
        import logging
        
        # Set up logging
        log_file = Path(temp_workspace) / "test.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        
        # Perform operation that should log
        cleaner = MacCleaner()
        with patch('mac_cleaner.mac_cleaner.Path.home', return_value=Path(temp_workspace)):
            logger.info("Starting test cleaning operation")
            result = cleaner.clean_category("user_cache", dry_run=True)
            logger.info("Completed test cleaning operation")
        
        # Verify log file was created and contains entries
        assert log_file.exists(), "Log file should be created"
        log_content = log_file.read_text()
        assert "Starting test cleaning operation" in log_content
        assert "Completed test cleaning operation" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
