#!/usr/bin/env python3
"""
Tests for configuration management.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import tempfile
import os
import yaml
from pathlib import Path
from mac_cleaner.config_manager import (
    ConfigManager,
    CleanerConfig,
    SecurityConfig,
    BackupConfig,
    WebConfig,
    LoggingConfig,
    get_config,
    get_config_manager,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "security": {"require_confirmation": False, "max_file_size_mb": 500},
            "backup": {"enabled": False, "backup_dir": "/tmp/test_backup"},
            "web": {"port": 8080, "host": "0.0.0.0"},
            "logging": {"level": "DEBUG"},
            "dry_run_default": False,
        }
        yaml.dump(config_data, f)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def config_manager(temp_config_file):
    """Create a ConfigManager instance with temporary config file."""
    return ConfigManager(temp_config_file)


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        manager = ConfigManager()
        config = manager.get_config()

        assert isinstance(config, CleanerConfig)
        assert config.security.require_confirmation is True
        assert config.backup.enabled is True
        assert config.web.port == 5000
        assert config.logging.level == "INFO"

    def test_load_custom_config(self, config_manager):
        """Test loading custom configuration from file."""
        config = config_manager.get_config()

        assert config.security.require_confirmation is False
        assert config.security.max_file_size_mb == 500
        assert config.backup.enabled is False
        assert config.backup.backup_dir == "/tmp/test_backup"
        assert config.web.port == 8080
        assert config.web.host == "0.0.0.0"
        assert config.logging.level == "DEBUG"
        assert config.dry_run_default is False

    def test_save_config(self, config_manager):
        """Test saving configuration to file."""
        config = config_manager.get_config()
        config.security.require_confirmation = True
        config.security.max_file_size_mb = 2000

        success = config_manager.save_config(config)
        assert success

        # Reload and verify
        new_manager = ConfigManager(config_manager.config_file)
        new_config = new_manager.get_config()

        assert new_config.security.require_confirmation is True
        assert new_config.security.max_file_size_mb == 2000

    def test_update_config(self, config_manager):
        """Test updating configuration values."""
        success = config_manager.update_config(
            dry_run_default=False, security_require_confirmation=True
        )
        assert success

        config = config_manager.get_config()
        assert config.dry_run_default is False
        assert config.security.require_confirmation is True

    def test_reset_to_defaults(self, config_manager):
        """Test resetting configuration to defaults."""
        # Modify config
        config = config_manager.get_config()
        config.security.require_confirmation = False

        # Reset
        success = config_manager.reset_to_defaults()
        assert success

        # Verify reset
        new_config = config_manager.get_config()
        assert new_config.security.require_confirmation is True

    def test_validate_config_valid(self, config_manager):
        """Test validation of valid configuration."""
        issues = config_manager.validate_config()
        assert len(issues) == 0

    def test_validate_config_invalid(self, config_manager):
        """Test validation of invalid configuration."""
        config = config_manager.get_config()
        config.security.max_file_size_mb = -100
        config.web.port = 70000
        config.logging.level = "INVALID"

        issues = config_manager.validate_config()
        assert len(issues) >= 3
        assert any("max_file_size_mb" in issue for issue in issues)
        assert any("port" in issue for issue in issues)
        assert any("level" in issue for issue in issues)

    def test_environment_overrides(self, config_manager):
        """Test environment variable overrides."""
        # Set environment variables
        os.environ["MAC_CLEANER_REQUIRE_CONFIRMATION"] = "false"
        os.environ["MAC_CLEANER_MAX_FILE_SIZE_MB"] = "2000"
        os.environ["MAC_CLEANER_WEB_PORT"] = "8080"
        os.environ["MAC_CLEANER_LOG_LEVEL"] = "DEBUG"

        try:
            overrides = config_manager.get_environment_overrides()

            assert overrides["security_require_confirmation"] is False
            assert overrides["security_max_file_size_mb"] == 2000
            assert overrides["web_port"] == 8080
            assert overrides["logging_level"] == "DEBUG"
        finally:
            # Clean up environment
            for key in [
                "MAC_CLEANER_REQUIRE_CONFIRMATION",
                "MAC_CLEANER_MAX_FILE_SIZE_MB",
                "MAC_CLEANER_WEB_PORT",
                "MAC_CLEANER_LOG_LEVEL",
            ]:
                if key in os.environ:
                    del os.environ[key]

    def test_apply_environment_overrides(self, config_manager):
        """Test applying environment variable overrides."""
        # Set environment variables
        os.environ["MAC_CLEANER_REQUIRE_CONFIRMATION"] = "false"
        os.environ["MAC_CLEANER_WEB_PORT"] = "8080"

        try:
            config_manager.apply_environment_overrides()
            config = config_manager.get_config()

            assert config.security.require_confirmation is False
            assert config.web.port == 8080
        finally:
            # Clean up environment
            for key in ["MAC_CLEANER_REQUIRE_CONFIRMATION", "MAC_CLEANER_WEB_PORT"]:
                if key in os.environ:
                    del os.environ[key]

    def test_backup_path_expansion(self):
        """Test backup path expansion with ~."""
        manager = ConfigManager()
        config = manager.get_config()

        # Should expand ~ to full home path
        assert not config.backup.backup_dir.startswith("~")
        assert str(Path.home()) in config.backup.backup_dir


class TestConfigDataclasses:
    """Test configuration dataclasses."""

    def test_security_config_defaults(self):
        """Test SecurityConfig default values."""
        config = SecurityConfig()
        assert config.require_confirmation is True
        assert config.allow_system_paths is False
        assert config.max_file_size_mb == 1000
        assert len(config.protected_paths) > 0

    def test_backup_config_defaults(self):
        """Test BackupConfig default values."""
        config = BackupConfig()
        assert config.enabled is True
        assert config.backup_dir == "~/.mac_cleaner_backup"
        assert config.max_backup_age_days == 30
        assert config.auto_cleanup is True

    def test_web_config_defaults(self):
        """Test WebConfig default values."""
        config = WebConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 5000
        assert config.secret_key is None
        assert config.csrf_enabled is True
        assert config.rate_limit == "100 per hour"

    def test_logging_config_defaults(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.log_file is None
        assert config.max_log_size_mb == 10
        assert config.backup_count == 5

    def test_cleaner_config_defaults(self):
        """Test CleanerConfig default values."""
        config = CleanerConfig()
        assert config.dry_run_default is True
        assert len(config.categories_enabled) > 0
        assert "cache" in config.categories_enabled
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.backup, BackupConfig)
        assert isinstance(config.web, WebConfig)
        assert isinstance(config.logging, LoggingConfig)


class TestGlobalConfigManager:
    """Test global configuration manager functions."""

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns the same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_get_config_function(self):
        """Test get_config function."""
        config = get_config()
        assert isinstance(config, CleanerConfig)
        assert config.security.require_confirmation is True
