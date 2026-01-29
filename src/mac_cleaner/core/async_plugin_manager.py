#!/usr/bin/env python3
"""
Async plugin execution system for enhanced performance.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from dataclasses import dataclass

from ..interfaces import CleanerPlugin, ConfigInterface, SafetyLevel


@dataclass
class AsyncPluginResult:
    """Result of async plugin operation"""
    plugin_name: str
    plugin_category: str
    success: bool
    duration_ms: float
    paths_processed: int
    size_processed: int
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class PluginExecutionPlan:
    """Execution plan for plugin operations"""
    plugins: List[CleanerPlugin]
    execution_order: List[str]  # Plugin names in execution order
    concurrent_groups: List[List[str]]  # Groups that can run concurrently
    estimated_duration_ms: float


class AsyncPluginExecutor:
    """Async executor for plugin operations with intelligent scheduling"""
    
    def __init__(self, max_workers: int = 4, enable_priority_execution: bool = True):
        self.max_workers = max_workers
        self.enable_priority_execution = enable_priority_execution
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Plugin performance tracking
        self.plugin_performance: Dict[str, List[float]] = {}
        
    async def execute_plugins_parallel(
        self, 
        plugins: List[CleanerPlugin], 
        operation: str,
        paths: Optional[List[str]] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Execute plugins in parallel where possible"""
        start_time = time.time()
        
        # Create execution plan
        plan = self._create_execution_plan(plugins, operation)
        
        self.logger.info(f"Executing {len(plugins)} plugins with plan: {len(plan.concurrent_groups)} concurrent groups")
        
        # Execute according to plan
        all_results = []
        total_duration = 0
        
        for group in plan.concurrent_groups:
            group_start = time.time()
            
            # Get plugins for this group
            group_plugins = [p for p in plugins if p.name in group]
            
            # Execute group concurrently
            if len(group_plugins) == 1:
                # Single plugin, execute directly
                result = await self._execute_single_plugin(group_plugins[0], operation, paths, dry_run)
                all_results.append(result)
            else:
                # Multiple plugins, execute concurrently
                tasks = [
                    self._execute_single_plugin(plugin, operation, paths, dry_run)
                    for plugin in group_plugins
                ]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in group_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Plugin execution error: {result}")
                        # Create error result
                        all_results.append(AsyncPluginResult(
                            plugin_name="unknown",
                            plugin_category="unknown",
                            success=False,
                            duration_ms=0,
                            paths_processed=0,
                            size_processed=0,
                            error_message=str(result)
                        ))
                    else:
                        all_results.append(result)
            
            group_duration = (time.time() - group_start) * 1000
            total_duration += group_duration
            
            self.logger.debug(f"Plugin group completed in {group_duration:.1f}ms")
        
        # Process results
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        
        total_paths = sum(r.paths_processed for r in successful_results)
        total_size = sum(r.size_processed for r in successful_results)
        
        overall_duration = (time.time() - start_time) * 1000
        
        return {
            "execution_plan": {
                "total_plugins": len(plugins),
                "concurrent_groups": len(plan.concurrent_groups),
                "estimated_duration_ms": plan.estimated_duration_ms,
                "actual_duration_ms": overall_duration
            },
            "results": {
                "successful": [self._result_to_dict(r) for r in successful_results],
                "failed": [self._result_to_dict(r) for r in failed_results]
            },
            "summary": {
                "total_plugins": len(plugins),
                "successful_plugins": len(successful_results),
                "failed_plugins": len(failed_results),
                "total_paths_processed": total_paths,
                "total_size_processed": total_size,
                "total_size_human": self._format_bytes(total_size),
                "overall_duration_ms": overall_duration,
                "efficiency_score": self._calculate_efficiency(plan.estimated_duration_ms, overall_duration)
            }
        }
    
    async def execute_plugins_with_progress(
        self,
        plugins: List[CleanerPlugin],
        operation: str,
        paths: Optional[List[str]] = None,
        dry_run: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute plugins with progress updates"""
        total_plugins = len(plugins)
        completed = 0
        
        yield {
            "type": "start",
            "total_plugins": total_plugins,
            "progress": 0.0
        }
        
        # Create execution plan
        plan = self._create_execution_plan(plugins, operation)
        
        for group in plan.concurrent_groups:
            group_plugins = [p for p in plugins if p.name in group]
            
            # Execute group
            if len(group_plugins) == 1:
                result = await self._execute_single_plugin(group_plugins[0], operation, paths, dry_run)
                completed += 1
                
                yield {
                    "type": "plugin_complete",
                    "plugin_name": result.plugin_name,
                    "result": self._result_to_dict(result),
                    "progress": completed / total_plugins,
                    "completed": completed,
                    "total_plugins": total_plugins
                }
                
                if progress_callback:
                    progress_callback({
                        "type": "plugin_complete",
                        "plugin_name": result.plugin_name,
                        "progress": completed / total_plugins
                    })
            else:
                # Execute group concurrently
                tasks = [
                    self._execute_single_plugin(plugin, operation, paths, dry_run)
                    for plugin in group_plugins
                ]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in group_results:
                    completed += 1
                    
                    if isinstance(result, Exception):
                        yield {
                            "type": "plugin_error",
                            "error": str(result),
                            "progress": completed / total_plugins,
                            "completed": completed,
                            "total_plugins": total_plugins
                        }
                    else:
                        yield {
                            "type": "plugin_complete",
                            "plugin_name": result.plugin_name,
                            "result": self._result_to_dict(result),
                            "progress": completed / total_plugins,
                            "completed": completed,
                            "total_plugins": total_plugins
                        }
                    
                    if progress_callback:
                        progress_callback({
                            "type": "plugin_complete",
                            "progress": completed / total_plugins
                        })
        
        yield {
            "type": "complete",
            "progress": 1.0,
            "completed": completed,
            "total_plugins": total_plugins
        }
    
    async def _execute_single_plugin(
        self,
        plugin: CleanerPlugin,
        operation: str,
        paths: Optional[List[str]] = None,
        dry_run: bool = True
    ) -> AsyncPluginResult:
        """Execute a single plugin asynchronously"""
        loop = asyncio.get_event_loop()
        start_time = time.time()
        
        try:
            # Determine paths for this plugin
            if paths:
                plugin_paths = [p for p in paths if plugin.can_handle_path(p)]
            else:
                plugin_paths = plugin.get_cleanable_paths()
            
            # Execute operation in thread pool
            if operation == "analyze":
                result = await loop.run_in_executor(
                    self.executor,
                    plugin.analyze_paths,
                    plugin_paths
                )
                paths_processed = len(result.get("paths", []))
                size_processed = result.get("total_size", 0)
                details = result
                
            elif operation == "clean":
                result = await loop.run_in_executor(
                    self.executor,
                    plugin.clean_paths,
                    plugin_paths,
                    dry_run
                )
                paths_processed = len(result.get("analyzed", [])) + len(result.get("skipped", []))
                size_processed = result.get("total_analyzed", 0)
                details = result
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            duration = (time.time() - start_time) * 1000
            
            # Track performance
            if plugin.name not in self.plugin_performance:
                self.plugin_performance[plugin.name] = []
            self.plugin_performance[plugin.name].append(duration)
            
            return AsyncPluginResult(
                plugin_name=plugin.name,
                plugin_category=plugin.category,
                success=True,
                duration_ms=duration,
                paths_processed=paths_processed,
                size_processed=size_processed,
                details=details
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            # Track failed performance
            if plugin.name not in self.plugin_performance:
                self.plugin_performance[plugin.name] = []
            self.plugin_performance[plugin.name].append(duration)
            
            return AsyncPluginResult(
                plugin_name=plugin.name,
                plugin_category=plugin.category,
                success=False,
                duration_ms=duration,
                paths_processed=0,
                size_processed=0,
                error_message=str(e)
            )
    
    def _create_execution_plan(self, plugins: List[CleanerPlugin], operation: str) -> PluginExecutionPlan:
        """Create optimized execution plan for plugins"""
        if not self.enable_priority_execution:
            # Simple plan: all plugins can run concurrently
            return PluginExecutionPlan(
                plugins=plugins,
                execution_order=[p.name for p in plugins],
                concurrent_groups=[[p.name for p in plugins]],
                estimated_duration_ms=self._estimate_concurrent_duration(plugins)
            )
        
        # Priority-based execution plan
        # Group plugins by priority and category conflicts
        
        # Sort plugins by priority (higher = runs first)
        sorted_plugins = sorted(plugins, key=lambda p: p.priority, reverse=True)
        
        # Create concurrent groups based on priority tiers
        priority_tiers = {}
        for plugin in sorted_plugins:
            tier = plugin.priority // 10  # Group by tens
            if tier not in priority_tiers:
                priority_tiers[tier] = []
            priority_tiers[tier].append(plugin)
        
        # Build concurrent groups
        concurrent_groups = []
        for tier in sorted(priority_tiers.keys(), reverse=True):
            tier_plugins = priority_tiers[tier]
            
            # Check for conflicts within the tier
            # For now, assume plugins in same tier can run concurrently
            # In a more sophisticated implementation, we'd check for resource conflicts
            group_names = [p.name for p in tier_plugins]
            concurrent_groups.append(group_names)
        
        estimated_duration = self._estimate_plan_duration(concurrent_groups, plugins)
        
        return PluginExecutionPlan(
            plugins=plugins,
            execution_order=[p.name for p in sorted_plugins],
            concurrent_groups=concurrent_groups,
            estimated_duration_ms=estimated_duration
        )
    
    def _estimate_concurrent_duration(self, plugins: List[CleanerPlugin]) -> float:
        """Estimate duration if all plugins run concurrently"""
        if not plugins:
            return 0.0
        
        # Use historical performance data if available
        durations = []
        for plugin in plugins:
            if plugin.name in self.plugin_performance and self.plugin_performance[plugin.name]:
                avg_duration = sum(self.plugin_performance[plugin.name]) / len(self.plugin_performance[plugin.name])
                durations.append(avg_duration)
            else:
                # Default estimate based on plugin category
                durations.append(self._get_default_duration_estimate(plugin))
        
        # Return the maximum (bottleneck) if running concurrently
        return max(durations) if durations else 1000.0  # Default 1 second
    
    def _estimate_plan_duration(self, concurrent_groups: List[List[str]], plugins: List[CleanerPlugin]) -> float:
        """Estimate total duration for execution plan"""
        total_duration = 0.0
        
        for group in concurrent_groups:
            group_plugins = [p for p in plugins if p.name in group]
            group_duration = self._estimate_concurrent_duration(group_plugins)
            total_duration += group_duration
        
        return total_duration
    
    def _get_default_duration_estimate(self, plugin: CleanerPlugin) -> float:
        """Get default duration estimate for a plugin"""
        # Base estimates by category (in milliseconds)
        category_estimates = {
            "cache": 500,      # Cache analysis is usually fast
            "temp": 300,       # Temp files are fast
            "logs": 800,       # Logs might be numerous
            "development": 1200,  # Dev files can be large
            "user": 600,       # User directories vary
        }
        
        return category_estimates.get(plugin.category, 1000.0)
    
    def _calculate_efficiency(self, estimated: float, actual: float) -> float:
        """Calculate efficiency score (estimated vs actual)"""
        if estimated == 0:
            return 1.0
        
        # Efficiency closer to 1.0 is better
        efficiency = min(2.0, actual / estimated)  # Cap at 2.0
        return max(0.0, 2.0 - efficiency)  # Invert so higher is better
    
    def _result_to_dict(self, result: AsyncPluginResult) -> Dict[str, Any]:
        """Convert AsyncPluginResult to dictionary"""
        return {
            "plugin_name": result.plugin_name,
            "plugin_category": result.plugin_category,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "paths_processed": result.paths_processed,
            "size_processed": result.size_processed,
            "size_processed_human": self._format_bytes(result.size_processed),
            "error_message": result.error_message,
            "details": result.details
        }
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def get_plugin_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for plugins"""
        stats = {}
        
        for plugin_name, durations in self.plugin_performance.items():
            if durations:
                stats[plugin_name] = {
                    "executions": len(durations),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "total_duration_ms": sum(durations)
                }
        
        return stats
    
    def reset_performance_tracking(self) -> None:
        """Reset performance tracking data"""
        self.plugin_performance.clear()
        self.logger.info("Performance tracking reset")
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


class SmartPluginScheduler:
    """Smart scheduler for plugin operations based on system conditions"""
    
    def __init__(self, executor: AsyncPluginExecutor):
        self.executor = executor
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def schedule_optimal_execution(
        self,
        plugins: List[CleanerPlugin],
        operation: str,
        paths: Optional[List[str]] = None,
        dry_run: bool = True,
        system_load_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Schedule plugin execution based on current system conditions"""
        # Check system load
        system_load = await self._get_system_load()
        
        if system_load > system_load_threshold:
            self.logger.warning(f"High system load ({system_load:.2f}), adjusting execution strategy")
            # Reduce concurrency for high load
            original_workers = self.executor.max_workers
            self.executor.max_workers = max(1, original_workers // 2)
            
            try:
                result = await self.executor.execute_plugins_parallel(plugins, operation, paths, dry_run)
                result["system_conditions"] = {
                    "load": system_load,
                    "threshold": system_load_threshold,
                    "strategy": "reduced_concurrency",
                    "original_workers": original_workers,
                    "adjusted_workers": self.executor.max_workers
                }
                return result
            finally:
                self.executor.max_workers = original_workers
        else:
            # Normal execution
            result = await self.executor.execute_plugins_parallel(plugins, operation, paths, dry_run)
            result["system_conditions"] = {
                "load": system_load,
                "threshold": system_load_threshold,
                "strategy": "normal"
            }
            return result
    
    async def _get_system_load(self) -> float:
        """Get current system load (0.0 to 1.0)"""
        try:
            import psutil
            
            # Get CPU load
            cpu_load = psutil.cpu_percent(interval=0.1) / 100.0
            
            # Get memory load
            memory = psutil.virtual_memory()
            memory_load = memory.percent / 100.0
            
            # Get disk I/O load (simplified)
            disk_load = 0.0
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    # This is a simplified metric
                    disk_load = min(1.0, (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024 * 1024))  # Normalized by GB
            except:
                pass
            
            # Return the maximum load
            return max(cpu_load, memory_load, disk_load)
            
        except ImportError:
            # psutil not available, return moderate load
            return 0.5
        except Exception as e:
            self.logger.error(f"Error getting system load: {e}")
            return 0.5
