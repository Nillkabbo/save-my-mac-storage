#!/usr/bin/env python3
"""
Privilege management for macOS Cleaner.
Handles privilege escalation and elevation safely.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path
from typing import Tuple, Optional


class PrivilegeManager:
    """Manages privilege escalation and elevation safely"""

    def __init__(self):
        self.current_user = getpass.getuser()
        self.is_root = self.is_running_as_root()

    @staticmethod
    def is_running_as_root() -> bool:
        """
        Check if the current process is running as root.
        
        Returns:
            True if running as root, False otherwise
        """
        return os.geteuid() == 0

    def requires_sudo(self, path: str) -> bool:
        """
        Check if a path requires sudo privileges to access.
        
        Args:
            path: The path to check
            
        Returns:
            True if sudo is required, False otherwise
        """
        try:
            resolved_path = Path(path).expanduser().resolve()
            
            # Check if path exists and is writable
            if not resolved_path.exists():
                # For non-existent paths, check parent directory
                parent = resolved_path.parent
                if not parent.exists():
                    return True  # Parent doesn't exist, likely needs sudo
                return not os.access(parent, os.W_OK)
            
            # Check if we can write to the path
            if resolved_path.is_file():
                return not os.access(resolved_path, os.W_OK)
            elif resolved_path.is_dir():
                return not os.access(resolved_path, os.W_OK)
            
            return True
            
        except (OSError, PermissionError):
            return True

    def can_write_to_path(self, path: str) -> bool:
        """
        Check if we can write to a given path.
        
        Args:
            path: The path to check
            
        Returns:
            True if writable, False otherwise
        """
        try:
            resolved_path = Path(path).expanduser().resolve()
            
            if not resolved_path.exists():
                # Check parent directory for non-existent paths
                parent = resolved_path.parent
                if not parent.exists():
                    return False
                return os.access(parent, os.W_OK)
            
            return os.access(resolved_path, os.W_OK)
            
        except (OSError, PermissionError):
            return False

    def prompt_for_elevation(self, operation: str = "perform this operation") -> bool:
        """
        Prompt the user for privilege elevation with clear explanation.
        
        Args:
            operation: Description of the operation requiring elevation
            
        Returns:
            True if user agrees to elevation, False otherwise
        """
        if self.is_root:
            return True
        
        print(f"\n🔐 Privilege Elevation Required")
        print(f"Operation: {operation}")
        print(f"Current user: {self.current_user}")
        print("\nThis operation requires administrator privileges.")
        print("You will be prompted for your password to continue.")
        
        try:
            response = input("\nDo you want to continue? [y/N]: ").strip().lower()
            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return False

    def elevate_privileges(self, operation: str = "perform this operation") -> bool:
        """
        Safely elevate privileges using sudo.
        
        Args:
            operation: Description of the operation requiring elevation
            
        Returns:
            True if elevation successful, False otherwise
        """
        if self.is_root:
            return True
        
        if not self.prompt_for_elevation(operation):
            return False
        
        try:
            # Use sudo to re-run the current script with elevated privileges
            script_path = sys.argv[0] if sys.argv else sys.executable
            args = [script_path] + sys.argv[1:]
            
            print(f"\nRequesting administrator privileges...")
            result = subprocess.run(
                ['sudo'] + args,
                check=True,
                capture_output=False,
                text=True
            )
            
            # If we get here, the elevated process completed successfully
            sys.exit(0)
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to elevate privileges: {e}")
            return False
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False
        except Exception as e:
            print(f"Unexpected error during privilege elevation: {e}")
            return False

    def check_and_handle_privileges(self, path: str, operation: str = "access this path") -> Tuple[bool, str]:
        """
        Check privileges for a path and handle elevation if needed.
        
        Args:
            path: The path to check
            operation: Description of the operation
            
        Returns:
            Tuple of (success, message)
        """
        if self.can_write_to_path(path):
            return True, "Sufficient privileges"
        
        if self.requires_sudo(path):
            if not self.prompt_for_elevation(f"{operation} at {path}"):
                return False, "Privilege elevation declined by user"
            
            if not self.elevate_privileges(f"{operation} at {path}"):
                return False, "Failed to elevate privileges"
            
            return True, "Privileges elevated successfully"
        
        return False, "Insufficient privileges and elevation not available"

    def get_safe_working_directory(self) -> str:
        """
        Get a safe working directory that doesn't require elevated privileges.
        
        Returns:
            Path to a safe working directory
        """
        # Prefer user home directory
        home = Path.home()
        
        # Try common safe directories
        safe_dirs = [
            home / ".mac_cleaner_workspace",
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            home,
        ]
        
        for safe_dir in safe_dirs:
            try:
                safe_dir.mkdir(exist_ok=True)
                if self.can_write_to_path(str(safe_dir)):
                    return str(safe_dir)
            except (OSError, PermissionError):
                continue
        
        # Fallback to temporary directory
        import tempfile
        temp_dir = tempfile.gettempdir()
        return temp_dir

    def warn_about_risks(self, operation: str) -> None:
        """
        Display warning about running with elevated privileges.
        
        Args:
            operation: Description of the operation
        """
        if self.is_root:
            print("\n⚠️  WARNING: Running with elevated privileges")
            print(f"Operation: {operation}")
            print("\nRunning as root can be dangerous. Be careful with:")
            print("- File deletions (cannot be undone)")
            print("- System modifications")
            print("- Directory permissions")
            print("\nOnly proceed if you understand the risks.")


# Global instance
_privilege_manager = None


def get_privilege_manager() -> PrivilegeManager:
    """Get the global privilege manager instance."""
    global _privilege_manager
    if _privilege_manager is None:
        _privilege_manager = PrivilegeManager()
    return _privilege_manager


def check_privileges_for_path(path: str, operation: str = "access this path") -> Tuple[bool, str]:
    """
    Convenience function to check privileges for a path.
    
    Args:
        path: The path to check
        operation: Description of the operation
        
    Returns:
        Tuple of (success, message)
    """
    manager = get_privilege_manager()
    return manager.check_and_handle_privileges(path, operation)


__all__ = [
    "PrivilegeManager",
    "get_privilege_manager", 
    "check_privileges_for_path",
]
