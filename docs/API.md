# API Documentation

## Overview

The macOS Cleaner provides a comprehensive API for disk usage analysis through multiple interfaces:

- **CLI Interface**: Command-line tool for scripting and automation
- **Web API**: RESTful API for web integration
- **Python API**: Direct Python module usage

## CLI Interface

### Installation

```bash
pip install macos-cleaner
```

### Basic Commands

#### Help and Information
```bash
# Show help
mac-cleaner --help

# Show version
mac-cleaner --version

# Show system information
mac-cleaner info
```

#### Analysis Commands

##### Analyze Disk Usage
```bash
# Full system analysis
mac-cleaner analyze

# JSON output
mac-cleaner analyze --json

# Plugin-specific analysis
mac-cleaner analyze --plugin "Browser Cache Cleaner"
```

##### List Available Plugins
```bash
# List all plugins
mac-cleaner plugins

# JSON output
mac-cleaner plugins --json
```

##### Read-Only "Cleaning" (Analysis)
```bash
# Analyze specific category
mac-cleaner clean --category cache --dry-run

# Plugin-based analysis
mac-cleaner clean --plugin "Browser Cache Cleaner" --verbose

# JSON output
mac-cleaner clean --plugin "Browser Cache Cleaner" --json
```

#### Backup Management
```bash
# Create backup
mac-cleaner backup --path "/path/to/file"

# List backups
mac-cleaner restore --list-backups

# Restore backup
mac-cleaner restore --restore "backup_name"
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--dry-run/--no-dry-run` | Analysis mode (default: analysis only) | `--dry-run` |
| `--category` | Category to analyze | `--category cache` |
| `--plugin` | Specific plugin to use | `--plugin "Browser Cache Cleaner"` |
| `--json` | JSON output format | `--json` |
| `--verbose, -v` | Verbose output | `--verbose` |
| `--force` | Skip confirmations | `--force` |
| `--config` | Configuration file path | `--config config.yaml` |

### Available Categories

- `cache` - System and application caches
- `temp` - Temporary files
- `logs` - Log files
- `trash` - Trash directory
- `browser_cache` - Browser-specific caches
- `all` - All categories (default)

### Available Plugins

| Plugin Name | Category | Description |
|-------------|----------|-------------|
| Browser Cache Cleaner | cache | Cleans cache files from web browsers |
| System Cache Cleaner | cache | Cleans system cache files |
| Log File Cleaner | logs | Cleans old log files |
| Temporary File Cleaner | temp | Cleans temporary files |
| Xcode Cleaner | development | Cleans Xcode derived data and archives |
| Docker Cleaner | development | Cleans Docker unused images, containers, and volumes |
| Downloads Cleaner | user | Cleans old files from Downloads folder |

## Web API

### Base URL
```
http://127.0.0.1:5002
```

### Endpoints

#### GET `/api/status`
Get current operation status.

**Response:**
```json
{
  "status": "idle|analyzing|completed|error",
  "progress": 0,
  "message": "Status message",
  "results": {}
}
```

#### GET `/api/analyze`
Start system analysis.

**Response:**
```json
{
  "success": true,
  "message": "Analysis started"
}
```

#### POST `/api/clean`
Start analysis of specific categories.

**Request:**
```json
{
  "dry_run": true,
  "categories": ["cache", "temp"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Analysis started"
}
```

#### POST `/api/open_finder`
Open directory in Finder.

**Request:**
```json
{
  "path": "/Users/username/Downloads"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Opened /Users/username/Downloads in Finder"
}
```

#### POST `/api/backup`
Create backup of specified path.

**Request:**
```json
{
  "path": "/Users/username/Documents"
}
```

**Response:**
```json
{
  "success": true,
  "backup_path": "/Users/username/.mac_cleaner_backup/Documents"
}
```

### Rate Limiting

All API endpoints are rate-limited:
- Analyze: 20 requests per minute
- Clean: 5 requests per minute
- Open Finder: 30 requests per minute
- Backup: 10 requests per minute

### CSRF Protection

All POST requests require CSRF protection. Include the token in headers:
```
X-CSRFToken: <csrf_token>
```

## Python API

### Basic Usage

```python
from mac_cleaner import MacCleaner, SpaceAnalyzer
from mac_cleaner.plugins import register_builtin_plugins, PluginManager

# Initialize cleaner
cleaner = MacCleaner()

# Get system information
info = cleaner.get_system_info()
print(f"Total space: {info['total_space_human']}")

# Analyze disk usage
analyzer = SpaceAnalyzer()
report = analyzer.generate_report()

# Use plugins
plugin_manager = register_builtin_plugins(PluginManager())
browser_plugin = plugin_manager.get_plugin("Browser Cache Cleaner")

# Analyze with plugin
results = browser_plugin.analyze_paths()
print(f"Browser cache size: {results['total_size_human']}")
```

