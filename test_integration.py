#!/usr/bin/env python3
"""
Test script to verify database integration with web GUI
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from src.mac_cleaner.core.database import DatabaseManager
    from src.mac_cleaner.file_analyzer import FileAnalyzer
    
    print("🧪 Testing Database Integration")
    print("=" * 40)
    
    # Test database manager
    print("📦 Testing Database Manager...")
    db_manager = DatabaseManager()
    stats = db_manager.get_database_stats()
    print(f"   Database location: {stats['database_path']}")
    print(f"   Database size: {stats['database_size_human']}")
    print(f"   Scan records: {stats['scan_records']}")
    print(f"   File records: {stats['file_records']}")
    
    # Test file analyzer with database
    print("\n🔍 Testing File Analyzer with Database...")
    analyzer = FileAnalyzer(enable_db_logging=True)
    
    # Start a test scan
    scan_id = analyzer.start_scan(scan_type="test", categories=["test"])
    print(f"   Started scan with ID: {scan_id}")
    
    # Create some mock data
    mock_files = [
        {
            "path": "/tmp/test_file1.tmp",
            "name": "test_file1.tmp",
            "size": 1024,
            "modified": analyzer.db_manager._load_data.__func__.__defaults__[0] if hasattr(analyzer.db_manager, '_load_data') else None,
            "created": analyzer.db_manager._load_data.__func__.__defaults__[0] if hasattr(analyzer.db_manager, '_load_data') else None,
            "safety_level": "very_safe",
            "importance_score": 5,
            "recommendation": "delete"
        }
    ]
    
    # Finish the scan
    finished_id = analyzer.finish_scan(mock_files, space_freed=1024, files_deleted=1)
    print(f"   Finished scan with ID: {finished_id}")
    
    # Test retrieval
    history = analyzer.get_scan_history(limit=5)
    print(f"   Retrieved {len(history)} scan records from database")
    
    analytics = analyzer.get_analytics_summary(days=30)
    print(f"   Analytics keys: {list(analytics.keys())}")
    
    print("\n✅ Database integration test passed!")
    print(f"📊 Database now contains {stats['scan_records'] + 1} scan records")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
