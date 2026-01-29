#!/usr/bin/env python3
"""
Test script for Phase 5: Distribution & Deployment.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_setup_py():
    """Test setup.py configuration"""
    print("\n🔧 Testing setup.py Configuration")
    print("=" * 50)
    
    try:
        # Check if setup.py exists
        setup_file = Path(__file__).parent / "setup.py"
        if not setup_file.exists():
            print("❌ setup.py not found")
            return False
        
        # Test setup.py syntax
        result = subprocess.run([
            sys.executable, "-m", "py_compile", str(setup_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ setup.py syntax is valid")
            
            # Test setup.py configuration
            result = subprocess.run([
                sys.executable, "setup.py", "--help-commands"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ setup.py configuration is valid")
                return True
            else:
                print("❌ setup.py configuration error")
                print(result.stderr)
                return False
        else:
            print("❌ setup.py syntax error")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing setup.py: {e}")
        return False

def test_homebrew_formula():
    """Test Homebrew formula"""
    print("\n🍺 Testing Homebrew Formula")
    print("=" * 50)
    
    try:
        formula_file = Path(__file__).parent / "homebrew" / "macos-cleaner.rb"
        if not formula_file.exists():
            print("❌ Homebrew formula not found")
            return False
        
        # Read formula content
        content = formula_file.read_text()
        
        # Check required elements
        required_elements = [
            "class MacosCleaner",
            "desc ",
            "homepage ",
            "url ",
            "sha256 ",
            "depends_on",
            "def install"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing formula elements: {missing_elements}")
            return False
        
        print("✅ Homebrew formula structure is valid")
        
        # Test formula syntax (basic Ruby check)
        if "sha256_placeholder" in content:
            print("⚠️  Formula contains placeholder SHA256 (expected for development)")
        
        print("✅ Homebrew formula test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Homebrew formula: {e}")
        return False

def test_docker_configuration():
    """Test Docker configuration"""
    print("\n🐳 Testing Docker Configuration")
    print("=" * 50)
    
    try:
        # Check Dockerfile
        dockerfile = Path(__file__).parent / "Dockerfile"
        if not dockerfile.exists():
            print("❌ Dockerfile not found")
            return False
        
        dockerfile_content = dockerfile.read_text()
        
        # Check Dockerfile elements
        required_dockerfile_elements = [
            "FROM python:",
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "EXPOSE 5000",
            "CMD"
        ]
        
        missing_dockerfile = []
        for element in required_dockerfile_elements:
            if element not in dockerfile_content:
                missing_dockerfile.append(element)
        
        if missing_dockerfile:
            print(f"❌ Missing Dockerfile elements: {missing_dockerfile}")
            return False
        
        print("✅ Dockerfile structure is valid")
        
        # Check docker-compose.yml
        compose_file = Path(__file__).parent / "docker-compose.yml"
        if not compose_file.exists():
            print("❌ docker-compose.yml not found")
            return False
        
        compose_content = compose_file.read_text()
        
        # Check docker-compose elements
        required_compose_elements = [
            "version:",
            "services:",
            "maccleaner-web:",
            "build:",
            "ports:"
        ]
        
        missing_compose = []
        for element in required_compose_elements:
            if element not in compose_content:
                missing_compose.append(element)
        
        if missing_compose:
            print(f"❌ Missing docker-compose elements: {missing_compose}")
            return False
        
        print("✅ docker-compose.yml structure is valid")
        
        # Check .dockerignore
        dockerignore = Path(__file__).parent / ".dockerignore"
        if not dockerignore.exists():
            print("⚠️  .dockerignore not found (recommended)")
        else:
            print("✅ .dockerignore found")
        
        print("✅ Docker configuration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Docker configuration: {e}")
        return False

def test_build_scripts():
    """Test build scripts"""
    print("\n🔨 Testing Build Scripts")
    print("=" * 50)
    
    scripts = [
        "scripts/build_app.py",
        "scripts/create_dmg.py", 
        "scripts/build_and_publish.py",
        "scripts/docker_build.py",
        "scripts/update_homebrew.rb",
        "scripts/release.py"
    ]
    
    all_valid = True
    
    for script in scripts:
        script_path = Path(__file__).parent / script
        if not script_path.exists():
            print(f"❌ Script not found: {script}")
            all_valid = False
            continue
        
        # Test script syntax
        result = subprocess.run([
            sys.executable, "-m", "py_compile", str(script_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {script} syntax is valid")
        else:
            print(f"❌ {script} syntax error")
            print(result.stderr)
            all_valid = False
    
    return all_valid

def test_manifest():
    """Test MANIFEST.in"""
    print("\n📦 Testing MANIFEST.in")
    print("=" * 50)
    
    try:
        manifest_file = Path(__file__).parent / "MANIFEST.in"
        if not manifest_file.exists():
            print("❌ MANIFEST.in not found")
            return False
        
        content = manifest_file.read_text()
        
        # Check required includes
        required_includes = [
            "include README.md",
            "include LICENSE",
            "recursive-include src/mac_cleaner *.py",
            "recursive-include src/mac_cleaner/templates *",
            "include requirements.txt"
        ]
        
        missing_includes = []
        for include in required_includes:
            if include not in content:
                missing_includes.append(include)
        
        if missing_includes:
            print(f"⚠️  Missing recommended includes: {missing_includes}")
        
        # Check for important exclusions
        important_exclusions = [
            "global-exclude *.pyc",
            "global-exclude __pycache__",
            "prune build",
            "prune dist"
        ]
        
        missing_exclusions = []
        for exclusion in important_exclusions:
            if exclusion not in content:
                missing_exclusions.append(exclusion)
        
        if missing_exclusions:
            print(f"⚠️  Missing recommended exclusions: {missing_exclusions}")
        
        print("✅ MANIFEST.in structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing MANIFEST.in: {e}")
        return False

def test_ci_cd_configuration():
    """Test CI/CD configuration"""
    print("\n🔄 Testing CI/CD Configuration")
    print("=" * 50)
    
    try:
        # Check GitHub Actions workflow
        workflow_file = Path(__file__).parent / ".github" / "workflows" / "release.yml"
        if not workflow_file.exists():
            print("❌ GitHub Actions workflow not found")
            return False
        
        content = workflow_file.read_text()
        
        # Check required workflow elements
        required_elements = [
            "on:",
            "push:",
            "tags:",
            "jobs:",
            "test:",
            "build:",
            "publish:",
            "create-release:"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing workflow elements: {missing_elements}")
            return False
        
        print("✅ GitHub Actions workflow structure is valid")
        
        # Check for security best practices
        security_elements = [
            "permissions:",
            "environment: release",
            "secrets.PYPI_API_TOKEN"
        ]
        
        missing_security = []
        for element in security_elements:
            if element not in content:
                missing_security.append(element)
        
        if missing_security:
            print(f"⚠️  Missing security elements: {missing_security}")
        
        print("✅ CI/CD configuration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing CI/CD configuration: {e}")
        return False

def test_package_structure():
    """Test package structure for distribution"""
    print("\n📁 Testing Package Structure")
    print("=" * 50)
    
    try:
        # Check core package structure
        required_dirs = [
            "src/mac_cleaner",
            "src/mac_cleaner/core",
            "src/mac_cleaner/plugins",
            "src/mac_cleaner/gui",
            "src/mac_cleaner/web",
            "src/mac_cleaner/utils"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = Path(__file__).parent / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            print(f"❌ Missing directories: {missing_dirs}")
            return False
        
        print("✅ Package structure is valid")
        
        # Check required files
        required_files = [
            "src/mac_cleaner/__init__.py",
            "src/mac_cleaner/core/__init__.py",
            "src/mac_cleaner/__version__.py",
            "README.md",
            "LICENSE",
            "requirements.txt",
            "pyproject.toml"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = Path(__file__).parent / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"⚠️  Missing files: {missing_files}")
        
        print("✅ Package structure test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing package structure: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Phase 5: Distribution & Deployment Test Suite")
    print("=" * 60)
    print("Testing distribution and deployment configuration")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Setup Configuration", test_setup_py()))
    test_results.append(("Homebrew Formula", test_homebrew_formula()))
    test_results.append(("Docker Configuration", test_docker_configuration()))
    test_results.append(("Build Scripts", test_build_scripts()))
    test_results.append(("MANIFEST.in", test_manifest()))
    test_results.append(("CI/CD Configuration", test_ci_cd_configuration()))
    test_results.append(("Package Structure", test_package_structure()))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 5 tests passed successfully!")
        print("\n📦 Distribution and deployment is ready!")
        print("🚀 You can now build and release the application!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    # Run the test suite
    exit_code = main()
    sys.exit(exit_code)
