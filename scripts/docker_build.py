#!/usr/bin/env python3
"""
Docker build and deployment script for macOS Cleaner.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description="", check=True):
    """Run a command with error handling"""
    if description:
        print(f"🔨 {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def build_docker_image(tag="maccleaner:latest"):
    """Build Docker image"""
    print("🐳 Building Docker Image")
    print("=" * 50)
    
    # Ensure we're in project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Build command
    cmd = f"docker build -t {tag} ."
    
    if run_command(cmd, f"Building Docker image with tag: {tag}"):
        print(f"✅ Docker image built successfully: {tag}")
        return True
    else:
        print("❌ Docker build failed")
        return False

def run_docker_compose(action="up", services=None):
    """Run Docker Compose commands"""
    print("🚀 Running Docker Compose")
    print("=" * 50)
    
    cmd = f"docker-compose {action}"
    if services:
        cmd += f" {' '.join(services)}"
    
    if action in ["up", "start"]:
        cmd += " -d"  # Run detached
    
    if run_command(cmd, f"Docker compose {action}"):
        print(f"✅ Docker compose {action} completed")
        return True
    else:
        print(f"❌ Docker compose {action} failed")
        return False

def show_status():
    """Show Docker container status"""
    print("📊 Docker Container Status")
    print("=" * 50)
    
    run_command("docker ps -a", "Showing all containers", check=False)
    
    print("\n📋 Docker Compose Status")
    run_command("docker-compose ps", "Showing compose status", check=False)

def stop_containers():
    """Stop all containers"""
    print("🛑 Stopping Docker Containers")
    print("=" * 50)
    
    run_command("docker-compose down", "Stopping all containers")
    run_command("docker system prune -f", "Cleaning up unused resources", check=False)

def clean_docker():
    """Clean Docker resources"""
    print("🧹 Cleaning Docker Resources")
    print("=" * 50)
    
    run_command("docker-compose down -v", "Stopping containers and removing volumes")
    run_command("docker system prune -af", "Removing all unused Docker resources")
    run_command("docker volume prune -f", "Removing unused volumes")

def setup_environment():
    """Setup Docker environment"""
    print("⚙️ Setting up Docker Environment")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    # Create necessary directories
    directories = ["logs", "data", "config", "nginx/ssl"]
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Create sample configuration
    config_file = project_root / "config" / "production.yaml"
    if not config_file.exists():
        sample_config = """
# Production configuration for macOS Cleaner
cleaner:
  dry_run_default: true
  backup_enabled: true
  log_level: INFO

security:
  require_confirmation: false
  allow_system_paths: false

web:
  host: "0.0.0.0"
  port: 5000
  debug: false
  secret_key: "change-this-in-production"

logging:
  level: INFO
  file_enabled: true
  file_path: "/app/logs/maccleaner.log"
"""
        config_file.write_text(sample_config)
        print(f"📝 Created sample configuration: {config_file}")
    
    print("✅ Docker environment setup complete")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Docker build and deployment for macOS Cleaner")
    parser.add_argument("action", choices=[
        "build", "up", "down", "restart", "status", "clean", "setup"
    ], help="Action to perform")
    parser.add_argument("--tag", default="maccleaner:latest", help="Docker image tag")
    parser.add_argument("--services", nargs="*", help="Specific services to target")
    
    args = parser.parse_args()
    
    # Ensure we're in project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    success = True
    
    if args.action == "build":
        success = build_docker_image(args.tag)
    
    elif args.action == "up":
        success = run_docker_compose("up", args.services)
    
    elif args.action == "down":
        success = run_docker_compose("down", args.services)
    
    elif args.action == "restart":
        success = run_docker_compose("down", args.services) and run_docker_compose("up", args.services)
    
    elif args.action == "status":
        show_status()
    
    elif args.action == "clean":
        clean_docker()
    
    elif args.action == "setup":
        setup_environment()
    
    if success:
        print("\n🎉 Docker operation completed successfully!")
    else:
        print("\n❌ Docker operation failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
