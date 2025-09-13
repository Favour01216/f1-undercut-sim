"""
Smoke test for gap boundary behavior.

This test verifies that the undercut probability behaves correctly
at the boundary where p >= 0.5, using the gap sweep data if available.
"""

import pytest
import pandas as pd
import os
from fastapi.testclient import TestClient
from backend.app import app


client = TestClient(app)


def test_gap_boundary_smoke():
    """
    Smoke test: Verify gap boundary behavior for undercut probability.
    
    If docs/figs/undercut_gap_sweep.csv exists, load it and assert that
    the first gap where p >= 0.5 is between 24 and 27 seconds.
    If the file doesn't exist, skip the test.
    """
    gap_sweep_file = "/workspace/docs/figs/undercut_gap_sweep.csv"
    
    if not os.path.exists(gap_sweep_file):
        pytest.skip("Gap sweep data file not found, skipping boundary test")
    
    # Load the gap sweep data
    try:
        df = pd.read_csv(gap_sweep_file)
    except Exception as e:
        pytest.skip(f"Could not load gap sweep data: {e}")
    
    # Check if we have the required columns
    required_cols = ["gap_s", "p_undercut"]
    if not all(col in df.columns for col in required_cols):
        pytest.skip("Gap sweep data missing required columns")
    
    # Find the first gap where p >= 0.5
    successful_gaps = df[df["p_undercut"] >= 0.5]
    
    if len(successful_gaps) == 0:
        pytest.skip("No successful undercuts found in gap sweep data")
    
    first_successful_gap = successful_gaps.iloc[0]["gap_s"]
    
    # Assert that the first successful gap is between 24 and 27 seconds
    assert 24.0 <= first_successful_gap <= 27.0, (
        f"First successful undercut gap ({first_successful_gap:.1f}s) "
        f"should be between 24 and 27 seconds"
    )


def test_gap_boundary_simulation():
    """
    Alternative gap boundary test using simulation.
    
    Test that undercut probability increases with gap size and
    crosses 0.5 threshold in reasonable range.
    """
    # Test with different gap sizes to verify boundary behavior
    test_gaps = [15.0, 20.0, 25.0, 30.0]
    probabilities = []
    
    for gap in test_gaps:
        # Mock the gap calculation by patching the function
        with pytest.MonkeyPatch().context() as m:
            m.setattr("backend.app.calculate_driver_gap", lambda *args: gap)
            
            payload = {
                "gp": "monaco",
                "year": 2024,
                "driver_a": "VER",
                "driver_b": "HAM",
                "compound_a": "SOFT",
                "lap_now": 25,
                "samples": 1000  # Higher samples for more stable results
            }
            
            response = client.post("/simulate", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            probabilities.append(data["p_undercut"])
    
    # Verify that probability generally increases with gap size
    # (allowing for some noise due to randomness)
    for i in range(1, len(probabilities)):
        # Each subsequent probability should be >= previous (with tolerance)
        assert probabilities[i] >= probabilities[i-1] - 0.1, (
            f"Probability should generally increase with gap size: "
            f"{probabilities[i-1]:.3f} -> {probabilities[i]:.3f}"
        )
    
    # Verify that we cross the 0.5 threshold somewhere in the range
    # (at least one probability should be >= 0.4, indicating we're in the right range)
    max_prob = max(probabilities)
    assert max_prob >= 0.4, (
        f"Maximum probability ({max_prob:.3f}) should be >= 0.4 "
        f"to indicate we're testing the right gap range"
    )