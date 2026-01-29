#!/usr/bin/env python3
"""
Core components for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from .config_manager import ConfigurationManager, get_config, set_config
from .enhanced_cleaner import EnhancedCleaner
from .async_cleaner import AsyncCleaner, AsyncPluginManager
from .async_plugin_manager import AsyncPluginExecutor, SmartPluginScheduler
from .analytics import UsageAnalytics, UsageEvent, SpaceUsageSnapshot
from .scheduler import SmartScheduler, ScheduledTask, ScheduleType, TaskExecutionResult
from .notifications import NotificationManager, SmartNotificationManager, NotificationMessage, NotificationType

__all__ = [
    'ConfigurationManager',
    'get_config',
    'set_config',
    'EnhancedCleaner',
    'AsyncCleaner',
    'AsyncPluginManager',
    'AsyncPluginExecutor',
    'SmartPluginScheduler',
    'UsageAnalytics',
    'UsageEvent',
    'SpaceUsageSnapshot',
    'SmartScheduler',
    'ScheduledTask',
    'ScheduleType',
    'TaskExecutionResult',
    'NotificationManager',
    'SmartNotificationManager',
    'NotificationMessage',
    'NotificationType',
]
