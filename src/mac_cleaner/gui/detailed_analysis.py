#!/usr/bin/env python3
"""
Standalone Detailed GUI for macOS Cleaner - Web-based alternative.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mac_cleaner.file_analyzer import FileAnalyzer
from mac_cleaner.safety_manager import SafetyManager
from mac_cleaner.space_analyzer import SpaceAnalyzer
import tempfile
import json

def main():
    """Run detailed analysis in terminal."""
    print("🍎 macOS Cleaner - Detailed Analysis")
    print("=" * 50)
    
    try:
        # Initialize components
        analyzer = SpaceAnalyzer()
        safety = SafetyManager()
        file_analyzer = FileAnalyzer()
        
        print("✓ Components initialized")
        
        # Analyze user directories
        print("\n🔍 Analyzing user directories...")
        report = analyzer.analyze_user_directories()
        
        print(f"\n📊 Analysis Results:")
        print(f"  Total analyzed: {analyzer.format_bytes(report.get('total_size', 0))}")
        
        # Show directories
        print(f"\n📁 Directories analyzed:")
        for dir_name, dir_info in report.get('directories', {}).items():
            size = dir_info.get('size', 0)
            print(f"  {dir_name}: {analyzer.format_bytes(size)}")
        
        # Show recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:5]:  # Show top 5
                print(f"  • {rec}")
        
        # Interactive file analysis
        print(f"\n🔍 Interactive Analysis")
        print("Enter file paths to analyze (or 'quit' to exit):")
        
        while True:
            try:
                path = input("\nFile path: ").strip()
                if path.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not path:
                    continue
                
                if not os.path.exists(path):
                    print(f"❌ Path does not exist: {path}")
                    continue
                
                # Analyze file
                analysis = file_analyzer.analyze_file(path)
                print(f"\n📋 Analysis for: {path}")
                print(f"  Size: {analysis.get('size', 'N/A')} bytes")
                print(f"  Safety Level: {analysis.get('safety_level', 'Unknown')}")
                print(f"  Importance Score: {analysis.get('importance_score', 0)}/100")
                print(f"  Recommendation: {analysis.get('recommendation', 'Unknown')}")
                print(f"  Modified: {analysis.get('modification_date', 'Unknown')}")
                
                # Safety check
                is_safe = safety.is_path_safe(path)
                print(f"  Safe to delete: {'Yes' if is_safe else 'No'}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error analyzing path: {e}")
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
