# 🍎 macOS Cleaner - Usage Examples

## 📊 Disk Analysis Tool

The macOS Cleaner provides comprehensive disk usage analysis and insights for macOS systems:

### Launch Options
```bash
# Quick launcher (recommended)
./run_cleaner.sh
# Choose option 1 for Web Interface

# Direct launch
mac-cleaner web
```

### Key Features

#### 1. **Disk Analysis**
- Comprehensive system scan for space usage
- Large file identification
- Cache and temporary file analysis
- Safety recommendations for each category

#### 2. **Web Interface**
- Modern browser-based interface
- Real-time analysis progress
- Detailed space breakdown
- Export capabilities

#### 3. **Command Line Interface**
- Scriptable analysis operations
- JSON output for automation
- Plugin-based extensible architecture

## 🚀 Basic Usage Examples

### Quick System Analysis
```bash
# Get system information
mac-cleaner info

# Analyze disk usage
mac-cleaner analyze

# List available plugins
mac-cleaner plugins
```

### Advanced Analysis
```bash
# Analyze specific category
mac-cleaner clean --dry-run --category cache

# Get JSON output for scripting
mac-cleaner analyze --json

# Use specific plugin
mac-cleaner clean --plugin "Browser Cache Cleaner"
```

### Backup Management
```bash
# Create backup before analysis
mac-cleaner backup --path "~/Downloads"

# List available backups
mac-cleaner restore --list-backups

# Restore from backup
mac-cleaner restore --restore backup_20240129_120000
```

## 📈 Real-World Scenarios

### Scenario 1: Low Disk Space Investigation
```bash
# Quick overview
mac-cleaner info

# Detailed analysis
mac-cleaner analyze

# Focus on largest space consumers
mac-cleaner clean --dry-run --category cache
```

### Scenario 2: Automated Monitoring
```bash
# Script for daily monitoring
#!/bin/bash
mac-cleaner analyze --json > daily_analysis.json
# Process JSON data for alerts/reports
```

### Scenario 3: Development Environment Cleanup
```bash
# Check development-related space usage
mac-cleaner clean --dry-run --plugin "Xcode Cleaner"
mac-cleaner clean --dry-run --plugin "Docker Cleaner"
```

## 🔧 Integration Examples

### Python Integration
```python
from mac_cleaner.space_analyzer import SpaceAnalyzer

# Create analyzer instance
analyzer = SpaceAnalyzer()

# Generate report
report = analyzer.generate_report()

# Print results
analyzer.print_report(report)
```

### Web API Integration
```bash
# Start web server
mac-cleaner web --host 0.0.0.0 --port 8080

# Access API endpoints
curl http://localhost:8080/api/status
curl http://localhost:8080/api/analyze
```

## 💡 Pro Tips

1. **Always use --dry-run first** to preview what would be analyzed
2. **JSON output** is perfect for scripting and automation
3. **Web interface** provides the best user experience for exploration
4. **Plugin system** allows for custom analysis rules
5. **Regular analysis** helps track space usage trends

## 🛡️ Safety Best Practices

- This tool operates in **read-only mode** for safety
- Always review analysis results before taking any action
- Use backup features for important directories
- Test in non-critical directories first

## 📞 Support

For issues and feature requests, please refer to the project documentation.

---

**Made with ❤️ for macOS users who want precise control over their storage analysis**
