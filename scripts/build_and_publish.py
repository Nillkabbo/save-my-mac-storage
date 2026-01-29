#!/usr/bin/env python3
"""
Build and publish macOS Cleaner to PyPI.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import subprocess
import shutil
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

def check_environment():
    """Check if environment is ready for publishing"""
    print("🔍 Checking Environment")
    print("=" * 50)
    
    # Check if we have the required tools
    tools = ["python", "pip", "twine"]
    for tool in tools:
        success, _ = run_command(f"which {tool}", f"Checking for {tool}")
        if not success:
            print(f"❌ {tool} not found. Please install it first.")
            return False
    
    # Check if we're logged in to PyPI
    success, _ = run_command("twine check", "Checking PyPI authentication", check=False)
    if not success:
        print("⚠️  Not logged into PyPI. Run 'twine upload --repository testpypi dist/*' first.")
    
    print("✅ Environment check complete")
    return True

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning Build Artifacts")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Remove build directories
    for dir_name in ["build", "dist", "*.egg-info"]:
        for path in project_root.glob(dir_name):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Removed: {path}")
    
    # Remove compiled Python files
    for pattern in ["**/*.pyc", "**/*.pyo", "**/__pycache__"]:
        for path in project_root.glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
    
    print("✅ Build artifacts cleaned")

def build_package():
    """Build the package"""
    print("📦 Building Package")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Install build dependencies
    success, _ = run_command("pip install --upgrade build twine", "Installing build dependencies")
    if not success:
        return False
    
    # Build the package
    success, _ = run_command("python -m build", "Building package")
    if not success:
        return False
    
    # Check the package
    success, _ = run_command("twine check dist/*", "Checking package")
    if not success:
        return False
    
    print("✅ Package built successfully")
    return True

def publish_to_testpypi():
    """Publish to TestPyPI"""
    print("🧪 Publishing to TestPyPI")
    print("=" * 50)
    
    success, _ = run_command(
        "twine upload --repository testpypi dist/*",
        "Uploading to TestPyPI",
        check=False
    )
    
    if success:
        print("✅ Published to TestPyPI successfully")
        print("📦 Install with: pip install --index-url https://test.pypi.org/simple/ macos-cleaner")
        return True
    else:
        print("❌ Failed to publish to TestPyPI")
        return False

def publish_to_pypi():
    """Publish to PyPI"""
    print("🚀 Publishing to PyPI")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("Are you sure you want to publish to PyPI? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Publication cancelled")
        return False
    
    success, _ = run_command(
        "twine upload dist/*",
        "Uploading to PyPI",
        check=False
    )
    
    if success:
        print("✅ Published to PyPI successfully")
        print("📦 Install with: pip install macos-cleaner")
        return True
    else:
        print("❌ Failed to publish to PyPI")
        return False

def show_package_info():
    """Show information about the built package"""
    print("📋 Package Information")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    if not dist_dir.exists():
        print("❌ No package found. Build the package first.")
        return
    
    # List package files
    for package_file in dist_dir.glob("*"):
        size_mb = package_file.stat().st_size / (1024 * 1024)
        print(f"📦 {package_file.name}: {size_mb:.1f} MB")
    
    # Show package contents (for wheel)
    wheel_file = dist_dir.glob("*.whl")
    if wheel_file:
        wheel_path = next(wheel_file)
        print(f"\n📂 Contents of {wheel_path.name}:")
        success, output = run_command(f"python -m zipfile -l {wheel_path}", "Listing wheel contents", check=False)
        if success and output:
            lines = output.strip().split('\n')
            for line in lines[-10:]:  # Show last 10 files
                print(f"   {line}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build and publish macOS Cleaner to PyPI")
    parser.add_argument("action", choices=[
        "check", "clean", "build", "test", "publish", "info"
    ], help="Action to perform")
    
    args = parser.parse_args()
    
    # Ensure we're in project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if args.action == "check":
        success = check_environment()
    
    elif args.action == "clean":
        clean_build()
        success = True
    
    elif args.action == "build":
        clean_build()
        success = build_package()
        if success:
            show_package_info()
    
    elif args.action == "test":
        clean_build()
        if build_package():
            success = publish_to_testpypi()
        else:
            success = False
    
    elif args.action == "publish":
        clean_build()
        if build_package():
            success = publish_to_pypi()
        else:
            success = False
    
    elif args.action == "info":
        show_package_info()
        success = True
    
    if success:
        print("\n🎉 Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
