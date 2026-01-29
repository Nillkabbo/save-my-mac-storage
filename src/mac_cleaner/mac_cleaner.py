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
        self.stats = {"files_deleted": 0, "space_freed": 0, "errors": []}
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

    def get_system_info(self) -> Dict:
        return {
            "platform": platform.system(),
            "release": platform.mac_ver()[0],
            "processor": platform.processor(),
            "total_memory": psutil.virtual_memory().total,
            "disk_usage": psutil.disk_usage("/").total,
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
        disk = psutil.disk_usage("/")
        return {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "usage_percent": (disk.used / disk.total) * 100,
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

    def clean_directory(self, path: str, dry_run: bool = True) -> Tuple[int, int]:
        files_deleted = 0
        space_freed = 0

        if not os.path.exists(path):
            return files_deleted, space_freed

        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isfile(item_path):
                        file_size = os.path.getsize(item_path)
                        if not dry_run:
                            send2trash(item_path)
                        files_deleted += 1
                        space_freed += file_size
                        self.logger.info(
                            f"{'[DRY RUN] ' if dry_run else ''}Deleted file: {item_path}"
                        )
                    elif os.path.isdir(item_path):
                        dir_size = self.get_directory_size(item_path)
                        if not dry_run:
                            send2trash(item_path)
                        files_deleted += 1
                        space_freed += dir_size
                        self.logger.info(
                            f"{'[DRY RUN] ' if dry_run else ''}Deleted directory: {item_path}"
                        )
                except (OSError, PermissionError) as e:
                    self.stats["errors"].append(f"Error deleting {item_path}: {str(e)}")
        except (OSError, PermissionError) as e:
            self.stats["errors"].append(f"Error accessing {path}: {str(e)}")
        return files_deleted, space_freed

    def clean_category(self, category: str, dry_run: bool = True) -> Dict:
        if category not in self.cleanable_paths:
            return {"error": f"Unknown category: {category}"}

        result = {"files_deleted": 0, "space_freed": 0, "paths_cleaned": []}

        for path in self.cleanable_paths[category]:
            if os.path.exists(path):
                files, space = self.clean_directory(path, dry_run)
                result["files_deleted"] += files
                result["space_freed"] += space
                result["paths_cleaned"].append(path)

        return result

    def clean_all(self, dry_run: bool = True) -> Dict:
        results = {}
        total_files = 0
        total_space = 0

        for category in self.cleanable_paths.keys():
            result = self.clean_category(category, dry_run)
            results[category] = result
            total_files += result.get("files_deleted", 0)
            total_space += result.get("space_freed", 0)

        return {
            "categories": results,
            "total_files": total_files,
            "total_space": total_space,
            "total_space_human": self.format_bytes(total_space),
        }


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
            print("\n🧹 Cleaning...")
            results = cleaner.clean_all(dry_run=False)
            print("\n✅ Cleaning complete!")
            print(f"Files deleted: {results['total_files']}")
            print(f"Space freed: {results['total_space_human']}")

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
