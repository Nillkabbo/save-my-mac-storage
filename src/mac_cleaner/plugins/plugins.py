#!/usr/bin/env python3
"""
Built-in plugins for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
from pathlib import Path
from typing import List, Optional
from ..interfaces import CleanerPlugin, SafetyLevel, ConfigInterface


class BrowserCacheCleaner(CleanerPlugin):
    """Plugin for cleaning browser caches"""

    @property
    def name(self) -> str:
        return "Browser Cache Cleaner"

    @property
    def category(self) -> str:
        return "cache"

    @property
    def description(self) -> str:
        return "Cleans cache files from web browsers"

    @property
    def priority(self) -> int:
        return 80  # High priority - safe and effective

    def get_cleanable_paths(self) -> List[str]:
        """Return browser cache paths"""
        home = Path.home()
        paths = [
            str(home / "Library" / "Caches" / "Google" / "Chrome"),
            str(home / "Library" / "Caches" / "Firefox"),
            str(home / "Library" / "Caches" / "com.apple.Safari"),
            str(home / "Library" / "Caches" / "com.microsoft.edgemac"),
            str(home / "Library" / "Caches" / "com.operasoftware.Opera"),
        ]
        return [p for p in paths if Path(p).exists()]

    def is_safe_to_clean(self, path: str) -> bool:
        """Browser caches are safe to clean"""
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Browser caches are very safe to clean"""
        return SafetyLevel.VERY_SAFE


class SystemCacheCleaner(CleanerPlugin):
    """Plugin for cleaning system caches"""

    @property
    def name(self) -> str:
        return "System Cache Cleaner"

    @property
    def category(self) -> str:
        return "cache"

    @property
    def description(self) -> str:
        return "Cleans system cache files"

    @property
    def priority(self) -> int:
        return 30  # Lower priority - more cautious

    def get_cleanable_paths(self) -> List[str]:
        """Return system cache paths"""
        paths = [
            "/Library/Caches",
            "/System/Library/Caches",
            "~/Library/Caches",
        ]
        return [
            str(Path(p).expanduser()) for p in paths if Path(p).expanduser().exists()
        ]

    def is_safe_to_clean(self, path: str) -> bool:
        """Check if system cache path is safe"""
        # Be more careful with system paths
        if path.startswith("/System/Library/Caches"):
            return False  # Don't clean system caches by default
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for system cache paths"""
        if path.startswith("/System/Library/Caches"):
            return SafetyLevel.CRITICAL
        elif path.startswith("/Library/Caches"):
            return SafetyLevel.IMPORTANT
        else:
            return SafetyLevel.SAFE


class LogFileCleaner(CleanerPlugin):
    """Plugin for cleaning log files"""

    @property
    def name(self) -> str:
        return "Log File Cleaner"

    @property
    def category(self) -> str:
        return "logs"

    @property
    def description(self) -> str:
        return "Cleans old log files"

    @property
    def priority(self) -> int:
        return 40  # Moderate priority

    def get_cleanable_paths(self) -> List[str]:
        """Return log file paths"""
        paths = [
            "~/Library/Logs",
            "/var/log",
            "/Library/Logs",
            "~/Library/Logs/DiagnosticReports",
        ]
        return [
            str(Path(p).expanduser()) for p in paths if Path(p).expanduser().exists()
        ]

    def is_safe_to_clean(self, path: str) -> bool:
        """Check if log path is safe to clean"""
        # Don't clean system logs by default
        if path.startswith("/var/log") or path.startswith("/Library/Logs"):
            return False
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for log paths"""
        if path.startswith("/var/log"):
            return SafetyLevel.CRITICAL
        elif path.startswith("/Library/Logs"):
            return SafetyLevel.IMPORTANT
        else:
            return SafetyLevel.MODERATE


