#!/usr/bin/env python3
"""
Web-based GUI for macOS Cleaner
Provides a browser-based interface when tkinter is not available

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import os
import sys
import json
import threading
import time
import argparse
from pathlib import Path
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify
# from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from mac_cleaner.mac_cleaner import MacCleaner
from mac_cleaner.safety_manager import SafetyManager
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.security import validate_finder_path, SecurityValidator
from mac_cleaner.categories import CATEGORY_MAP
from mac_cleaner.config import get_allowed_finder_roots, get_allowed_backup_roots

app = Flask(__name__, template_folder='templates')
app.config["SECRET_KEY"] = os.environ.get("MAC_CLEANER_SECRET_KEY") or "dev-change-me"

# CSRF protection disabled for development tool
# csrf = CSRFProtect(app)
# app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]

limiter_storage = os.environ.get("MAC_CLEANER_LIMITER_STORAGE")
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=limiter_storage,
)


# Add template filters
@app.template_filter("basename")
def basename_filter(path):
    return os.path.basename(path)


@app.template_filter("dirname")
def dirname_filter(path):
    return os.path.dirname(path)


@app.template_filter("human_size")
def human_size_filter(bytes_size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


# Global variables
cleaner_instance = None
safety_manager = None
space_analyzer = None


def initialize_components():
    """Initialize cleaner components"""
    global cleaner_instance, safety_manager, space_analyzer
    
    if cleaner_instance is None:
        cleaner_instance = MacCleaner()
        safety_manager = SafetyManager()
        space_analyzer = SpaceAnalyzer()


@app.route("/")
def index():
    """Main dashboard page"""
    initialize_components()
    
    try:
        # Get system information
        disk_info = space_analyzer.get_disk_usage() if space_analyzer else {}
        system_info = {
            "platform": os.uname().sysname,
            "release": os.uname().release,
            "machine": os.uname().machine,
        }
        
        return render_template(
            "index.html",
            disk_info=disk_info,
            system_info=system_info,
            categories=CATEGORY_MAP,
        )
    except Exception as e:
        return render_template("error.html", error=str(e))


@app.route("/api/status")
@limiter.limit("10 per minute")
def api_status():
    """Get system status"""
    initialize_components()
    
    try:
        disk_info = space_analyzer.get_disk_usage() if space_analyzer else {}
        return jsonify({
            "status": "ok",
            "disk_info": disk_info,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
@limiter.limit("5 per minute")
def api_analyze():
    """Analyze system for cleaning"""
    initialize_components()
    
    try:
        # Use the correct method that exists in MacCleaner
        analysis = cleaner_instance.analyze_cleanable_space()
        
        # Convert to the expected format
        results = {}
        total_size = 0
        total_files = 0
        
        for category, data in analysis.items():
            results[category] = {
                "total_size": data.get("total_size", 0),
                "total_size_human": data.get("total_size_human", "0 B"),
                "file_count": len(data.get("details", [])),
                "details": data.get("details", [])
            }
            total_size += data.get("total_size", 0)
            total_files += len(data.get("details", []))
        
        # Use the correct method to generate a comprehensive report
        report = space_analyzer.generate_report()
        
        return jsonify({
            "success": True,
            "results": results,
            "space_analyzed": total_size,
            "space_analyzed_human": space_analyzer.format_bytes(total_size),
            "files_analyzed": total_files,
            "disk_usage": report.get("disk_usage", {}),
            "user_directories": report.get("user_directories", {}),
            "top_recommendations": report.get("top_recommendations", []),
            "large_files": report.get("large_files", []),
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/clean", methods=["POST"])
@limiter.limit("2 per minute")
def api_clean():
    """Clean selected categories"""
    initialize_components()
    
    try:
        data = request.get_json() or {}
        categories = data.get("categories", [])
        dry_run = data.get("dry_run", True)
        
        if not categories:
            return jsonify({"error": "No categories specified"}), 400
        
        results = {}
        total_freed = 0
        total_deleted = 0
        
        for category in categories:
            if category in CATEGORY_MAP:
                try:
                    # Create backup if not dry run
                    if not dry_run:
                        safety_manager.create_backup()
                    
                    # Clean category
                    clean_result = cleaner_instance.clean_category(category, dry_run=dry_run)
                    results[category] = clean_result
                    total_freed += clean_result.get("space_freed", 0)
                    total_deleted += clean_result.get("files_deleted", 0)
                except Exception as e:
                    results[category] = {"error": str(e)}
        
        return jsonify({
            "results": results,
            "summary": {
                "total_freed": total_freed,
                "total_deleted": total_deleted,
                "categories_cleaned": len([r for r in results.values() if "error" not in r]),
                "dry_run": dry_run,
            },
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/open_finder", methods=["POST"])
@limiter.limit("20 per minute")
def api_open_finder():
    """Open location in Finder"""
    try:
        data = request.get_json() or {}
        path = data.get("path", "")
        
        if not path:
            return jsonify({"error": "No path specified"}), 400
        
        # Validate path
        allowed_roots = get_allowed_finder_roots()
        is_valid, error_message, safe_path = validate_finder_path(path, allowed_roots)
        if not is_valid:
            return jsonify({"error": f"Invalid path: {error_message}"}), 400
        
        # Open in Finder
        subprocess.run(["open", "-R", safe_path], check=True)
        
        return jsonify({
            "success": True,
            "message": f"Opened {safe_path} in Finder",
            "path": safe_path,
        })
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to open in Finder"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html", error="Internal server error"), 500


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="macOS Cleaner Web GUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Initialize components
    initialize_components()
    
    print(f"🌐 Starting macOS Cleaner Web GUI")
    print(f"📋 Open your browser to: http://{args.host}:{args.port}")
    print(f"🔧 Debug mode: {'enabled' if args.debug else 'disabled'}")
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False,  # Prevent issues with threading
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down web GUI...")
    except Exception as e:
        print(f"❌ Error starting web GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
