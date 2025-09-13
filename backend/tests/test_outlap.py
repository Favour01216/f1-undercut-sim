"""
Tests for OutlapModel (Outlap Performance Model)
"""

import pytest
import numpy as np
import pandas as pd
from models.outlap import OutlapModel


def test_outlap_model_sample_positive_values(sample_outlap_data, deterministic_rng):
    """Test OutlapModel.sample returns positive values."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    # Test all available compounds
    for compound in model.compound_models.keys():
        samples = model.sample(compound, 100, rng=deterministic_rng)
        
        # Should be non-negative (outlap penalties can't be negative)
        assert all(s >= 0.0 for s in samples)
        
        # Should be bounded (max 5 seconds penalty)
        assert all(s <= 5.0 for s in samples)


def test_outlap_model_deterministic_sampling(sample_outlap_data):
    """Test deterministic sampling with RNG."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    # Get first available compound
    compound = list(model.compound_models.keys())[0]
    
    # Sample with deterministic RNG
    rng1 = np.random.default_rng(seed=42)
    samples1 = model.sample(compound, 50, rng=rng1)
    
    # Reset and sample again
    rng2 = np.random.default_rng(seed=42)
    samples2 = model.sample(compound, 50, rng=rng2)
    
    # Should be identical
    np.testing.assert_array_equal(samples1, samples2)


def test_outlap_model_single_sample(sample_outlap_data, deterministic_rng):
    """Test single sample returns float."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    compound = list(model.compound_models.keys())[0]
    single_sample = model.sample(compound, 1, rng=deterministic_rng)
    
    assert isinstance(single_sample, (float, np.floating))
    assert 0.0 <= single_sample <= 5.0


def test_outlap_model_multiple_samples(sample_outlap_data, deterministic_rng):
    """Test multiple samples returns array."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    compound = list(model.compound_models.keys())[0]
    samples = model.sample(compound, 20, rng=deterministic_rng)
    
    assert isinstance(samples, np.ndarray)
    assert len(samples) == 20
    assert all(0.0 <= s <= 5.0 for s in samples)


def test_outlap_model_compound_differences(sample_outlap_data):
    """Test that different compounds have different characteristics."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    # Should fit multiple compounds
    assert len(model.compound_models) >= 2
    
    # Each compound should have reasonable penalties
    for compound, compound_model in model.compound_models.items():
        mean_penalty = compound_model['mean_penalty']
        std_penalty = compound_model['std_penalty']
        
        assert 0.0 <= mean_penalty <= 3.0  # Reasonable F1 outlap penalty
        assert std_penalty > 0.0  # Should have variability


def test_outlap_model_fit_requirements(sample_outlap_data):
    """Test model fitting requirements."""
    model = OutlapModel()
    
    # Should fit successfully
    result = model.fit(sample_outlap_data)
    assert result is model  # Method chaining
    assert model.fitted
    assert len(model.compound_models) > 0


def test_outlap_model_empty_data():
    """Test with empty data."""
    model = OutlapModel()
    
    with pytest.raises(ValueError, match="empty DataFrame"):
        model.fit(pd.DataFrame())


def test_outlap_model_insufficient_data():
    """Test with insufficient total data."""
    model = OutlapModel()
    df = pd.DataFrame({
        'lap_time': [90.0, 90.5],
        'compound': ['SOFT', 'SOFT'],
        'stint_lap': [1, 2]
    })
    
    with pytest.raises(ValueError, match="Insufficient data"):
        model.fit(df)


def test_outlap_model_sample_before_fit():
    """Test sampling before fitting."""
    model = OutlapModel()
    
    with pytest.raises(RuntimeError, match="must be fitted"):
        model.sample('SOFT', 10)


def test_outlap_model_invalid_compound(sample_outlap_data):
    """Test sampling with invalid compound."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    with pytest.raises(ValueError, match="not available"):
        model.sample('INVALID', 10)


def test_outlap_model_invalid_sample_count(sample_outlap_data):
    """Test invalid sample counts."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    compound = list(model.compound_models.keys())[0]
    
    with pytest.raises(ValueError, match="must be positive"):
        model.sample(compound, 0)
    
    with pytest.raises(ValueError, match="must be positive"):
        model.sample(compound, -5)


def test_outlap_model_case_insensitive_compounds(sample_outlap_data, deterministic_rng):
    """Test compound names are case insensitive."""
    model = OutlapModel()
    model.fit(sample_outlap_data)
    
    # Get first available compound
    compound = list(model.compound_models.keys())[0]
    
    # Should work with different cases
    sample_upper = model.sample(compound.upper(), 1, rng=deterministic_rng)
    sample_lower = model.sample(compound.lower(), 1, rng=deterministic_rng)
    
    # Both should return valid values
    assert isinstance(sample_upper, (float, np.floating))
    assert isinstance(sample_lower, (float, np.floating))
