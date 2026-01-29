# 🍎 macOS Cleaner - Read-Only Disk Analysis Tool

> **⚠️ IMPORTANT**: This tool operates in **read-only mode** and will **NEVER delete or modify** any files on your system. It only analyzes disk usage and provides insights.

A safe, comprehensive macOS disk usage analysis tool that helps you understand what's consuming space on your Mac without any risk of data loss.

## ✨ Features

- **🔍 Read-Only Analysis**: Analyzes disk usage without any risk of data loss
- **📊 Comprehensive Analysis**: Detailed space analysis with file-level insights
- **🎯 Plugin System**: Modular analysis with specific plugins (Browser, System, Development, etc.)
- **📋 Multiple Interfaces**: CLI, GUI, and Web interfaces
- **📈 Detailed Reports**: JSON output and comprehensive logging
- **🔒 Security Focused**: Built-in path validation and safety checks
- **⚙️ Configurable**: YAML-based configuration system
- **🧪 Well Tested**: Comprehensive test coverage

## 🚀 Quick Start

### Installation

1. Clone or download the project:
```bash
git clone <repository-url>
cd mac-cleaner
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage

#### GUI Version (Recommended)
```bash
mac-cleaner gui
```

#### Command Line Version
```bash
mac-cleaner clean --dry-run --category all
```

## 📋 What It Cleans

### User Cache Files
- Application caches
- Browser caches (Chrome, Firefox, Safari)
- System user caches

### System Cache Files
- Library caches
- System caches
- Temporary files

### Log Files
- Application logs
- System logs
- Crash reports

### Other Files
- Trash contents
- Recent documents history
- Temporary downloads

## 🛡️ Safety Features

### Protected Paths
The cleaner automatically protects critical system paths:
- `/System`, `/usr`, `/bin`, `/sbin`
- `/Applications`, `/Library/Preferences`
- `/Library/Keychains`, user configuration files

### Backup System
- Automatic backup before deletion
- Session-based backup organization
- Easy restore functionality
- Backup manifest with checksums

### File Validation
- Critical file detection
- Recent modification warnings
- Large file identification

## 📊 GUI Features

- **System Information Display**: Shows macOS version, memory, and disk space
- **Space Analysis**: Detailed breakdown of cleanable space by category
- **Interactive Controls**: Clean all or selected categories
- **Dry Run Mode**: Preview deletions without actual removal
- **Real-time Progress**: Visual feedback during cleaning operations
- **Activity Log**: Scrollable log of all operations

## 🔧 Advanced Usage

### Command Line Options

```bash
# Dry run (preview only)
mac-cleaner clean --dry-run --category all

# Clean specific category
mac-cleaner clean --no-dry-run --category cache

# Analyze disk usage
mac-cleaner analyze

# Show help
mac-cleaner --help
```

### CLI Help (Excerpt)

```text
$ mac-cleaner --help
Usage: mac-cleaner [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  analyze
  clean
  detailed-gui
  gui
  web
```

### Backup Management

```python
from mac_cleaner.safety_manager import SafetyManager

# Create safety manager instance
safety = SafetyManager()

# List all backups
backups = safety.list_backups()

# Restore from specific session
safety.restore_backup('20231201_143022')

# Clean old backups (older than 30 days)
safety.cleanup_old_backups(days_to_keep=30)
```

## 📁 Project Structure

```
mac-cleaner/
├── src/mac_cleaner/        # Package source
├── gui_cleaner.py          # GUI interface
├── detailed_gui.py         # Detailed analysis GUI
├── web_gui.py              # Web interface
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── .mac_cleaner_backup/    # Backup directory (created automatically)
```

## ⚙️ Requirements

- Python 3.7 or higher
- macOS 10.14 or later
- Administrative privileges (for system files)

### Python Dependencies
- `psutil` - System information and process management
- `send2trash` - Safe file deletion to trash
- `flask-wtf` - CSRF protection for web GUI
- `flask-limiter` - Rate limiting for web GUI

## 🔒 Security & Privacy

- **No Data Collection**: The cleaner works entirely offline
- **Local Processing**: All operations happen on your machine
- **Transparent Operations**: Detailed logs of all actions
- **Safe by Default**: Dry run mode enabled by default in GUI
- **Security Policy**: See `SECURITY.md` for reporting vulnerabilities

### Web Interface Notes
- Runs on localhost only
- Requires `MAC_CLEANER_SECRET_KEY` for CSRF protection
- For production rate limits, set `MAC_CLEANER_LIMITER_STORAGE` (ex: `redis://localhost:6379`)

### Environment Setup

- Copy `.env.example` and set values for your environment

## 🐛 Troubleshooting

### Permission Issues
If you encounter permission errors, try running with sudo:
```bash
sudo mac-cleaner clean --no-dry-run --category all
```

### Large Files Not Deleting
Some large files may be locked by applications. Close running applications and try again.

### Backup Restoration
Backups are stored in `~/.mac_cleaner_backup/`. You can manually restore files if needed.

## 📝 Changelog

### v1.0.0
- Initial release
- Core cleaning functionality
- GUI interface
- Safety and backup features
- Comprehensive logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see `LICENSE` for details.

## 🔖 Versioning

- Version is defined in `src/mac_cleaner/__version__.py`
- Update `CHANGELOG.md` for every release
- CLI version: `mac-cleaner --version`

## ✅ Release Checklist

- [ ] All tests pass (`pytest`)
- [ ] Update `CHANGELOG.md`
- [ ] Bump `src/mac_cleaner/__version__.py`
- [ ] Verify CLI/GUI/Web basic flows
- [ ] Tag the release

## ⚠️ Disclaimer

This software modifies your filesystem. While built with safety features, always:
- Review dry run results before cleaning
- Keep important backups
- Use at your own risk

The authors are not responsible for any data loss or system issues.

## 📞 Support

For issues, questions, or feature requests:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Made with ❤️ for macOS users**
