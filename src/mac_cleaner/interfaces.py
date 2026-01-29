#!/usr/bin/env python3
"""
Interface definitions for macOS Cleaner plugin architecture.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Protocol, Any, Optional
from pathlib import Path


class CleanerInterface(Protocol):
    """Interface for all cleaner implementations"""
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze what can be cleaned"""
        ...
    
    def clean(self, dry_run: bool = True) -> Dict[str, Any]:
        """Perform cleaning operation"""
        ...
    
    def estimate_space(self) -> int:
        """Estimate reclaimable space in bytes"""
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


class CleanerPlugin(ABC):
    """Base class for cleaner plugins"""
    
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
    
    @abstractmethod
    def get_cleanable_paths(self) -> List[str]:
        """Return list of paths that can be cleaned"""
        pass
    
    @abstractmethod
    def is_safe_to_clean(self, path: str) -> bool:
        """Check if specific path is safe to clean"""
        pass
    
    def analyze_paths(self) -> Dict[str, Any]:
        """Analyze cleanable paths and return detailed info"""
        results = {
            "paths": [],
            "total_size": 0,
            "file_count": 0,
            "safe_to_clean": True
        }
        
        for path in self.get_cleanable_paths():
            path_obj = Path(path)
            if path_obj.exists():
                size = self._get_directory_size(path_obj)
                file_count = self._count_files(path_obj)
                is_safe = self.is_safe_to_clean(path)
                
                results["paths"].append({
                    "path": path,
                    "size": size,
                    "size_human": self._format_bytes(size),
                    "file_count": file_count,
                    "safe": is_safe
                })
                
                results["total_size"] += size
                results["file_count"] += file_count
                
                if not is_safe:
                    results["safe_to_clean"] = False
        
        results["total_size_human"] = self._format_bytes(results["total_size"])
        return results
    
    def clean_paths(self, dry_run: bool = True) -> Dict[str, Any]:
        """Analyze cleanable paths (READ-ONLY MODE - Analysis Only)"""
        results = {
            "analyzed": [],
            "skipped": [],
            "errors": [],
            "total_analyzed": 0,
            "mode": "read_only_analysis"
        }
        
        for path in self.get_cleanable_paths():
            if not self.is_safe_to_clean(path):
                results["skipped"].append({"path": path, "reason": "Not safe to analyze"})
                continue
            
            try:
                path_obj = Path(path)
                if path_obj.exists():
                    size = self._get_directory_size(path_obj)
                    file_count = self._count_files(path_obj)
                    
                    results["analyzed"].append({
                        "path": path,
                        "size": size,
                        "size_human": self._format_bytes(size),
                        "file_count": file_count,
                        "action": "analyzed_only"
                    })
                    
                    results["total_analyzed"] += size
                        
            except Exception as e:
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
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"


class PluginManager:
    """Manager for loading and running plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, CleanerPlugin] = {}
        self.categories: Dict[str, List[CleanerPlugin]] = {}
    
    def register_plugin(self, plugin: CleanerPlugin):
        """Register a plugin"""
        self.plugins[plugin.name] = plugin
        
        if plugin.category not in self.categories:
            self.categories[plugin.category] = []
        self.categories[plugin.category].append(plugin)
    
    def get_plugin(self, name: str) -> Optional[CleanerPlugin]:
        """Get plugin by name"""
        return self.plugins.get(name)
    
    def get_plugins_by_category(self, category: str) -> List[CleanerPlugin]:
        """Get all plugins in a category"""
        return self.categories.get(category, [])
    
    def get_all_plugins(self) -> List[CleanerPlugin]:
        """Get all registered plugins"""
        return list(self.plugins.values())
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return list(self.categories.keys())
    
    def analyze_all(self) -> Dict[str, Any]:
        """Analyze all plugins"""
        results = {
            "categories": {},
            "total_size": 0,
            "total_files": 0,
            "plugins": {}
        }
        
        for plugin_name, plugin in self.plugins.items():
            plugin_results = plugin.analyze_paths()
            results["plugins"][plugin_name] = plugin_results
            results["total_size"] += plugin_results["total_size"]
            results["total_files"] += plugin_results["file_count"]
            
            if plugin.category not in results["categories"]:
                results["categories"][plugin.category] = {
                    "size": 0,
                    "files": 0,
                    "plugins": []
                }
            
            results["categories"][plugin.category]["size"] += plugin_results["total_size"]
            results["categories"][plugin.category]["files"] += plugin_results["file_count"]
            results["categories"][plugin.category]["plugins"].append(plugin_name)
        
        results["total_size_human"] = self._format_bytes(results["total_size"])
        return results
    
    def clean_all(self, categories: List[str] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Clean all plugins or specific categories"""
        results = {
            "categories": {},
            "total_freed": 0,
            "plugins": {}
        }
        
        plugins_to_clean = []
        if categories:
            for category in categories:
                plugins_to_clean.extend(self.get_plugins_by_category(category))
        else:
            plugins_to_clean = self.get_all_plugins()
        
        for plugin in plugins_to_clean:
            plugin_results = plugin.clean_paths(dry_run=dry_run)
            results["plugins"][plugin.name] = plugin_results
            results["total_freed"] += plugin_results["total_freed"]
            
            if plugin.category not in results["categories"]:
                results["categories"][plugin.category] = {
                    "freed": 0,
                    "plugins": []
                }
            
            results["categories"][plugin.category]["freed"] += plugin_results["total_freed"]
            results["categories"][plugin.category]["plugins"].append(plugin.name)
        
        results["total_freed_human"] = self._format_bytes(results["total_freed"])
        return results
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
