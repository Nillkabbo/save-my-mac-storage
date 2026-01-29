#!/usr/bin/env python3
"""
File Analyzer - Detailed file analysis with importance scoring and Finder integration

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import subprocess
import json
import shutil
import platform
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import mimetypes
import stat
import logging

from .core.database import DatabaseManager, ScanRecord, FileRecord, SystemSnapshot


class FileAnalyzer:
    def __init__(self, enable_db_logging: bool = True):
        self.safe_extensions = {
            ".tmp",
            ".temp",
            ".cache",
            ".log",
            ".old",
            ".bak",
            ".swp",
            ".dmp",
            ".crash",
            ".DS_Store",
            ".Thumbs.db",
            ".part",
            ".download",
            ".partial",
            ".sync",
            ".torrent",
        }

        self.important_extensions = {
            ".app",
            ".kext",
            ".driver",
            ".plist",
            ".json",
            ".xml",
            ".conf",
            ".ini",
            ".cfg",
            ".key",
            ".p12",
            ".pem",
            ".doc",
            ".docx",
            ".pdf",
            ".pages",
            ".numbers",
            ".keynote",
        }

        self.large_file_threshold = 100 * 1024 * 1024
        self.old_file_threshold = 30
        
        # Initialize database manager
        self.db_manager = DatabaseManager() if enable_db_logging else None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Current scan tracking
        self.current_scan_id = None
        self.scan_start_time = None

    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single file and return detailed information"""
        try:
            stat_info = os.stat(file_path)

            file_info = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat_info.st_size,
                "size_human": self.format_bytes(stat_info.st_size),
                "modified": datetime.fromtimestamp(stat_info.st_mtime),
                "created": datetime.fromtimestamp(stat_info.st_ctime),
                "accessed": datetime.fromtimestamp(stat_info.st_atime),
                "is_file": os.path.isfile(file_path),
                "is_directory": os.path.isdir(file_path),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "is_hidden": file_path.startswith("."),
                "extension": os.path.splitext(file_path)[1].lower(),
                "mime_type": mimetypes.guess_type(file_path)[0],
                "importance_score": 0,
                "safety_level": "unknown",
                "recommendation": "unknown",
            }

            file_info["importance_score"] = self.calculate_importance_score(file_info)
            file_info["safety_level"] = self.determine_safety_level(file_info)
            file_info["recommendation"] = self.get_recommendation(file_info)

            return file_info

        except (OSError, PermissionError) as e:
            return {
                "path": file_path,
                "error": str(e),
                "importance_score": 0,
                "safety_level": "error",
                "recommendation": "skip",
            }

    def calculate_importance_score(self, file_info: Dict) -> int:
        """Calculate importance score (0-100, higher = more important)"""
        score = 50

        ext = file_info.get("extension", "")
        if ext in self.important_extensions:
            score += 30
        elif ext in self.safe_extensions:
            score -= 20

        now = datetime.now()
        modified = file_info.get("modified", now)
        days_old = (now - modified).days

        if days_old > self.old_file_threshold:
            score -= 15
        elif days_old < 7:
            score += 10

        size = file_info.get("size", 0)
        if size > self.large_file_threshold:
            score += 5
        elif size < 1024:
            score -= 10

        if file_info.get("is_hidden", False):
            score -= 5

        path = file_info.get("path", "")
        if any(system_dir in path for system_dir in ["/Library/", "/System/", "/usr/"]):
            score += 20

        if any(
            user_dir in path for user_dir in ["/Documents/", "/Desktop/", "/Downloads/"]
        ):
            score += 15

        return max(0, min(100, score))

    def determine_safety_level(self, file_info: Dict) -> str:
        """Determine safety level for deletion"""
        score = file_info.get("importance_score", 50)

        if score >= 80:
            return "critical"
        if score >= 60:
            return "important"
        if score >= 40:
            return "moderate"
        if score >= 20:
            return "safe"
        return "very_safe"

    def get_recommendation(self, file_info: Dict) -> str:
        """Get deletion recommendation"""
        safety = file_info.get("safety_level", "unknown")
        ext = file_info.get("extension", "")
        path = file_info.get("path", "")

        if "error" in file_info:
            return "skip"

        if safety in ["critical", "important"]:
            return "keep"
        if safety == "moderate":
            return "review"
        if ext in self.safe_extensions:
            return "delete"
        if any(cache_dir in path for cache_dir in ["/Caches/", "/cache/", "/tmp/"]):
            return "delete"
        return "review"

    def scan_directory(
        self, directory: str, max_depth: int = 3, max_files: int = 1000
    ) -> List[Dict]:
        """Scan directory and return detailed file analysis"""
        files = []
        files_scanned = 0

        try:
            for root, dirs, filenames in os.walk(directory):
                current_depth = root[len(directory) :].count(os.sep)
                if current_depth > max_depth:
                    continue

                for filename in filenames:
                    if files_scanned >= max_files:
                        return files

                    file_path = os.path.join(root, filename)
                    file_info = self.analyze_file(file_path)
                    files.append(file_info)
                    files_scanned += 1

        except (OSError, PermissionError):
            pass

        return files

    def format_bytes(self, bytes_size) -> str:
        """Format bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def open_in_finder(self, path: str) -> bool:
        """Open file or directory in Finder"""
        try:
            if os.path.exists(path):
                subprocess.run(["open", "-R", path], check=True)
                return True
            return False
        except subprocess.CalledProcessError:
            return False

    def get_directory_summary(self, directory: str) -> Dict:
        """Get summary statistics for a directory"""
        if not os.path.exists(directory):
            return {"error": "Directory not found"}

        total_size = 0
        file_count = 0
        dir_count = 0
        files_by_safety = {
            "critical": 0,
            "important": 0,
            "moderate": 0,
            "safe": 0,
            "very_safe": 0,
            "error": 0,
        }

        try:
            for root, dirs, filenames in os.walk(directory):
                dir_count += len(dirs)

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        file_info = self.analyze_file(file_path)
                        total_size += file_info.get("size", 0)
                        file_count += 1
                        safety = file_info.get("safety_level", "error")
                        files_by_safety[safety] += 1
                    except:
                        files_by_safety["error"] += 1

        except (OSError, PermissionError):
            pass

        return {
            "path": directory,
            "total_size": total_size,
            "total_size_human": self.format_bytes(total_size),
            "file_count": file_count,
            "directory_count": dir_count,
            "files_by_safety": files_by_safety,
            "deletable_size": self.estimate_deletable_size(directory),
        }

    def estimate_deletable_size(self, directory: str) -> int:
        """Estimate how much space can be safely deleted"""
        deletable_size = 0

        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        file_info = self.analyze_file(file_path)
                        if file_info.get("recommendation") in ["delete", "review"]:
                            deletable_size += file_info.get("size", 0)
                    except:
                        continue
        except (OSError, PermissionError):
            pass

        return deletable_size

    def export_analysis(self, files: List[Dict], output_file: str) -> bool:
        """Export analysis results to JSON file"""
        try:
            with open(output_file, "w") as f:
                json.dump(files, f, indent=2, default=str)
            return True
        except:
            return False

    def get_top_space_consumers(self, directory: str, top_n: int = 20) -> List[Dict]:
        """Get top N files consuming the most space"""
        files = self.scan_directory(directory, max_files=1000)
        return sorted(files, key=lambda x: x.get("size", 0), reverse=True)[:top_n]

    def get_old_files(self, directory: str, days_old: int = 30) -> List[Dict]:
        """Get files older than specified days"""
        files = self.scan_directory(directory, max_files=1000)
        cutoff_date = datetime.now() - timedelta(days=days_old)

        old_files = []
        for file_info in files:
            modified = file_info.get("modified")
            if modified and modified < cutoff_date:
                old_files.append(file_info)

        return sorted(old_files, key=lambda x: x.get("modified", datetime.now()))

    def start_scan(self, scan_type: str = "full", categories: List[str] = None) -> Optional[int]:
        """Start a new scan and return scan ID"""
        if not self.db_manager:
            return None
            
        self.scan_start_time = datetime.now()
        self.current_scan_id = None
        
        # Create initial scan record (will be updated when scan completes)
        scan_record = ScanRecord(
            timestamp=self.scan_start_time,
            scan_type=scan_type,
            categories_scanned=categories or [],
            success=True
        )
        
        self.current_scan_id = self.db_manager.save_scan_record(scan_record)
        self.logger.info(f"Started scan with ID: {self.current_scan_id}")
        return self.current_scan_id

    def finish_scan(self, files_scanned: List[Dict], space_freed: int = 0, files_deleted: int = 0, errors: int = 0) -> Optional[int]:
        """Finish current scan and save all results to database"""
        if not self.db_manager or not self.current_scan_id:
            return None
            
        try:
            # Calculate scan statistics
            total_files = len(files_scanned)
            total_size = sum(f.get("size", 0) for f in files_scanned)
            duration = (datetime.now() - self.scan_start_time).total_seconds() if self.scan_start_time else 0
            
            # Categorize files
            categories = set()
            scan_summary = {
                "safety_levels": {},
                "recommendations": {},
                "file_types": {},
                "total_deletable_size": 0
            }
            
            for file_info in files_scanned:
                # Determine category based on path
                category = self._categorize_file(file_info.get("path", ""))
                categories.add(category)
                
                # Update summary statistics
                safety = file_info.get("safety_level", "unknown")
                scan_summary["safety_levels"][safety] = scan_summary["safety_levels"].get(safety, 0) + 1
                
                recommendation = file_info.get("recommendation", "unknown")
                scan_summary["recommendations"][recommendation] = scan_summary["recommendations"].get(recommendation, 0) + 1
                
                file_type = file_info.get("extension", "unknown")
                scan_summary["file_types"][file_type] = scan_summary["file_types"].get(file_type, 0) + 1
                
                if recommendation in ["delete", "review"]:
                    scan_summary["total_deletable_size"] += file_info.get("size", 0)
            
            # Update scan record
            scan_record = ScanRecord(
                id=self.current_scan_id,
                timestamp=self.scan_start_time,
                scan_type="full",
                total_files_scanned=total_files,
                total_size_scanned=total_size,
                duration_seconds=duration,
                categories_scanned=list(categories),
                scan_summary=scan_summary,
                space_freed=space_freed,
                files_deleted=files_deleted,
                errors_count=errors,
                success=errors == 0
            )
            
            # Save updated scan record
            self.db_manager.save_scan_record(scan_record)
            
            # Save file records
            file_records = []
            for file_info in files_scanned:
                file_record = FileRecord(
                    scan_id=self.current_scan_id,
                    file_path=file_info.get("path", ""),
                    file_name=file_info.get("name", ""),
                    file_size=file_info.get("size", 0),
                    modified_time=file_info.get("modified", datetime.now()),
                    created_time=file_info.get("created", datetime.now()),
                    file_type=file_info.get("extension", ""),
                    safety_level=file_info.get("safety_level", "unknown"),
                    importance_score=file_info.get("importance_score", 50),
                    recommendation=file_info.get("recommendation", "review"),
                    category=self._categorize_file(file_info.get("path", "")),
                    was_deleted=False
                )
                file_records.append(file_record)
            
            self.db_manager.save_file_records(file_records, self.current_scan_id)
            
            # Save system snapshot
            self._save_system_snapshot()
            
            self.logger.info(f"Completed scan {self.current_scan_id}: {total_files} files, {self.format_bytes(total_size)}")
            
            scan_id = self.current_scan_id
            self.current_scan_id = None
            self.scan_start_time = None
            
            return scan_id
            
        except Exception as e:
            self.logger.error(f"Error finishing scan: {e}")
            return None

    def _categorize_file(self, file_path: str) -> str:
        """Categorize file based on its path"""
        path_lower = file_path.lower()
        
        if any(cache_dir in path_lower for cache_dir in ["/cache/", "/caches/", "/tmp/"]):
            return "cache"
        elif any(log_dir in path_lower for log_dir in ["/log/", "/logs/"]):
            return "logs"
        elif "/trash/" in path_lower or ".trash" in path_lower:
            return "trash"
        elif any(browser_dir in path_lower for browser_dir in ["/chrome/", "/firefox/", "/safari/"]):
            return "browser"
        elif any(dev_dir in path_lower for dev_dir in ["/node_modules/", "/.git/", "/build/", "/dist/"]):
            return "development"
        elif any(media_dir in path_lower for media_dir in ["/movies/", "/music/", "/pictures/", "/photos/"]):
            return "media"
        elif any(doc_dir in path_lower for doc_dir in ["/documents/", "/desktop/", "/downloads/"]):
            return "documents"
        elif any(sys_dir in path_lower for sys_dir in ["/library/", "/system/", "/usr/"]):
            return "system"
        else:
            return "other"

    def _save_system_snapshot(self) -> None:
        """Save current system snapshot to database"""
        if not self.db_manager:
            return
            
        try:
            # Get disk usage
            disk_usage = shutil.disk_usage("/")
            
            # Get platform info
            platform_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
            
            # Get memory info
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            }
            
            # Get category breakdown (simplified)
            category_breakdown = {
                "cache": 0,
                "logs": 0,
                "trash": 0,
                "browser": 0,
                "development": 0,
                "media": 0,
                "documents": 0,
                "system": 0,
                "other": 0
            }
            
            snapshot = SystemSnapshot(
                timestamp=datetime.now(),
                total_disk_space=disk_usage.total,
                used_space=disk_usage.used,
                free_space=disk_usage.free,
                platform_info=platform_info,
                memory_info=memory_info,
                category_breakdown=category_breakdown
            )
            
            self.db_manager.save_system_snapshot(snapshot)
            
        except Exception as e:
            self.logger.error(f"Error saving system snapshot: {e}")

    def get_scan_history(self, limit: int = 50) -> List[Dict]:
        """Get scan history from database"""
        if not self.db_manager:
            return []
        return self.db_manager.get_scan_history(limit)

    def get_analytics_summary(self, days: int = 30) -> Dict:
        """Get analytics summary from database"""
        if not self.db_manager:
            return {}
        return self.db_manager.get_analytics_summary(days)

    def get_top_space_consumers(self, days: int = 30, limit: int = 20) -> List[Dict]:
        """Get top space consuming files from database"""
        if not self.db_manager:
            return []
        return self.db_manager.get_top_space_consumers(days, limit)

    def mark_files_deleted(self, file_paths: List[str]) -> None:
        """Mark files as deleted in the database"""
        if self.db_manager:
            self.db_manager.mark_files_deleted(file_paths)


__all__ = ["FileAnalyzer"]
