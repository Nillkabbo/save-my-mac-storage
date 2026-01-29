#!/usr/bin/env python3
"""
Update Homebrew formula with new release information.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import hashlib
import requests
import re
from pathlib import Path

def get_file_sha256(url: str) -> str:
    """Download file and calculate SHA256"""
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    sha256_hash = hashlib.sha256()
    for chunk in response.iter_content(chunk_size=8192):
        sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def update_formula(version: str = "1.0.0"):
    """Update the Homebrew formula with new version and checksums"""
    print("🍺 Updating Homebrew Formula")
    print("=" * 50)
    
    # Paths
    project_root = Path(__file__).parent.parent
    formula_path = project_root / "homebrew" / "macos-cleaner.rb"
    
    if not formula_path.exists():
        print("❌ Formula file not found!")
        return False
    
    # URLs
    base_url = "https://github.com/mac-cleaner/macos-cleaner"
    archive_url = f"{base_url}/archive/refs/tags/v{version}.tar.gz"
    
    try:
        # Get SHA256 for main archive
        main_sha256 = get_file_sha256(archive_url)
        print(f"✅ Main archive SHA256: {main_sha256}")
        
        # Get SHA256 for setuptools (this would need to be updated periodically)
        setuptools_url = "https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-68.2.2.tar.gz"
        setuptools_sha256 = get_file_sha256(setuptools_url)
        print(f"✅ setuptools SHA256: {setuptools_sha256}")
        
        # Get SHA256 for wheel
        wheel_url = "https://files.pythonhosted.org/packages/source/w/wheel/wheel-0.41.2.tar.gz"
        wheel_sha256 = get_file_sha256(wheel_url)
        print(f"✅ wheel SHA256: {wheel_sha256}")
        
        # Read current formula
        formula_content = formula_path.read_text()
        
        # Update version and SHA256
        formula_content = re.sub(
            r'url "https://github\.com/mac-cleaner/macos-cleaner/archive/refs/tags/v.*\.tar\.gz"',
            f'url "{archive_url}"',
            formula_content
        )
        
        formula_content = re.sub(
            r'sha256 "[a-f0-9]{64}"',
            f'sha256 "{main_sha256}"',
            formula_content
        )
        
        # Update setuptools SHA256
        formula_content = re.sub(
            r'resource "setuptools".*?sha256 "[a-f0-9]{64}"',
            f'''resource "setuptools" do
      url "https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-68.2.2.tar.gz"
      sha256 "{setuptools_sha256}"
    end''',
            formula_content,
            flags=re.DOTALL
        )
        
        # Update wheel SHA256
        formula_content = re.sub(
            r'resource "wheel".*?sha256 "[a-f0-9]{64}"',
            f'''resource "wheel" do
      url "https://files.pythonhosted.org/packages/source/w/wheel/wheel-0.41.2.tar.gz"
      sha256 "{wheel_sha256}"
    end''',
            formula_content,
            flags=re.DOTALL
        )
        
        # Write updated formula
        formula_path.write_text(formula_content)
        
        print(f"✅ Formula updated successfully!")
        print(f"📁 Formula file: {formula_path}")
        
        # Show what changed
        print("\n📋 Changes made:")
        print(f"  - Version: {version}")
        print(f"  - Archive URL: {archive_url}")
        print(f"  - Main SHA256: {main_sha256}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating formula: {e}")
        return False

def create_tap_info():
    """Create information about setting up a Homebrew tap"""
    print("\n📚 Homebrew Tap Setup Information")
    print("=" * 50)
    
    tap_info = '''
# Homebrew Tap Setup for macOS Cleaner

## 1. Create a Tap Repository

Users can install macOS Cleaner via a custom tap:

```bash
# Add the tap
brew tap mac-cleaner/tap https://github.com/mac-cleaner/homebrew-tap

# Install macOS Cleaner
brew install mac-cleaner

# Or install with all features
brew install mac-cleaner --with-all
```

## 2. Manual Installation

Users can also install manually:

```bash
# Download the formula
curl -O https://raw.githubusercontent.com/mac-cleaner/macos-cleaner/main/homebrew/macos-cleaner.rb

# Install
brew install --formula ./macos-cleaner.rb
```

## 3. Update Formula

When releasing a new version:

1. Update the version in the formula
2. Run `scripts/update_homebrew.rb` to update checksums
3. Commit the updated formula
4. Create a new release tag

## 4. Testing

Test the formula:

```bash
# Test installation
brew install --formula ./homebrew/macos-cleaner.rb

# Test commands
mac-cleaner --version
mac-cleaner --help

# Test service
brew services start mac-cleaner
```

## 5. Service Management

The formula includes a service for the web interface:

```bash
# Start the service
brew services start mac-cleaner

# Stop the service
brew services stop mac-cleaner

# Check status
brew services list | grep mac-cleaner
```
'''
    
    tap_file = Path(__file__).parent.parent / "homebrew" / "TAP_SETUP.md"
    tap_file.write_text(tap_info)
    print(f"📝 Tap setup information written to: {tap_file}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = "1.0.0"
    
    success = update_formula(version)
    
    if success:
        create_tap_info()
        print("\n🎉 Homebrew formula update complete!")
    else:
        print("\n❌ Failed to update Homebrew formula")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
