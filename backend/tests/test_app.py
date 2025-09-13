"""
Tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app


client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns basic API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "F1 Undercut Simulator API" in data["message"]


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_models_status_endpoint():
    """Test the models status endpoint."""
    response = client.get("/api/v1/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "deg_model" in data["models"]
    assert "pit_model" in data["models"]
    assert "outlap_model" in data["models"]


def test_simulate_endpoint_structure():
    """Test the simulate endpoint returns proper structure."""
    # This should work with the mocked data from conftest.py
    request_body = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM", 
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100
    }
    
    response = client.post("/simulate", json=request_body)
    assert response.status_code == 200
    data = response.json()
    
    # Check required keys exist
    assert "p_undercut" in data
    assert "pitLoss_s" in data
    assert "outLapDelta_s" in data
    assert "assumptions" in data