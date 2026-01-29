# 🍎 macOS Cleaner - Usage Examples

## 📊 Disk Analysis Tool

The macOS Cleaner provides a safe, comprehensive environment for macOs storage analysis:

### Launch Options
```bash
# Recommended: Web Interface
mac-cleaner web

# Desktop GUI
mac-cleaner gui

# Analysis only (CLI)
mac-cleaner analyze
```

## 🚀 Basic Usage Scenarios

### Scenario 1: Identify Large Space Consumers
```bash
# Get a quick summary of disk usage
mac-cleaner info

# Run a full system analysis
mac-cleaner analyze
```

### Scenario 2: Deep Dive into Application Caches
```bash
# Use the focused cache analysis plugin
mac-cleaner analyze --plugin "System Cache Cleaner"
```

### Scenario 3: Investigating Large Files
```bash
# The analysis report automatically highlights files over 100MB
# You can see these in the 'Large Files' tab of the Web UI
```

## 🌐 Web Dashboard (Enhanced)

The new professional web interface offers:

1.  **Sidebar Navigation**: Quickly switch between Recommendations, Folder Analysis, and Large Files.
2.  **Live Progress**: Real-time feedback during deep scans.
3.  **Finder Integration**: Click the "Show" button next to any path to instantly reveal it in macOS Finder.
4.  **Professional Modals**: Native-style alerts for better error handling and confirmations.
5.  **Shimmer Visuals**: Modern loading states for a premium feel.

### Launching the Web UI
```bash
mac-cleaner web --port 5000
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

## 🛡️ Safety & Security

- **Strict Read-Only**: This tool is an analysis engine only. It will suggest what *can* be optimized but will not perform deletions.
- **Protected Paths**: System-critical directories (like `/System`) are flagged and protected during analysis.
- **Local Privacy**: No data ever leaves your computer.

---

**Made with ❤️ for users who value system stability and clarity**
