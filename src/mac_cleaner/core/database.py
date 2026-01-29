#!/usr/bin/env python3
"""
Database Manager - SQLite database for scan records and system analytics

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class ScanRecord:
    """Represents a complete scan record"""
    id: Optional[int] = None
    timestamp: datetime = None
    scan_type: str = "full"  # full, quick, custom
    total_files_scanned: int = 0
    total_size_scanned: int = 0
    duration_seconds: float = 0.0
    categories_scanned: List[str] = None
    scan_summary: Dict = None
    space_freed: int = 0
    files_deleted: int = 0
    errors_count: int = 0
    success: bool = True
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.categories_scanned is None:
            self.categories_scanned = []
        if self.scan_summary is None:
            self.scan_summary = {}


@dataclass
class FileRecord:
    """Represents a single file record in a scan"""
    id: Optional[int] = None
    scan_id: int = None
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    modified_time: datetime = None
    created_time: datetime = None
    file_type: str = ""
    safety_level: str = "unknown"
    importance_score: int = 50
    recommendation: str = "review"
    category: str = "unknown"
    was_deleted: bool = False
    deletion_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.modified_time is None:
            self.modified_time = datetime.now()
        if self.created_time is None:
            self.created_time = datetime.now()


@dataclass
class SystemSnapshot:
    """Represents a system state snapshot"""
    id: Optional[int] = None
    timestamp: datetime = None
    total_disk_space: int = 0
    used_space: int = 0
    free_space: int = 0
    platform_info: Dict = None
    memory_info: Dict = None
    category_breakdown: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.platform_info is None:
            self.platform_info = {}
        if self.memory_info is None:
            self.memory_info = {}
        if self.category_breakdown is None:
            self.category_breakdown = {}


class DatabaseManager:
    """SQLite database manager for scan records and analytics"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".mac_cleaner" / "mac_cleaner.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize database
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        with self.get_connection() as conn:
            # Scan records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    scan_type TEXT NOT NULL,
                    total_files_scanned INTEGER NOT NULL,
                    total_size_scanned INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    categories_scanned TEXT NOT NULL,
                    scan_summary TEXT NOT NULL,
                    space_freed INTEGER NOT NULL,
                    files_deleted INTEGER NOT NULL,
                    errors_count INTEGER NOT NULL,
                    success BOOLEAN NOT NULL
                )
            """)
            
            # File records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    modified_time DATETIME NOT NULL,
                    created_time DATETIME NOT NULL,
                    file_type TEXT NOT NULL,
                    safety_level TEXT NOT NULL,
                    importance_score INTEGER NOT NULL,
                    recommendation TEXT NOT NULL,
                    category TEXT NOT NULL,
                    was_deleted BOOLEAN NOT NULL,
                    deletion_timestamp DATETIME,
                    FOREIGN KEY (scan_id) REFERENCES scan_records (id)
                )
            """)
            
            # System snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    total_disk_space INTEGER NOT NULL,
                    used_space INTEGER NOT NULL,
                    free_space INTEGER NOT NULL,
                    platform_info TEXT NOT NULL,
                    memory_info TEXT NOT NULL,
                    category_breakdown TEXT NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_records(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_scan_id ON file_records(scan_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON file_records(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_safety ON file_records(safety_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON system_snapshots(timestamp)")
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def save_scan_record(self, scan_record: ScanRecord) -> int:
        """Save a scan record and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scan_records (
                    timestamp, scan_type, total_files_scanned, total_size_scanned,
                    duration_seconds, categories_scanned, scan_summary,
                    space_freed, files_deleted, errors_count, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_record.timestamp.isoformat(),
                scan_record.scan_type,
                scan_record.total_files_scanned,
                scan_record.total_size_scanned,
                scan_record.duration_seconds,
                json.dumps(scan_record.categories_scanned),
                json.dumps(scan_record.scan_summary),
                scan_record.space_freed,
                scan_record.files_deleted,
                scan_record.errors_count,
                scan_record.success
            ))
            
            scan_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Saved scan record with ID: {scan_id}")
            return scan_id
    
    def save_file_records(self, file_records: List[FileRecord], scan_id: int) -> None:
        """Save multiple file records for a scan"""
        with self.get_connection() as conn:
            for file_record in file_records:
                file_record.scan_id = scan_id
                conn.execute("""
                    INSERT INTO file_records (
                        scan_id, file_path, file_name, file_size,
                        modified_time, created_time, file_type,
                        safety_level, importance_score, recommendation,
                        category, was_deleted, deletion_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_record.scan_id,
                    file_record.file_path,
                    file_record.file_name,
                    file_record.file_size,
                    file_record.modified_time.isoformat(),
                    file_record.created_time.isoformat(),
                    file_record.file_type,
                    file_record.safety_level,
                    file_record.importance_score,
                    file_record.recommendation,
                    file_record.category,
                    file_record.was_deleted,
                    file_record.deletion_timestamp.isoformat() if file_record.deletion_timestamp else None
                ))
            
            conn.commit()
            self.logger.info(f"Saved {len(file_records)} file records for scan {scan_id}")
    
    def save_system_snapshot(self, snapshot: SystemSnapshot) -> int:
        """Save a system snapshot and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO system_snapshots (
                    timestamp, total_disk_space, used_space, free_space,
                    platform_info, memory_info, category_breakdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp.isoformat(),
                snapshot.total_disk_space,
                snapshot.used_space,
                snapshot.free_space,
                json.dumps(snapshot.platform_info),
                json.dumps(snapshot.memory_info),
                json.dumps(snapshot.category_breakdown)
            ))
            
            snapshot_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Saved system snapshot with ID: {snapshot_id}")
            return snapshot_id
    
    def get_scan_history(self, limit: int = 50) -> List[Dict]:
        """Get scan history"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM scan_records 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            records = []
            for row in cursor.fetchall():
                record = dict(row)
                record['categories_scanned'] = json.loads(record['categories_scanned'])
                record['scan_summary'] = json.loads(record['scan_summary'])
                records.append(record)
            
            return records
    
    def get_scan_details(self, scan_id: int) -> Dict:
        """Get detailed information about a specific scan"""
        with self.get_connection() as conn:
            # Get scan record
            cursor = conn.execute("""
                SELECT * FROM scan_records WHERE id = ?
            """, (scan_id,))
            
            scan_record = cursor.fetchone()
            if not scan_record:
                return {"error": "Scan record not found"}
            
            scan_data = dict(scan_record)
            scan_data['categories_scanned'] = json.loads(scan_data['categories_scanned'])
            scan_data['scan_summary'] = json.loads(scan_data['scan_summary'])
            
            # Get file records for this scan
            cursor = conn.execute("""
                SELECT * FROM file_records WHERE scan_id = ?
                ORDER BY file_size DESC
            """, (scan_id,))
            
            file_records = []
            for row in cursor.fetchall():
                file_data = dict(row)
                file_records.append(file_data)
            
            scan_data['file_records'] = file_records
            return scan_data
    
    def get_system_snapshots(self, days: int = 30) -> List[Dict]:
        """Get system snapshots for the last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM system_snapshots 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_date,))
            
            snapshots = []
            for row in cursor.fetchall():
                snapshot = dict(row)
                snapshot['platform_info'] = json.loads(snapshot['platform_info'])
                snapshot['memory_info'] = json.loads(snapshot['memory_info'])
                snapshot['category_breakdown'] = json.loads(snapshot['category_breakdown'])
                snapshots.append(snapshot)
            
            return snapshots
    
    def get_analytics_summary(self, days: int = 30) -> Dict:
        """Get analytics summary for the last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            # Scan statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    SUM(total_files_scanned) as total_files,
                    SUM(total_size_scanned) as total_size,
                    SUM(space_freed) as total_space_freed,
                    SUM(files_deleted) as total_files_deleted,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_scans
                FROM scan_records 
                WHERE timestamp >= ?
            """, (cutoff_date,))
            
            scan_stats = dict(cursor.fetchone())
            
            # Category breakdown
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count, SUM(file_size) as total_size
                FROM file_records fr
                JOIN scan_records sr ON fr.scan_id = sr.id
                WHERE sr.timestamp >= ?
                GROUP BY category
                ORDER BY total_size DESC
            """, (cutoff_date,))
            
            category_stats = [dict(row) for row in cursor.fetchall()]
            
            # Safety level breakdown
            cursor = conn.execute("""
                SELECT safety_level, COUNT(*) as count, SUM(file_size) as total_size
                FROM file_records fr
                JOIN scan_records sr ON fr.scan_id = sr.id
                WHERE sr.timestamp >= ?
                GROUP BY safety_level
                ORDER BY count DESC
            """, (cutoff_date,))
            
            safety_stats = [dict(row) for row in cursor.fetchall()]
            
            # Daily scan counts
            cursor = conn.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as scans
                FROM scan_records
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (cutoff_date,))
            
            daily_scans = [dict(row) for row in cursor.fetchall()]
            
            return {
                "period_days": days,
                "scan_statistics": scan_stats,
                "category_breakdown": category_stats,
                "safety_breakdown": safety_stats,
                "daily_scans": daily_scans
            }
    
    def get_top_space_consumers(self, days: int = 30, limit: int = 20) -> List[Dict]:
        """Get top space consuming files from recent scans"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT file_path, file_name, file_size, safety_level, 
                       category, recommendation, fr.modified_time
                FROM file_records fr
                JOIN scan_records sr ON fr.scan_id = sr.id
                WHERE sr.timestamp >= ? AND fr.was_deleted = 0
                ORDER BY fr.file_size DESC
                LIMIT ?
            """, (cutoff_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_files_by_safety_level(self, safety_level: str, days: int = 30) -> List[Dict]:
        """Get files by safety level from recent scans"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT file_path, file_name, file_size, category, recommendation,
                       fr.modified_time, sr.timestamp as scan_timestamp
                FROM file_records fr
                JOIN scan_records sr ON fr.scan_id = sr.id
                WHERE sr.timestamp >= ? AND fr.safety_level = ? AND fr.was_deleted = 0
                ORDER BY fr.file_size DESC
            """, (cutoff_date, safety_level))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_files_deleted(self, file_paths: List[str]) -> None:
        """Mark files as deleted in the database"""
        with self.get_connection() as conn:
            for file_path in file_paths:
                conn.execute("""
                    UPDATE file_records 
                    SET was_deleted = 1, deletion_timestamp = ?
                    WHERE file_path = ?
                """, (datetime.now().isoformat(), file_path))
            
            conn.commit()
            self.logger.info(f"Marked {len(file_paths)} files as deleted")
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> None:
        """Clean up old records to manage database size"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        with self.get_connection() as conn:
            # Delete old file records
            cursor = conn.execute("""
                DELETE FROM file_records 
                WHERE scan_id IN (
                    SELECT id FROM scan_records WHERE timestamp < ?
                )
            """, (cutoff_date,))
            
            files_deleted = cursor.rowcount
            
            # Delete old scan records
            cursor = conn.execute("""
                DELETE FROM scan_records WHERE timestamp < ?
            """, (cutoff_date,))
            
            scans_deleted = cursor.rowcount
            
            # Delete old system snapshots
            cursor = conn.execute("""
                DELETE FROM system_snapshots WHERE timestamp < ?
            """, (cutoff_date,))
            
            snapshots_deleted = cursor.rowcount
            
            conn.commit()
            self.logger.info(f"Cleaned up old records: {scans_deleted} scans, {files_deleted} files, {snapshots_deleted} snapshots")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            # Table counts
            cursor = conn.execute("SELECT COUNT(*) FROM scan_records")
            scan_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM file_records")
            file_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM system_snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Date range
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM scan_records")
            date_range = cursor.fetchone()
            
            return {
                "database_path": str(self.db_path),
                "database_size_bytes": db_size,
                "database_size_human": self._format_bytes(db_size),
                "scan_records": scan_count,
                "file_records": file_count,
                "system_snapshots": snapshot_count,
                "date_range": {
                    "earliest": date_range[0],
                    "latest": date_range[1]
                }
            }
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"


__all__ = ["DatabaseManager", "ScanRecord", "FileRecord", "SystemSnapshot"]
