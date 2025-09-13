"""
Smoke tests for core API behavior.

These tests verify that the basic API functionality works correctly
with mocked services and returns expected response structure.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import app


client = TestClient(app)


def test_api_smoke_simulate_endpoint():
    """Smoke test: POST /simulate with patched services returns 200 and expected keys."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100
    }
    
    response = client.post("/simulate", json=payload)
    
    # Should return 200 OK
    assert response.status_code == 200
    
    data = response.json()
    
    # Should have all required keys
    required_keys = ["p_undercut", "pitLoss_s", "outLapDelta_s"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Should have reasonable value ranges
    assert 0.0 <= data["p_undercut"] <= 1.0, "Probability should be between 0 and 1"
    assert 10.0 <= data["pitLoss_s"] <= 60.0, "Pit loss should be reasonable"
    assert 0.0 <= data["outLapDelta_s"] <= 5.0, "Outlap delta should be reasonable"
    
    # Should have assumptions key
    assert "assumptions" in data, "Should include assumptions"
    assert isinstance(data["assumptions"], dict), "Assumptions should be a dict"


def test_api_smoke_health_endpoint():
    """Smoke test: Health endpoint returns expected response."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_smoke_root_endpoint():
    """Smoke test: Root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "F1 Undercut Simulator" in data["message"]


def test_api_smoke_models_status():
    """Smoke test: Models status endpoint returns expected structure."""
    response = client.get("/api/v1/models/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have models and api_clients keys
    assert "models" in data
    assert "api_clients" in data
    
    # Should have model status information
    models = data["models"]
    assert "deg_model" in models
    assert "pit_model" in models
    assert "outlap_model" in models
    
    # Should have API client information
    api_clients = data["api_clients"]
    assert "openf1_client" in api_clients
    assert "jolpica_client" in api_clients