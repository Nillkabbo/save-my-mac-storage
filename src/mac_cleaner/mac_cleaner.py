#!/usr/bin/env python3
"""
macOS Cleaner - A comprehensive system cleaning tool for macOS

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import shutil
import sys
import platform
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import psutil
from send2trash import send2trash


class MacCleaner:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.cleanable_paths = self.get_cleanable_paths()
        self.stats = {"files_identified": 0, "space_identified": 0, "errors": []}
        self.setup_logging()

    def setup_logging(self):
        log_dir = Path.home() / ".mac_cleaner_logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"cleaner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def get_accurate_disk_usage(self) -> Dict:
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

    def get_system_info(self) -> Dict:
        """Get comprehensive system information."""
        import platform

        # Get accurate disk usage
        disk_info = self.get_accurate_disk_usage()
        total_space = disk_info["total"]
        used_space = disk_info["used"]
        free_space = disk_info["free"]
        usage_percent = disk_info["usage_percent"]

        # Memory info
        memory = psutil.virtual_memory()

        return {
            "platform": platform.system(),
            "macos_version": platform.mac_ver()[0],
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "total_memory": memory.total,
            "total_memory_human": self.format_bytes(memory.total),
            "total_space": total_space,
            "total_space_human": self.format_bytes(total_space),
            "used_space": used_space,
            "used_space_human": self.format_bytes(used_space),
            "free_space": free_space,
            "free_space_human": self.format_bytes(free_space),
            "disk_usage_percent": round(usage_percent, 1),
        }

    def get_cleanable_paths(self) -> Dict[str, List[str]]:
        home = Path.home()
        return {
            "user_cache": [str(home / "Library" / "Caches"), str(home / ".cache")],
            "system_cache": ["/Library/Caches", "/System/Library/Caches"],
            "temp_files": [
                "/tmp",
                str(
                    home
                    / "Library"
                    / "Application Support"
                    / "com.apple.sharedfilelist"
                    / "com.apple.LSSharedFileList.ApplicationRecentDocuments"
                ),
            ],
            "logs": [str(home / "Library" / "Logs"), "/Library/Logs"],
            "trash": [str(home / ".Trash")],
            "browser_cache": [
                str(home / "Library" / "Caches" / "Google" / "Chrome"),
                str(home / "Library" / "Caches" / "Firefox"),
                str(home / "Library" / "Caches" / "com.apple.Safari"),
            ],
        }

    def get_directory_size(self, path: str) -> int:
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

    def get_disk_usage(self) -> Dict:
        """Get disk usage information"""
        disk_info = self.get_accurate_disk_usage()
        return {
            "total_gb": disk_info["total"] / (1024**3),
            "used_gb": disk_info["used"] / (1024**3),
            "free_gb": disk_info["free"] / (1024**3),
            "usage_percent": disk_info["usage_percent"],
        }

    def analyze_cleanable_space(self) -> Dict[str, Dict]:
        analysis = {}
        for category, paths in self.cleanable_paths.items():
            category_size = 0
            category_details = []
            for path in paths:
                if os.path.exists(path):
                    size = self.get_directory_size(path)
                    category_size += size
                    category_details.append(
                        {
                            "path": path,
                            "size": size,
                            "size_human": self.format_bytes(size),
                        }
                    )
            analysis[category] = {
                "total_size": category_size,
                "total_size_human": self.format_bytes(category_size),
                "details": category_details,
            }
        return analysis

    def format_bytes(self, bytes_size) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def analyze_category(
        self, category: str, dry_run: bool = True, progress=None
    ) -> Dict:
        """Analyze a specific category for potential savings (Read-Only)"""
        self.logger.info(f"🔍 ANALYZING category: {category} (read-only mode)")

        if not dry_run:
            self.logger.warning(
                "⚠️  Live cleaning is disabled - running in analysis mode only"
            )
            dry_run = True

        paths = self.cleanable_paths.get(category, [])
        if not paths:
            return {
                "files_identified": 0,
                "space_identified": 0,
                "space_identified_human": "0 B",
                "error": "Category not found",
            }

        total_files = 0
        total_size = 0
        results = []

        for path in paths:
            if progress:
                progress()

            try:
                path_obj = Path(path)
                if not path_obj.exists():
                    continue

                # Only analyze, never delete
                size = self._get_directory_size(path_obj)
                file_count = len([f for f in path_obj.rglob("*") if f.is_file()])

                total_files += file_count
                total_size += size

                results.append(
                    {
                        "path": path,
                        "size": size,
                        "size_human": self.format_bytes(size),
                        "files_found": file_count,
                        "action": "analyzed_only",
                    }
                )

                self.logger.info(
                    f"📊 Analyzed {path}: {file_count} files, {self.format_bytes(size)}"
                )

            except Exception as e:
                self.logger.error(f"Error analyzing {path}: {e}")
                results.append({"path": path, "error": str(e)})

        return {
            "category": category,
            "files_identified": total_files,
            "space_identified": total_size,
            "space_identified_human": self.format_bytes(total_size),
            "files_analyzed": total_files,
            "space_analyzed": total_size,
            "space_analyzed_human": self.format_bytes(total_size),
            "paths_analyzed": results,
            "mode": "read_only_analysis",
            "files_deleted": 0,  # Backward compatibility
            "space_freed": 0,    # Backward compatibility
        }

    def _get_directory_size(self, path: Path) -> int:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, PermissionError):
                    continue
        return total_size

    def analyze_all(self, dry_run: bool = True) -> Dict:
        """Analyze all categories for potential savings (Read-Only)"""
        self.logger.info("🔍 ANALYZING all categories (read-only mode)")

        if not dry_run:
            self.logger.warning(
                "⚠️  Live cleaning is disabled - running in analysis mode only"
            )
            dry_run = True

        results = {}
        total_files = 0
        total_space = 0

        for category in self.cleanable_paths.keys():
            result = self.analyze_category(category, dry_run)
            results[category] = result
            total_files += result.get("files_analyzed", 0)
            total_space += result.get("space_analyzed", 0)

        return {
            "categories": results,
            "total_files": total_files,
            "total_space": total_space,
            "total_space_human": self.format_bytes(total_space),
            "files_analyzed": total_files,
            "space_analyzed": total_space,
            "space_analyzed_human": self.format_bytes(total_space),
            "mode": "read_only_analysis",
            "files_deleted": 0,  # Backward compatibility
            "space_freed": 0,    # Backward compatibility
        }

    # Backward compatibility aliases
    clean_category = analyze_category
    clean_all = analyze_all


def main():
    print("🍎 macOS Cleaner")
    print("=" * 50)

    cleaner = MacCleaner()

    print(f"System: {cleaner.system_info['platform']} {cleaner.system_info['release']}")
    print(f"Total Memory: {cleaner.format_bytes(cleaner.system_info['total_memory'])}")
    print(f"Disk Space: {cleaner.format_bytes(cleaner.system_info['disk_usage'])}")
    print()

    print("📊 Analyzing cleanable space...")
    analysis = cleaner.analyze_cleanable_space()

    total_cleanable = 0
    for category, info in analysis.items():
        if info["total_size"] > 0:
            print(f"{category.replace('_', ' ').title()}: {info['total_size_human']}")
            total_cleanable += info["total_size"]

    print(f"\nTotal space that can be freed: {cleaner.format_bytes(total_cleanable)}")

    choice = input("\nDo you want to proceed with cleaning? (y/N): ").lower().strip()

    if choice == "y":
        confirm = input("This will permanently delete files. Are you sure? (y/N): ")
        if confirm.lower().strip() == "y":
            print("\n📊 Analyzing...")
            results = cleaner.analyze_all(dry_run=True)
            print("\n✅ Analysis complete!")
            print(f"Files identified: {results['total_files']}")
            print(f"Potential savings: {results['total_space_human']}")

            if cleaner.stats["errors"]:
                print(f"\n⚠️  Errors encountered: {len(cleaner.stats['errors'])}")
                for error in cleaner.stats["errors"][:5]:
                    print(f"  - {error}")
        else:
            print("Cancelled.")
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()
