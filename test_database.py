#!/usr/bin/env python3
"""
Test Database Functionality - Simple test script for SQLite database

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.mac_cleaner.core.database import DatabaseManager, ScanRecord, FileRecord, SystemSnapshot
from src.mac_cleaner.file_analyzer import FileAnalyzer


def test_database_functionality():
    """Test basic database functionality"""
    print("🧪 Testing Database Functionality")
    print("=" * 40)
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_mac_cleaner.db"
        
        try:
            # Initialize database
            print("📦 Initializing database...")
            db_manager = DatabaseManager(str(db_path))
            
            # Test database stats
            print("📊 Getting database stats...")
            stats = db_manager.get_database_stats()
            print(f"   Database path: {stats['database_path']}")
            print(f"   Database size: {stats['database_size_human']}")
            print(f"   Scan records: {stats['scan_records']}")
            print(f"   File records: {stats['file_records']}")
            
            # Create test scan record
            print("🔍 Creating test scan record...")
            scan_record = ScanRecord(
                timestamp=datetime.now(),
                scan_type="test",
                total_files_scanned=100,
                total_size_scanned=1024 * 1024 * 10,  # 10MB
                duration_seconds=5.5,
                categories_scanned=["cache", "logs"],
                scan_summary={"test": "data"},
                space_freed=1024 * 1024,  # 1MB
                files_deleted=5,
                errors_count=0,
                success=True
            )
            
            scan_id = db_manager.save_scan_record(scan_record)
            print(f"   Saved scan record with ID: {scan_id}")
            
            # Create test file records
            print("📁 Creating test file records...")
            file_records = [
                FileRecord(
                    scan_id=scan_id,
                    file_path="/tmp/test1.txt",
                    file_name="test1.txt",
                    file_size=1024,
                    safety_level="safe",
                    importance_score=20,
                    recommendation="delete",
                    category="cache"
                ),
                FileRecord(
                    scan_id=scan_id,
                    file_path="/tmp/test2.log",
                    file_name="test2.log",
                    file_size=2048,
                    safety_level="very_safe",
                    importance_score=10,
                    recommendation="delete",
                    category="logs"
                )
            ]
            
            db_manager.save_file_records(file_records, scan_id)
            print(f"   Saved {len(file_records)} file records")
            
            # Create test system snapshot
            print("💾 Creating test system snapshot...")
            snapshot = SystemSnapshot(
                timestamp=datetime.now(),
                total_disk_space=1024 * 1024 * 1024 * 100,  # 100GB
                used_space=1024 * 1024 * 1024 * 50,       # 50GB
                free_space=1024 * 1024 * 1024 * 50,       # 50GB
                platform_info={"system": "Darwin", "release": "21.6.0"},
                memory_info={"total": 8589934592, "available": 4294967296},
                category_breakdown={"cache": 1024*1024, "logs": 512*1024}
            )
            
            snapshot_id = db_manager.save_system_snapshot(snapshot)
            print(f"   Saved system snapshot with ID: {snapshot_id}")
            
            # Test retrieval
            print("🔍 Testing data retrieval...")
            
            # Get scan history
            scan_history = db_manager.get_scan_history(limit=10)
            print(f"   Retrieved {len(scan_history)} scan records")
            
            # Get scan details
            scan_details = db_manager.get_scan_details(scan_id)
            print(f"   Retrieved scan details: {len(scan_details.get('file_records', []))} files")
            
            # Get system snapshots
            snapshots = db_manager.get_system_snapshots(days=30)
            print(f"   Retrieved {len(snapshots)} system snapshots")
            
            # Get analytics summary
            analytics = db_manager.get_analytics_summary(days=30)
            print(f"   Analytics summary generated: {list(analytics.keys())}")
            
            # Get top space consumers
            top_consumers = db_manager.get_top_space_consumers(days=30, limit=10)
            print(f"   Retrieved {len(top_consumers)} top space consumers")
            
            # Test file analyzer integration
            print("🔧 Testing FileAnalyzer integration...")
            analyzer = FileAnalyzer(enable_db_logging=True)
            
            # Start a scan
            test_scan_id = analyzer.start_scan(scan_type="test_integration", categories=["test"])
            print(f"   Started scan with ID: {test_scan_id}")
            
            # Create some mock file data
            mock_files = [
                {
                    "path": "/tmp/mock1.tmp",
                    "name": "mock1.tmp",
                    "size": 1024,
                    "modified": datetime.now(),
                    "created": datetime.now(),
                    "safety_level": "very_safe",
                    "importance_score": 5,
                    "recommendation": "delete"
                },
                {
                    "path": "/tmp/mock2.cache",
                    "name": "mock2.cache", 
                    "size": 2048,
                    "modified": datetime.now(),
                    "created": datetime.now(),
                    "safety_level": "safe",
                    "importance_score": 15,
                    "recommendation": "delete"
                }
            ]
            
            # Finish the scan
            finished_scan_id = analyzer.finish_scan(mock_files, space_freed=3072, files_deleted=2)
            print(f"   Finished scan with ID: {finished_scan_id}")
            
            # Test retrieval through analyzer
            analyzer_history = analyzer.get_scan_history(limit=5)
            print(f"   Analyzer retrieved {len(analyzer_history)} scans")
            
            analyzer_analytics = analyzer.get_analytics_summary(days=30)
            print(f"   Analyzer analytics: {list(analyzer_analytics.keys())}")
            
            print("\n✅ All database tests passed!")
            
            # Final database stats
            final_stats = db_manager.get_database_stats()
            print(f"\n📊 Final Database Stats:")
            print(f"   Scan records: {final_stats['scan_records']}")
            print(f"   File records: {final_stats['file_records']}")
            print(f"   System snapshots: {final_stats['system_snapshots']}")
            print(f"   Database size: {final_stats['database_size_human']}")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    return True


def test_database_performance():
    """Test database performance with larger datasets"""
    print("\n⚡ Testing Database Performance")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "perf_test.db"
        
        try:
            db_manager = DatabaseManager(str(db_path))
            
            # Create multiple scan records
            print("📈 Creating multiple scan records...")
            start_time = datetime.now()
            
            for i in range(10):
                scan_record = ScanRecord(
                    timestamp=datetime.now() - timedelta(days=i),
                    scan_type=f"performance_test_{i}",
                    total_files_scanned=100 * (i + 1),
                    total_size_scanned=1024 * 1024 * (i + 1),
                    duration_seconds=1.0 * (i + 1),
                    categories_scanned=["cache", "logs", "temp"],
                    scan_summary={"test": f"batch_{i}"},
                    space_freed=1024 * 1024 * i // 2,
                    files_deleted=10 * i,
                    errors_count=0,
                    success=True
                )
                db_manager.save_scan_record(scan_record)
            
            creation_time = (datetime.now() - start_time).total_seconds()
            print(f"   Created 10 scan records in {creation_time:.2f} seconds")
            
            # Test query performance
            print("🔍 Testing query performance...")
            start_time = datetime.now()
            
            scan_history = db_manager.get_scan_history(limit=50)
            analytics = db_manager.get_analytics_summary(days=30)
            top_consumers = db_manager.get_top_space_consumers(days=30, limit=20)
            
            query_time = (datetime.now() - start_time).total_seconds()
            print(f"   Executed queries in {query_time:.2f} seconds")
            print(f"   Retrieved {len(scan_history)} scans, {len(top_consumers)} top consumers")
            
            print("✅ Performance tests passed!")
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False
            
    return True


if __name__ == "__main__":
    print("🍎 macOS Cleaner Database Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run basic functionality tests
    if not test_database_functionality():
        success = False
    
    # Run performance tests
    if not test_database_performance():
        success = False
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
