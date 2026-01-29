# Installation Guide

This guide covers different installation methods for the macOS Cleaner application.

## Prerequisites

- **Python 3.9+** required
- **macOS** (designed for macOS systems)
- **pip** package manager

### Check Python Version
```bash
python3 --version
# Should show Python 3.9.x or higher
```

### Check pip
```bash
pip3 --version
# Should show pip version
```

## Installation Methods

### Method 1: Development Installation (Recommended)

This installs the application in editable mode, allowing you to make changes that are immediately reflected.

```bash
# Clone or navigate to the project directory
cd /path/to/windsurf-project

# Install in editable mode
pip install -e .
```

**Benefits:**
- Changes to source code are immediately available
- Includes all command-line scripts
- Easy to uninstall with `pip uninstall macos-cleaner`

### Method 2: Install from Requirements

```bash
# Navigate to the project directory
cd /path/to/windsurf-project

# Install dependencies
pip install -r requirements.txt
```

### Method 3: Install with Optional Dependencies

#### Development Dependencies
```bash
pip install -e ".[dev]"
```
Includes: pytest, black, mypy, flake8, bandit, safety, build, twine

#### Web Dependencies
```bash
pip install -e ".[web]"
```
Includes: gunicorn, flask-cors

#### All Dependencies
```bash
pip install -e ".[dev,web]"
```

### Method 4: Traditional pip Install (if published)

```bash
pip install macos-cleaner
```

## Post-Installation Verification

### Check Installation
```bash
# Verify the application is installed
mac-cleaner --version

# Show available commands
mac-cleaner --help
```

### Test All Interfaces

#### CLI Interface
```bash
# Test system information
mac-cleaner info

# Test analysis (dry run)
mac-cleaner analyze
```

#### GUI Interface
```bash
# Launch standard GUI
mac-cleaner gui

# Launch detailed analysis GUI
mac-cleaner detailed-gui
```

#### Web Interface
```bash
# Launch web interface
mac-cleaner web

# Or specify custom port
mac-cleaner web --port 8080
```

## Available Commands

After installation, you'll have access to these commands:

- **`mac-cleaner`** - Main CLI interface
- **`mac-cleaner-gui`** - Direct GUI launcher
- **`mac-cleaner web`** - Direct web interface launcher

### Main Commands
```bash
mac-cleaner web           # Launch web interface
mac-cleaner analyze       # Analyze disk usage
mac-cleaner clean         # Clean system files (use --dry-run first)
mac-cleaner info          # Show system information
mac-cleaner plugins       # List available plugins
mac-cleaner backup        # Create backup
mac-cleaner restore       # Manage backups
```

## Troubleshooting

### Common Issues

#### 1. Command Not Found
```bash
# If mac-cleaner command is not found, try:
python3 -m mac_cleaner.cli --help

# Or check if pip installed scripts in PATH:
which mac-cleaner
```

#### 2. Permission Denied
```bash
# Use user installation if system-wide install fails:
pip install --user -e .

# Or use virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### 3. Python Version Incompatible
```bash
# Check if you have the right Python version:
python3 --version

# If using pyenv, ensure correct version:
pyenv global 3.11.12
```

#### 4. Dependencies Conflicts
```bash
# Create fresh virtual environment:
python3 -m venv mac-cleaner-env
source mac-cleaner-env/bin/activate
pip install -e .
```

### Virtual Environment Setup (Recommended)

For isolated installation:

```bash
# Create virtual environment
python3 -m venv mac-cleaner-env

# Activate environment
source mac-cleaner-env/bin/activate

# Install application
pip install -e .

# Deactivate when done
deactivate
```

## Uninstallation

### Remove Application
```bash
pip uninstall macos-cleaner
```

### Remove Virtual Environment
```bash
# If using virtual environment
deactivate
rm -rf mac-cleaner-env
```

## Development Setup

For developers who want to contribute:

```bash
# Clone repository
git clone <repository-url>
cd mac-cleaner

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
mypy src/

# Security check
bandit -r src/
```

## Configuration

After installation, you can configure the application:

```bash
# Create configuration file
mac-cleaner --config ~/.mac-cleaner.yaml

# Or specify custom config
mac-cleaner --config /path/to/config.yaml
```

## Next Steps

Once installed:

1. **Read the README** for usage instructions
2. **Check USAGE_EXAMPLES.md** for practical examples
3. **Review SECURITY.md** for safety information
4. **Run with --dry-run first** to preview operations

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Check the GitHub issues page
4. Ensure all prerequisites are met
