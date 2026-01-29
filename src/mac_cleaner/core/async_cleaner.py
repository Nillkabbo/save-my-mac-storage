#!/usr/bin/env python3
"""
Async operations for concurrent file analysis and cleaning.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple
from dataclasses import dataclass

from ..interfaces import (
    CleanerInterface, 
    PluginManager, 
    ConfigInterface, 
    OperationMode,
    SafetyLevel,
    AnalysisResult,
    CleaningResult
)


@dataclass
class AsyncAnalysisResult:
    """Result of async analysis operation"""
    path: str
    size_bytes: int
    file_count: int
    safety_level: SafetyLevel
    duration_ms: float
    error: Optional[str] = None


@dataclass
class AsyncCleaningResult:
    """Result of async cleaning operation"""
    path: str
    success: bool
    size_freed: int
    duration_ms: float
    error_message: Optional[str] = None
    safety_level: SafetyLevel = SafetyLevel.SAFE


class AsyncCleaner:
    """Async implementation of cleaner operations for better performance"""
    
    def __init__(self, config: Optional[ConfigInterface] = None, max_workers: int = 4):
        self.config = config
        self.max_workers = max_workers
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def analyze_async(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Async analysis of multiple paths concurrently"""
        start_time = time.time()
        
        if paths is None:
            # Get paths from plugin manager
            from ..plugins import get_all_cleanable_paths
            paths = get_all_cleanable_paths()
        
        self.logger.info(f"Starting async analysis of {len(paths)} paths")
        
        # Create tasks for concurrent analysis
        tasks = [self._analyze_path_async(path) for path in paths]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_results = []
        total_size = 0
        total_files = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "path": paths[i],
                    "error": str(result)
                })
            elif isinstance(result, AsyncAnalysisResult):
                if result.error:
                    failed_results.append({
                        "path": result.path,
                        "error": result.error
                    })
                else:
                    successful_results.append(result)
                    total_size += result.size_bytes
                    total_files += result.file_count
        
        duration = time.time() - start_time
        
        return {
            "total_size": total_size,
            "total_size_human": self._format_bytes(total_size),
            "total_files": total_files,
            "successful_paths": len(successful_results),
            "failed_paths": len(failed_results),
            "duration_seconds": duration,
            "paths_per_second": len(paths) / duration if duration > 0 else 0,
            "results": {
                "successful": [self._result_to_dict(r) for r in successful_results],
                "failed": failed_results
            }
        }
    
    async def clean_async(self, paths: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Async cleaning of multiple paths concurrently"""
        start_time = time.time()
        
        if paths is None:
            from ..plugins import get_all_cleanable_paths
            paths = get_all_cleanable_paths()
        
        mode = "DRY RUN" if dry_run else "CLEAN"
        self.logger.info(f"Starting async {mode} of {len(paths)} paths")
        
        # Create tasks for concurrent cleaning
        tasks = [self._clean_path_async(path, dry_run) for path in paths]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_results = []
        total_freed = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "path": paths[i],
                    "error": str(result)
                })
            elif isinstance(result, AsyncCleaningResult):
                if result.success:
                    successful_results.append(result)
                    total_freed += result.size_freed
                else:
                    failed_results.append({
                        "path": result.path,
                        "error": result.error_message
                    })
        
        duration = time.time() - start_time
        
        return {
            "total_freed": total_freed,
            "total_freed_human": self._format_bytes(total_freed),
            "successful_paths": len(successful_results),
            "failed_paths": len(failed_results),
            "duration_seconds": duration,
            "paths_per_second": len(paths) / duration if duration > 0 else 0,
            "mode": mode,
            "results": {
                "successful": [self._clean_result_to_dict(r) for r in successful_results],
                "failed": failed_results
            }
        }
    
    async def analyze_with_progress(self, paths: Optional[List[str]] = None) -> AsyncIterator[Dict[str, Any]]:
        """Async analysis with progress updates"""
        if paths is None:
            from ..plugins import get_all_cleanable_paths
            paths = get_all_cleanable_paths()
        
        total_paths = len(paths)
        processed = 0
        total_size = 0
        total_files = 0
        
        yield {
            "type": "start",
            "total_paths": total_paths,
            "progress": 0.0
        }
        
        for path in paths:
            try:
                result = await self._analyze_path_async(path)
                if not result.error:
                    total_size += result.size_bytes
                    total_files += result.file_count
                
                processed += 1
                progress = processed / total_paths
                
                yield {
                    "type": "progress",
                    "path": path,
                    "result": self._result_to_dict(result),
                    "progress": progress,
                    "processed": processed,
                    "total_paths": total_paths,
                    "current_totals": {
                        "size": total_size,
                        "files": total_files,
                        "size_human": self._format_bytes(total_size)
                    }
                }
                
            except Exception as e:
                self.logger.error(f"Error analyzing {path}: {e}")
                processed += 1
                progress = processed / total_paths
                
                yield {
                    "type": "error",
                    "path": path,
                    "error": str(e),
                    "progress": progress,
                    "processed": processed,
                    "total_paths": total_paths
                }
        
        yield {
            "type": "complete",
            "total_size": total_size,
            "total_size_human": self._format_bytes(total_size),
            "total_files": total_files,
            "processed": processed,
            "total_paths": total_paths,
            "progress": 1.0
        }
    
    async def _analyze_path_async(self, path: str) -> AsyncAnalysisResult:
        """Analyze a single path asynchronously"""
        loop = asyncio.get_event_loop()
        start_time = time.time()
        
        try:
            # Run the blocking I/O operations in thread pool
            size, file_count, safety_level = await loop.run_in_executor(
                self.executor, 
                self._analyze_path_sync, 
                path
            )
            
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return AsyncAnalysisResult(
                path=path,
                size_bytes=size,
                file_count=file_count,
                safety_level=safety_level,
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return AsyncAnalysisResult(
                path=path,
                size_bytes=0,
                file_count=0,
                safety_level=SafetyLevel.CRITICAL,
                duration_ms=duration,
                error=str(e)
            )
    
    async def _clean_path_async(self, path: str, dry_run: bool) -> AsyncCleaningResult:
        """Clean a single path asynchronously"""
        loop = asyncio.get_event_loop()
        start_time = time.time()
        
        try:
            # Run the blocking operations in thread pool
            success, size_freed, error = await loop.run_in_executor(
                self.executor,
                self._clean_path_sync,
                path,
                dry_run
            )
            
            duration = (time.time() - start_time) * 1000
            
            return AsyncCleaningResult(
                path=path,
                success=success,
                size_freed=size_freed,
                duration_ms=duration,
                error_message=error
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return AsyncCleaningResult(
                path=path,
                success=False,
                size_freed=0,
                duration_ms=duration,
                error_message=str(e)
            )
    
    def _analyze_path_sync(self, path: str) -> Tuple[int, int, SafetyLevel]:
        """Synchronous path analysis for use in thread pool"""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return 0, 0, SafetyLevel.SAFE
        
        # Calculate size and file count
        total_size = 0
        file_count = 0
        
        try:
            if path_obj.is_file():
                total_size = path_obj.stat().st_size
                file_count = 1
            else:
                for item in path_obj.rglob("*"):
                    if item.is_file():
                        try:
                            total_size += item.stat().st_size
                            file_count += 1
                        except (OSError, PermissionError):
                            continue
        except (OSError, PermissionError):
            pass
        
        # Determine safety level
        safety_level = self._determine_safety_level(path)
        
        return total_size, file_count, safety_level
    
    def _clean_path_sync(self, path: str, dry_run: bool) -> Tuple[bool, int, Optional[str]]:
        """Synchronous path cleaning for use in thread pool"""
        if dry_run:
            # In dry run mode, just simulate the operation
            path_obj = Path(path)
            if path_obj.exists():
                size = self._get_directory_size_sync(path_obj)
                return True, size, None
            else:
                return False, 0, "Path does not exist"
        
        # Actual cleaning would go here
        # For now, we'll keep the read-only behavior
        return False, 0, "Actual cleaning not implemented in Phase 4"
    
    def _determine_safety_level(self, path: str) -> SafetyLevel:
        """Determine safety level for a path"""
        # Check against protected paths
        protected_patterns = [
            "/System",
            "/usr/bin",
            "/usr/sbin",
            "/bin",
            "/sbin",
            "/etc",
            "/var/root",
            "/Library/Keychains",
            "~/.ssh",
            "~/.gnupg"
        ]
        
        expanded_path = os.path.expanduser(path)
        for pattern in protected_patterns:
            expanded_pattern = os.path.expanduser(pattern)
            if expanded_path.startswith(expanded_pattern):
                return SafetyLevel.CRITICAL
        
        # Check for user data directories
        user_patterns = [
            "~/Documents",
            "~/Desktop",
            "~/Downloads",
            "~/Pictures",
            "~/Movies",
            "~/Music"
        ]
        
        for pattern in user_patterns:
            expanded_pattern = os.path.expanduser(pattern)
            if expanded_path.startswith(expanded_pattern):
                return SafetyLevel.IMPORTANT
        
        # Check for cache and temp directories
        safe_patterns = [
            "~/Library/Caches",
            "/tmp",
            "/var/tmp",
            "~/.cache"
        ]
        
        for pattern in safe_patterns:
            expanded_pattern = os.path.expanduser(pattern)
            if expanded_path.startswith(expanded_pattern):
                return SafetyLevel.VERY_SAFE
        
        return SafetyLevel.SAFE
    
    def _get_directory_size_sync(self, path: Path) -> int:
        """Synchronous directory size calculation"""
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
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def _result_to_dict(self, result: AsyncAnalysisResult) -> Dict[str, Any]:
        """Convert AsyncAnalysisResult to dictionary"""
        return {
            "path": result.path,
            "size_bytes": result.size_bytes,
            "size_human": self._format_bytes(result.size_bytes),
            "file_count": result.file_count,
            "safety_level": result.safety_level.value,
            "duration_ms": result.duration_ms,
            "error": result.error
        }
    
    def _clean_result_to_dict(self, result: AsyncCleaningResult) -> Dict[str, Any]:
        """Convert AsyncCleaningResult to dictionary"""
        return {
            "path": result.path,
            "success": result.success,
            "size_freed": result.size_freed,
            "size_freed_human": self._format_bytes(result.size_freed),
            "duration_ms": result.duration_ms,
            "safety_level": result.safety_level.value,
            "error_message": result.error_message
        }
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


class AsyncPluginManager:
    """Async wrapper for plugin manager operations"""
    
    def __init__(self, plugin_manager: PluginManager, max_workers: int = 4):
        self.plugin_manager = plugin_manager
        self.async_cleaner = AsyncCleaner(max_workers=max_workers)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def analyze_all_async(self, categories: Optional[List[str]] = None, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Async version of analyze_all"""
        start_time = time.time()
        
        # Get plugins to analyze
        plugins_to_analyze = self.plugin_manager._get_plugins_for_operation(categories, paths)
        
        # Create analysis tasks for each plugin
        tasks = []
        for plugin in plugins_to_analyze:
            if paths:
                plugin_paths = [p for p in paths if plugin.can_handle_path(p)]
            else:
                plugin_paths = plugin.get_cleanable_paths()
            
            if plugin_paths:
                task = self.async_cleaner.analyze_async(plugin_paths)
                tasks.append((plugin.name, plugin.category, task))
        
        # Execute all plugin analyses concurrently
        results = {
            "categories": {},
            "total_size": 0,
            "total_files": 0,
            "plugins": {},
            "analysis_time": self.plugin_manager._get_timestamp(),
            "plugins_analyzed": len(tasks),
            "duration_seconds": 0
        }
        
        plugin_results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
        
        for i, (plugin_name, plugin_category, _) in enumerate(tasks):
            result = plugin_results[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"Error in async analysis for plugin {plugin_name}: {result}")
                results["plugins"][plugin_name] = {"error": str(result)}
            else:
                results["plugins"][plugin_name] = result
                
                # Update category totals
                if plugin_category not in results["categories"]:
                    results["categories"][plugin_category] = {
                        "size": 0,
                        "files": 0,
                        "plugins": [],
                    }
                
                results["categories"][plugin_category]["size"] += result["total_size"]
                results["categories"][plugin_category]["files"] += result["total_files"]
                results["categories"][plugin_category]["plugins"].append(plugin_name)
                
                results["total_size"] += result["total_size"]
                results["total_files"] += result["total_files"]
        
        results["duration_seconds"] = time.time() - start_time
        results["total_size_human"] = self.plugin_manager._format_bytes(results["total_size"])
        
        return results
    
    async def clean_all_async(
        self, 
        categories: Optional[List[str]] = None, 
        paths: Optional[List[str]] = None, 
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Async version of clean_all"""
        start_time = time.time()
        
        # Get plugins to clean
        plugins_to_clean = self.plugin_manager._get_plugins_for_operation(categories, paths)
        
        # Create cleaning tasks for each plugin
        tasks = []
        for plugin in plugins_to_clean:
            if paths:
                plugin_paths = [p for p in paths if plugin.can_handle_path(p)]
            else:
                plugin_paths = plugin.get_cleanable_paths()
            
            if plugin_paths:
                task = self.async_cleaner.clean_async(plugin_paths, dry_run)
                tasks.append((plugin.name, plugin.category, task))
        
        # Execute all plugin cleaning concurrently
        results = {
            "categories": {},
            "total_freed": 0,
            "plugins": {},
            "operation_time": self.plugin_manager._get_timestamp(),
            "plugins_processed": len(tasks),
            "mode": "dry_run" if dry_run else "clean",
            "duration_seconds": 0
        }
        
        plugin_results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
        
        for i, (plugin_name, plugin_category, _) in enumerate(tasks):
            result = plugin_results[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"Error in async cleaning for plugin {plugin_name}: {result}")
                results["plugins"][plugin_name] = {"error": str(result)}
            else:
                results["plugins"][plugin_name] = result
                
                # Update category totals
                if plugin_category not in results["categories"]:
                    results["categories"][plugin_category] = {
                        "freed": 0,
                        "plugins": [],
                    }
                
                results["categories"][plugin_category]["freed"] += result["total_freed"]
                results["categories"][plugin_category]["plugins"].append(plugin_name)
                
                results["total_freed"] += result["total_freed"]
        
        results["duration_seconds"] = time.time() - start_time
        results["total_freed_human"] = self.plugin_manager._format_bytes(results["total_freed"])
        
        return results
