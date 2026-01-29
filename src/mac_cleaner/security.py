#!/usr/bin/env python3
"""
Security helpers for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import shlex
import hashlib
from pathlib import Path
from typing import Iterable, Tuple, List, Optional


class SecurityValidator:
    """Advanced security validation for file operations"""

    # Protected system paths that should never be accessed
    PROTECTED_SYSTEM_PATHS = {
        "/System",
        "/usr",
        "/bin",
        "/sbin",
        "/etc",
        "/var/root",
        "/Applications",
        "/Library/Keychains",
        "/Library/Preferences",
        "/private/var/db",
        "/private/var/root",
        "/.Spotlight-V100",
        "/.fseventsd",
        "/dev",
        "/cores",
        "/automount",
        "/Network",
        "/Volumes",
        "/net",
        "/home",
        "/opt",
        "/private",
        "/tmp",
        "/var",
        "/usr/local",
        "/System/Library",
        "/Library/Frameworks",
        "/System/Library/Frameworks",
        "/Library/Application Support",
        "/System/Library/Application Support",
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        "/System/Library/LaunchAgents",
        "/System/Library/LaunchDaemons",
        "/Library/Extensions",
        "/System/Library/Extensions",
        "/usr/libexec",
        "/var/db",
        "/var/log",
        "/var/spool",
        "/var/tmp",
        "/etc/cron.d",
        "/etc/cron.daily",
        "/etc/cron.hourly",
        "/etc/cron.monthly",
        "/etc/cron.weekly",
    }

    # Protected user paths that require explicit confirmation
    PROTECTED_USER_PATHS = {
        "~/Documents",
        "~/Desktop",
        "~/Downloads",
        "~/Library/Keychains",
        "~/Library/Preferences",
        "~/.ssh",
        "~/.gnupg",
        "~/.config",
        "~/Library/Application Support",
        "~/Library/Caches/com.apple.finder",
        "~/Library/Caches/com.apple.systempreferences",
        "~/Library/Containers",
        "~/Library/Group Containers",
        "~/Library/Passes",
        "~/Library/PhoneIntents",
        "~/Library/PersonalizationPortrait",
        "~/Library/Preferences",
        "~/Library/Safari",
        "~/Library/SpellChecker",
        "~/Library/Templates",
        "~/Library/Voice",
        "~/.aws",
        "~/.docker",
        "~/.kube",
        "~/.npm",
        "~/.pip",
        "~/.cache",
        "~/.local",
        "~/.config",
        "~/Pictures",
        "~/Movies",
        "~/Music",
        "~/Public",
        "~/Parallels",
        "~/VirtualBox VMs",
        "~/VMware",
    }

    @staticmethod
    def validate_path(path: str, allowed_prefixes: List[str]) -> Tuple[bool, str]:
        """
        Validate a path against allowed prefixes and protected paths.

        Args:
            path: The path to validate
            allowed_prefixes: List of allowed path prefixes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path or not isinstance(path, str):
            return False, "Invalid path: path must be a non-empty string"

        try:
            # Expand user home and resolve to absolute path
            resolved_path = Path(path).expanduser().resolve()

            # Check against protected system paths
            for protected in SecurityValidator.PROTECTED_SYSTEM_PATHS:
                protected_path = Path(protected).expanduser().resolve()
                if resolved_path.is_relative_to(protected_path):
                    return (
                        False,
                        f"Access denied: {path} is in protected system path {protected}",
                    )

            # Check against protected user paths
            for protected in SecurityValidator.PROTECTED_USER_PATHS:
                protected_path = Path(protected).expanduser().resolve()
                if resolved_path.is_relative_to(protected_path):
                    return (
                        False,
                        f"Access denied: {path} is in protected user path {protected}",
                    )

            # Check if path is within allowed prefixes
            for prefix in allowed_prefixes:
                prefix_path = Path(prefix).expanduser().resolve()
                if resolved_path.is_relative_to(prefix_path):
                    return True, ""

            return False, f"Access denied: {path} is not within allowed prefixes"

        except (OSError, ValueError, RuntimeError) as e:
            return False, f"Invalid path: {str(e)}"

    @staticmethod
    def sanitize_shell_input(input_str: str) -> str:
        """
        Sanitize input for safe shell usage.

        Args:
            input_str: Input string to sanitize

        Returns:
            Sanitized string safe for shell usage
        """
        if not input_str or not isinstance(input_str, str):
            return ""

        # Remove dangerous characters and patterns
        dangerous_patterns = [
            ";",
            "&",
            "|",
            "`",
            "$",
            "(",
            ")",
            "<",
            ">",
            '"',
            "'",
            "${",
            "`",
            "$(",
            "&&",
            "||",
            ">>",
            "<<",
        ]

        sanitized = input_str
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, "")

        # Use shlex.quote for additional safety
        return shlex.quote(sanitized.strip())

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate filename for safe operations.

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename or not isinstance(filename, str):
            return False, "Invalid filename: must be a non-empty string"

        # Check for dangerous patterns
        dangerous_patterns = [
            "..",
            "/",
            "\\",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|",
            "\0",
            "\n",
            "\r",
            "\t",
        ]

        for pattern in dangerous_patterns:
            if pattern in filename:
                return (
                    False,
                    f"Invalid filename: contains dangerous character '{pattern}'",
                )

        # Check length
        if len(filename) > 255:
            return False, "Invalid filename: too long (max 255 characters)"

        return True, ""

    @staticmethod
    def calculate_secure_checksum(file_path: str) -> str:
        """
        Calculate SHA-256 checksum for file integrity verification.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 checksum as hex string
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (OSError, IOError):
            return ""

    @staticmethod
    def is_safe_file_size(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
        """
        Check if file size is within safe limits.

        Args:
            file_path: Path to the file
            max_size_mb: Maximum allowed size in MB

        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024

            if file_size > max_size_bytes:
                return (
                    False,
                    f"File too large: {file_size} bytes (max: {max_size_bytes} bytes)",
                )

            return True, ""
        except (OSError, IOError):
            return False, f"Cannot access file: {file_path}"


def sanitize_shell_input(value: str) -> str:
    """Sanitize a string for safe shell usage."""
    return SecurityValidator.sanitize_shell_input(value or "")


def _resolve_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def is_path_within(path: str, allowed_roots: Iterable[str]) -> bool:
    """Check whether path resolves within one of allowed roots."""
    resolved_path = _resolve_path(path)
    for root in allowed_roots:
        resolved_root = _resolve_path(root)
        try:
            common = os.path.commonpath([resolved_path, resolved_root])
        except ValueError:
            continue
        if common == resolved_root:
            return True
    return False


def validate_finder_path(
    path: str, allowed_roots: Iterable[str]
) -> Tuple[bool, str, str]:
    """Validate path for Finder access and return normalized path."""
    if not path:
        return False, "No path provided", ""

    try:
        resolved_path = _resolve_path(path)
    except (OSError, RuntimeError, ValueError):
        return False, "Invalid path", ""

    if not os.path.exists(resolved_path):
        return False, "Path does not exist", ""

    if not is_path_within(resolved_path, allowed_roots):
        return False, "Path is not allowed", ""

    return True, "", resolved_path


__all__ = [
    "SecurityValidator",
    "sanitize_shell_input",
    "is_path_within",
    "validate_finder_path",
]
