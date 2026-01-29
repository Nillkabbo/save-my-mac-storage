#!/usr/bin/env python3
"""
Smart scheduling with background tasks for automated cleaning.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from ..interfaces import ConfigInterface
from .analytics import UsageAnalytics, UsageEvent
from .async_plugin_manager import AsyncPluginExecutor, SmartPluginScheduler


class ScheduleType(Enum):
    """Types of scheduling"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    INTERVAL = "interval"
    SMART = "smart"


@dataclass
class ScheduledTask:
    """Represents a scheduled cleaning task"""
    id: str
    name: str
    schedule_type: ScheduleType
    enabled: bool = True
    categories: List[str] = field(default_factory=list)
    paths: List[str] = field(default_factory=list)
    dry_run: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Schedule-specific parameters
    cron_expression: Optional[str] = None
    interval_hours: Optional[int] = None
    interval_days: Optional[int] = None
    specific_time: Optional[dt_time] = None
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    
    # Smart scheduling parameters
    auto_adjust: bool = False
    min_interval_hours: int = 6
    max_interval_hours: int = 168  # 1 week
    target_disk_usage_percent: float = 80.0


@dataclass
class TaskExecutionResult:
    """Result of a scheduled task execution"""
    task_id: str
    task_name: str
    execution_time: datetime
    success: bool
    duration_seconds: float
    paths_processed: int
    size_freed: int
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SmartScheduler:
    """Smart scheduler for automated cleaning operations"""
    
    def __init__(self, config: Optional[ConfigInterface] = None, data_dir: Optional[str] = None):
        self.config = config
        self.data_dir = Path(data_dir or "~/.mac_cleaner_scheduler").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Components
        self.analytics = UsageAnalytics(str(self.data_dir))
        self.async_executor = AsyncPluginExecutor()
        self.smart_plugin_scheduler = SmartPluginScheduler(self.async_executor)
        
        # Scheduler setup
        if APSCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        else:
            self.scheduler = None
            self.logger.warning("APScheduler not available, limited scheduling functionality")
        
        # Task management
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecutionResult] = []
        
        # Data files
        self.tasks_file = self.data_dir / "scheduled_tasks.json"
        self.history_file = self.data_dir / "execution_history.json"
        
        # Event callbacks
        self.task_callbacks: List[Callable[[TaskExecutionResult], None]] = []
        
        # Load existing data
        self._load_tasks()
        self._load_history()
        
        # Status
        self.running = False
    
    def start(self) -> bool:
        """Start the scheduler"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return True
        
        if not APSCHEDULER_AVAILABLE:
            self.logger.error("Cannot start scheduler: APScheduler not available")
            return False
        
        try:
            self.scheduler.start()
            self.running = True
            
            # Schedule all enabled tasks
            for task in self.tasks.values():
                if task.enabled:
                    self._schedule_task(task)
            
            self.logger.info("Smart scheduler started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the scheduler"""
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return True
        
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
            self.running = False
            self.logger.info("Smart scheduler stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
            return False
    
    def add_task(self, task: ScheduledTask) -> bool:
        """Add a new scheduled task"""
        try:
            # Validate task
            if not self._validate_task(task):
                return False
            
            # Add to tasks
            self.tasks[task.id] = task
            
            # Schedule if enabled and scheduler is running
            if task.enabled and self.running:
                self._schedule_task(task)
            
            # Save
            self._save_tasks()
            
            self.logger.info(f"Added scheduled task: {task.name} ({task.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add task {task.name}: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id not in self.tasks:
            self.logger.warning(f"Task not found: {task_id}")
            return False
        
        try:
            # Remove from scheduler
            if self.scheduler:
                self.scheduler.remove_job(task_id)
            
            # Remove from tasks
            task_name = self.tasks[task_id].name
            del self.tasks[task_id]
            
            # Save
            self._save_tasks()
            
            self.logger.info(f"Removed scheduled task: {task_name} ({task_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove task {task_id}: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.enabled = True
        
        if self.running:
            self._schedule_task(task)
        
        self._save_tasks()
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.enabled = False
        
        if self.scheduler:
            try:
                self.scheduler.remove_job(task_id)
            except:
                pass  # Job might not exist
        
        self._save_tasks()
        return True
    
    def get_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks"""
        return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a specific task"""
        return self.tasks.get(task_id)
    
    def get_execution_history(self, limit: int = 100) -> List[TaskExecutionResult]:
        """Get execution history"""
        return self.execution_history[-limit:]
    
    async def run_task_now(self, task_id: str) -> TaskExecutionResult:
        """Run a task immediately"""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        self.logger.info(f"Running task immediately: {task.name}")
        
        start_time = datetime.now()
        
        try:
            # Get plugins for this task
            from ..plugins import get_plugins_by_categories
            plugins = get_plugins_by_categories(task.categories) if task.categories else []
            
            if not plugins:
                raise ValueError("No plugins available for this task")
            
            # Execute task
            result = await self.smart_plugin_scheduler.schedule_optimal_execution(
                plugins=plugins,
                operation="clean",
                paths=task.paths,
                dry_run=task.dry_run
            )
            
            # Create execution result
            execution_result = TaskExecutionResult(
                task_id=task.id,
                task_name=task.name,
                execution_time=start_time,
                success=True,
                duration_seconds=result["summary"]["overall_duration_ms"] / 1000.0,
                paths_processed=result["summary"]["total_paths_processed"],
                size_freed=result["summary"]["total_size_processed"],
                details=result
            )
            
            # Update task statistics
            task.last_run = start_time
            task.run_count += 1
            task.success_count += 1
            
            # Record usage event
            usage_event = UsageEvent(
                timestamp=start_time,
                operation_type="scheduled_clean",
                paths_processed=execution_result.paths_processed,
                size_processed=execution_result.size_freed,
                duration_seconds=execution_result.duration_seconds,
                categories=task.categories,
                success=True
            )
            self.analytics.record_event(usage_event)
            
            # Record space snapshot
            await self._record_space_snapshot()
            
            # Auto-adjust smart tasks
            if task.schedule_type == ScheduleType.SMART and task.auto_adjust:
                await self._auto_adjust_smart_task(task)
            
            # Save and notify
            self._save_tasks()
            self._save_history()
            self._notify_callbacks(execution_result)
            
            self.logger.info(f"Task completed successfully: {task.name}")
            return execution_result
            
        except Exception as e:
            # Create error result
            execution_result = TaskExecutionResult(
                task_id=task.id,
                task_name=task.name,
                execution_time=start_time,
                success=False,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                paths_processed=0,
                size_freed=0,
                error_message=str(e)
            )
            
            # Update task statistics
            task.last_run = start_time
            task.run_count += 1
            task.error_count += 1
            task.last_error = str(e)
            
            # Record usage event
            usage_event = UsageEvent(
                timestamp=start_time,
                operation_type="scheduled_clean",
                paths_processed=0,
                size_processed=0,
                duration_seconds=execution_result.duration_seconds,
                categories=task.categories,
                success=False,
                error_message=str(e)
            )
            self.analytics.record_event(usage_event)
            
            # Save and notify
            self._save_tasks()
            self._save_history()
            self._notify_callbacks(execution_result)
            
            self.logger.error(f"Task failed: {task.name} - {e}")
            return execution_result
    
    def add_task_callback(self, callback: Callable[[TaskExecutionResult], None]) -> None:
        """Add a callback for task execution results"""
        self.task_callbacks.append(callback)
    
    def remove_task_callback(self, callback: Callable[[TaskExecutionResult], None]) -> None:
        """Remove a task callback"""
        if callback in self.task_callbacks:
            self.task_callbacks.remove(callback)
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for t in self.tasks.values() if t.enabled)
        
        # Recent execution statistics
        recent_history = [h for h in self.execution_history 
                         if h.execution_time > datetime.now() - timedelta(days=7)]
        
        recent_success_rate = 0
        if recent_history:
            recent_success_rate = sum(1 for h in recent_history if h.success) / len(recent_history)
        
        return {
            "running": self.running,
            "scheduler_available": APSCHEDULER_AVAILABLE,
            "tasks": {
                "total": total_tasks,
                "enabled": enabled_tasks,
                "disabled": total_tasks - enabled_tasks
            },
            "executions": {
                "total": len(self.execution_history),
                "last_week": len(recent_history),
                "recent_success_rate": recent_success_rate
            },
            "analytics": {
                "usage_events": len(self.analytics.events),
                "space_snapshots": len(self.analytics.snapshots)
            }
        }
    
    def _schedule_task(self, task: ScheduledTask) -> bool:
        """Schedule a task with the scheduler"""
        if not self.scheduler:
            return False
        
        try:
            # Remove existing job if any
            try:
                self.scheduler.remove_job(task.id)
            except:
                pass
            
            # Create trigger based on schedule type
            trigger = None
            
            if task.schedule_type == ScheduleType.ONCE:
                if task.next_run:
                    trigger = CronTrigger(
                        year=task.next_run.year,
                        month=task.next_run.month,
                        day=task.next_run.day,
                        hour=task.next_run.hour,
                        minute=task.next_run.minute
                    )
            
            elif task.schedule_type == ScheduleType.DAILY:
                if task.specific_time:
                    trigger = CronTrigger(
                        hour=task.specific_time.hour,
                        minute=task.specific_time.minute
                    )
                else:
                    trigger = CronTrigger(hour=2, minute=0)  # Default 2 AM
            
            elif task.schedule_type == ScheduleType.WEEKLY:
                if task.specific_time and task.days_of_week:
                    trigger = CronTrigger(
                        day_of_week=','.join(str(d) for d in task.days_of_week),
                        hour=task.specific_time.hour,
                        minute=task.specific_time.minute
                    )
                else:
                    trigger = CronTrigger(day_of_week=0, hour=2, minute=0)  # Monday 2 AM
            
            elif task.schedule_type == ScheduleType.INTERVAL:
                if task.interval_hours:
                    trigger = IntervalTrigger(hours=task.interval_hours)
                elif task.interval_days:
                    trigger = IntervalTrigger(days=task.interval_days)
            
            elif task.schedule_type == ScheduleType.SMART:
                # Smart scheduling - start with daily and adjust
                trigger = CronTrigger(hour=2, minute=0)
            
            if trigger:
                self.scheduler.add_job(
                    func=self._execute_scheduled_task,
                    trigger=trigger,
                    args=[task.id],
                    id=task.id,
                    name=task.name,
                    replace_existing=True
                )
                
                self.logger.info(f"Scheduled task: {task.name} ({task.id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task {task.name}: {e}")
            return False
    
    def _execute_scheduled_task(self, task_id: str) -> None:
        """Execute a scheduled task (called by scheduler)"""
        # Run in async context
        asyncio.create_task(self.run_task_now(task_id))
    
    async def _auto_adjust_smart_task(self, task: ScheduledTask) -> None:
        """Auto-adjust smart task based on analytics"""
        try:
            # Get usage patterns
            patterns = self.analytics.analyze_patterns()
            
            # Get prediction
            prediction = self.analytics.predict_space_usage()
            
            # Get schedule recommendation
            schedule_rec = self.analytics.suggest_cleanup_schedule()
            
            # Adjust interval based on recommendations
            if schedule_rec.get("overall_recommendation"):
                min_interval = schedule_rec["overall_recommendation"].get("minimum_interval_days", 7)
                
                # Convert to hours
                new_interval_hours = max(task.min_interval_hours, 
                                        min(task.max_interval_hours, min_interval * 24))
                
                if task.interval_hours != new_interval_hours:
                    task.interval_hours = new_interval_hours
                    
                    # Reschedule with new interval
                    if task.enabled and self.running:
                        self._schedule_task(task)
                    
                    self.logger.info(f"Auto-adjusted smart task {task.name} interval to {new_interval_hours} hours")
            
        except Exception as e:
            self.logger.error(f"Failed to auto-adjust smart task {task.name}: {e}")
    
    async def _record_space_snapshot(self) -> None:
        """Record current disk space snapshot"""
        try:
            import psutil
            
            # Get disk usage
            disk_usage = psutil.disk_usage('/')
            
            # Get category breakdown (simplified)
            category_breakdown = {}
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "total_disk_space": disk_usage.total,
                "used_space": disk_usage.used,
                "free_space": disk_usage.free,
                "category_breakdown": category_breakdown
            }
            
            # This would be enhanced with actual category breakdown
            # For now, just record basic disk usage
            
        except ImportError:
            self.logger.warning("psutil not available, cannot record space snapshot")
        except Exception as e:
            self.logger.error(f"Failed to record space snapshot: {e}")
    
    def _validate_task(self, task: ScheduledTask) -> bool:
        """Validate a scheduled task"""
        if not task.id or not task.name:
            self.logger.error("Task must have id and name")
            return False
        
        if task.schedule_type == ScheduleType.INTERVAL:
            if not task.interval_hours and not task.interval_days:
                self.logger.error("Interval task must have interval_hours or interval_days")
                return False
        
        if task.schedule_type == ScheduleType.SMART:
            if task.auto_adjust and (not task.min_interval_hours or not task.max_interval_hours):
                self.logger.error("Smart task with auto_adjust must have min/max interval hours")
                return False
        
        return True
    
    def _job_executed(self, event) -> None:
        """Handle successful job execution"""
        self.logger.debug(f"Job executed successfully: {event.job_id}")
    
    def _job_error(self, event) -> None:
        """Handle job execution error"""
        self.logger.error(f"Job execution error: {event.job_id} - {event.exception}")
    
    def _notify_callbacks(self, result: TaskExecutionResult) -> None:
        """Notify all registered callbacks"""
        for callback in self.task_callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"Error in task callback: {e}")
    
    def _load_tasks(self) -> None:
        """Load tasks from file"""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                    
                for task_data in tasks_data:
                    # Convert string enums back to enums
                    task_data["schedule_type"] = ScheduleType(task_data["schedule_type"])
                    
                    # Convert datetime strings back to datetime objects
                    for field in ["last_run", "next_run", "created_at"]:
                        if task_data.get(field):
                            task_data[field] = datetime.fromisoformat(task_data[field])
                    
                    # Convert time string back to time object
                    if task_data.get("specific_time"):
                        time_str = task_data["specific_time"]
                        task_data["specific_time"] = dt_time.fromisoformat(time_str)
                    
                    task = ScheduledTask(**task_data)
                    self.tasks[task.id] = task
                    
                self.logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
                
        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")
    
    def _save_tasks(self) -> None:
        """Save tasks to file"""
        try:
            tasks_data = []
            for task in self.tasks.values():
                task_dict = task.__dict__.copy()
                
                # Convert enums to strings
                task_dict["schedule_type"] = task.schedule_type.value
                
                # Convert datetime objects to strings
                for field in ["last_run", "next_run", "created_at"]:
                    if task_dict.get(field):
                        task_dict[field] = task_dict[field].isoformat()
                
                # Convert time object to string
                if task_dict.get("specific_time"):
                    task_dict["specific_time"] = task_dict["specific_time"].isoformat()
                
                tasks_data.append(task_dict)
            
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving tasks: {e}")
    
    def _load_history(self) -> None:
        """Load execution history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    
                for result_data in history_data:
                    # Convert datetime string back to datetime object
                    result_data["execution_time"] = datetime.fromisoformat(result_data["execution_time"])
                    
                    result = TaskExecutionResult(**result_data)
                    self.execution_history.append(result)
                    
                self.logger.info(f"Loaded {len(self.execution_history)} execution records")
                
        except Exception as e:
            self.logger.error(f"Error loading execution history: {e}")
    
    def _save_history(self) -> None:
        """Save execution history to file"""
        try:
            # Keep only last 1000 records
            history_to_save = self.execution_history[-1000:]
            
            history_data = []
            for result in history_to_save:
                result_dict = result.__dict__.copy()
                result_dict["execution_time"] = result.execution_time.isoformat()
                history_data.append(result_dict)
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving execution history: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.running:
            self.stop()
