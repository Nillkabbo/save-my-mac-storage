#!/usr/bin/env python3
"""
Create DMG installer for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Create DMG installer"""
    print("💿 Creating macOS Cleaner DMG Installer")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if app bundle exists
    app_path = project_root / "dist" / "macOS Cleaner.app"
    if not app_path.exists():
        print("❌ App bundle not found. Run build_app.py first!")
        return False
    
    # Create DMG directory
    dmg_dir = project_root / "dmg_temp"
    dmg_dir.mkdir(exist_ok=True)
    
    try:
        # Copy app to DMG directory
        dmg_app_path = dmg_dir / "macOS Cleaner.app"
        if dmg_app_path.exists():
            shutil.rmtree(dmg_app_path)
        shutil.copytree(app_path, dmg_app_path)
        print(f"📦 Copied app bundle to DMG directory")
        
        # Create Applications folder symlink
        applications_link = dmg_dir / "Applications"
        if applications_link.exists():
            applications_link.unlink()
        applications_link.symlink_to("/Applications", target_is_directory=True)
        print("📁 Created Applications folder symlink")
        
        # Create DMG background folder and image
        background_dir = dmg_dir / ".background"
        background_dir.mkdir(exist_ok=True)
        
        # Create a simple background image (optional)
        background_script = '''
tell application "Finder"
    set the name of every disk whose name is "macOS Cleaner" to "macOS Cleaner"
    open the startup disk
    set the view of the front Finder window to icon view
    set the bounds of the front Finder window to {400, 100, 920, 440}
    set the position of item "macOS Cleaner.app" of front Finder window to {130, 150}
    set the position of item "Applications" of front Finder window to {510, 150}
    set background picture of view of the front Finder window to file ".background:background.png"
    close the front Finder window
    open the startup disk
end tell
'''
        
        # Write AppleScript for DMG setup
        script_file = dmg_dir / "setup_dmg.scpt"
        script_file.write_text(background_script)
        
        # Create DMG
        dmg_name = "macOS-Cleaner-1.0.0"
        dmg_path = project_root / "dist" / f"{dmg_name}.dmg"
        
        print("🔨 Creating DMG...")
        
        # Remove existing DMG
        if dmg_path.exists():
            dmg_path.unlink()
        
        # Create DMG using hdiutil
        create_cmd = [
            "hdiutil", "create",
            "-volname", "macOS Cleaner",
            "-srcfolder", str(dmg_dir),
            "-ov",
            "-format", "UDZO",
            "-imagekey", "zlib-level=9",
            str(dmg_path)
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ DMG created successfully: {dmg_path}")
            
            # Get DMG size
            dmg_size = dmg_path.stat().st_size
            print(f"📊 DMG size: {dmg_size / (1024*1024):.1f} MB")
            
            # Try to run the setup script
            try:
                print("🎨 Configuring DMG appearance...")
                subprocess.run([
                    "osascript", 
                    str(script_file)
                ], capture_output=True, text=True)
                print("✅ DMG appearance configured")
            except Exception as e:
                print(f"⚠️  DMG configuration failed: {e}")
            
            return True
        else:
            print("❌ DMG creation failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    
    except Exception as e:
        print(f"❌ Error creating DMG: {e}")
        return False
    
    finally:
        # Cleanup temporary directory
        if dmg_dir.exists():
            shutil.rmtree(dmg_dir)
            print("🧹 Cleaned up temporary files")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
