#!/usr/bin/env python3
"""
Quick test to verify the web GUI frontend is working
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_frontend():
    """Test that the frontend can make API calls successfully"""
    base_url = "http://127.0.0.1:5007"
    
    print("🧪 Testing Frontend Integration")
    print("=" * 40)
    
    try:
        # Test that we can load the main page
        print("📄 Testing main page load...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Main page loaded successfully")
            # Check that the page contains our JavaScript
            if "startAnalysis" in response.text:
                print("   ✅ JavaScript functions found in page")
            else:
                print("   ❌ JavaScript functions not found")
                return False
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
            return False
        
        # Test that the analyze API works
        print("🔍 Testing analyze API...")
        analyze_data = {
            "categories": ["cache", "logs", "temp"]
        }
        response = requests.post(
            f"{base_url}/api/analyze",
            json=analyze_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Analyze API working")
            print(f"   📊 Response structure: {list(data.keys())}")
        else:
            print(f"   ❌ Analyze API failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
        
        print("\n✅ Frontend integration test passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web GUI")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def start_web_server():
    """Start the web server in background"""
    print("🚀 Starting web server on port 5007...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "mac_cleaner.web.web_gui",
            "--host", "127.0.0.1", "--port", "5007"
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
        success = test_frontend()
        
        if success:
            print("\n🎉 Frontend integration test completed successfully!")
            print("💡 The web GUI should now work without CSRF token errors")
        else:
            print("\n💥 Frontend integration test failed!")
            sys.exit(1)
            
    finally:
        # Clean up
        if web_process:
            web_process.terminate()
            web_process.wait()
            print("\n🧹 Web server stopped")
