"""
Tests for FastAPI endpoints with comprehensive validation testing
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint returns correct format."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


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
        "samples": 1000,  # Use smaller sample for faster testing
    }

    response = client.post("/simulate", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Check required keys
    required_keys = [
        "p_undercut",
        "pitLoss_s",
        "outLapDelta_s",
        "avgMargin_s",
        "assumptions",
    ]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"

    # Check data types
    assert isinstance(data["p_undercut"], (int, float))
    assert isinstance(data["pitLoss_s"], (int, float))
    assert isinstance(data["outLapDelta_s"], (int, float))
    assert isinstance(data["avgMargin_s"], (int, float)) or data["avgMargin_s"] is None
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
        "samples": 1000,
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
    error_data = response.json()
    assert "detail" in error_data


def test_simulate_endpoint_invalid_compound():
    """Test with invalid compound."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "INVALID",  # Invalid compound
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_invalid_gp():
    """Test with invalid Grand Prix circuit."""
    payload = {
        "gp": "invalid_circuit",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_negative_lap():
    """Test with negative lap number."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": -1,  # Invalid negative lap
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_lap_too_high():
    """Test with lap number exceeding maximum."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 101,  # Invalid: exceeds max of 100
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_samples_too_low():
    """Test with samples below minimum."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 0,  # Invalid: below minimum of 1
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_samples_too_high():
    """Test with samples exceeding maximum."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 10001,  # Invalid: exceeds max of 10000
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_year_too_low():
    """Test with year below minimum."""
    payload = {
        "gp": "monaco",
        "year": 2019,  # Invalid: below minimum of 2020
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_year_too_high():
    """Test with year exceeding maximum."""
    payload = {
        "gp": "monaco",
        "year": 2025,  # Invalid: exceeds maximum of 2024
        "driver_a": "VER",
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_empty_driver_names():
    """Test with empty driver names."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "",  # Invalid: empty string
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_driver_name_too_long():
    """Test with driver name exceeding maximum length."""
    payload = {
        "gp": "monaco",
        "year": 2024,
        "driver_a": "A" * 51,  # Invalid: exceeds max length of 50
        "driver_b": "HAM",
        "compound_a": "SOFT",
        "lap_now": 25,
        "samples": 100,
    }

    response = client.post("/simulate", json=payload)
    assert response.status_code == 422  # Validation error


def test_simulate_endpoint_valid_compounds():
    """Test all valid tire compounds."""
    valid_compounds = ["SOFT", "MEDIUM", "HARD"]

    for compound in valid_compounds:
        payload = {
            "gp": "monaco",
            "year": 2024,
            "driver_a": "VER",
            "driver_b": "HAM",
            "compound_a": compound,
            "lap_now": 25,
            "samples": 100,
        }

        response = client.post("/simulate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["assumptions"]["compound_used"] == compound


def test_simulate_endpoint_valid_gp_circuits():
    """Test all valid Grand Prix circuits."""
    valid_circuits = [
        "bahrain",
        "imola",
        "monza",
        "monaco",
        "spain",
        "canada",
        "austria",
        "silverstone",
        "hungary",
        "belgium",
        "netherlands",
        "italy",
        "singapore",
        "japan",
        "qatar",
        "usa",
        "mexico",
        "brazil",
        "abu_dhabi",
        "australia",
    ]

    for circuit in valid_circuits[:5]:  # Test first 5 to avoid long test times
        payload = {
            "gp": circuit,
            "year": 2024,
            "driver_a": "VER",
            "driver_b": "HAM",
            "compound_a": "SOFT",
            "lap_now": 25,
            "samples": 100,
        }

        response = client.post("/simulate", json=payload)
        assert response.status_code == 200


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
            "samples": 1000,
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
        "samples": 100,
    }

    # This test would actually call real APIs if not mocked
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
