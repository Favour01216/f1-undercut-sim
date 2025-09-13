"""
Tests for PitModel (Pit Stop Time Loss Model)
"""

import numpy as np
import pandas as pd
import pytest

from backend.models.pit import PitModel


@pytest.fixture
def sample_pit_data():
    """Create sample pit stop data for testing."""
    np.random.seed(42)

    # Simulate realistic pit stop times: normal distribution around 25s
    n_stops = 100
    pit_losses = np.random.normal(25.0, 3.0, n_stops)

    return pd.DataFrame(
        {
            "time_loss": pit_losses,
            "pit_duration": pit_losses - np.random.normal(5, 1, n_stops),  # Approximate
        }
    )


@pytest.fixture
def minimal_pit_data():
    """Minimal valid pit stop dataset."""
    return pd.DataFrame(
        {
            "time_loss": [22.5, 25.0, 27.5, 23.8, 26.2],
            "pit_duration": [18.0, 20.5, 23.0, 19.5, 22.0],
        }
    )


class TestPitModel:
    """Test suite for PitModel."""

    def test_initialization(self):
        """Test model initialization."""
        model = PitModel()
        assert model.mean_loss is None
        assert model.std_loss is None
        assert not model.fitted
        assert model.sample_count == 0
        assert model.distribution is None

    def test_fit_valid_data(self, sample_pit_data):
        """Test fitting with valid pit stop data."""
        model = PitModel()
        result = model.fit(sample_pit_data)

        # Should return self for chaining
        assert result is model

        # Model should be fitted
        assert model.fitted
        assert model.mean_loss is not None
        assert model.std_loss is not None
        assert model.sample_count > 0
        assert model.distribution is not None

        # Parameters should be reasonable for F1 pit stops
        assert 15 < model.mean_loss < 40
        assert 0 < model.std_loss < 10

    def test_fit_empty_dataframe(self):
        """Test fitting with empty DataFrame."""
        model = PitModel()

        with pytest.raises(ValueError, match="empty DataFrame"):
            model.fit(pd.DataFrame())

    def test_fit_missing_columns(self):
        """Test fitting with missing required columns."""
        model = PitModel()
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})

        with pytest.raises(ValueError, match="No pit time column"):
            model.fit(df)

    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data points."""
        model = PitModel()
        df = pd.DataFrame({"time_loss": [25.0, 23.0], "pit_duration": [20.0, 18.5]})

        with pytest.raises(ValueError, match="Insufficient data"):
            model.fit(df)

    def test_fit_with_pit_duration_only(self):
        """Test fitting using only pit duration (estimating total loss)."""
        model = PitModel()
        df = pd.DataFrame({"pit_duration": [20.0, 22.5, 21.0, 23.8, 19.5]})

        model.fit(df)
        assert model.fitted
        assert (
            model.mean_loss > 20
        )  # Should be higher than pit duration due to overhead

    def test_alternative_column_names(self):
        """Test fitting with alternative column names."""
        model = PitModel()
        df = pd.DataFrame({"duration": [20.0, 22.5, 21.0, 23.8, 19.5]})

        model.fit(df)
        assert model.fitted

    def test_sample_before_fitting(self):
        """Test sampling before model is fitted."""
        model = PitModel()

        with pytest.raises(RuntimeError, match="must be fitted"):
            model.sample(10)

    def test_sample_single_value(self, minimal_pit_data):
        """Test sampling single value."""
        model = PitModel()
        model.fit(minimal_pit_data)

        sample = model.sample(1)
        assert isinstance(sample, (int, float, np.number))
        assert 10 <= sample <= 60  # Reasonable bounds for F1 pit stops

    def test_sample_multiple_values(self, minimal_pit_data):
        """Test sampling multiple values."""
        model = PitModel()
        model.fit(minimal_pit_data)

        samples = model.sample(100)
        assert len(samples) == 100
        assert all(10 <= s <= 60 for s in samples)  # All within bounds

        # Check distribution properties
        sample_mean = np.mean(samples)
        sample_std = np.std(samples)

        # Should be close to fitted parameters (within tolerance)
        assert abs(sample_mean - model.mean_loss) < 2.0
        assert abs(sample_std - model.std_loss) < 1.0

    def test_sample_invalid_n(self, minimal_pit_data):
        """Test sampling with invalid n parameter."""
        model = PitModel()
        model.fit(minimal_pit_data)

        with pytest.raises(ValueError, match="must be positive"):
            model.sample(0)

        with pytest.raises(ValueError, match="must be positive"):
            model.sample(-5)

    def test_probability_faster_than(self, minimal_pit_data):
        """Test probability calculation."""
        model = PitModel()
        model.fit(minimal_pit_data)

        # Test with mean value (should be ~0.5)
        prob_mean = model.probability_faster_than(model.mean_loss)
        assert 0.4 < prob_mean < 0.6

        # Test with extreme values
        prob_low = model.probability_faster_than(10.0)
        prob_high = model.probability_faster_than(50.0)

        assert 0.0 <= prob_low <= prob_high <= 1.0

    def test_get_percentiles(self, minimal_pit_data):
        """Test percentile calculation."""
        model = PitModel()
        model.fit(minimal_pit_data)

        percentiles = model.get_percentiles([25, 50, 75])

        assert len(percentiles) == 3
        assert percentiles[25] < percentiles[50] < percentiles[75]

        # 50th percentile should be close to mean
        assert abs(percentiles[50] - model.mean_loss) < 0.5

    def test_get_percentiles_invalid(self, minimal_pit_data):
        """Test percentile calculation with invalid values."""
        model = PitModel()
        model.fit(minimal_pit_data)

        # Should ignore invalid percentiles
        percentiles = model.get_percentiles([-10, 150, 50])
        assert len(percentiles) == 1  # Only 50 is valid
        assert 50 in percentiles

    def test_simulate_pit_window(self, minimal_pit_data):
        """Test pit window simulation."""
        model = PitModel()
        model.fit(minimal_pit_data)

        simulation = model.simulate_pit_window(n_simulations=100)

        assert "simulations" in simulation
        assert simulation["simulations"] == 100
        assert "mean_loss" in simulation
        assert "percentiles" in simulation
        assert "probability_under_25s" in simulation
        assert "probability_over_30s" in simulation
        assert "samples" in simulation

        assert len(simulation["samples"]) == 100

    def test_get_model_info_before_fitting(self):
        """Test getting model info before fitting."""
        model = PitModel()
        info = model.get_model_info()

        assert not info["fitted"]
        assert "error" in info

    def test_get_model_info_after_fitting(self, minimal_pit_data):
        """Test getting model info after fitting."""
        model = PitModel()
        model.fit(minimal_pit_data)
        info = model.get_model_info()

        assert info["fitted"]
        assert info["distribution"] == "normal"
        assert "parameters" in info
        assert "sample_count" in info
        assert "typical_range" in info
        assert "percentiles" in info

    def test_compare_scenarios(self, minimal_pit_data):
        """Test scenario comparison."""
        model = PitModel()
        model.fit(minimal_pit_data)

        scenarios = {"fast_pit": 22.0, "normal_pit": 25.0, "slow_pit": 28.0}

        comparison = model.compare_scenarios(scenarios)

        assert "scenarios" in comparison
        assert "baseline_mean" in comparison
        assert "recommendation" in comparison

        for scenario_name in scenarios.keys():
            assert scenario_name in comparison["scenarios"]
            scenario = comparison["scenarios"][scenario_name]
            assert "probability_faster" in scenario
            assert "risk_level" in scenario

    def test_outlier_handling(self):
        """Test handling of outlier pit stop times."""
        # Create data with outliers
        normal_times = [23.0, 25.0, 27.0, 24.5, 26.2]
        outlier_times = [5.0, 90.0]  # Extreme outliers

        df = pd.DataFrame({"time_loss": normal_times + outlier_times})

        model = PitModel()
        model.fit(df)

        # Should fit successfully but parameters should be reasonable
        assert model.fitted
        assert 15 < model.mean_loss < 40  # Still reasonable despite outliers

    def test_minimum_variability(self):
        """Test handling of data with very low variability."""
        # All values are the same
        df = pd.DataFrame({"time_loss": [25.0, 25.0, 25.0, 25.0, 25.0]})

        model = PitModel()
        model.fit(df)

        assert model.fitted
        assert model.std_loss >= 1.0  # Minimum variability enforced

    def test_method_chaining(self, minimal_pit_data):
        """Test that fit() returns self for method chaining."""
        model = PitModel()

        # Should be able to chain fit() -> sample()
        sample = model.fit(minimal_pit_data).sample(1)
        assert isinstance(sample, (int, float, np.number))
