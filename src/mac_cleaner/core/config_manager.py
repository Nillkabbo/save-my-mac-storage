#!/usr/bin/env python3
"""
Enhanced configuration management for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from ..interfaces import ConfigInterface


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
class PluginConfig:
    """Plugin configuration settings."""

    enabled_plugins: List[str] = field(default_factory=list)
    disabled_plugins: List[str] = field(default_factory=list)
    plugin_directories: List[str] = field(
        default_factory=lambda: [
            "src.mac_cleaner.plugins",
            "mac_cleaner_plugins",
        ]
    )
    auto_discover: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    file_enabled: bool = True
    console_enabled: bool = True
    log_dir: str = "~/.mac_cleaner_logs"
    max_log_files: int = 10
    max_log_size_mb: int = 10


@dataclass
class CleanerConfig:
    """Main cleaner configuration."""

    security: SecurityConfig = field(default_factory=SecurityConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    web: WebConfig = field(default_factory=WebConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # General settings
    dry_run_default: bool = True
    verbose: bool = False
    parallel_operations: bool = True
    max_workers: int = 4


class ConfigurationManager(ConfigInterface):
    """Enhanced configuration manager implementing ConfigInterface."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.config = CleanerConfig()
        self._dirty = False
        
        # Load configuration if file exists
        if Path(self.config_file).exists():
            self.load(self.config_file)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        try:
            keys = key.split('.')
            obj = self.config
            
            # Navigate to the parent object
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    # Create nested dict if needed
                    if not hasattr(obj, '__dict__'):
                        setattr(obj, k, {})
                    obj = getattr(obj, k)
            
            # Set the final value
            setattr(obj, keys[-1], value)
            self._dirty = True
            
        except Exception as e:
            raise ValueError(f"Failed to set config key '{key}': {e}")
    
    def load(self, source: Union[str, Dict[str, Any]]) -> None:
        """Load configuration from source."""
        if isinstance(source, str):
            # Load from file
            path = Path(source).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {source}")
            
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
        else:
            # Load from dictionary
            data = source
        
        # Update configuration object
        self._update_config_from_dict(data)
        self._dirty = False
    
    def save(self, target: Optional[str] = None) -> None:
        """Save configuration to target."""
        if target is None:
            target = self.config_file
        
        path = Path(target).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dictionary
        data = asdict(self.config)
        
        # Save based on file extension
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == '.json':
                json.dump(data, f, indent=2)
            else:
                # Default to YAML
                yaml.dump(data, f, default_flow_style=False, indent=2)
        
        self._dirty = False
    
    def validate(self) -> bool:
        """Validate configuration."""
        try:
            # Validate security config
            if self.config.security.max_file_size_mb <= 0:
                return False
            
            # Validate backup config
            if self.config.backup.max_backup_age_days < 0:
                return False
            
            # Validate web config
            if not (1 <= self.config.web.port <= 65535):
                return False
            
            # Validate logging config
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.config.logging.level not in valid_levels:
                return False
            
            # Validate general config
            if self.config.max_workers <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return asdict(self.config)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = CleanerConfig()
        self._dirty = True
    
    def merge(self, other_config: Union['ConfigurationManager', Dict[str, Any]]) -> None:
        """Merge with another configuration."""
        if isinstance(other_config, ConfigurationManager):
            other_data = other_config.get_all()
        else:
            other_data = other_config
        
        self._update_config_from_dict(other_data)
        self._dirty = True
    
    def _get_default_config_file(self) -> str:
        """Get default configuration file path."""
        config_dir = Path.home() / ".config" / "mac_cleaner"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.yaml")
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration object from dictionary."""
        if 'security' in data:
            self._update_dataclass(self.config.security, data['security'])
        
        if 'backup' in data:
            self._update_dataclass(self.config.backup, data['backup'])
        
        if 'web' in data:
            self._update_dataclass(self.config.web, data['web'])
        
        if 'plugins' in data:
            self._update_dataclass(self.config.plugins, data['plugins'])
        
        if 'logging' in data:
            self._update_dataclass(self.config.logging, data['logging'])
        
        # Update general settings
        for key, value in data.items():
            if hasattr(self.config, key) and key not in ['security', 'backup', 'web', 'plugins', 'logging']:
                setattr(self.config, key, value)
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update a dataclass object from dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    @property
    def is_dirty(self) -> bool:
        """Check if configuration has been modified."""
        return self._dirty


# Global configuration instance
_global_config: Optional[ConfigurationManager] = None


def get_config() -> ConfigurationManager:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = ConfigurationManager()
    return _global_config


def set_config(config: ConfigurationManager) -> None:
    """Set global configuration instance."""
    global _global_config
    _global_config = config
