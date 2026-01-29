# 🍎 macOS Cleaner - Read-Only Disk Analysis Tool

> **⚠️ IMPORTANT**: This tool operates in **read-only mode** and will **NEVER delete or modify** any files on your system. It only analyzes disk usage and provides insights.

A safe, comprehensive macOS disk usage analysis tool that helps you understand what's consuming space on your Mac with built-in safety features to prevent accidental data loss.

A safe, comprehensive macOS disk usage analysis tool that helps you understand what's consuming space on your Mac with built-in safety features to prevent accidental data loss.

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

📖 **For detailed installation instructions, see [INSTALLATION.md](docs/INSTALLATION.md)**

**Quick Install:**
```bash
# Navigate to project directory
cd mack-clearn

# Install in editable mode (recommended)
pip install -e .
```

**Alternative:**
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
```bash
./run_cleaner.sh
# Interactive menu with all options
```

## 📊 Usage Examples

### Basic Analysis
```bash
# Get system information
mac-cleaner info

# Analyze disk usage
mac-cleaner analyze

# Focus on specific categories
mac-cleaner clean --dry-run --category cache
```

### Advanced Usage
```bash
# JSON output for scripting
mac-cleaner analyze --json

# Use specific analysis plugin
mac-cleaner clean --plugin "Browser Cache Cleaner"

# Create backup before manual cleanup
mac-cleaner backup --path "~/Downloads"
```

## �️ Safety Features

- **Read-Only Operation**: No files are modified during analysis
- **Safety Scoring**: Each file category gets a safety recommendation
- **Protected Paths**: System directories are automatically excluded
- **Backup Integration**: Optional backup before any manual actions
- **Validation**: All paths are validated before processing

## � What Gets Analyzed

### User Directories
- Desktop, Documents, Downloads, Movies, Music, Pictures
- Library/Caches, Library/Logs, Library/Application Support
- Library/Containers, Library/Group Containers

### System Areas
- System caches and temporary files
- Application support directories
- Development tool caches (Xcode, Docker, etc.)

### File Categories
- **Cache Files**: Browser caches, system caches, application caches
- **Log Files**: Application logs, system logs, crash reports
- **Temporary Files**: Build artifacts, downloads, installation files
- **Large Files**: Files over 100MB with detailed information

## 🔧 Configuration

### Default Settings
The tool works out-of-the-box with sensible defaults. Configuration files are stored in:
- `~/.mac_cleaner/` - User configuration
- `~/.mac_cleaner_backup/` - Backup directory

### Custom Configuration
```yaml
# ~/.mac_cleaner/config.yaml
analysis:
  exclude_paths:
    - "/Users/yourname/Important"
    - "/Volumes/External"
  
plugins:
  enabled:
    - "Browser Cache Cleaner"
    - "System Cache Cleaner"
  
safety:
  auto_backup: true
  protected_paths:
    - "/System"
    - "/Library"
```

## 📈 Sample Output

```
🍎 MACOS SPACE ANALYSIS REPORT
================================================================================

💾 DISK USAGE:
   Total: 228.27 GB
   Used:  190.31 GB (83.4%)
   Free:  12.60 GB

🎯 TOP RECOMMENDATIONS:
   1. System Caches: 19.27 GB - Safe to clear
   2. Library/Caches: 16.74 GB - Safe to clear  
   3. Application Support: 30.81 GB - Review carefully
   4. Downloads: 1.83 GB - Review old files

📄 LARGE FILES (Top 10):
   📄 408.18 MB - Screen Recording 2025-02-11.mov
   📄 354.34 MB - Backup Migration.zip
   📄 330.21 MB - MicrosoftEdge-114.0.1823.37.pkg
```

## 🧪 Development

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=mac_cleaner
```

### Project Structure
```
src/mac_cleaner/
├── cli.py              # Command-line interface
├── space_analyzer.py   # Core analysis engine
├── safety_manager.py   # Safety and backup features
├── web/               # Web interface
├── plugins/           # Analysis plugins
└── core/              # Core functionality
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- **New Analysis Plugins**: Add support for specific applications
- **Web Interface**: Improve the browser-based UI
- **Documentation**: Help improve guides and examples
- **Testing**: Add more comprehensive test coverage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � Security

- **No data collection**: No information is sent to external servers
- **Local operation**: All analysis happens on your machine
- **Open source**: Full code transparency
- **Safety first**: Read-only operation prevents accidental data loss
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
