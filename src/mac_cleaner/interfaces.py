#!/usr/bin/env python3
"""
Interface definitions for macOS Cleaner plugin architecture.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Protocol, Any, Optional, Union, Iterator
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import logging


class OperationMode(Enum):
    """Operation modes for cleaning operations"""
    ANALYZE = "analyze"
    DRY_RUN = "dry_run"
    CLEAN = "clean"


class SafetyLevel(Enum):
    """Safety levels for cleaning operations"""
    CRITICAL = "critical"  # Never clean
    IMPORTANT = "important"  # Require confirmation
    MODERATE = "moderate"  # Generally safe
    SAFE = "safe"  # Safe to clean
    VERY_SAFE = "very_safe"  # Always safe


@dataclass
class CleaningResult:
    """Result of a cleaning operation"""
    path: str
    operation: str
    success: bool
    size_freed: int = 0
    error_message: Optional[str] = None
    safety_level: SafetyLevel = SafetyLevel.SAFE
    timestamp: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of an analysis operation"""
    path: str
    size_bytes: int
    file_count: int
    safety_level: SafetyLevel
    last_modified: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None


class CleanerInterface(Protocol):
    """Interface for all cleaner implementations"""

    def analyze(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze what can be cleaned"""
        ...

    def clean(self, dry_run: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform cleaning operation"""
        ...

    def estimate_space(self, paths: Optional[List[str]] = None) -> int:
        """Estimate reclaimable space in bytes"""
        ...

    def get_safety_info(self, path: str) -> SafetyLevel:
        """Get safety level for a specific path"""
        ...

    def validate_operation(self, operation: OperationMode, paths: List[str]) -> bool:
        """Validate if operation can be performed"""
        ...


class StorageInterface(ABC):
    """Abstract storage operations"""

    @abstractmethod
    def get_size(self, path: str) -> int:
        """Get size of file or directory in bytes"""
        pass

    @abstractmethod
    def delete(self, path: str, safe: bool = True) -> bool:
        """Delete file or directory"""
        pass

    @abstractmethod
    def backup(self, path: str) -> str:
        """Create backup of file or directory"""
        pass

    @abstractmethod
    def restore(self, backup_path: str, target_path: str) -> bool:
        """Restore from backup"""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists"""
        pass

    @abstractmethod
    def is_readable(self, path: str) -> bool:
        """Check if path is readable"""
        pass

    @abstractmethod
    def is_writable(self, path: str) -> bool:
        """Check if path is writable"""
        pass

    @abstractmethod
    def get_metadata(self, path: str) -> Dict[str, Any]:
        """Get file/directory metadata"""
        pass


class ConfigInterface(Protocol):
    """Interface for configuration management"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        ...

    def load(self, source: Union[str, Dict[str, Any]]) -> None:
        """Load configuration from source"""
        ...

    def save(self, target: Optional[str] = None) -> None:
        """Save configuration to target"""
        ...

    def validate(self) -> bool:
        """Validate configuration"""
        ...


class SecurityInterface(Protocol):
    """Interface for security operations"""

    def validate_path(self, path: str, allowed_prefixes: List[str]) -> bool:
        """Validate path is within allowed prefixes"""
        ...

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input"""
        ...

    def check_privileges(self, path: str) -> bool:
        """Check if we have required privileges"""
        ...

    def is_protected_path(self, path: str) -> bool:
        """Check if path is protected"""
        ...


class CleanerPlugin(ABC):
    """Base class for cleaner plugins"""

    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable plugin name"""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Plugin category (cache, logs, temp, etc.)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description"""
        pass

    @property
    def version(self) -> str:
        """Plugin version"""
        return "1.0.0"

    @property
    def author(self) -> str:
        """Plugin author"""
        return "macOS Cleaner contributors"

    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled"""
        return True

    @property
    def priority(self) -> int:
        """Plugin priority (higher = runs first)"""
        return 50

    @abstractmethod
    def get_cleanable_paths(self) -> List[str]:
        """Return list of paths that can be cleaned"""
        pass

    @abstractmethod
    def is_safe_to_clean(self, path: str) -> bool:
        """Check if specific path is safe to clean"""
        pass

    def get_safety_level(self, path: str) -> SafetyLevel:
        """Get safety level for a specific path"""
        if not self.is_safe_to_clean(path):
            return SafetyLevel.CRITICAL
        return SafetyLevel.SAFE

    def can_handle_path(self, path: str) -> bool:
        """Check if plugin can handle the given path"""
        cleanable_paths = self.get_cleanable_paths()
        return any(path.startswith(p) or p.startswith(path) for p in cleanable_paths)

    def validate_paths(self, paths: List[str]) -> List[str]:
        """Validate and filter paths that can be cleaned"""
        valid_paths = []
        for path in paths:
            if self.can_handle_path(path) and self.is_safe_to_clean(path):
                valid_paths.append(path)
        return valid_paths

    def analyze_paths(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze cleanable paths and return detailed info"""
        if paths is None:
            paths = self.get_cleanable_paths()
        
        results = {
            "plugin_name": self.name,
            "category": self.category,
            "paths": [],
            "total_size": 0,
            "file_count": 0,
            "safe_to_clean": True,
            "analysis_time": None
        }

        from datetime import datetime
        results["analysis_time"] = datetime.now().isoformat()

        for path in paths:
            if not self.can_handle_path(path):
                continue
                
            path_obj = Path(path)
            if path_obj.exists():
                try:
                    size = self._get_directory_size(path_obj)
                    file_count = self._count_files(path_obj)
                    safety_level = self.get_safety_level(path)
                    metadata = self._get_path_metadata(path_obj)

                    path_result = {
                        "path": path,
                        "size": size,
                        "size_human": self._format_bytes(size),
                        "file_count": file_count,
                        "safe": safety_level != SafetyLevel.CRITICAL,
                        "safety_level": safety_level.value,
                        "metadata": metadata
                    }

                    results["paths"].append(path_result)
                    results["total_size"] += size
                    results["file_count"] += file_count

                    if safety_level == SafetyLevel.CRITICAL:
                        results["safe_to_clean"] = False

                except Exception as e:
                    self.logger.error(f"Error analyzing path {path}: {e}")
                    results["paths"].append({
                        "path": path,
                        "error": str(e),
                        "safe": False
                    })

        results["total_size_human"] = self._format_bytes(results["total_size"])
        return results

    def clean_paths(self, paths: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Clean specified paths (READ-ONLY MODE - Analysis Only)"""
        if paths is None:
            paths = self.get_cleanable_paths()
            
        results = {
            "plugin_name": self.name,
            "category": self.category,
            "mode": "read_only_analysis",
            "analyzed": [],
            "skipped": [],
            "errors": [],
            "total_analyzed": 0,
            "operation_time": None
        }

        from datetime import datetime
        results["operation_time"] = datetime.now().isoformat()

        for path in paths:
            if not self.can_handle_path(path):
                results["skipped"].append(
                    {"path": path, "reason": "Plugin cannot handle this path"}
                )
                continue

            if not self.is_safe_to_clean(path):
                results["skipped"].append(
                    {"path": path, "reason": "Not safe to analyze"}
                )
                continue

            try:
                path_obj = Path(path)
                if path_obj.exists():
                    size = self._get_directory_size(path_obj)
                    file_count = self._count_files(path_obj)

                    results["analyzed"].append(
                        {
                            "path": path,
                            "size": size,
                            "size_human": self._format_bytes(size),
                            "file_count": file_count,
                            "action": "analyzed_only",
                            "safety_level": self.get_safety_level(path).value
                        }
                    )

                    results["total_analyzed"] += size

            except Exception as e:
                self.logger.error(f"Error processing path {path}: {e}")
                results["errors"].append({"path": path, "error": str(e)})

        results["total_analyzed_human"] = self._format_bytes(results["total_analyzed"])
        return results

    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory"""
        total_size = 0
        try:
            if path.is_file():
                return path.stat().st_size

            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

        return total_size

    def _count_files(self, path: Path) -> int:
        """Count total files in directory"""
        count = 0
        try:
            if path.is_file():
                return 1

            for item in path.rglob("*"):
                if item.is_file():
                    count += 1
        except (OSError, PermissionError):
            pass

        return count

    def _get_path_metadata(self, path: Path) -> Dict[str, Any]:
        """Get metadata for a path"""
        try:
            stat = path.stat()
            return {
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "size": stat.st_size,
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "permissions": oct(stat.st_mode)[-3:],
            }
        except (OSError, PermissionError):
            return {}

    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"


class PluginManager:
    """Enhanced manager for loading and running plugins"""

    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config
        self.plugins: Dict[str, CleanerPlugin] = {}
        self.categories: Dict[str, List[CleanerPlugin]] = {}
        self.plugin_registry: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def register_plugin(self, plugin: CleanerPlugin) -> bool:
        """Register a plugin with validation"""
        try:
            # Validate plugin
            if not self._validate_plugin(plugin):
                self.logger.error(f"Plugin validation failed: {plugin.name}")
                return False

            self.plugins[plugin.name] = plugin

            if plugin.category not in self.categories:
                self.categories[plugin.category] = []
            self.categories[plugin.category].append(plugin)

            # Sort by priority
            self.categories[plugin.category].sort(key=lambda p: p.priority, reverse=True)

            # Update registry
            self.plugin_registry[plugin.name] = {
                "name": plugin.name,
                "category": plugin.category,
                "description": plugin.description,
                "version": plugin.version,
                "author": plugin.author,
                "enabled": plugin.enabled,
                "priority": plugin.priority,
                "registered_at": self._get_timestamp()
            }

            self.logger.info(f"Successfully registered plugin: {plugin.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering plugin {plugin.name}: {e}")
            return False

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin"""
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]
        del self.plugins[name]

        if plugin.category in self.categories:
            self.categories[plugin.category] = [
                p for p in self.categories[plugin.category] if p.name != name
            ]

        if name in self.plugin_registry:
            del self.plugin_registry[name]

        self.logger.info(f"Successfully unregistered plugin: {name}")
        return True

    def get_plugin(self, name: str) -> Optional[CleanerPlugin]:
        """Get plugin by name"""
        return self.plugins.get(name)

    def get_plugins_by_category(self, category: str) -> List[CleanerPlugin]:
        """Get all plugins in a category (sorted by priority)"""
        return self.categories.get(category, [])

    def get_enabled_plugins(self) -> List[CleanerPlugin]:
        """Get all enabled plugins"""
        return [p for p in self.plugins.values() if p.enabled]

    def get_all_plugins(self) -> List[CleanerPlugin]:
        """Get all registered plugins"""
        return list(self.plugins.values())

    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return list(self.categories.keys())

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin registry information"""
        return self.plugin_registry.get(name)

    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get all plugin registry information"""
        return self.plugin_registry.copy()

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name in self.plugins:
            # Note: This would need to be implemented in the plugin class
            self.logger.info(f"Plugin {name} enable requested")
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        if name in self.plugins:
            # Note: This would need to be implemented in the plugin class
            self.logger.info(f"Plugin {name} disable requested")
            return True
        return False

    def discover_plugins(self, plugin_paths: Optional[List[str]] = None) -> int:
        """Discover and load plugins from specified paths"""
        discovered_count = 0
        
        if plugin_paths is None:
            plugin_paths = [
                "src.mac_cleaner.plugins",  # Built-in plugins
                "mac_cleaner_plugins",      # External plugins
            ]

        for plugin_path in plugin_paths:
            try:
                discovered_count += self._load_plugins_from_path(plugin_path)
            except Exception as e:
                self.logger.error(f"Error loading plugins from {plugin_path}: {e}")

        self.logger.info(f"Discovered {discovered_count} plugins")
        return discovered_count

    def analyze_all(self, categories: Optional[List[str]] = None, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze all plugins or specific categories/paths"""
        results = {
            "categories": {},
            "total_size": 0,
            "total_files": 0,
            "plugins": {},
            "analysis_time": self._get_timestamp(),
            "plugins_analyzed": 0
        }

        plugins_to_analyze = self._get_plugins_for_operation(categories, paths)

        for plugin in plugins_to_analyze:
            try:
                plugin_results = plugin.analyze_paths(paths)
                results["plugins"][plugin.name] = plugin_results
                results["total_size"] += plugin_results["total_size"]
                results["total_files"] += plugin_results["file_count"]
                results["plugins_analyzed"] += 1

                # Update category results
                if plugin.category not in results["categories"]:
                    results["categories"][plugin.category] = {
                        "size": 0,
                        "files": 0,
                        "plugins": [],
                    }

                results["categories"][plugin.category]["size"] += plugin_results[
                    "total_size"
                ]
                results["categories"][plugin.category]["files"] += plugin_results[
                    "file_count"
                ]
                results["categories"][plugin.category]["plugins"].append(plugin.name)

            except Exception as e:
                self.logger.error(f"Error analyzing plugin {plugin.name}: {e}")
                results["plugins"][plugin.name] = {"error": str(e)}

        results["total_size_human"] = self._format_bytes(results["total_size"])
        return results

    def clean_all(
        self, 
        categories: Optional[List[str]] = None, 
        paths: Optional[List[str]] = None, 
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Clean all plugins or specific categories/paths"""
        results = {
            "categories": {},
            "total_freed": 0,
            "plugins": {},
            "operation_time": self._get_timestamp(),
            "plugins_processed": 0,
            "mode": "dry_run" if dry_run else "clean"
        }

        plugins_to_clean = self._get_plugins_for_operation(categories, paths)

        for plugin in plugins_to_clean:
            try:
                plugin_results = plugin.clean_paths(paths, dry_run=dry_run)
                results["plugins"][plugin.name] = plugin_results
                results["total_freed"] += plugin_results["total_analyzed"]
                results["plugins_processed"] += 1

                # Update category results
                if plugin.category not in results["categories"]:
                    results["categories"][plugin.category] = {
                        "freed": 0,
                        "plugins": [],
                    }

                results["categories"][plugin.category]["freed"] += plugin_results[
                    "total_analyzed"
                ]
                results["categories"][plugin.category]["plugins"].append(plugin.name)

            except Exception as e:
                self.logger.error(f"Error processing plugin {plugin.name}: {e}")
                results["plugins"][plugin.name] = {"error": str(e)}

        results["total_freed_human"] = self._format_bytes(results["total_freed"])
        return results

    def _get_plugins_for_operation(
        self, 
        categories: Optional[List[str]] = None, 
        paths: Optional[List[str]] = None
    ) -> List[CleanerPlugin]:
        """Get plugins that should be used for an operation"""
        plugins_to_use = []

        if paths:
            # Find plugins that can handle the specified paths
            for plugin in self.get_enabled_plugins():
                if any(plugin.can_handle_path(path) for path in paths):
                    plugins_to_use.append(plugin)
        elif categories:
            # Get plugins from specified categories
            for category in categories:
                plugins_to_use.extend(self.get_plugins_by_category(category))
        else:
            # Get all enabled plugins
            plugins_to_use = self.get_enabled_plugins()

        # Remove duplicates and sort by priority
        unique_plugins = list({p.name: p for p in plugins_to_use}.values())
        unique_plugins.sort(key=lambda p: p.priority, reverse=True)
        
        return unique_plugins

    def _validate_plugin(self, plugin: CleanerPlugin) -> bool:
        """Validate a plugin before registration"""
        try:
            # Check required properties
            required_props = ['name', 'category', 'description']
            for prop in required_props:
                if not getattr(plugin, prop, None):
                    self.logger.error(f"Plugin missing required property: {prop}")
                    return False

            # Check required methods
            required_methods = ['get_cleanable_paths', 'is_safe_to_clean']
            for method in required_methods:
                if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                    self.logger.error(f"Plugin missing required method: {method}")
                    return False

            # Test get_cleanable_paths returns list
            paths = plugin.get_cleanable_paths()
            if not isinstance(paths, list):
                self.logger.error("Plugin get_cleanable_paths must return a list")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Plugin validation error: {e}")
            return False

    def _load_plugins_from_path(self, plugin_path: str) -> int:
        """Load plugins from a specific path (placeholder for future implementation)"""
        # This would implement dynamic plugin loading
        # For now, return 0 as we're using static registration
        return 0

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
