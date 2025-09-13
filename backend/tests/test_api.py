"""
Tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "F1 Undercut Simulator" in data["message"]


def test_simulate_endpoint_success():
    """Test POST /simulate returns status 200 and has expected JSON keys."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 1000  # Use smaller sample for faster testing
    }
    
    response = client.post("/simulate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required keys
    required_keys = ["p_undercut", "pitLoss_s", "outLapDelta_s", "assumptions"]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    
    # Check data types
    assert isinstance(data["p_undercut"], (int, float))
    assert isinstance(data["pitLoss_s"], (int, float))
    assert isinstance(data["outLapDelta_s"], (int, float))
    assert isinstance(data["assumptions"], dict)
    
    # Check reasonable ranges
    assert 0.0 <= data["p_undercut"] <= 1.0
    assert 10.0 <= data["pitLoss_s"] <= 60.0
    assert 0.0 <= data["outLapDelta_s"] <= 5.0


def test_simulate_endpoint_deterministic():
    """Test that simulate endpoint returns deterministic results."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER", 
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 1000
    }
    
    # Make two identical requests
    response1 = client.post("/simulate", json=payload)
    response2 = client.post("/simulate", json=payload)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Results should be identical due to deterministic RNG
    assert abs(data1["p_undercut"] - data2["p_undercut"]) < 1e-6
    assert abs(data1["pitLoss_s"] - data2["pitLoss_s"]) < 1e-6
    assert abs(data1["outLapDelta_s"] - data2["outLapDelta_s"]) < 1e-6


def test_simulate_endpoint_validation_errors():
    """Test validation errors for simulate endpoint."""
    # Missing required field
    payload = {
        "gp": "monaco",
        "year": 2024,
        # Missing driver_a, driver_b, compound_a, lap_now
    }
    
    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_invalid_compound():
    """Test with invalid compound."""
    payload = {
        "gp": "monaco", 
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "INVALID",  # Invalid compound
        "lap_now": 25,
        "samples": 100
    }
    
    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_edge_cases():
    """Test edge cases for simulate endpoint."""
    # Test with different compounds
    compounds = ["SOFT", "MEDIUM", "HARD"]
    
    for compound in compounds:
        payload = {
            "gp": "silverstone",
            "year": 2024,
            "driver_a": "VER",
            "driver_b": "HAM", 
            "compound_a": compound,
            "lap_now": 30,
            "samples": 1000
        }
        
        response = client.post("/simulate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["assumptions"]["compound_used"] == compound


@pytest.mark.integration
def test_simulate_endpoint_with_real_data():
    """Integration test that would hit real APIs (marked for exclusion in CI)."""
    # This test would be excluded in CI with: pytest -m "not integration"
    payload = {
        "gp": "monaco",
        "year": 2023,  # Different year for integration test
        "driver_a": "VER",
        "driver_b": "LEC",
        "compound_a": "SOFT",
        "lap_now": 20,
        "samples": 100
    }
    
    # This test would actually call real APIs if not mocked
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
