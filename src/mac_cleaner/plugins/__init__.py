#!/usr/bin/env python3
"""
Plugins package for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from .plugins import (
    BrowserCacheCleaner,
    SystemCacheCleaner,
    LogFileCleaner,
    TempFileCleaner,
    XcodeCleaner,
    DockerCleaner,
    DownloadsCleaner,
    register_builtin_plugins,
    get_all_plugins,
    get_plugins_by_categories,
    get_all_cleanable_paths
)

__all__ = [
    'BrowserCacheCleaner',
    'SystemCacheCleaner',
    'LogFileCleaner',
    'TempFileCleaner',
    'XcodeCleaner',
    'DockerCleaner',
    'DownloadsCleaner',
    'register_builtin_plugins',
    'get_all_plugins',
    'get_plugins_by_categories',
    'get_all_cleanable_paths',
]
