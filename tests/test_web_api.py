#!/usr/bin/env python3
"""
Tests for web API interface.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from web_gui import app, cleaning_status


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_cleaner():
    """Mock cleaner components"""
    with (
        patch("web_gui.MacCleaner") as mock_cleaner_class,
        patch("web_gui.SafetyManager") as mock_safety_class,
        patch("web_gui.SpaceAnalyzer") as mock_analyzer_class,
    ):

        # Mock cleaner
        mock_cleaner = Mock()
        mock_cleaner_class.return_value = mock_cleaner
        mock_cleaner.clean_category.return_value = {
            "files_deleted": 10,
            "space_freed": 1024,
            "space_freed_human": "1.0 KB",
        }

        # Mock safety manager
        mock_safety = Mock()
        mock_safety_class.return_value = mock_safety
        mock_safety.create_backup.return_value = True

        # Mock space analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.generate_report.return_value = {
            "disk_usage": {
                "total": 1000000000000,
                "used": 500000000000,
                "free": 500000000000,
                "usage_percent": 50.0,
            },
            "top_recommendations": [
                {
                    "location": "/tmp",
                    "reason": "Temporary files",
                    "size_human": "100 MB",
                    "priority": "medium",
                }
            ],
            "user_directories": {
                "directories": {
                    "Downloads": {
                        "path": "/Users/test/Downloads",
                        "size_human": "50 MB",
                        "safe_to_delete": True,
                        "recommendation": "Review old files",
                    }
                }
            },
            "large_files": [
                {
                    "path": "/Users/test/large_file.zip",
                    "size_human": "25 MB",
                    "age_days": 30,
                }
            ],
        }

        yield mock_cleaner, mock_safety, mock_analyzer


class TestAPIStatus:
    """Test API status endpoint"""

    def test_api_status_returns_json(self, client):
        """Test status endpoint returns proper JSON"""
        response = client.get("/api/status")
        assert response.status_code == 200
        payload = response.get_json()
        assert "status" in payload
        assert "progress" in payload
        assert "message" in payload

    def test_api_status_default_values(self, client):
        """Test status endpoint has default values"""
        response = client.get("/api/status")
        payload = response.get_json()
        assert payload["status"] == "idle"
        assert payload["progress"] == 0


class TestAPIAnalyze:
    """Test API analyze endpoint"""

    def test_api_analyze_success(self, client, mock_cleaner):
        """Test analyze endpoint starts analysis"""
        response = client.get("/api/analyze")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "started" in payload["message"].lower()

    def test_api_analyze_rate_limit(self, client):
        """Test analyze endpoint has rate limiting"""
        # Make multiple requests quickly
        responses = []
        for _ in range(25):  # Exceed the 20 per minute limit
            responses.append(client.get("/api/analyze"))

        # Should eventually hit rate limit
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Should hit rate limit after many requests"


class TestAPIClean:
    """Test API clean endpoint"""

    def test_api_clean_success(self, client, mock_cleaner):
        """Test clean endpoint starts cleaning"""
        data = {"dry_run": True, "categories": ["cache", "temp"]}
        response = client.post("/api/clean", json=data, content_type="application/json")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "started" in payload["message"].lower()

    def test_api_clean_invalid_categories(self, client):
        """Test clean endpoint rejects invalid categories"""
        data = {"dry_run": True, "categories": "invalid"}  # Should be a list
        response = client.post("/api/clean", json=data)
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is False
        assert "Categories must be a list" in payload["error"]

    def test_api_clean_missing_data(self, client):
        """Test clean endpoint handles missing data"""
        response = client.post("/api/clean", json={})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True  # Should use defaults

    def test_api_clean_rate_limit(self, client):
        """Test clean endpoint has rate limiting"""
        data = {"dry_run": True, "categories": ["cache"]}

        # Make multiple requests quickly
        responses = []
        for _ in range(8):  # Exceed the 5 per minute limit
            responses.append(client.post("/api/clean", json=data))

        # Should eventually hit rate limit
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Should hit rate limit after many requests"


class TestAPIOpenFinder:
    """Test API open finder endpoint"""

    def test_api_open_finder_success(self, client):
        """Test open finder endpoint with valid path"""
        with (
            patch("web_gui.validate_finder_path") as mock_validate,
            patch("subprocess.run") as mock_subprocess,
        ):

            mock_validate.return_value = (True, "", "/Users/test")

            data = {"path": "/Users/test"}
            response = client.post("/api/open_finder", json=data)

            assert response.status_code == 200
            payload = response.get_json()
            assert payload["success"] is True
            assert "opened" in payload["message"].lower()

    def test_api_open_finder_invalid_path(self, client):
        """Test open finder endpoint with invalid path"""
        data = {"path": ""}  # Empty path
        response = client.post("/api/open_finder", json=data)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is False
        assert "No path specified" in payload["error"]

    def test_api_open_finder_non_string_path(self, client):
        """Test open finder endpoint with non-string path"""
        data = {"path": 123}  # Not a string
        response = client.post("/api/open_finder", json=data)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is False
        assert "Invalid path" in payload["error"]

    def test_api_open_finder_unsafe_path(self, client):
        """Test open finder endpoint with unsafe path"""
        with patch("web_gui.validate_finder_path") as mock_validate:
            mock_validate.return_value = (False, "Path not allowed", "")

            data = {"path": "/etc/passwd"}
            response = client.post("/api/open_finder", json=data)

            assert response.status_code == 200
            payload = response.get_json()
            assert payload["success"] is False
            assert "not allowed" in payload["error"]

    def test_api_open_finder_rate_limit(self, client):
        """Test open finder endpoint has rate limiting"""
        with patch("web_gui.validate_finder_path") as mock_validate:
            mock_validate.return_value = (True, "", "/Users/test")

            data = {"path": "/Users/test"}

            # Make multiple requests quickly
            responses = []
            for _ in range(35):  # Exceed the 30 per minute limit
                responses.append(client.post("/api/open_finder", json=data))

            # Should eventually hit rate limit
            rate_limited = any(r.status_code == 429 for r in responses)
            assert rate_limited, "Should hit rate limit after many requests"


class TestAPIBackup:
    """Test API backup endpoint"""

    def test_api_backup_success(self, client):
        """Test backup endpoint with valid path"""
        with patch("web_gui.validate_finder_path") as mock_validate:
            mock_validate.return_value = (True, "", "/Users/test")

            data = {"path": "/Users/test"}
            response = client.post("/api/backup", json=data)

            assert response.status_code == 200
            payload = response.get_json()
            assert payload["success"] is True
            assert payload["backup_path"] == "/Users/test"

    def test_api_backup_invalid_path(self, client):
        """Test backup endpoint with invalid path"""
        data = {"path": ""}  # Empty path
        response = client.post("/api/backup", json=data)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is False
        assert "No path specified" in payload["error"]

    def test_api_backup_unsafe_path(self, client):
        """Test backup endpoint with unsafe path"""
        with patch("web_gui.validate_finder_path") as mock_validate:
            mock_validate.return_value = (False, "Path not allowed", "")

            data = {"path": "/etc/passwd"}
            response = client.post("/api/backup", json=data)

            assert response.status_code == 200
            payload = response.get_json()
            assert payload["success"] is False
            assert "not allowed" in payload["error"]

    def test_api_backup_rate_limit(self, client):
        """Test backup endpoint has rate limiting"""
        with patch("web_gui.validate_finder_path") as mock_validate:
            mock_validate.return_value = (True, "", "/Users/test")

            data = {"path": "/Users/test"}

            # Make multiple requests quickly
            responses = []
            for _ in range(12):  # Exceed the 10 per minute limit
                responses.append(client.post("/api/backup", json=data))

            # Should eventually hit rate limit
            rate_limited = any(r.status_code == 429 for r in responses)
            assert rate_limited, "Should hit rate limit after many requests"


class TestWebInterface:
    """Test web interface endpoints"""

    def test_index_page_loads(self, client):
        """Test main index page loads"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"macOS Cleaner" in response.data
        assert b"Analyze System" in response.data

    def test_index_page_uses_template(self, client):
        """Test index page uses proper template"""
        response = client.get("/")
        assert response.status_code == 200
        # Should contain HTML structure
        assert b"<!DOCTYPE html>" in response.data
        assert b"<html" in response.data