class TempFileCleaner(CleanerPlugin):
    """Plugin for cleaning temporary files"""

    @property
    def name(self) -> str:
        return "Temporary File Cleaner"

    @property
    def category(self) -> str:
        return "temp"

    @property
    def description(self) -> str:
        return "Cleans temporary files"

    @property
    def priority(self) -> int:
        return 70  # High priority - generally safe

    def get_cleanable_paths(self) -> List[str]:
        """Return temp file paths"""
        paths = [
            "/tmp",
            "/var/tmp",
            "~/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments",
            "~/.Trash",
        ]
        return [
            str(Path(p).expanduser()) for p in paths if Path(p).expanduser().exists()
        ]

    def is_safe_to_clean(self, path: str) -> bool:
        """Check if temp path is safe to clean"""
        # Don't clean system temp directories by default
        if path.startswith("/tmp") or path.startswith("/var/tmp"):
            return False
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for temp paths"""
        if path.startswith("/tmp") or path.startswith("/var/tmp"):
            return SafetyLevel.IMPORTANT
        elif path.endswith(".Trash"):
            return SafetyLevel.SAFE
        else:
            return SafetyLevel.MODERATE


class XcodeCleaner(CleanerPlugin):
    """Plugin for cleaning Xcode derived data"""

    @property
    def name(self) -> str:
        return "Xcode Cleaner"

    @property
    def category(self) -> str:
        return "development"

    @property
    def description(self) -> str:
        return "Cleans Xcode derived data and archives"

    @property
    def priority(self) -> int:
        return 60  # Moderate-high priority

    def get_cleanable_paths(self) -> List[str]:
        """Return Xcode paths"""
        home = Path.home()
        paths = [
            str(home / "Library" / "Developer" / "Xcode" / "DerivedData"),
            str(home / "Library" / "Developer" / "Xcode" / "Archives"),
            str(home / "Library" / "MobileDevice" / "Provisioning Profiles"),
        ]
        return [p for p in paths if Path(p).exists()]

    def is_safe_to_clean(self, path: str) -> bool:
        """Xcode derived data is safe to clean"""
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for Xcode paths"""
        if "DerivedData" in path:
            return SafetyLevel.VERY_SAFE
        elif "Archives" in path:
            return SafetyLevel.IMPORTANT  # Might contain important builds
        else:
            return SafetyLevel.SAFE


class DockerCleaner(CleanerPlugin):
    """Plugin for cleaning Docker resources"""

    @property
    def name(self) -> str:
        return "Docker Cleaner"

    @property
    def category(self) -> str:
        return "development"

    @property
    def description(self) -> str:
        return "Cleans Docker unused images, containers, and volumes"

    @property
    def priority(self) -> int:
        return 50  # Moderate priority

    def get_cleanable_paths(self) -> List[str]:
        """Return Docker paths"""
        paths = [
            "~/Library/Containers/com.docker.docker",
            "/var/lib/docker",
            "~/.docker",
        ]
        return [
            str(Path(p).expanduser()) for p in paths if Path(p).expanduser().exists()
        ]

    def is_safe_to_clean(self, path: str) -> bool:
        """Docker resources are generally safe to clean"""
        return True

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for Docker paths"""
        return SafetyLevel.SAFE


class DownloadsCleaner(CleanerPlugin):
    """Plugin for cleaning old downloads"""

    @property
    def name(self) -> str:
        return "Downloads Cleaner"

    @property
    def category(self) -> str:
        return "user"

    @property
    def description(self) -> str:
        return "Cleans old files from Downloads folder"

    @property
    def priority(self) -> int:
        return 20  # Low priority - requires manual review

    def get_cleanable_paths(self) -> List[str]:
        """Return Downloads path"""
        downloads = Path.home() / "Downloads"
        return [str(downloads)] if downloads.exists() else []

    def is_safe_to_clean(self, path: str) -> bool:
        """Downloads folder needs manual review"""
        return False  # Require manual confirmation

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Downloads folder requires manual review"""
        return SafetyLevel.IMPORTANT


def register_builtin_plugins(plugin_manager) -> None:
    """Register all built-in plugins with the plugin manager"""
    plugins = [
        BrowserCacheCleaner(),
        SystemCacheCleaner(),
        LogFileCleaner(),
        TempFileCleaner(),
        XcodeCleaner(),
        DockerCleaner(),
        DownloadsCleaner(),
    ]

    for plugin in plugins:
        success = plugin_manager.register_plugin(plugin)
        if not success:
            print(f"Warning: Failed to register plugin {plugin.name}")

    return plugin_manager


def get_all_plugins() -> List[CleanerPlugin]:
    """Get all built-in plugins as a list"""
    return [
        BrowserCacheCleaner(),
        SystemCacheCleaner(),
        LogFileCleaner(),
        TempFileCleaner(),
        XcodeCleaner(),
        DockerCleaner(),
        DownloadsCleaner(),
    ]


def get_plugins_by_categories(categories: List[str]) -> List[CleanerPlugin]:
    """Get plugins by specified categories"""
    all_plugins = get_all_plugins()
    return [p for p in all_plugins if p.category in categories]


def get_all_cleanable_paths() -> List[str]:
    """Get all cleanable paths from all plugins"""
    all_paths = []
    for plugin in get_all_plugins():
        all_paths.extend(plugin.get_cleanable_paths())
    return list(set(all_paths))  # Remove duplicates
