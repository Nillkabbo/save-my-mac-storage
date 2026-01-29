#!/usr/bin/env python3
"""
Configuration management for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class SecurityConfig:
    """Security configuration settings."""

    require_confirmation: bool = True
    allow_system_paths: bool = False
    max_file_size_mb: int = 1000
    protected_paths: List[str] = field(
        default_factory=lambda: [
            "/System",
            "/usr/bin",
            "/Library/Keychains",
            "/etc",
            "/var/root",
        ]
    )


@dataclass
class BackupConfig:
    """Backup configuration settings."""

    enabled: bool = True
    backup_dir: str = "~/.mac_cleaner_backup"
    max_backup_age_days: int = 30
    auto_cleanup: bool = True


@dataclass
class WebConfig:
    """Web interface configuration."""

    host: str = "127.0.0.1"
    port: int = 5000
    secret_key: Optional[str] = None
    csrf_enabled: bool = True
    rate_limit: str = "100 per hour"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    log_file: Optional[str] = None
    max_log_size_mb: int = 10
    backup_count: int = 5


@dataclass
class CleanerConfig:
    """Main configuration for macOS Cleaner."""

    security: SecurityConfig = field(default_factory=SecurityConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    web: WebConfig = field(default_factory=WebConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Cleaner-specific settings
    dry_run_default: bool = True
    categories_enabled: List[str] = field(
        default_factory=lambda: ["cache", "temp", "logs", "trash", "browser_cache"]
    )

    def __post_init__(self):
        """Post-initialization processing."""
        # Expand user paths
        if self.backup.backup_dir.startswith("~"):
            self.backup.backup_dir = str(Path(self.backup.backup_dir).expanduser())


class ConfigManager:
    """Configuration manager for macOS Cleaner."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file. If None, uses default locations.
        """
        self.config_file = self._get_config_path(config_file)
        self.config = self.load_config()

    def _get_config_path(self, config_file: Optional[str] = None) -> Path:
        """Get configuration file path."""
        if config_file:
            return Path(config_file)

        # Check for config in multiple locations
        possible_paths = [
            Path.cwd() / "mac_cleaner.yaml",
            Path.cwd() / "mac_cleaner.yml",
            Path.home() / ".mac_cleaner" / "config.yaml",
            Path.home() / ".config" / "mac_cleaner" / "config.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Return default path (will be created if needed)
        return Path.home() / ".config" / "mac_cleaner" / "config.yaml"

    def load_config(self) -> CleanerConfig:
        """Load configuration from file."""
        if not self.config_file.exists():
            # Create default config
            config = CleanerConfig()
            self.save_config(config)
            return config

        try:
            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f) or {}

            # Handle nested config structure
            if "security" in data:
                security_config = SecurityConfig(**data["security"])
            else:
                security_config = SecurityConfig()

            if "backup" in data:
                backup_config = BackupConfig(**data["backup"])
            else:
                backup_config = BackupConfig()

            if "web" in data:
                web_config = WebConfig(**data["web"])
            else:
                web_config = WebConfig()

            if "logging" in data:
                logging_config = LoggingConfig(**data["logging"])
            else:
                logging_config = LoggingConfig()

            # Extract other top-level config
            other_config = {
                k: v
                for k, v in data.items()
                if k not in ["security", "backup", "web", "logging"]
            }

            return CleanerConfig(
                security=security_config,
                backup=backup_config,
                web=web_config,
                logging=logging_config,
                **other_config,
            )

        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return CleanerConfig()

    def save_config(self, config: CleanerConfig) -> bool:
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary
            config_dict = asdict(config)

            with open(self.config_file, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_config(self) -> CleanerConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, **kwargs) -> bool:
        """Update configuration with new values."""
        try:
            for key, value in kwargs.items():
                # Handle nested configuration updates
                if key == "dry_run_default":
                    self.config.dry_run_default = value
                elif key == "security_require_confirmation":
                    self.config.security.require_confirmation = value
                elif key == "security_allow_system_paths":
                    self.config.security.allow_system_paths = value
                elif key == "security_max_file_size_mb":
                    self.config.security.max_file_size_mb = value
                elif key == "backup_enabled":
                    self.config.backup.enabled = value
                elif key == "backup_backup_dir":
                    self.config.backup.backup_dir = value
                elif key == "backup_max_backup_age_days":
                    self.config.backup.max_backup_age_days = value
                elif key == "web_host":
                    self.config.web.host = value
                elif key == "web_port":
                    self.config.web.port = value
                elif key == "web_secret_key":
                    self.config.web.secret_key = value
                elif key == "logging_level":
                    self.config.logging.level = value
                elif key == "logging_log_file":
                    self.config.logging.log_file = value
                else:
                    # Try to set as direct attribute
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                    else:
                        print(f"Unknown config key: {key}")
                        return False

            return self.save_config(self.config)
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        self.config = CleanerConfig()
        return self.save_config(self.config)

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Validate security config
        if self.config.security.max_file_size_mb < 0:
            issues.append("Security max_file_size_mb must be positive")

        # Validate backup config
        if self.config.backup.max_backup_age_days < 0:
            issues.append("Backup max_backup_age_days must be positive")

        # Validate web config
        if not (1 <= self.config.web.port <= 65535):
            issues.append("Web port must be between 1 and 65535")

        # Validate logging config
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.config.logging.level not in valid_levels:
            issues.append(f"Logging level must be one of: {valid_levels}")

        return issues

    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}

        # Security overrides
        if "MAC_CLEANER_REQUIRE_CONFIRMATION" in os.environ:
            overrides["security_require_confirmation"] = os.environ[
                "MAC_CLEANER_REQUIRE_CONFIRMATION"
            ].lower() in ["true", "1"]

        if "MAC_CLEANER_MAX_FILE_SIZE_MB" in os.environ:
            try:
                overrides["security_max_file_size_mb"] = int(
                    os.environ["MAC_CLEANER_MAX_FILE_SIZE_MB"]
                )
            except ValueError:
                pass

        # Backup overrides
        if "MAC_CLEANER_BACKUP_DIR" in os.environ:
            overrides["backup_backup_dir"] = os.environ["MAC_CLEANER_BACKUP_DIR"]

        # Web overrides
        if "MAC_CLEANER_WEB_HOST" in os.environ:
            overrides["web_host"] = os.environ["MAC_CLEANER_WEB_HOST"]

        if "MAC_CLEANER_WEB_PORT" in os.environ:
            try:
                overrides["web_port"] = int(os.environ["MAC_CLEANER_WEB_PORT"])
            except ValueError:
                pass

        if "MAC_CLEANER_SECRET_KEY" in os.environ:
            overrides["web_secret_key"] = os.environ["MAC_CLEANER_SECRET_KEY"]

        # Logging overrides
        if "MAC_CLEANER_LOG_LEVEL" in os.environ:
            overrides["logging_level"] = os.environ["MAC_CLEANER_LOG_LEVEL"]

        return overrides

    def apply_environment_overrides(self):
        """Apply environment variable overrides to configuration."""
        overrides = self.get_environment_overrides()

        for key, value in overrides.items():
            # Apply overrides using the same logic as update_config
            self.update_config(**{key: value})


# Global config manager instance
_config_manager = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config() -> CleanerConfig:
    """Get current configuration."""
    return get_config_manager().get_config()
