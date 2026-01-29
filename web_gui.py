#!/usr/bin/env python3
"""
Web-based GUI for macOS Cleaner
Provides a browser-based interface when tkinter is not available
"""

import os
import sys
import json
import threading
import time
from pathlib import Path
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

SRC_ROOT = Path(__file__).resolve().parent / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

from mac_cleaner.mac_cleaner import MacCleaner
from mac_cleaner.safety_manager import SafetyManager
from mac_cleaner.space_analyzer import SpaceAnalyzer
from mac_cleaner.security import validate_finder_path
from mac_cleaner.categories import CATEGORY_MAP
from mac_cleaner.config import get_allowed_finder_roots, get_allowed_backup_roots

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("MAC_CLEANER_SECRET_KEY") or "dev-change-me"
app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]
csrf = CSRFProtect(app)
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


# Global cleaner instance
cleaner = None
safety_manager = None
space_analyzer = None
cleaning_status = {"status": "idle", "progress": 0, "message": "", "results": {}}


def initialize_cleaner():
    """Initialize the cleaner and safety manager"""
    global cleaner, safety_manager, space_analyzer
    try:
        cleaner = MacCleaner()
        safety_manager = SafetyManager()
        space_analyzer = SpaceAnalyzer()
        return True
    except Exception as e:
        print(f"Error initializing cleaner: {e}")
        return False


@app.route("/")
def index():
    """Main dashboard page"""
    try:
        # Don't initialize here - let it load quickly
        return render_template("index.html")
    except Exception as e:
        return f"Error loading dashboard: {e}", 500


@app.route("/api/analyze")
@limiter.limit("20 per minute")
def api_analyze():
    """Analyze system space asynchronously"""
    try:
        if not space_analyzer:
            initialize_cleaner()
        if not space_analyzer:
            return jsonify({"success": False, "error": "Analyzer unavailable"})

        # Start analysis in background thread
        def analyze_background():
            global cleaning_status
            try:
                cleaning_status["status"] = "analyzing"
                cleaning_status["progress"] = 0
                cleaning_status["message"] = "Analyzing disk usage..."

                space_report = space_analyzer.generate_report()

                cleaning_status["status"] = "completed"
                cleaning_status["progress"] = 100
                cleaning_status["message"] = "Analysis complete!"
                cleaning_status["space_report"] = space_report

            except Exception as e:
                cleaning_status["status"] = "error"
                cleaning_status["message"] = f"Error: {str(e)}"

        threading.Thread(target=analyze_background, daemon=True).start()

        return jsonify({"success": True, "message": "Analysis started"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/open_finder", methods=["POST"])
@limiter.limit("30 per minute")
def api_open_finder():
    """Open directory in Finder"""
    try:
        data = request.get_json(silent=True) or {}
        path = data.get("path")
        if not isinstance(path, str):
            return jsonify({"success": False, "error": "Invalid path"})
        allowed_roots = get_allowed_finder_roots()
        is_valid, error_message, safe_path = validate_finder_path(path, allowed_roots)
        if not is_valid:
            return jsonify({"success": False, "error": error_message})

        subprocess.run(["open", "-R", safe_path], check=True)

        return jsonify({"success": True, "message": f"Opened {safe_path} in Finder"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/clean", methods=["POST"])
@limiter.limit("5 per minute")
def api_clean():
    """Start cleaning process"""
    try:
        data = request.get_json(silent=True) or {}
        dry_run = bool(data.get("dry_run", True))
        categories = data.get("categories", ["cache", "temp", "logs"])
        if not isinstance(categories, list):
            return jsonify({"success": False, "error": "Categories must be a list"})

        if not cleaner:
            initialize_cleaner()
        if not cleaner:
            return jsonify({"success": False, "error": "Cleaner unavailable"})

        # Start cleaning in background thread
        def clean_background():
            global cleaning_status
            try:
                cleaning_status["status"] = "running"
                cleaning_status["progress"] = 0
                cleaning_status["message"] = "Starting cleaning process..."

                results = {}
                total_steps = len(categories)

                for i, category in enumerate(categories):
                    cleaning_status["progress"] = int((i / total_steps) * 100)
                    cleaning_status["message"] = f"Cleaning {category}..."

                    mapped = CATEGORY_MAP.get(category, [])
                    if not mapped:
                        results[category] = {"error": "Unknown category"}
                        continue

                    category_results = []
                    for mapped_category in mapped:
                        category_results.append(
                            cleaner.clean_category(mapped_category, dry_run=dry_run)
                        )
                    results[category] = category_results

                cleaning_status["status"] = "completed"
                cleaning_status["progress"] = 100
                cleaning_status["message"] = "Cleaning completed!"
                cleaning_status["results"] = results

            except Exception as e:
                cleaning_status["status"] = "error"
                cleaning_status["message"] = f"Error: {str(e)}"

        threading.Thread(target=clean_background, daemon=True).start()

        return jsonify({"success": True, "message": "Cleaning started"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/status")
def api_status():
    """Get current cleaning status"""
    return jsonify(cleaning_status)


@app.route("/api/backup", methods=["POST"])
@limiter.limit("10 per minute")
def api_backup():
    """Create system backup"""
    try:
        if not safety_manager:
            initialize_cleaner()
        if not safety_manager:
            return jsonify({"success": False, "error": "Backup unavailable"})
        data = request.get_json(silent=True) or {}
        path = data.get("path")
        if not isinstance(path, str):
            return jsonify({"success": False, "error": "Invalid path"})
        allowed_roots = get_allowed_backup_roots()
        is_valid, error_message, safe_path = validate_finder_path(path, allowed_roots)
        if not is_valid:
            return jsonify({"success": False, "error": error_message})

        success = safety_manager.create_backup(safe_path)
        return jsonify({"success": success, "backup_path": safe_path})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def create_templates():
    """Create HTML templates"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(templates_dir, exist_ok=True)


def main():
    """Main function to run the web GUI"""
    print("🌐 Starting macOS Cleaner Web Interface...")

    # Create templates directory
    create_templates()

    # Initialize cleaner
    if not initialize_cleaner():
        print("❌ Failed to initialize cleaner")
        return 1

    # Find available port
    port = 5000
    while port < 5010:
        try:
            app.run(host="127.0.0.1", port=port, debug=False)
            break
        except OSError:
            port += 1

    print(f"🚀 Web interface available at: http://127.0.0.1:{port}")
    print("📋 Open this URL in your browser to use the cleaner")

    return 0


if __name__ == "__main__":
    sys.exit(main())
