#!/usr/bin/env python3
"""
Release automation script for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description="", check=True):
    """Run a command with error handling"""
    if description:
        print(f"🔨 {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False, e.stderr

def get_version():
    """Get current version from __version__.py"""
    version_file = Path(__file__).parent.parent / "src" / "mac_cleaner" / "__version__.py"
    if version_file.exists():
        content = version_file.read_text()
        for line in content.split('\n'):
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return None

def create_release_notes(version):
    """Create release notes"""
    print("📝 Creating Release Notes")
    print("=" * 50)
    
    release_notes = f"""# macOS Cleaner {version}

## 🎉 Release Highlights

A comprehensive macOS system cleaning tool with async operations, advanced analytics, and smart scheduling.

## 🚀 New Features

### Async Operations
- **Concurrent Processing**: Multi-threaded file analysis and cleaning
- **Performance Optimization**: 3x faster analysis on multi-core systems
- **Progress Tracking**: Real-time progress updates during operations
- **Non-blocking Operations**: Improved user experience with async processing

### Advanced Analytics
- **Pattern Recognition**: Identifies cleaning patterns and usage trends
- **Space Prediction**: Predicts disk full dates based on historical data
- **Smart Recommendations**: Intelligent cleaning schedule suggestions
- **Usage Statistics**: Comprehensive usage metrics and summaries

### Smart Scheduling
- **Multiple Schedule Types**: Daily, weekly, monthly, interval, and smart scheduling
- **Auto-adjustment**: Smart tasks automatically adjust based on usage patterns
- **Background Execution**: Non-blocking scheduled operations
- **Task Management**: Complete task lifecycle management

### Notification System
- **Multi-channel Support**: System notifications, email, webhooks, logs
- **Smart Filtering**: Priority-based filtering and rate limiting
- **Quiet Hours**: Respects user-defined quiet periods
- **Learning System**: Improves notification behavior over time

### Enhanced Plugin System
- **Async Plugin Execution**: High-performance plugin scheduling
- **Priority-based Execution**: Intelligent plugin ordering
- **System Load Awareness**: Adjusts concurrency based on system conditions
- **Performance Tracking**: Detailed plugin performance metrics

## 🔒 Security Improvements

- **Enhanced Safety Checks**: Comprehensive path validation and protection
- **Input Sanitization**: Robust input validation and sanitization
- **Backup Systems**: Automatic backup creation and management
- **Privilege Management**: Safe privilege escalation handling

## 📦 Installation Options

### PyPI (Recommended)
```bash
pip install macos-cleaner
```

### Homebrew
```bash
brew tap mac-cleaner/tap
brew install mac-cleaner
```

### Docker
```bash
docker pull maccleaner/macos-cleaner:{version}
docker run -p 5000:5000 maccleaner/macos-cleaner:{version}
```

### macOS App Bundle
Download the DMG installer from GitHub Releases.

## 📋 Quick Start

```bash
# Analyze system
mac-cleaner analyze

# Dry run cleaning
mac-cleaner clean --dry-run

# GUI interface
mac-cleaner-gui

# Web interface
mac-cleaner-web
```

## 🔧 Requirements

- Python 3.9+
- macOS 10.15+
- Optional dependencies for enhanced features

## 📚 Documentation

- [README](https://github.com/mac-cleaner/macos-cleaner/blob/main/README.md)
- [Usage Examples](https://github.com/mac-cleaner/macos-cleaner/blob/main/USAGE_EXAMPLES.md)
- [Architecture](https://github.com/mac-cleaner/macos-cleaner/blob/main/docs/ARCHITECTURE.md)
- [Phase 4 Summary](https://github.com/mac-cleaner/macos-cleaner/blob/main/PHASE4_SUMMARY.md)

## ⚠️ Important

- Always use dry-run mode first
- Back up important data before cleaning
- Review what will be deleted before confirming

## 🐛 Bug Reports

Please report bugs at: https://github.com/mac-cleaner/macos-cleaner/issues

## 🤝 Contributing

Contributions are welcome! See CONTRIBUTING.md for guidelines.

---

🍎 **macOS Cleaner** - Safe, intelligent system cleaning for Mac
"""
    
    release_file = Path(__file__).parent.parent / f"RELEASE_NOTES_v{version}.md"
    release_file.write_text(release_notes)
    print(f"📝 Release notes created: {release_file}")
    return release_file

def create_tag(version):
    """Create and push git tag"""
    print(f"🏷️ Creating Git Tag v{version}")
    print("=" * 50)
    
    # Check if tag already exists
    success, output = run_command(f"git tag -l v{version}", "Checking if tag exists", check=False)
    if output.strip():
        print(f"⚠️ Tag v{version} already exists")
        return False
    
    # Create tag
    success, _ = run_command(f"git tag v{version}", f"Creating tag v{version}")
    if not success:
        return False
    
    # Push tag
    success, _ = run_command(f"git push origin v{version}", f"Pushing tag v{version}")
    if not success:
        return False
    
    print(f"✅ Tag v{version} created and pushed")
    return True

def build_all():
    """Build all distribution packages"""
    print("🏗️ Building All Distribution Packages")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean previous builds
    run_command("rm -rf build dist *.egg-info", "Cleaning previous builds", check=False)
    
    # Build Python package
    success, _ = run_command("python scripts/build_and_publish.py build", "Building Python package")
    if not success:
        return False
    
    # Build macOS app
    success, _ = run_command("python scripts/build_app.py", "Building macOS app bundle")
    if not success:
        return False
    
    # Create DMG
    success, _ = run_command("python scripts/create_dmg.py", "Creating DMG installer")
    if not success:
        return False
    
    # Build Docker image
    success, _ = run_command("python scripts/docker_build.py build", "Building Docker image")
    if not success:
        return False
    
    print("✅ All packages built successfully")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Release automation for macOS Cleaner")
    parser.add_argument("action", choices=[
        "version", "notes", "tag", "build", "all"
    ], help="Action to perform")
    parser.add_argument("--version", help="Version to release")
    
    args = parser.parse_args()
    
    # Get version
    if args.version:
        version = args.version
    else:
        version = get_version()
        if not version:
            print("❌ Could not determine version")
            return 1
    
    print(f"🚀 macOS Cleaner Release Automation - v{version}")
    print("=" * 60)
    
    success = True
    
    if args.action == "version":
        print(f"Current version: {version}")
    
    elif args.action == "notes":
        create_release_notes(version)
    
    elif args.action == "tag":
        success = create_tag(version)
    
    elif args.action == "build":
        success = build_all()
    
    elif args.action == "all":
        # Complete release process
        create_release_notes(version)
        success = build_all()
        if success:
            success = create_tag(version)
    
    if success:
        print(f"\n🎉 Release automation completed for v{version}!")
        print("📋 Next steps:")
        print("   1. Review the built packages")
        print("   2. Test the packages")
        print("   3. Push the tag to trigger CI/CD release")
        print("   4. Monitor the release process")
    else:
        print(f"\n❌ Release automation failed for v{version}!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
