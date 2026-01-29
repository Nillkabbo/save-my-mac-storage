#!/usr/bin/env python3
"""
Safety Manager for macOS Cleaner - Provides backup and safety features

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
import hashlib


class SafetyManager:
    def __init__(self):
        self.backup_dir = Path.home() / ".mac_cleaner_backup"
        self.backup_dir.mkdir(exist_ok=True)
        self.manifest_file = self.backup_dir / "backup_manifest.json"
        self.protected_paths = self.get_protected_paths()
        self.current_session = self.create_session()

    def get_protected_paths(self) -> Set[str]:
        """Get list of paths that should never be touched"""
        return {
            "/System",
            "/System/Library",
            "/usr",
            "/bin",
            "/sbin",
            "/etc",
            "/var/root",
            "/Applications",
            "/Library/Preferences",
            "/Library/Keychains",
            "/Users/Shared",
            "/Network",
            "/automount",
            "/bin",
            "/cores",
            "/dev",
            "/home",
            "/net",
            "/private",
            "/sbin",
            "/var",
        }

    def create_session(self) -> str:
        """Create a unique session ID for this cleaning session"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def is_path_safe(self, path: str) -> bool:
        """Check if a path is safe to clean"""
        path = os.path.abspath(path)

        for protected in self.protected_paths:
            if path.startswith(protected):
                return False

        dangerous_extensions = {".app", ".kext", ".driver", ".plugin", ".bundle"}

        if any(path.endswith(ext) for ext in dangerous_extensions):
            return False

        return True

    def create_backup(self, file_path: str) -> bool:
        """Create backup of a file before deletion"""
        try:
            if not os.path.exists(file_path):
                return False

            relative_path = os.path.relpath(file_path, "/")
            backup_path = self.backup_dir / self.current_session / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            if os.path.isfile(file_path):
                shutil.copy2(file_path, backup_path)
            elif os.path.isdir(file_path):
                shutil.copytree(file_path, backup_path, dirs_exist_ok=True)

            self.update_manifest(file_path, str(backup_path))
            return True

        except Exception as e:
            print(f"Backup failed for {file_path}: {e}")
            return False

    def update_manifest(self, original_path: str, backup_path: str):
        """Update backup manifest with file information"""
        manifest = self.load_manifest()

        file_info = {
            "original_path": original_path,
            "backup_path": str(backup_path),
            "timestamp": datetime.now().isoformat(),
            "session": self.current_session,
            "size": self.get_size(original_path),
            "checksum": (
                self.calculate_checksum(original_path)
                if os.path.isfile(original_path)
                else ""
            ),
        }

        manifest["backups"].append(file_info)
        self.save_manifest(manifest)

    def load_manifest(self) -> Dict:
        """Load backup manifest"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r") as f:
                    return json.load(f)
            except:
                pass

        return {"backups": [], "sessions": {}}

    def save_manifest(self, manifest: Dict):
        """Save backup manifest"""
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

    def get_size(self, path: str) -> int:
        """Get size of file or directory"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        if os.path.isdir(path):
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except:
                        continue
            return total
        return 0

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""

    def restore_backup(self, session_id: Optional[str] = None) -> bool:
        """Restore files from backup"""
        if session_id is None:
            session_id = self.current_session

        session_backup_dir = self.backup_dir / session_id
        if not session_backup_dir.exists():
            return False

        manifest = self.load_manifest()
        restored_files = 0

        for backup_info in manifest["backups"]:
            if backup_info["session"] == session_id:
                original_path = backup_info["original_path"]
                backup_path = backup_info["backup_path"]

                try:
                    if os.path.exists(backup_path):
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)

                        if os.path.isfile(backup_path):
                            shutil.copy2(backup_path, original_path)
                        elif os.path.isdir(backup_path):
                            if os.path.exists(original_path):
                                shutil.rmtree(original_path)
                            shutil.copytree(backup_path, original_path)

                        restored_files += 1

                except Exception as e:
                    print(f"Restore failed for {original_path}: {e}")

        return restored_files > 0

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        manifest = self.load_manifest()
        sessions = {}

        for backup in manifest["backups"]:
            session = backup["session"]
            if session not in sessions:
                sessions[session] = {
                    "session_id": session,
                    "files": [],
                    "total_size": 0,
                    "timestamp": backup["timestamp"],
                }

            sessions[session]["files"].append(backup)
            sessions[session]["total_size"] += backup.get("size", 0)

        return list(sessions.values())

    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Clean up old backup sessions"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        manifest = self.load_manifest()

        sessions_to_remove = set()
        for backup in manifest["backups"]:
            backup_time = datetime.fromisoformat(backup["timestamp"]).timestamp()
            if backup_time < cutoff_date:
                sessions_to_remove.add(backup["session"])

        for session_id in sessions_to_remove:
            session_dir = self.backup_dir / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)

        manifest["backups"] = [
            b for b in manifest["backups"] if b["session"] not in sessions_to_remove
        ]
        self.save_manifest(manifest)

        return len(sessions_to_remove)


class FileValidator:
    """Validates files before deletion"""

    CRITICAL_FILES = {
        ".bash_profile",
        ".bashrc",
        ".zshrc",
        ".profile",
        ".ssh",
        ".gnupg",
        ".config",
        "Library/Preferences",
        "Library/Keychains",
        "Application Support",
    }

    @staticmethod
    def is_critical_file(file_path: str) -> bool:
        """Check if file is critical and shouldn't be deleted"""
        path_parts = file_path.split("/")

        for critical in FileValidator.CRITICAL_FILES:
            if critical in path_parts:
                return True

        return False

    @staticmethod
    def is_recently_modified(file_path: str, days: int = 7) -> bool:
        """Check if file was modified recently"""
        try:
            mtime = os.path.getmtime(file_path)
            return (datetime.now().timestamp() - mtime) < (days * 24 * 60 * 60)
        except:
            return False

    @staticmethod
    def is_large_file(file_path: str, size_mb: int = 100) -> bool:
        """Check if file is large"""
        try:
            return os.path.getsize(file_path) > (size_mb * 1024 * 1024)
        except:
            return False


__all__ = ["SafetyManager", "FileValidator"]
