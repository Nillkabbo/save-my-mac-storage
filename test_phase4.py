#!/usr/bin/env python3
"""
Test script for Phase 4: Advanced features (async operations, analytics).

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from datetime import time as dt_time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mac_cleaner.core import (
    AsyncCleaner, 
    UsageAnalytics, 
    AsyncPluginExecutor,
    SmartScheduler,
    NotificationManager,
    ScheduledTask,
    ScheduleType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_async_operations():
    """Test async operations"""
    print("\n🚀 Testing Async Operations")
    print("=" * 50)
    
    try:
        # Create async cleaner
        cleaner = AsyncCleaner(max_workers=4)
        
        # Test with some sample paths
        test_paths = [
            "~/.cache",
            "/tmp",
            "~/Library/Caches"
        ]
        
        print("Testing async analysis...")
        start_time = time.time()
        
        # Run async analysis
        result = await cleaner.analyze_async(test_paths)
        
        duration = time.time() - start_time
        
        print(f"✅ Async analysis completed in {duration:.2f} seconds")
        print(f"   Total size: {result['total_size_human']}")
        print(f"   Total files: {result['total_files']}")
        print(f"   Successful paths: {result['successful_paths']}")
        print(f"   Failed paths: {result['failed_paths']}")
        print(f"   Processing rate: {result['paths_per_second']:.1f} paths/second")
        
        return True
        
    except Exception as e:
        print(f"❌ Async operations test failed: {e}")
        return False

async def test_async_plugin_executor():
    """Test async plugin executor"""
    print("\n🔌 Testing Async Plugin Executor")
    print("=" * 50)
    
    try:
        # Create plugin executor
        executor = AsyncPluginExecutor(max_workers=4)
        
        # Get some plugins (this would normally come from plugin manager)
        from mac_cleaner.plugins import get_all_plugins
        plugins = get_all_plugins()[:3]  # Test with first 3 plugins
        
        if not plugins:
            print("⚠️  No plugins available for testing")
            return True
        
        print(f"Testing with {len(plugins)} plugins...")
        
        # Execute plugins in parallel
        result = await executor.execute_plugins_parallel(
            plugins=plugins,
            operation="analyze"
        )
        
        print(f"✅ Plugin execution completed")
        print(f"   Total plugins: {result['summary']['total_plugins']}")
        print(f"   Successful plugins: {result['summary']['successful_plugins']}")
        print(f"   Failed plugins: {result['summary']['failed_plugins']}")
        print(f"   Total paths processed: {result['summary']['total_paths_processed']}")
        print(f"   Total size processed: {result['summary']['total_size_human']}")
        print(f"   Overall duration: {result['summary']['overall_duration_ms']:.1f}ms")
        print(f"   Efficiency score: {result['summary']['efficiency_score']:.2f}")
        
        # Test with progress
        print("\nTesting with progress updates...")
        
        async for progress_update in executor.execute_plugins_with_progress(
            plugins=plugins,
            operation="analyze"
        ):
            if progress_update["type"] == "plugin_complete":
                print(f"   Plugin completed: {progress_update['plugin_name']} ({progress_update['progress']:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Async plugin executor test failed: {e}")
        return False

def test_analytics():
    """Test analytics module"""
    print("\n📊 Testing Analytics Module")
    print("=" * 50)
    
    try:
        # Create analytics instance
        analytics = UsageAnalytics()
        
        # Record some sample events
        from mac_cleaner.core.analytics import UsageEvent
        from datetime import datetime, timedelta
        
        # Create sample events
        events = [
            UsageEvent(
                timestamp=datetime.now() - timedelta(days=2),
                operation_type="analyze",
                paths_processed=150,
                size_processed=1024*1024*500,  # 500MB
                duration_seconds=5.2,
                categories=["cache", "temp"],
                success=True
            ),
            UsageEvent(
                timestamp=datetime.now() - timedelta(days=1),
                operation_type="clean",
                paths_processed=200,
                size_processed=1024*1024*800,  # 800MB
                duration_seconds=8.1,
                categories=["cache", "logs"],
                success=True
            ),
            UsageEvent(
                timestamp=datetime.now() - timedelta(hours=6),
                operation_type="analyze",
                paths_processed=120,
                size_processed=1024*1024*300,  # 300MB
                duration_seconds=3.8,
                categories=["temp"],
                success=True
            )
        ]
        
        # Record events
        for event in events:
            analytics.record_event(event)
        
        print(f"✅ Recorded {len(events)} sample events")
        
        # Test pattern analysis
        print("Analyzing patterns...")
        patterns = analytics.analyze_patterns()
        
        if "error" not in patterns:
            print(f"✅ Pattern analysis completed")
            print(f"   Total events analyzed: {patterns['total_events']}")
            print(f"   Category patterns found: {len(patterns['category_patterns'])}")
            print(f"   Recommendations: {len(patterns['recommendations'])}")
            
            for rec in patterns['recommendations']:
                print(f"   - {rec}")
        else:
            print(f"⚠️  Pattern analysis: {patterns['error']}")
        
        # Test usage summary
        print("Getting usage summary...")
        summary = analytics.get_usage_summary(days=7)
        
        if "error" not in summary:
            print(f"✅ Usage summary generated")
            print(f"   Total operations: {summary['total_operations']}")
            print(f"   Success rate: {summary['success_rate']:.1%}")
            print(f"   Total size processed: {summary['total_size_processed_human']}")
            print(f"   Most active day: {summary['most_active_day']}")
        else:
            print(f"⚠️  Usage summary: {summary['error']}")
        
        # Test prediction
        print("Testing space prediction...")
        prediction = analytics.predict_space_usage(days_ahead=30)
        
        print(f"✅ Space prediction completed")
        print(f"   Days until full: {prediction.days_until_full}")
        print(f"   Confidence: {prediction.confidence:.1%}")
        print(f"   Assumptions: {len(prediction.assumptions)}")
        
        # Test schedule recommendation
        print("Testing schedule recommendation...")
        schedule = analytics.suggest_cleanup_schedule()
        
        if "error" not in schedule:
            print(f"✅ Schedule recommendation generated")
            print(f"   Generated at: {schedule['generated_at']}")
            print(f"   Schedule intervals: {list(schedule['schedule'].keys())}")
        else:
            print(f"⚠️  Schedule recommendation: {schedule['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False

def test_scheduler():
    """Test smart scheduler"""
    print("\n⏰ Testing Smart Scheduler")
    print("=" * 50)
    
    try:
        # Create scheduler
        scheduler = SmartScheduler()
        
        print("Creating sample scheduled task...")
        
        # Create a sample task
        task = ScheduledTask(
            id="test_task_1",
            name="Test Daily Cache Cleaning",
            schedule_type=ScheduleType.DAILY,
            categories=["cache"],
            dry_run=True
        )
        
        # Add task
        success = scheduler.add_task(task)
        
        if success:
            print(f"✅ Task added successfully: {task.name}")
            
            # Get tasks
            tasks = scheduler.get_tasks()
            print(f"   Total tasks: {len(tasks)}")
            
            # Get scheduler status
            status = scheduler.get_scheduler_status()
            print(f"✅ Scheduler status:")
            print(f"   Running: {status['running']}")
            print(f"   Total tasks: {status['tasks']['total']}")
            print(f"   Enabled tasks: {status['tasks']['enabled']}")
            
        else:
            print(f"❌ Failed to add task")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

def test_notifications():
    """Test notification system"""
    print("\n🔔 Testing Notification System")
    print("=" * 50)
    
    try:
        # Create notification manager
        notification_manager = NotificationManager()
        
        print("Testing basic notification...")
        
        # Create test notification
        from mac_cleaner.core.notifications import NotificationMessage, NotificationType, NotificationChannel
        
        message = NotificationMessage(
            title="Test Notification",
            message="This is a test notification from macOS Cleaner Phase 4",
            notification_type=NotificationType.SYSTEM_WARNING,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG],
            priority="normal"
        )
        
        # Send notification
        success = notification_manager.send_notification(message)
        
        if success:
            print(f"✅ Notification sent successfully")
        else:
            print(f"⚠️  Notification sending had issues")
        
        # Test task completion notification
        print("Testing task completion notification...")
        
        from mac_cleaner.core.scheduler import TaskExecutionResult
        from datetime import datetime
        
        task_result = TaskExecutionResult(
            task_id="test_task",
            task_name="Test Task",
            execution_time=datetime.now(),
            success=True,
            duration_seconds=5.2,
            paths_processed=100,
            size_freed=1024*1024*100  # 100MB
        )
        
        success = notification_manager.notify_task_completion(task_result)
        
        if success:
            print(f"✅ Task completion notification sent")
        else:
            print(f"⚠️  Task completion notification had issues")
        
        # Test space warning
        print("Testing space warning notification...")
        
        success = notification_manager.notify_space_warning(
            free_space_gb=10.5,
            usage_percent=89.5
        )
        
        if success:
            print(f"✅ Space warning notification sent")
        else:
            print(f"⚠️  Space warning notification had issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Phase 4: Advanced Features Test Suite")
    print("=" * 60)
    print("Testing async operations, analytics, and smart scheduling")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Async Operations", await test_async_operations()))
    test_results.append(("Async Plugin Executor", await test_async_plugin_executor()))
    test_results.append(("Analytics Module", test_analytics()))
    test_results.append(("Smart Scheduler", test_scheduler()))
    test_results.append(("Notification System", test_notifications()))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 4 tests passed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
