#!/usr/bin/env python3
"""
Build macOS application bundle using py2app.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Build the macOS application bundle"""
    print("🍎 Building macOS Cleaner Application Bundle")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if py2app is available
    try:
        import py2app
        print("✅ py2app is available")
    except ImportError:
        print("❌ py2app not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "py2app"], check=True)
    
    # Create build directory
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("🧹 Cleaned previous build directory")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("🧹 Cleaned previous dist directory")
    
    # Create py2app setup
    py2app_setup = '''
"""
py2app setup for macOS Cleaner
"""

from setuptools import setup

APP = ['mac_cleaner/gui/main.py']
DATA_FILES = [
    'src/mac_cleaner/config/*.yaml',
    'src/mac_cleaner/templates/*',
    'src/mac_cleaner/static/*'
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'resources/mac_cleaner.icns',
    'plist': {
        'CFBundleName': 'macOS Cleaner',
        'CFBundleDisplayName': 'macOS Cleaner',
        'CFBundleIdentifier': 'com.maccleaner.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': 'macOS Cleaner',
        'CFBundleIconFile': 'mac_cleaner.icns',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'macOS Cleaner Analysis',
                'CFBundleTypeExtensions': ['json'],
                'CFBundleTypeRole': 'Editor'
            }
        ]
    },
    'packages': [
        'mac_cleaner',
        'mac_cleaner.core',
        'mac_cleaner.plugins',
        'mac_cleaner.gui',
        'mac_cleaner.web',
        'mac_cleaner.utils'
    ],
    'includes': [
        'asyncio',
        'concurrent.futures',
        'pathlib',
        'json',
        'yaml',
        'psutil',
        'send2trash',
        'flask',
        'click',
        'tkinter',
        'threading',
        'queue',
        'datetime',
        'logging',
        'configparser'
    ],
    'excludes': [
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'cv2'
    ],
    'site_packages': True,
    'strip': True,
    'optimize': 2
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
'''
    
    # Write py2app setup file
    setup_file = project_root / "setup_py2app.py"
    setup_file.write_text(py2app_setup)
    
    try:
        # Build the app
        print("🔨 Building application bundle...")
        result = subprocess.run([
            sys.executable, 
            "setup_py2app.py", 
            "py2app"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Application bundle built successfully!")
            
            # Check if app was created
            app_path = dist_dir / "macOS Cleaner.app"
            if app_path.exists():
                print(f"📦 App bundle created at: {app_path}")
                
                # Get app size
                app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
                print(f"📊 App bundle size: {app_size / (1024*1024):.1f} MB")
                
                # Try to sign the app (if codesign is available)
                try:
                    print("🔐 Attempting to sign application...")
                    sign_result = subprocess.run([
                        "codesign", 
                        "--deep", 
                        "--force", 
                        "--verify", 
                        "--verbose",
                        "--sign", "-",
                        str(app_path)
                    ], capture_output=True, text=True)
                    
                    if sign_result.returncode == 0:
                        print("✅ Application signed successfully")
                    else:
                        print("⚠️  Application signing failed (this is normal for development)")
                except FileNotFoundError:
                    print("⚠️  codesign not found, skipping code signing")
                
                return True
            else:
                print("❌ App bundle not found in dist directory")
                return False
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error: {e}")
        return False
    
    finally:
        # Cleanup setup file
        if setup_file.exists():
            setup_file.unlink()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
