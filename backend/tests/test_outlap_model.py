"""
Tests for OutlapModel (Outlap Performance Model)
"""

import pytest
import numpy as np
import pandas as pd
from backend.models.outlap import OutlapModel


@pytest.fixture
def sample_outlap_data():
    """Create sample outlap data for testing."""
    np.random.seed(42)
    
    # Simulate realistic F1 lap data with different compounds
    data = []
    
    # Different outlap penalties by compound
    compound_penalties = {'SOFT': 0.5, 'MEDIUM': 1.2, 'HARD': 2.0}
    base_time = 90.0
    
    for compound, base_penalty in compound_penalties.items():
        # Generate stint data
        for stint in range(10):  # 10 stints per compound
            stint_length = np.random.randint(8, 25)
            
            for lap in range(1, stint_length + 1):
                if lap == 1:  # Outlap
                    penalty = np.random.normal(base_penalty, 0.2)
                    lap_time = base_time + max(0, penalty)
                else:  # Warmed up laps
                    penalty = np.random.normal(0.0, 0.1)
                    lap_time = base_time + penalty
                
                data.append({
                    'lap_time': lap_time,
                    'compound': compound,
                    'stint_lap': lap,
                })
    
    return pd.DataFrame(data)


@pytest.fixture
def minimal_outlap_data():
    """Minimal valid outlap dataset."""
    return pd.DataFrame({
        'lap_time': [
            # SOFT: 3 outlaps, 3 warmed (minimum for model)
            91.5, 91.3, 91.0,  # outlaps  
            90.2, 90.0, 90.1,  # warmed
            # MEDIUM: 3 outlaps, 3 warmed
            92.2, 92.0, 91.8,  # outlaps
            90.8, 90.6, 90.7   # warmed  
        ],
        'compound': ['SOFT'] * 6 + ['MEDIUM'] * 6,
        'stint_lap': [1, 1, 1, 3, 4, 5, 1, 1, 1, 3, 4, 5]
    })


