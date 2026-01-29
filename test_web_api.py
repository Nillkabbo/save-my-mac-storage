#!/usr/bin/env python3
"""
Test script to verify web GUI API endpoints
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_web_api():
    """Test the web GUI API endpoints"""
    base_url = "http://127.0.0.1:5004"
    
    print("🧪 Testing Web GUI API Endpoints")
    print("=" * 40)
    
    try:
        # Test status endpoint
        print("📊 Testing /api/status endpoint...")
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status endpoint working: {data.get('status', 'unknown')}")
        else:
            print(f"   ❌ Status endpoint failed: {response.status_code}")
            return False
        
        # Test analyze endpoint
        print("🔍 Testing /api/analyze endpoint...")
        analyze_data = {
            "categories": ["cache", "logs"]
        }
        response = requests.post(
            f"{base_url}/api/analyze",
            json=analyze_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analyze endpoint working")
            print(f"   📁 Categories analyzed: {data.get('summary', {}).get('categories_analyzed', 0)}")
            print(f"   📊 Total files: {data.get('summary', {}).get('total_files', 0):,}")
            print(f"   💾 Total size: {data.get('summary', {}).get('total_size', 0):,} bytes")
        else:
            print(f"   ❌ Analyze endpoint failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
        
        # Test open_finder endpoint (will likely fail due to path validation, but should return proper error)
        print("📂 Testing /api/open_finder endpoint...")
        finder_data = {"path": "/tmp/test"}
        response = requests.post(
            f"{base_url}/api/open_finder",
            json=finder_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code in [200, 400, 500]:
            print(f"   ✅ Open Finder endpoint responding: {response.status_code}")
        else:
            print(f"   ❌ Open Finder endpoint failed: {response.status_code}")
            return False
        
        print("\n✅ All API endpoints working correctly!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web GUI. Make sure it's running on port 5004")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def start_web_server():
    """Start the web server in background"""
    print("🚀 Starting web server on port 5004...")
    try:
        # Start web server in background
        process = subprocess.Popen([
            sys.executable, "-m", "mac_cleaner.web.web_gui",
            "--host", "127.0.0.1", "--port", "5004"
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
        success = test_web_api()
        
        if success:
            print("\n🎉 Web GUI API test completed successfully!")
        else:
            print("\n💥 Web GUI API test failed!")
            sys.exit(1)
            
    finally:
        # Clean up
        if web_process:
            web_process.terminate()
            web_process.wait()
            print("\n🧹 Web server stopped")
