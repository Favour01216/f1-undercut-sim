"""
Tests for DegModel (Tire Degradation Model)
"""

import numpy as np
import pandas as pd
import pytest

from backend.models.deg import DegModel


def test_deg_model_fit_predict(sample_lap_data, deterministic_rng):
    """Test DegModel.fit then predict; assert lap times increase with age."""
    model = DegModel()

    # Fit the model
    model.fit(sample_lap_data)

    # Check model is fitted
    assert model.fitted
    assert model.coefficients is not None
    assert len(model.coefficients) == 3  # quadratic: a, b, c
    assert model.baseline_time is not None
    assert model.r_squared is not None

    # Test predictions increase with tire age (degradation)
    age_5 = model.predict(5)
    age_15 = model.predict(15)
    age_25 = model.predict(25)

    # Should be non-negative
    assert age_5 >= 0
    assert age_15 >= 0
    assert age_25 >= 0

    # Should generally increase with age (allowing small tolerance for noise)
    assert age_25 > age_5 - 0.1  # Allow small tolerance

    # R-squared should be reasonable for synthetic data
    assert model.r_squared > 0.5


def test_deg_model_predict_batch(sample_lap_data):
    """Test batch prediction."""
    model = DegModel()
    model.fit(sample_lap_data)

    ages = np.array([1, 10, 20, 30])
    predictions = model.predict_batch(ages)

    assert len(predictions) == len(ages)
    assert all(p >= 0 for p in predictions)

    # Generally increasing trend (with tolerance)
    diffs = np.diff(predictions)
    assert np.mean(diffs) >= -0.05  # Allow small negative differences due to noise


def test_deg_model_empty_data():
    """Test with empty data."""
    model = DegModel()

    with pytest.raises(ValueError, match="empty DataFrame"):
        model.fit(pd.DataFrame())


def test_deg_model_insufficient_data():
    """Test with insufficient data."""
    model = DegModel()
    df = pd.DataFrame({"lap_time": [90.0, 90.5], "tire_age": [1, 2]})

    with pytest.raises(ValueError, match="Insufficient data"):
        model.fit(df)


def test_deg_model_predict_before_fit():
    """Test prediction before fitting."""
    model = DegModel()

    with pytest.raises(RuntimeError, match="must be fitted"):
        model.predict(10)


def test_deg_model_tolerance_comparison():
    """Test predictions with float tolerance."""
    model = DegModel()

    # Create deterministic data
    ages = np.arange(1, 21)
    base_time = 90.0
    lap_times = base_time + 0.05 * ages + 0.001 * ages**2

    df = pd.DataFrame({"lap_time": lap_times, "tire_age": ages})

    model.fit(df)

    # Predict at specific ages
    pred_10 = model.predict(10)
    pred_20 = model.predict(20)

    # Use tolerance for float comparison
    expected_10 = 0.05 * 10 + 0.001 * 10**2  # Expected delta for age 10
    expected_20 = 0.05 * 20 + 0.001 * 20**2  # Expected delta for age 20

    # Should be within reasonable tolerance of expected values
    assert abs(pred_10 - expected_10) < 0.5
    assert abs(pred_20 - expected_20) < 0.5

    # Prediction should increase with age
    assert pred_20 > pred_10
