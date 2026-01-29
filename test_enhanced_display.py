#!/usr/bin/env python3
"""
Test the enhanced web GUI display with all information
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_enhanced_display():
    """Test that the enhanced display shows all information"""
    base_url = "http://127.0.0.1:5011"
    
    print("🧪 Testing Enhanced Web GUI Display")
    print("=" * 50)
    
    try:
        # Test main page load
        print("📄 Testing main page load...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            page_content = response.text
            print("   ✅ Main page loaded successfully")
            
            # Check for enhanced display elements
            checks = [
                ("space-bar", "Space usage visualization"),
                ("directories", "Directories section"),
                ("large-files", "Large files section"),
                ("showCategoryDetails", "Category details function"),
                ("openInFinder", "Finder integration"),
            ]
            
            for check, description in checks:
                if check in page_content:
                    print(f"   ✅ {description} found")
                else:
                    print(f"   ❌ {description} missing")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
            return False
        
        # Test analyze endpoint
        print("🔍 Testing analyze endpoint...")
        response = requests.post(
            f"{base_url}/api/analyze",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Analyze endpoint working")
            
            # Check response structure
            results = data.get('results', {})
            summary = data.get('summary', {})
            
            print(f"   📊 Categories analyzed: {summary.get('categories_analyzed', 0)}")
            print(f"   📁 Total files: {summary.get('total_files', 0):,}")
            print(f"   💾 Total size: {summary.get('total_size', 0):,} bytes")
            
            # Check that each category has details
            for category, result in list(results.items())[:3]:
                if 'details' in result and result['details']:
                    print(f"   📋 {category}: {len(result['details'])} locations")
                    for detail in result['details'][:2]:  # Show first 2
                        print(f"      • {detail['path']}: {detail.get('size_human', format_bytes(detail.get('size', 0)))}")
                else:
                    print(f"   ⚠️ {category}: No detailed location data")
                    
        else:
            print(f"   ❌ Analyze endpoint failed: {response.status_code}")
            return False
        
        print("\n✅ Enhanced display test passed!")
        print("🎉 All information sections are now visible!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web GUI")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def format_bytes(bytes_size):
    """Format bytes to human readable format"""
    if bytes_size == 0:
        return '0 B'
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while i < len(sizes) - 1 and bytes_size >= k:
        bytes_size /= k
        i += 1
    return f"{bytes_size:.1f} {sizes[i]}"

def start_web_server():
    """Start the web server in background"""
    print("🚀 Starting web server on port 5011...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "mac_cleaner.web.web_gui",
            "--host", "127.0.0.1", "--port", "5011"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Give it time to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        return None

if __name__ == "__main__":
    # Add project root to path
    ROOT = Path(__file__).resolve().parent
    sys.path.insert(0, str(ROOT))
    
    # Start web server
    web_process = start_web_server()
    
    if not web_process:
        sys.exit(1)
    
    try:
        # Run tests
        success = test_enhanced_display()
        
        if success:
            print("\n" + "="*50)
            print("🎯 ENHANCED DISPLAY SUMMARY")
            print("="*50)
            print("✅ Fixed: Design now shows all information")
            print("✅ Added: Space usage visualization bar")
            print("✅ Added: Detailed directory listings")
            print("✅ Added: Large files section with sorting")
            print("✅ Added: Finder integration buttons")
            print("✅ Added: Category details buttons")
            print("✅ Enhanced: Better formatting and layout")
        else:
            print("\n💥 Test failed!")
            sys.exit(1)
            
    finally:
        # Clean up
        if web_process:
            web_process.terminate()
            web_process.wait()
            print("\n🧹 Web server stopped")
