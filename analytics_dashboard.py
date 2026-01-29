#!/usr/bin/env python3
"""
Analytics Dashboard Launcher - Standalone launcher for the analytics dashboard

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from src.mac_cleaner.gui.analytics_gui import main
    
    if __name__ == "__main__":
        print("🍎 Starting macOS Cleaner Analytics Dashboard...")
        main()
        
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error starting analytics dashboard: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
