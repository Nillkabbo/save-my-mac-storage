# 🍎 macOS Cleaner - Read-Only Disk Analysis Tool

> [!IMPORTANT]
> This tool operates in **read-only mode** and will **NEVER delete or modify** any files on your system. It is designed for safe disk usage analysis and providing optimization insights.

A professional, comprehensive macOS disk usage analysis tool that helps you understand what's consuming space on your Mac with built-in safety features and a native macOS aesthetic.

## ✨ Features

- **🔍 Read-Only Analysis**: Analyzes disk usage without any risk of data loss.
- **📊 Professional Dashboard**: Modern, macOS-native web interface for clear data visualization.
- **🎯 Plugin System**: Modular analysis with specific plugins (Browser, System, Development, etc.).
- **📂 Finder Integration**: Open identified files and folders directly in Finder from the UI.
- **📋 Multiple Interfaces**: CLI, GUI, and Web interfaces for all user preferences.
- **📈 Detailed Reports**: Comprehensive summaries with safety recommendations.
- **🛡️ Security Focused**: Built-in path validation and input sanitization.
- **🧪 Well Tested**: Robust test suite ensuring reliability.

## 🚀 Quick Start

### Installation

📖 **For detailed installation instructions, see [INSTALLATION.md](docs/INSTALLATION.md)**

**Quick Install:**
```bash
# Navigate to project directory
cd mac-clean

# Install in editable mode (recommended)
pip install -e .
```

### Usage

#### Web Interface (Recommended)
```bash
mac-cleaner web
```
The web interface provides a professional dashboard with live analysis progress and "Show in Finder" capabilities.

#### Command Line Version
```bash
mac-cleaner analyze
```

## 📊 What Gets Analyzed

### User Directories
- Desktop, Documents, Downloads, Movies, Music, Pictures
- Library/Caches, Library/Logs, Library/Application Support
- Library/Containers, Library/Group Containers

### System Areas
- System caches and temporary files
- Application support directories
- Development tool caches (Xcode, Docker, etc.)

### File Categories
- **Cache Files**: Browser caches, system caches, application caches.
- **Log Files**: Application logs, system logs, crash reports.
- **Temporary Files**: Build artifacts, downloads, installation files.
- **Large Files**: Detailed info on files over 100MB.

## 🛡️ Safety Features

- **Read-Only Operation**: Guaranteed no file modification or deletion.
- **Protected Paths**: System directories are automatically handled with caution.
- **Safety Recommendations**: High/Medium/Low priority insights for optimization.
- **Path Validation**: Prevents unauthorized directory access.

## 📈 Sample Output

```
🍎 MACOS SPACE ANALYSIS REPORT
================================================================================

💾 DISK USAGE:
   Total: 228.27 GB
   Used:  190.31 GB (83.4%)
   Free:  12.60 GB

🎯 TOP RECOMMENDATIONS:
   1. System Caches: 19.27 GB - High Priority
   2. Library/Caches: 16.74 GB - High Priority
   3. Application Support: 30.81 GB - Medium Priority
   4. Downloads: 1.83 GB - Medium Priority

📄 LARGE FILES (Top 10):
   📄 408.18 MB - Screen Recording 2025-02-11.mov
   📄 354.34 MB - Backup Migration.zip
```

## 🔧 Configuration

The tool works out-of-the-box with sensible defaults. Configuration files are stored in `~/.mac_cleaner/`.

## 🧪 Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=mac_cleaner
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

- **No data collection**: No information is sent to external servers.
- **Local operation**: All analysis happens on your machine.
- **Open source**: Full code transparency.
- **Safety first**: Read-only operation prevents accidental data loss.

---

**Made with ❤️ for macOS users**