class TestOutlapModel:
    """Test suite for OutlapModel."""
    
    def test_initialization(self):
        """Test model initialization."""
        model = OutlapModel()
        assert model.compound_models == {}
        assert not model.fitted
        assert model.sample_counts == {}
    
    def test_fit_valid_data(self, sample_outlap_data):
        """Test fitting with valid outlap data."""
        model = OutlapModel()
        result = model.fit(sample_outlap_data)
        
        # Should return self for chaining
        assert result is model
        
        # Model should be fitted
        assert model.fitted
        assert len(model.compound_models) > 0
        
        # Check that at least one compound was fitted
        for compound, compound_model in model.compound_models.items():
            assert 'mean_penalty' in compound_model
            assert 'std_penalty' in compound_model
            assert 'baseline_time' in compound_model
            assert compound_model['mean_penalty'] >= 0
            assert compound_model['std_penalty'] > 0
    
    def test_fit_empty_dataframe(self):
        """Test fitting with empty DataFrame."""
        model = OutlapModel()
        
        with pytest.raises(ValueError, match="empty DataFrame"):
            model.fit(pd.DataFrame())
    
    def test_fit_missing_columns(self):
        """Test fitting with missing required columns."""
        model = OutlapModel()
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No column found from candidates"):
            model.fit(df)
    
    def test_fit_insufficient_data(self):
        """Test fitting with insufficient total data."""
        model = OutlapModel()
        df = pd.DataFrame({
            'lap_time': [90.0, 90.5],
            'compound': ['SOFT', 'SOFT'],
            'stint_lap': [1, 2]
        })
        
        with pytest.raises(ValueError, match="Could not fit model for any compounds"):
            model.fit(df)
    
    def test_alternative_column_names(self):
        """Test fitting with alternative column names."""
        model = OutlapModel()
        df = pd.DataFrame({
            'lap_duration': [
                # SOFT: 3 outlaps, 3 warmed (minimum for model)
                91.5, 91.3, 91.0,  # outlaps  
                90.2, 90.0, 90.1,  # warmed
                # MEDIUM: 3 outlaps, 3 warmed
                92.2, 92.0, 91.8,  # outlaps
                90.8, 90.6, 90.7   # warmed  
            ],
            'tire_compound': ['SOFT'] * 6 + ['MEDIUM'] * 6,
            'tire_age': [1, 1, 1, 3, 4, 5, 1, 1, 1, 3, 4, 5]
        })
        
        model.fit(df)
        assert model.fitted
    
    def test_compound_normalization(self):
        """Test compound name normalization."""
        model = OutlapModel()
        df = pd.DataFrame({
            'lap_time': [
                # SOFT variations: 3 outlaps, 3 warmed
                91.5, 91.3, 91.0,  # outlaps  
                90.2, 90.0, 90.1,  # warmed
                # MEDIUM variations: 3 outlaps, 3 warmed
                92.2, 92.0, 91.8,  # outlaps
                90.8, 90.6, 90.7   # warmed  
            ],
            'compound': ['s', 'S', 'soft'] * 2 + ['M', 'm', 'medium'] * 2,  # Various formats  
            'stint_lap': [1, 1, 1, 3, 4, 5, 1, 1, 1, 3, 4, 5]
        })
        
        model.fit(df)
        assert model.fitted
        
        # Should normalize to standard names
        fitted_compounds = set(model.compound_models.keys())
        expected_compounds = {'SOFT', 'MEDIUM'}
        assert fitted_compounds.issubset(expected_compounds)
    
    def test_sample_before_fitting(self):
        """Test sampling before model is fitted."""
        model = OutlapModel()
        
        with pytest.raises(RuntimeError, match="must be fitted"):
            model.sample('SOFT', 10)
    
    def test_sample_invalid_compound(self, minimal_outlap_data):
        """Test sampling with compound not in model."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        with pytest.raises(ValueError, match="not available"):
            model.sample('INVALID', 10)
    
    def test_sample_single_value(self, minimal_outlap_data):
        """Test sampling single value."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        # Get first available compound
        compound = list(model.compound_models.keys())[0]
        
        sample = model.sample(compound, 1)
        assert isinstance(sample, (int, float, np.number))
        assert 0 <= sample <= 5  # Reasonable penalty bounds
    
    def test_sample_multiple_values(self, minimal_outlap_data):
        """Test sampling multiple values."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        compound = list(model.compound_models.keys())[0]
        samples = model.sample(compound, 50)
        
        assert len(samples) == 50
        assert all(0 <= s <= 5 for s in samples)  # All within bounds
        
        # Check distribution properties
        sample_mean = np.mean(samples)
        expected_mean = model.compound_models[compound]['mean_penalty']
        
        # Should be reasonably close (within 2 standard deviations)
        std = model.compound_models[compound]['std_penalty']
        assert abs(sample_mean - expected_mean) < 2 * std
    
    def test_sample_invalid_n(self, minimal_outlap_data):
        """Test sampling with invalid n parameter."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        compound = list(model.compound_models.keys())[0]
        
        # Test n=0 returns empty array (edge case, but allowed) 
        result = model.sample(compound, 0)
        assert len(result) == 0
        
        # Test negative n raises error  
        with pytest.raises(ValueError, match="must be non-negative"):
            model.sample(compound, -1)
        
        with pytest.raises(ValueError, match="must be non-negative"):
            model.sample(compound, -5)
    
    def test_get_model_info_before_fitting(self):
        """Test getting model info before fitting."""
        model = OutlapModel()
        info = model.get_model_info()
        
        assert not info['fitted']
    
    def test_get_model_info_after_fitting(self, minimal_outlap_data):
        """Test getting model info after fitting."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        info = model.get_model_info()
        
        assert info['fitted']
        assert 'compounds' in info
        assert 'models' in info
        
        for compound in info['compounds']:
            assert compound in info['models']
            compound_info = info['models'][compound]
            assert 'mean_penalty' in compound_info
            assert 'std_penalty' in compound_info
            assert 'sample_count' in compound_info
    
    def test_compound_penalty_differences(self, sample_outlap_data):
        """Test that different compounds have different penalty characteristics."""
        model = OutlapModel()
        model.fit(sample_outlap_data)
        
        # Should have fitted multiple compounds
        assert len(model.compound_models) >= 2
        
        # Get penalties for available compounds
        penalties = {}
        for compound in model.compound_models:
            penalties[compound] = model.compound_models[compound]['mean_penalty']
        
        # There should be meaningful differences between compounds
        penalty_values = list(penalties.values())
        penalty_range = max(penalty_values) - min(penalty_values)
        assert penalty_range > 0.2  # At least 0.2s difference
    
    def test_outlap_vs_warmed_lap_identification(self, sample_outlap_data):
        """Test that model correctly identifies outlaps vs warmed laps."""
        model = OutlapModel()
        model.fit(sample_outlap_data)
        
        # All fitted compounds should have positive mean penalties
        for compound, compound_model in model.compound_models.items():
            assert compound_model['mean_penalty'] > 0, f"{compound} should have positive outlap penalty"
    
    def test_penalty_bounds_enforcement(self, minimal_outlap_data):
        """Test that penalty bounds are enforced."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        compound = list(model.compound_models.keys())[0]
        
        # Sample many values to test bounds
        samples = model.sample(compound, 1000)
        
        assert all(s >= 0.0 for s in samples), "All penalties should be non-negative"
        assert all(s <= 5.0 for s in samples), "All penalties should be <= 5s"
    
    def test_case_insensitive_compounds(self, minimal_outlap_data):
        """Test that compound names are case insensitive."""
        model = OutlapModel()
        model.fit(minimal_outlap_data)
        
        compound = list(model.compound_models.keys())[0]
        
        # Should work with different cases
        sample1 = model.sample(compound.upper(), 1)
        sample2 = model.sample(compound.lower(), 1)
        
        # Both should work (not testing equality since they're random)
        assert isinstance(sample1, (int, float, np.number))
        assert isinstance(sample2, (int, float, np.number))
    
    def test_insufficient_compound_data_handling(self):
        """Test handling when specific compounds have insufficient data."""
        # Create data with very little data for one compound
        data = []
        
        # Lots of SOFT data
        for i in range(20):
            data.extend([
                {'lap_time': 91.0, 'compound': 'SOFT', 'stint_lap': 1},
                {'lap_time': 90.0, 'compound': 'SOFT', 'stint_lap': 3},
            ])
        
        # Minimal HARD data (should be skipped)
        data.extend([
            {'lap_time': 92.0, 'compound': 'HARD', 'stint_lap': 1},
        ])
        
        df = pd.DataFrame(data)
        
        model = OutlapModel()
        model.fit(df)
        
        # Should fit successfully but only include SOFT
        assert model.fitted
        assert 'SOFT' in model.compound_models
        assert 'HARD' not in model.compound_models
    
    def test_method_chaining(self, minimal_outlap_data):
        """Test that fit() returns self for method chaining."""
        model = OutlapModel()
        
        # Should be able to chain fit() -> sample()
        compound = 'SOFT'  # We know this exists in minimal data
        sample = model.fit(minimal_outlap_data).sample(compound, 1)
        assert isinstance(sample, (int, float, np.number))
    
    def test_realistic_penalty_values(self, sample_outlap_data):
        """Test that fitted penalties are realistic for F1."""
        model = OutlapModel()
        model.fit(sample_outlap_data)
        
        for compound, compound_model in model.compound_models.items():
            penalty = compound_model['mean_penalty']
            
            # F1 outlap penalties typically 0.2-3.0 seconds
            assert 0.1 <= penalty <= 3.5, f"{compound} penalty {penalty}s seems unrealistic"
    
    def test_minimum_variability_enforcement(self):
        """Test that minimum variability is enforced."""
        # Create data with identical outlap times
        data = []
        for i in range(10):
            data.extend([
                {'lap_time': 91.0, 'compound': 'SOFT', 'stint_lap': 1},  # Identical outlaps
                {'lap_time': 90.0, 'compound': 'SOFT', 'stint_lap': 3},  # Identical warmed laps
            ])
        
        df = pd.DataFrame(data)
        
        model = OutlapModel()
        model.fit(df)
        
        assert model.fitted
        assert model.compound_models['SOFT']['std_penalty'] >= 0.1  # Minimum variability
