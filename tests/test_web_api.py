#!/usr/bin/env python3
"""
Tests for web API interface.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

from web_gui import app


def test_api_status_returns_json():
    client = app.test_client()
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert "status" in payload
    assert "progress" in payload
    assert "message" in payload
