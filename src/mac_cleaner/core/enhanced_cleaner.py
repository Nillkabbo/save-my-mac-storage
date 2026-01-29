#!/usr/bin/env python3
"""
Enhanced cleaner using the new plugin architecture.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..interfaces import (
    CleanerInterface, 
    PluginManager, 
    ConfigInterface, 
    OperationMode,
    SafetyLevel
)
from ..plugins import register_builtin_plugins
from .config_manager import get_config


class EnhancedCleaner(CleanerInterface):
    """Enhanced cleaner implementation using plugin architecture."""
    
    def __init__(self, config: Optional[ConfigInterface] = None):
        self.config = config or get_config()
        self.plugin_manager = PluginManager(self.config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Register built-in plugins
        register_builtin_plugins(self.plugin_manager)
        
        # Discover additional plugins if enabled
        if self.config.get('plugins.auto_discover', True):
            self.plugin_manager.discover_plugins()
    
    def analyze(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze what can be cleaned using all plugins."""
        self.logger.info("Starting analysis with enhanced cleaner")
        
        try:
            results = self.plugin_manager.analyze_all(paths=paths)
            
            # Add summary information
            results['summary'] = {
                'total_categories': len(results['categories']),
                'total_plugins': results['plugins_analyzed'],
                'safety_breakdown': self._get_safety_breakdown(results),
                'recommendations': self._get_recommendations(results)
            }
            
            self.logger.info(f"Analysis complete: {results['total_size_human']} across {results['total_files']} files")
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'error': str(e),
                'total_size': 0,
                'total_files': 0,
                'categories': {},
                'plugins': {}
            }
    
    def clean(self, dry_run: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform cleaning operation using all plugins."""
        mode = "DRY RUN" if dry_run else "CLEAN"
        self.logger.info(f"Starting {mode} operation with enhanced cleaner")
        
        try:
            # Validate operation first
            if not self.validate_operation(OperationMode.DRY_RUN if dry_run else OperationMode.CLEAN, paths or []):
                raise ValueError("Operation validation failed")
            
            results = self.plugin_manager.clean_all(paths=paths, dry_run=dry_run)
            
            # Add summary information
            results['summary'] = {
                'total_categories': len(results['categories']),
                'total_plugins': results['plugins_processed'],
                'mode': mode,
                'safety_breakdown': self._get_safety_breakdown(results),
                'warnings': self._get_warnings(results)
            }
            
            self.logger.info(f"{mode} complete: {results['total_freed_human']} processed")
            return results
            
        except Exception as e:
            self.logger.error(f"{mode} operation failed: {e}")
            return {
                'error': str(e),
                'total_freed': 0,
                'categories': {},
                'plugins': {},
                'mode': mode
            }
    
    def estimate_space(self, paths: Optional[List[str]] = None) -> int:
        """Estimate reclaimable space in bytes."""
        analysis = self.analyze(paths)
        return analysis.get('total_size', 0)
    
    def get_safety_info(self, path: str) -> SafetyLevel:
        """Get safety level for a specific path."""
        # Find plugins that can handle this path
        for plugin in self.plugin_manager.get_enabled_plugins():
            if plugin.can_handle_path(path):
                return plugin.get_safety_level(path)
        
        # Default to safe if no plugin handles it
        return SafetyLevel.SAFE
    
    def validate_operation(self, operation: OperationMode, paths: List[str]) -> bool:
        """Validate if operation can be performed."""
        try:
            # Check if we have required privileges
            for path in paths:
                if not self._check_path_privileges(path):
                    self.logger.warning(f"Insufficient privileges for path: {path}")
                    return False
            
            # Check if paths are protected
            protected_paths = self.config.get('security.protected_paths', [])
            for path in paths:
                if any(path.startswith(protected) for protected in protected_paths):
                    self.logger.warning(f"Path is protected: {path}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Operation validation failed: {e}")
            return False
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about all registered plugins."""
        return self.plugin_manager.get_all_plugin_info()
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return self.plugin_manager.get_categories()
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a specific plugin."""
        return self.plugin_manager.enable_plugin(plugin_name)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a specific plugin."""
        return self.plugin_manager.disable_plugin(plugin_name)
    
    def analyze_category(self, category: str) -> Dict[str, Any]:
        """Analyze a specific category."""
        return self.plugin_manager.analyze_all(categories=[category])
    
    def clean_category(self, category: str, dry_run: bool = True) -> Dict[str, Any]:
        """Clean a specific category."""
        return self.plugin_manager.clean_all(categories=[category], dry_run=dry_run)
    
    def _get_safety_breakdown(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Get breakdown of files by safety level."""
        breakdown = {level.value: 0 for level in SafetyLevel}
        
        for plugin_name, plugin_results in results.get('plugins', {}).items():
            if 'paths' in plugin_results:
                for path_info in plugin_results['paths']:
                    safety_level = path_info.get('safety_level', 'safe')
                    if safety_level in breakdown:
                        breakdown[safety_level] += 1
        
        return breakdown
    
    def _get_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Get cleaning recommendations based on analysis."""
        recommendations = []
        
        if results.get('total_size', 0) > 1024 * 1024 * 1024:  # > 1GB
            recommendations.append("Large amount of space can be freed. Consider running clean operation.")
        
        # Check for specific categories
        categories = results.get('categories', {})
        if 'cache' in categories and categories['cache'].get('size', 0) > 500 * 1024 * 1024:  # > 500MB
            recommendations.append("Cache files are consuming significant space and are safe to clean.")
        
        if 'temp' in categories and categories['temp'].get('size', 0) > 100 * 1024 * 1024:  # > 100MB
            recommendations.append("Temporary files can be safely cleaned.")
        
        return recommendations
    
    def _get_warnings(self, results: Dict[str, Any]) -> List[str]:
        """Get warnings for the cleaning operation."""
        warnings = []
        
        # Check for critical safety levels
        safety_breakdown = self._get_safety_breakdown(results)
        if safety_breakdown.get('critical', 0) > 0:
            warnings.append(f"{safety_breakdown['critical']} critical files will be skipped.")
        
        if safety_breakdown.get('important', 0) > 0:
            warnings.append(f"{safety_breakdown['important']} important files require careful review.")
        
        return warnings
    
    def _check_path_privileges(self, path: str) -> bool:
        """Check if we have sufficient privileges for a path."""
        try:
            path_obj = Path(path)
            if path_obj.exists():
                return os.access(path_obj, os.R_OK)
            return True  # Can't check non-existent paths
        except Exception:
            return False
