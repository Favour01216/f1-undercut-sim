"""
Tests for PitModel (Pit Stop Time Loss Model)
"""

import pytest
import numpy as np
import pandas as pd
from models.pit import PitModel


def test_pit_model_sample_deterministic(sample_pit_data, deterministic_rng):
    """Test PitModel.sample with deterministic RNG."""
    model = PitModel()
    model.fit(sample_pit_data)
    
    # Test reproducible sampling
    samples1 = model.sample(100, rng=deterministic_rng)
    
    # Reset RNG with same seed
    rng2 = np.random.default_rng(seed=42)
    samples2 = model.sample(100, rng=rng2)
    
    # Should be identical
    np.testing.assert_array_equal(samples1, samples2)


def test_pit_model_sample_mean_within_tolerance(sample_pit_data, deterministic_rng):
    """Test PitModel.sample mean within 3σ/√n tolerance."""
    model = PitModel()
    model.fit(sample_pit_data)
    
    n = 1000
    samples = model.sample(n, rng=deterministic_rng)
    
    sample_mean = np.mean(samples)
    expected_mean = model.mean_loss
    expected_std = model.std_loss
    
    # Statistical tolerance: 3σ/√n
    tolerance = 3 * expected_std / np.sqrt(n)
    
    assert abs(sample_mean - expected_mean) < tolerance
    
    # All samples should be within reasonable bounds
    assert all(10 <= s <= 60 for s in samples)


def test_pit_model_single_sample(sample_pit_data, deterministic_rng):
    """Test single sample returns float, not array."""
    model = PitModel()
    model.fit(sample_pit_data)
    
    single_sample = model.sample(1, rng=deterministic_rng)
    
    assert isinstance(single_sample, (float, np.floating))
    assert 10 <= single_sample <= 60


def test_pit_model_multiple_samples(sample_pit_data, deterministic_rng):
    """Test multiple samples returns array."""
    model = PitModel()
    model.fit(sample_pit_data)
    
    samples = model.sample(10, rng=deterministic_rng)
    
    assert isinstance(samples, np.ndarray)
    assert len(samples) == 10
    assert all(10 <= s <= 60 for s in samples)


def test_pit_model_fit_requirements(sample_pit_data):
    """Test model fitting requirements."""
    model = PitModel()
    
    # Should fit successfully
    result = model.fit(sample_pit_data)
    assert result is model  # Method chaining
    assert model.fitted
    assert model.mean_loss is not None
    assert model.std_loss is not None
    assert model.sample_count > 0


def test_pit_model_empty_data():
    """Test with empty data."""
    model = PitModel()
    
    with pytest.raises(ValueError, match="empty DataFrame"):
        model.fit(pd.DataFrame())


def test_pit_model_insufficient_data():
    """Test with insufficient data."""
    model = PitModel()
    df = pd.DataFrame({
        'pit_duration': [25.0, 23.0],
    })
    
    with pytest.raises(ValueError, match="Insufficient data"):
        model.fit(df)


def test_pit_model_sample_before_fit():
    """Test sampling before fitting."""
    model = PitModel()
    
    with pytest.raises(RuntimeError, match="must be fitted"):
        model.sample(10)


def test_pit_model_invalid_sample_count(sample_pit_data):
    """Test invalid sample counts."""
    model = PitModel()
    model.fit(sample_pit_data)
    
    with pytest.raises(ValueError, match="must be positive"):
        model.sample(0)
    
    with pytest.raises(ValueError, match="must be positive"):
        model.sample(-5)


def test_pit_model_bounds_enforcement(deterministic_rng):
    """Test that samples are clipped to reasonable bounds."""
    # Create model with extreme parameters
    df = pd.DataFrame({
        'time_loss': [100.0] * 10  # Very high pit losses
    })
    
    model = PitModel()
    model.fit(df)
    
    samples = model.sample(100, rng=deterministic_rng)
    
    # Should be clipped to maximum 60 seconds
    assert all(s <= 60.0 for s in samples)
    assert all(s >= 10.0 for s in samples)
