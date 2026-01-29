"""
Space Analyzer - Shows what's taking up space and what's safe to remove
Provides analysis and recommendations for disk optimization.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import psutil
from typing import List, Dict, Tuple, Optional
import shutil


class SpaceAnalyzer:
    def __init__(self):
        self.home = Path.home()
        self.recommendations = []
        self.large_files = []
        self.old_files = []

    def get_folder_size(self, path: Path) -> int:
        """Get size of a folder in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, PermissionError):
                        continue
            return total_size
        except (OSError, PermissionError):
            return 0

    def format_bytes(self, bytes_size) -> str:
        """Format bytes in human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def get_file_age_days(self, filepath: Path) -> int:
        """Get file age in days"""
        try:
            mtime = os.path.getmtime(filepath)
            file_date = datetime.fromtimestamp(mtime)
            age = (datetime.now() - file_date).days
            return age
        except (OSError, PermissionError):
            return 0

    def analyze_user_directories(self) -> Dict:
        """Analyze common user directories for space usage"""
        print("🔍 Analyzing user directories...")

        analysis = {"total_size": 0, "directories": {}, "recommendations": []}

        key_dirs = {
            "Desktop": self.home / "Desktop",
            "Documents": self.home / "Documents",
            "Downloads": self.home / "Downloads",
            "Movies": self.home / "Movies",
            "Music": self.home / "Music",
            "Pictures": self.home / "Pictures",
            "Library/Caches": self.home / "Library" / "Caches",
            "Library/Logs": self.home / "Library" / "Logs",
            "Library/Application Support": self.home
            / "Library"
            / "Application Support",
            "Library/Containers": self.home / "Library" / "Containers",
            "Library/Group Containers": self.home / "Library" / "Group Containers",
            "Library/Developer": self.home / "Library" / "Developer",
        }

        for name, path in key_dirs.items():
            if path.exists():
                size = self.get_folder_size(path)
                analysis["directories"][name] = {
                    "path": str(path),
                    "size": size,
                    "size_human": self.format_bytes(size),
                    "safe_to_delete": self.is_safe_to_delete(name, path),
                    "recommendation": self.get_recommendation(name, path, size),
                }
                analysis["total_size"] += size

                if size > 1024**3:
                    analysis["recommendations"].append(
                        {
                            "location": str(path),
                            "size_human": self.format_bytes(size),
                            "reason": f"Large directory ({name})",
                            "action": "Review contents",
                            "priority": "high" if size > 5 * 1024**3 else "medium",
                        }
                    )

        return analysis

    def is_safe_to_delete(self, name: str, path: Path) -> bool:
        """Determine if a directory is generally safe to delete"""
        safe_patterns = [
            "Caches",
            "Logs",
            "Temp",
            "Cache",
            "tmp",
            ".cache",
            "Application Support",
            "Containers",
            "Group Containers",
        ]

        dangerous_patterns = [
            "Documents",
            "Desktop",
            "Pictures",
            "Music",
            "Movies",
            "Library/Preferences",
            "Library/Keychains",
        ]

        path_str = str(path)

        for pattern in safe_patterns:
            if pattern in path_str:
                return True

        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False

        return False

    def get_recommendation(self, name: str, path: Path, size: int) -> str:
        """Get optimization recommendation for a directory"""
        if "Caches" in str(path):
            return "Safe to delete - these are temporary cache files"
        if "Logs" in str(path):
            return "Safe to delete - old log files can be removed"
        if "Temp" in str(path) or "tmp" in str(path):
            return "Safe to delete - temporary files"
        if "Application Support" in str(path):
            return "Caution - contains app data, review before deleting"
        if "Containers" in str(path):
            return "Caution - contains sandboxed app data"
        if "Downloads" in str(path):
            return "Review - delete old downloads you no longer need"
        if "Desktop" in str(path):
            return "Organize - move files to appropriate folders"
        if size > 5 * 1024**3:
            return "High priority - this directory is using significant space"
        return "Review - check if you need these files"

    def find_large_files(self, min_size_mb: int = 100) -> List[Dict]:
        """Find large files in user directory"""
        print("🔍 Finding large files...")

        large_files = []
        min_size_bytes = min_size_mb * 1024 * 1024

        search_dirs = [
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Movies",
            self.home / "Music",
            self.home / "Pictures",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        filepath = Path(root) / file
                        try:
                            size = os.path.getsize(filepath)
                            if size >= min_size_bytes:
                                large_files.append(
                                    {
                                        "path": str(filepath),
                                        "size": size,
                                        "size_human": self.format_bytes(size),
                                        "age_days": self.get_file_age_days(filepath),
                                        "type": "file",
                                    }
                                )
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        large_files.sort(key=lambda x: x["size"], reverse=True)
        return large_files[:50]

    def find_old_files(self, days_old: int = 365) -> List[Dict]:
        """Find files older than specified days"""
        print(f"🔍 Finding files older than {days_old} days...")

        old_files = []
        cutoff_date = datetime.now() - timedelta(days=days_old)

        search_dirs = [
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        filepath = Path(root) / file
                        try:
                            mtime = os.path.getmtime(filepath)
                            file_date = datetime.fromtimestamp(mtime)
                            if file_date < cutoff_date:
                                size = os.path.getsize(filepath)
                                old_files.append(
                                    {
                                        "path": str(filepath),
                                        "size": size,
                                        "size_human": self.format_bytes(size),
                                        "age_days": self.get_file_age_days(filepath),
                                        "modified_date": file_date.strftime("%Y-%m-%d"),
                                        "type": "file",
                                    }
                                )
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        old_files.sort(key=lambda x: x["age_days"], reverse=True)
        return old_files[:50]

    def get_system_cache_analysis(self) -> Dict:
        """Analyze system cache directories"""
        print("🔍 Analyzing system caches...")

        cache_dirs = [
            "/Library/Caches",
            "/System/Library/Caches",
            "/private/var/folders",
            str(self.home / "Library" / "Caches"),
            "/tmp",
            "/var/tmp",
        ]

        cache_analysis = {"total_cache_size": 0, "caches": []}

        for cache_dir in cache_dirs:
            path = Path(cache_dir)
            if path.exists():
                try:
                    size = self.get_folder_size(path)
                    cache_analysis["caches"].append(
                        {
                            "path": str(path),
                            "size": size,
                            "size_human": self.format_bytes(size),
                            "safe_to_delete": True,
                            "recommendation": "System cache - safe to clear",
                        }
                    )
                    cache_analysis["total_cache_size"] += size
                except (OSError, PermissionError):
                    cache_analysis["caches"].append(
                        {
                            "path": str(path),
                            "size": 0,
                            "size_human": "0 B",
                            "safe_to_delete": True,
                            "recommendation": "Access denied - run as sudo to clean",
                        }
                    )

        return cache_analysis

    def get_disk_usage(self) -> Dict:
        """Get accurate disk usage, prioritizing APFS Data volume over snapshots"""
        
        # First try to get APFS Data volume info (most accurate)
        data_volume_paths = [
            "/System/Volumes/Data",  # Standard APFS Data volume location
            "/Volumes/Data",         # Alternative location
        ]
        
        for data_path in data_volume_paths:
            try:
                if os.path.exists(data_path):
                    disk = psutil.disk_usage(data_path)
                    return {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "usage_percent": (disk.used / disk.total) * 100,
                        "source": f"apfs_data_{data_path.replace('/', '_')}"
                    }
            except (OSError, PermissionError):
                continue
        
        # Try diskutil as fallback for APFS containers
        import subprocess
        try:
            # Get diskutil info to find the Data volume
            result = subprocess.run(['diskutil', 'info', '/'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse diskutil output for accurate space info
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Container Total Space:' in line:
                        # Extract size from line like "Container Total Space: 245.1 GB (245107195904 Bytes)"
                        parts = line.split('(')
                        if len(parts) > 1:
                            total_bytes = int(parts[1].split(')')[0].replace(' Bytes', ''))
                            break
                else:
                    total_bytes = None
                    
                for line in lines:
                    if 'Container Free Space:' in line:
                        # Extract free space from line like "Container Free Space: 14.6 GB (14573715456 Bytes)"
                        parts = line.split('(')
                        if len(parts) > 1:
                            free_bytes = int(parts[1].split(')')[0].replace(' Bytes', ''))
                            break
                else:
                    free_bytes = None
                    
                for line in lines:
                    if 'Volume Used Space:' in line:
                        # Extract used space from line like "Volume Used Space: 12.3 GB (12271996928 Bytes)"
                        parts = line.split('(')
                        if len(parts) > 1:
                            used_bytes = int(parts[1].split(')')[0].replace(' Bytes', ''))
                            break
                else:
                    used_bytes = None
                
                if total_bytes and free_bytes is not None and used_bytes is not None:
                    return {
                        "total": total_bytes,
                        "used": used_bytes,
                        "free": free_bytes,
                        "usage_percent": (used_bytes / total_bytes) * 100,
                        "source": "diskutil"
                    }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, IndexError):
            pass
        
        # Final fallback to psutil (may show snapshot data)
        try:
            disk = psutil.disk_usage("/")
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": (disk.used / disk.total) * 100,
                "source": "psutil_fallback"
            }
        except Exception as e:
            print(f"Warning: Could not get disk usage: {e}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "usage_percent": 0,
                "source": "error"
            }

    def generate_report(self) -> Dict:
        """Generate comprehensive space analysis report"""
        print("📊 Generating space analysis report...")

        disk_info = self.get_disk_usage()

        report = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": {
                "total": disk_info["total"],
                "total_human": self.format_bytes(disk_info["total"]),
                "used": disk_info["used"],
                "used_human": self.format_bytes(disk_info["used"]),
                "free": disk_info["free"],
                "free_human": self.format_bytes(disk_info["free"]),
                "usage_percent": disk_info["usage_percent"],
                "data_source": disk_info["source"],
            },
            "user_directories": self.analyze_user_directories(),
            "large_files": self.find_large_files(),
            "old_files": self.find_old_files(),
            "system_caches": self.get_system_cache_analysis(),
            "top_recommendations": [],
        }

        all_recommendations = []

        for rec in report["user_directories"]["recommendations"]:
            all_recommendations.append(rec)

        if report["system_caches"]["total_cache_size"] > 1024**3:
            all_recommendations.append(
                {
                    "location": "System Caches",
                    "size_human": self.format_bytes(
                        report["system_caches"]["total_cache_size"]
                    ),
                    "reason": "Large system cache accumulation",
                    "action": "Clear system caches",
                    "priority": "high",
                }
            )

        priority_order = {"high": 3, "medium": 2, "low": 1}
        all_recommendations.sort(
            key=lambda x: (priority_order.get(x["priority"], 0), x["size_human"]),
            reverse=True,
        )

        report["top_recommendations"] = all_recommendations[:10]

        return report

    def print_report(self, report: Dict):
        """Print formatted report to console"""
        print("\n" + "=" * 80)
        print("🍎 MACOS SPACE ANALYSIS REPORT")
        print("=" * 80)

        disk = report["disk_usage"]
        print("\n💾 DISK USAGE:")
        print(f"   Total: {disk['total_human']}")
        print(f"   Used:  {disk['used_human']} ({disk['usage_percent']:.1f}%)")
        print(f"   Free:  {disk['free_human']}")
        print(f"   Source: {disk.get('data_source', 'Unknown')}")

        print("\n🎯 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(report["top_recommendations"], 1):
            priority_emoji = (
                "🔴"
                if rec["priority"] == "high"
                else "🟡" if rec["priority"] == "medium" else "🟢"
            )
            print(f"   {i}. {priority_emoji} {rec['location']}")
            print(f"      Size: {rec['size_human']}")
            print(f"      Action: {rec['action']}")
            print(f"      Reason: {rec['reason']}")
            print()

        print("📁 USER DIRECTORIES:")
        for name, info in report["user_directories"]["directories"].items():
            safe_emoji = "✅" if info["safe_to_delete"] else "⚠️"
            print(f"   {safe_emoji} {name}: {info['size_human']}")
            print(f"      Path: {info['path']}")
            print(f"      Recommendation: {info['recommendation']}")
            print()

        print("📄 LARGE FILES (Top 10):")
        for file in report["large_files"][:10]:
            print(f"   📄 {file['size_human']} - {file['path']}")
            print(f"      Age: {file['age_days']} days")
            print()

        print("🗑️  SYSTEM CACHES:")
        print(
            "   Total Cache Size: "
            f"{self.format_bytes(report['system_caches']['total_cache_size'])}"
        )
        for cache in report["system_caches"]["caches"]:
            if cache["size"] > 0:
                print(f"   📁 {cache['size_human']} - {cache['path']}")
                print(f"      {cache['recommendation']}")
        print()

    def save_report(self, report: Dict, filename=None):
        """Save report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"space_analysis_{timestamp}.json"

        filepath = self.home / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Report saved to: {filepath}")
        return filepath


def main():
    """Main function"""
    print("🔍 macOS Space Analyzer")
    print("=" * 50)

    analyzer = SpaceAnalyzer()

    report = analyzer.generate_report()

    analyzer.print_report(report)

    report_file = analyzer.save_report(report)

    print("\n✅ Analysis complete!")
    print(f"📄 Detailed report saved to: {report_file}")
    print("🌐 Open the report file to see exact file paths and recommendations")


if __name__ == "__main__":
    main()
