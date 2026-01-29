#!/usr/bin/env python3
"""
Notification system for cleaning completion and system events.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import logging
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    import pync
    PYNC_AVAILABLE = True
except ImportError:
    PYNC_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .scheduler import TaskExecutionResult


class NotificationType(Enum):
    """Types of notifications"""
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SYSTEM_WARNING = "system_warning"
    SPACE_LOW = "space_low"
    SCHEDULE_CHANGED = "schedule_changed"
    ERROR = "error"


class NotificationChannel(Enum):
    """Notification channels"""
    SYSTEM = "system"          # macOS notifications
    EMAIL = "email"            # Email notifications
    WEBHOOK = "webhook"        # Webhook notifications
    LOG = "log"               # Log file notifications
    CONSOLE = "console"       # Console output


@dataclass
class NotificationMessage:
    """Notification message"""
    title: str
    message: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    priority: str = "normal"  # low, normal, high, critical
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    enabled_channels: List[NotificationChannel]
    system_sound: str = "Glass"
    email_config: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    log_file: Optional[str] = None
    min_priority_for_system: str = "normal"
    min_priority_for_email: str = "high"
    min_priority_for_webhook: str = "normal"


class NotificationManager:
    """Manages notifications for various system events"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Ensure log directory exists if log channel is enabled
        if NotificationChannel.LOG in self.config.enabled_channels and self.config.log_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def send_notification(self, message: NotificationMessage) -> bool:
        """Send notification through configured channels"""
        success = True
        
        for channel in message.channels:
            if channel not in self.config.enabled_channels:
                continue
            
            # Check priority threshold
            if not self._check_priority_threshold(channel, message.priority):
                continue
            
            try:
                if channel == NotificationChannel.SYSTEM:
                    success &= self._send_system_notification(message)
                elif channel == NotificationChannel.EMAIL:
                    success &= self._send_email_notification(message)
                elif channel == NotificationChannel.WEBHOOK:
                    success &= self._send_webhook_notification(message)
                elif channel == NotificationChannel.LOG:
                    success &= self._send_log_notification(message)
                elif channel == NotificationChannel.CONSOLE:
                    success &= self._send_console_notification(message)
                
            except Exception as e:
                self.logger.error(f"Failed to send notification via {channel.value}: {e}")
                success = False
        
        return success
    
    def notify_task_completion(self, result: TaskExecutionResult) -> bool:
        """Send notification for task completion"""
        if result.success:
            message = NotificationMessage(
                title="macOS Cleaner - Task Completed",
                message=f"Task '{result.task_name}' completed successfully.\n"
                       f"Processed {result.paths_processed} paths, "
                       f"freed {self._format_bytes(result.size_freed)}.\n"
                       f"Duration: {result.duration_seconds:.1f} seconds.",
                notification_type=NotificationType.TASK_COMPLETED,
                channels=[NotificationChannel.SYSTEM, NotificationChannel.LOG],
                priority="normal",
                data={
                    "task_id": result.task_id,
                    "task_name": result.task_name,
                    "paths_processed": result.paths_processed,
                    "size_freed": result.size_freed,
                    "duration_seconds": result.duration_seconds
                }
            )
        else:
            message = NotificationMessage(
                title="macOS Cleaner - Task Failed",
                message=f"Task '{result.task_name}' failed.\n"
                       f"Error: {result.error_message}\n"
                       f"Duration: {result.duration_seconds:.1f} seconds.",
                notification_type=NotificationType.TASK_FAILED,
                channels=[NotificationChannel.SYSTEM, NotificationChannel.LOG],
                priority="high",
                data={
                    "task_id": result.task_id,
                    "task_name": result.task_name,
                    "error_message": result.error_message,
                    "duration_seconds": result.duration_seconds
                }
            )
        
        return self.send_notification(message)
    
    def notify_space_warning(self, free_space_gb: float, usage_percent: float) -> bool:
        """Send notification for low disk space"""
        message = NotificationMessage(
            title="macOS Cleaner - Disk Space Warning",
            message=f"Disk space is running low.\n"
                   f"Free space: {free_space_gb:.1f} GB ({usage_percent:.1f}% used)\n"
                   f"Consider running a cleaning operation.",
            notification_type=NotificationType.SPACE_LOW,
            channels=[NotificationChannel.SYSTEM, NotificationChannel.EMAIL],
            priority="high" if usage_percent > 90 else "normal",
            data={
                "free_space_gb": free_space_gb,
                "usage_percent": usage_percent
            }
        )
        
        return self.send_notification(message)
    
    def notify_system_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Send notification for system errors"""
        message = NotificationMessage(
            title="macOS Cleaner - System Error",
            message=f"A system error occurred:\n{error_message}",
            notification_type=NotificationType.ERROR,
            channels=[NotificationChannel.SYSTEM, NotificationChannel.LOG],
            priority="critical",
            data=context or {}
        )
        
        return self.send_notification(message)
    
    def notify_schedule_change(self, task_name: str, change_description: str) -> bool:
        """Send notification for schedule changes"""
        message = NotificationMessage(
            title="macOS Cleaner - Schedule Updated",
            message=f"Schedule for task '{task_name}' has been updated.\n"
                   f"Change: {change_description}",
            notification_type=NotificationType.SCHEDULE_CHANGED,
            channels=[NotificationChannel.LOG],
            priority="low",
            data={
                "task_name": task_name,
                "change_description": change_description
            }
        )
        
        return self.send_notification(message)
    
    def _send_system_notification(self, message: NotificationMessage) -> bool:
        """Send macOS system notification"""
        if not PYNC_AVAILABLE:
            self.logger.warning("pync not available, cannot send system notification")
            return False
        
        try:
            # Determine sound based on priority
            sound = self.config.system_sound
            if message.priority == "critical":
                sound = "Basso"
            elif message.priority == "high":
                sound = "Sosumi"
            
            pync.notify(
                message.message,
                title=message.title,
                sound=sound,
                timeout=10 if message.priority in ["high", "critical"] else 5
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}")
            return False
    
    def _send_email_notification(self, message: NotificationMessage) -> bool:
        """Send email notification"""
        if not self.config.email_config:
            self.logger.warning("Email not configured")
            return False
        
        try:
            # This is a placeholder for email implementation
            # In a real implementation, you'd use smtplib or a service like SendGrid
            
            email_config = self.config.email_config
            
            # Create email content
            subject = f"[macOS Cleaner] {message.title}"
            body = f"""
            {message.message}
            
            ---
            Timestamp: {message.timestamp.isoformat()}
            Type: {message.notification_type.value}
            Priority: {message.priority}
            """
            
            # Log email would be sent (placeholder)
            self.logger.info(f"Email notification would be sent:")
            self.logger.info(f"  To: {email_config.get('to', 'admin@example.com')}")
            self.logger.info(f"  Subject: {subject}")
            self.logger.info(f"  Body: {body[:100]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_webhook_notification(self, message: NotificationMessage) -> bool:
        """Send webhook notification"""
        if not REQUESTS_AVAILABLE:
            self.logger.warning("requests not available, cannot send webhook")
            return False
        
        if not self.config.webhook_url:
            self.logger.warning("Webhook URL not configured")
            return False
        
        try:
            payload = {
                "title": message.title,
                "message": message.message,
                "type": message.notification_type.value,
                "priority": message.priority,
                "timestamp": message.timestamp.isoformat(),
                "data": message.data or {}
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Webhook notification sent successfully to {self.config.webhook_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def _send_log_notification(self, message: NotificationMessage) -> bool:
        """Send notification to log file"""
        if not self.config.log_file:
            self.logger.warning("Log file not configured")
            return False
        
        try:
            log_entry = {
                "timestamp": message.timestamp.isoformat(),
                "title": message.title,
                "message": message.message,
                "type": message.notification_type.value,
                "priority": message.priority,
                "data": message.data
            }
            
            with open(self.config.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
            return False
    
    def _send_console_notification(self, message: NotificationMessage) -> bool:
        """Send notification to console"""
        try:
            # Format based on priority
            prefix = ""
            if message.priority == "critical":
                prefix = "🚨 "
            elif message.priority == "high":
                prefix = "⚠️ "
            elif message.priority == "normal":
                prefix = "ℹ️ "
            else:
                prefix = "💡 "
            
            console_message = f"{prefix}[{message.notification_type.value.upper()}] {message.title}: {message.message}"
            
            if message.priority in ["high", "critical"]:
                self.logger.error(console_message)
            elif message.priority == "normal":
                self.logger.warning(console_message)
            else:
                self.logger.info(console_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send console notification: {e}")
            return False
    
    def _check_priority_threshold(self, channel: NotificationChannel, priority: str) -> bool:
        """Check if message priority meets channel threshold"""
        priority_levels = {"low": 0, "normal": 1, "high": 2, "critical": 3}
        message_level = priority_levels.get(priority, 1)
        
        if channel == NotificationChannel.SYSTEM:
            threshold_level = priority_levels.get(self.config.min_priority_for_system, 1)
        elif channel == NotificationChannel.EMAIL:
            threshold_level = priority_levels.get(self.config.min_priority_for_email, 2)
        elif channel == NotificationChannel.WEBHOOK:
            threshold_level = priority_levels.get(self.config.min_priority_for_webhook, 1)
        else:
            return True  # No threshold for other channels
        
        return message_level >= threshold_level
    
    def _get_default_config(self) -> NotificationConfig:
        """Get default notification configuration"""
        return NotificationConfig(
            enabled_channels=[
                NotificationChannel.SYSTEM,
                NotificationChannel.LOG,
                NotificationChannel.CONSOLE
            ],
            system_sound="Glass",
            log_file="~/.mac_cleaner_notifications.log",
            min_priority_for_system="normal",
            min_priority_for_email="high",
            min_priority_for_webhook="normal"
        )
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"


class SmartNotificationManager:
    """Smart notification manager that learns from user behavior"""
    
    def __init__(self, base_manager: NotificationManager):
        self.base_manager = base_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Notification history and user preferences
        self.notification_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {
            "quiet_hours": {"start": 22, "end": 8},  # 10 PM to 8 AM
            "max_notifications_per_hour": 5,
            "consolidate_similar": True,
            "learning_enabled": True
        }
        
        # Rate limiting
        self.recent_notifications: List[datetime] = []
    
    def send_smart_notification(self, message: NotificationMessage) -> bool:
        """Send notification with smart filtering"""
        # Check if we should send this notification
        if not self._should_send_notification(message):
            return True  # Consider it successful (filtered)
        
        # Check quiet hours
        if self._is_quiet_hours() and message.priority not in ["high", "critical"]:
            self.logger.info("Notification suppressed due to quiet hours")
            return True
        
        # Check rate limiting
        if self._is_rate_limited():
            self.logger.info("Notification suppressed due to rate limiting")
            return True
        
        # Try to consolidate with recent similar notifications
        if self.user_preferences["consolidate_similar"]:
            consolidated = self._try_consolidate(message)
            if consolidated:
                return True
        
        # Send the notification
        success = self.base_manager.send_notification(message)
        
        # Track the notification
        self._track_notification(message, success)
        
        return success
    
    def _should_send_notification(self, message: NotificationMessage) -> bool:
        """Determine if notification should be sent based on learning"""
        if not self.user_preferences["learning_enabled"]:
            return True
        
        # Simple learning: if similar notifications were recently ignored, reduce priority
        recent_similar = [
            n for n in self.notification_history[-20:]  # Last 20 notifications
            if n["type"] == message.notification_type.value
            and n["timestamp"] > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_similar) > 3:
            # Too many similar notifications recently, suppress
            return False
        
        return True
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is during quiet hours"""
        now = datetime.now().hour
        quiet_start = self.user_preferences["quiet_hours"]["start"]
        quiet_end = self.user_preferences["quiet_hours"]["end"]
        
        if quiet_start > quiet_end:
            # Overnight quiet hours (e.g., 22:00 to 08:00)
            return now >= quiet_start or now < quiet_end
        else:
            # Same day quiet hours
            return quiet_start <= now < quiet_end
    
    def _is_rate_limited(self) -> bool:
        """Check if we're rate limited"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old notifications
        self.recent_notifications = [
            n for n in self.recent_notifications if n > one_hour_ago
        ]
        
        # Check limit
        max_per_hour = self.user_preferences["max_notifications_per_hour"]
        return len(self.recent_notifications) >= max_per_hour
    
    def _try_consolidate(self, message: NotificationMessage) -> bool:
        """Try to consolidate with recent similar notifications"""
        # Look for similar notifications in the last 5 minutes
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        for notification in reversed(self.notification_history):
            if (notification["timestamp"] > five_minutes_ago and
                notification["type"] == message.notification_type.value and
                notification["title"] == message.title):
                
                # Found similar notification, update it instead of sending new one
                notification["count"] = notification.get("count", 1) + 1
                notification["last_updated"] = datetime.now()
                
                self.logger.info(f"Consolidated notification: {message.title} (count: {notification['count']})")
                return True
        
        return False
    
    def _track_notification(self, message: NotificationMessage, success: bool) -> bool:
        """Track notification for learning"""
        self.recent_notifications.append(datetime.now())
        
        notification_record = {
            "timestamp": datetime.now(),
            "title": message.title,
            "type": message.notification_type.value,
            "priority": message.priority,
            "channels": [c.value for c in message.channels],
            "success": success,
            "count": 1
        }
        
        self.notification_history.append(notification_record)
        
        # Keep only last 1000 notifications
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]
        
        return success
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.user_preferences.update(preferences)
        self.logger.info(f"Updated notification preferences: {preferences}")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = len(self.notification_history)
        
        if total_notifications == 0:
            return {"total": 0}
        
        # Stats by type
        type_counts = {}
        for notification in self.notification_history:
            notification_type = notification["type"]
            type_counts[notification_type] = type_counts.get(notification_type, 0) + 1
        
        # Stats by priority
        priority_counts = {}
        for notification in self.notification_history:
            priority = notification["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Recent activity (last 24 hours)
        one_day_ago = datetime.now() - timedelta(days=1)
        recent_count = sum(
            1 for n in self.notification_history 
            if n["timestamp"] > one_day_ago
        )
        
        return {
            "total": total_notifications,
            "recent_24h": recent_count,
            "by_type": type_counts,
            "by_priority": priority_counts,
            "preferences": self.user_preferences
        }