### Plugin Development

```python
from mac_cleaner.interfaces import CleanerPlugin

class CustomPlugin(CleanerPlugin):
    @property
    def name(self) -> str:
        return "Custom Plugin"
    
    @property
    def category(self) -> str:
        return "custom"
    
    @property
    def description(self) -> str:
        return "Custom analysis plugin"
    
    def get_cleanable_paths(self) -> List[str]:
        return ["/path/to/analyze"]
    
    def is_safe_to_clean(self, path: str) -> bool:
        return True

# Register plugin
plugin_manager = PluginManager()
plugin_manager.register_plugin(CustomPlugin())
```

### Configuration

```python
from mac_cleaner.config_manager import get_config

# Load configuration
config = get_config()

# Update configuration
config.update_config(
    dry_run_default=True,
    logging_level="DEBUG"
)

# Access configuration
print(config.cleaner.backup_enabled)
print(config.web.port)
```

## Response Formats

### Analysis Response

```json
{
  "category": "cache",
  "files_analyzed": 1234,
  "space_analyzed": 1048576,
  "space_analyzed_human": "1.0 MB",
  "paths_analyzed": [
    {
      "path": "/Users/username/Library/Caches",
      "size": 1048576,
      "size_human": "1.0 MB",
      "files_found": 1234,
      "action": "analyzed_only"
    }
  ],
  "mode": "read_only_analysis"
}
```

### Plugin Response

```json
{
  "analyzed": [
    {
      "path": "/Users/username/Library/Caches/Chrome",
      "size": 1048576,
      "size_human": "1.0 MB",
      "file_count": 500,
      "action": "analyzed_only"
    }
  ],
  "skipped": [],
  "errors": [],
  "total_analyzed": 1048576,
  "total_analyzed_human": "1.0 MB",
  "mode": "read_only_analysis"
}
```

### System Info Response

```json
{
  "platform": "Darwin",
  "macos_version": "26.2",
  "python_version": "3.11.12",
  "total_space_human": "228.27 GB",
  "used_space_human": "11.43 GB",
  "free_space_human": "14.25 GB",
  "disk_usage_percent": 5.0
}
```

## Error Handling

### Common Error Responses

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Security Considerations

1. **Read-Only Operation**: The tool never deletes or modifies files
2. **Path Validation**: All paths are validated against allowed directories
3. **CSRF Protection**: Web API protected against CSRF attacks
4. **Rate Limiting**: API endpoints are rate-limited to prevent abuse
5. **Input Sanitization**: All user inputs are sanitized and validated

## Examples

### Scripting Example

```bash
#!/bin/bash
# Analyze browser cache size
echo "Analyzing browser cache..."
mac-cleaner clean --plugin "Browser Cache Cleaner" --json > browser_cache.json

# Extract size
SIZE=$(cat browser_cache.json | jq -r '.total_analyzed_human')
echo "Browser cache size: $SIZE"

# Analyze system usage
echo "Analyzing system usage..."
mac-cleaner analyze --json > system_analysis.json

# Get top recommendations
cat system_analysis.json | jq '.top_recommendations[0:3]'
```

### Python Integration Example

```python
import json
from mac_cleaner import SpaceAnalyzer

def get_disk_usage_report():
    """Generate comprehensive disk usage report."""
    analyzer = SpaceAnalyzer()
    report = analyzer.generate_report()
    
    # Extract key metrics
    disk_usage = report['disk_usage']
    recommendations = report['top_recommendations'][:5]
    
    return {
        'disk_usage': {
            'total': disk_usage['total_human'],
            'used': disk_usage['used_human'],
            'free': disk_usage['free_human'],
            'percent': disk_usage['usage_percent']
        },
        'recommendations': recommendations
    }

# Usage
if __name__ == "__main__":
    report = get_disk_usage_report()
    print(json.dumps(report, indent=2))
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Run with appropriate user permissions
2. **Module Not Found**: Ensure proper installation: `pip install -e .`
3. **Port Already in Use**: Web interface will automatically find available port
4. **Rate Limiting**: Wait for rate limit to reset or use different endpoints

### Debug Mode

Enable debug logging:
```bash
export MAC_CLEANER_LOG_LEVEL=DEBUG
mac-cleaner analyze --verbose
```

### Configuration Issues

Check configuration file:
```bash
mac-cleaner --config ~/.mac_cleaner/config.yaml analyze
```