class TestCSRFProtection:
    """Test CSRF protection"""

    def test_csrf_token_in_template(self, client):
        """Test CSRF token is available in template"""
        app.config["WTF_CSRF_ENABLED"] = True
        response = client.get("/")
        assert response.status_code == 200
        # The template should have access to csrf_token()
        # This is tested implicitly by the template rendering successfully


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/clean", data="invalid json", content_type="application/json"
        )
        # Should handle gracefully
        assert response.status_code == 200

    def test_missing_content_type(self, client):
        """Test handling of missing content type"""
        response = client.post("/api/clean", data='{"dry_run": true}')
        # Should handle gracefully
        assert response.status_code == 200

    def test_large_payload(self, client):
        """Test handling of large payload"""
        large_data = {"categories": ["cache"] * 1000, "dry_run": True}  # Large array
        response = client.post("/api/clean", json=large_data)
        # Should handle gracefully or reject appropriately
        assert response.status_code in [200, 413]


class TestBackgroundOperations:
    """Test background operation handling"""

    def test_analysis_background_execution(self, client, mock_cleaner):
        """Test analysis runs in background"""
        # Start analysis
        response = client.get("/api/analyze")
        assert response.status_code == 200

        # Check status changes
        import time

        time.sleep(0.1)  # Allow background thread to start

        status_response = client.get("/api/status")
        status = status_response.get_json()

        # Should have progressed beyond idle
        assert status["status"] in ["analyzing", "completed", "error"]

    def test_cleaning_background_execution(self, client, mock_cleaner):
        """Test cleaning runs in background"""
        data = {"dry_run": True, "categories": ["cache"]}

        # Start cleaning
        response = client.post("/api/clean", json=data)
        assert response.status_code == 200

        # Check status changes
        import time

        time.sleep(0.1)  # Allow background thread to start

        status_response = client.get("/api/status")
        status = status_response.get_json()

        # Should have progressed beyond idle
        assert status["status"] in ["running", "completed", "error"]
