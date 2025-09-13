"""
Test configuration and fixtures for F1 Undercut Simulator.

Sets up deterministic test environment with frozen time, timezone, and mocked API calls.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from datetime import datetime, timezone
import os
import freezegun


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables and timezone."""
    os.environ["ENV"] = "test"
    os.environ["TZ"] = "UTC"
    os.environ["OPENF1_BASE_URL"] = "http://localhost:9999"
    os.environ["JOLPICA_BASE_URL"] = "http://localhost:9999"


@pytest.fixture(scope="session", autouse=True)
def freeze_time():
    """Freeze time for deterministic tests."""
    with freezegun.freeze_time("2024-01-15T12:00:00Z"):
        yield


@pytest.fixture
def deterministic_rng():
    """Provide a deterministic random number generator."""
    return np.random.default_rng(seed=42)


@pytest.fixture
def sample_lap_data():
    """Generate sample lap data for testing."""
    np.random.seed(42)
    n_laps = 30
    
    # Create realistic tire degradation data
    tire_ages = np.arange(1, n_laps + 1)
    base_time = 90.0
    degradation = 0.05 * tire_ages + 0.002 * tire_ages**2
    noise = np.random.normal(0, 0.1, n_laps)
    
    lap_times = base_time + degradation + noise
    
    return pd.DataFrame({
        'lap_time': lap_times,
        'lap_duration': lap_times,  # Alternative column name
        'tire_age': tire_ages,
        'stint_lap_number': tire_ages,  # Alternative column name
        'compound': ['SOFT'] * 10 + ['MEDIUM'] * 10 + ['HARD'] * 10
    })


@pytest.fixture
def sample_pit_data():
    """Generate sample pit stop data for testing."""
    np.random.seed(42)
    n_stops = 20
    
    # Realistic F1 pit stop times
    pit_durations = np.random.normal(22, 2, n_stops)
    time_losses = pit_durations + np.random.normal(3, 1, n_stops)  # Add overhead
    
    return pd.DataFrame({
        'pit_duration': pit_durations,
        'duration': pit_durations,  # Alternative column name
        'time_loss': time_losses,
        'pit_loss_time': time_losses,  # Alternative column name
    })


@pytest.fixture
def sample_outlap_data():
    """Generate sample outlap data for testing."""
    np.random.seed(42)
    data = []
    
    compounds = ['SOFT', 'MEDIUM', 'HARD']
    outlap_penalties = {'SOFT': 0.5, 'MEDIUM': 1.2, 'HARD': 2.0}
    
    for compound in compounds:
        base_penalty = outlap_penalties[compound]
        
        # Generate multiple stints
        for stint in range(5):
            stint_length = np.random.randint(8, 20)
            base_time = 90.0
            
            for lap in range(1, stint_length + 1):
                if lap == 1:  # Outlap
                    penalty = np.random.normal(base_penalty, 0.2)
                    lap_time = base_time + max(0, penalty)
                else:  # Warmed up
                    penalty = np.random.normal(0.0, 0.1)
                    lap_time = base_time + penalty
                
                data.append({
                    'lap_time': lap_time,
                    'lap_duration': lap_time,
                    'compound': compound,
                    'tire_compound': compound,  # Alternative column name
                    'stint_lap': lap,
                    'tire_age': lap,  # Alternative column name
                })
    
    return pd.DataFrame(data)


@pytest.fixture(autouse=True)
def mock_api_calls():
    """Mock all external API calls to return static data."""
    # Mock OpenF1 API calls
    with patch('backend.services.openf1.OpenF1Client.get_laps') as mock_get_laps, \
         patch('backend.services.openf1.OpenF1Client.get_pit_events') as mock_get_pit_events, \
         patch('backend.services.jolpica.JolpicaClient.get_results') as mock_get_results, \
         patch('backend.services.jolpica.JolpicaClient.get_schedule') as mock_get_schedule:
        
        # Return empty DataFrames by default (can be overridden in specific tests)
        mock_get_laps.return_value = pd.DataFrame()
        mock_get_pit_events.return_value = pd.DataFrame()
        mock_get_results.return_value = pd.DataFrame()
        mock_get_schedule.return_value = pd.DataFrame()
        
        yield {
            'get_laps': mock_get_laps,
            'get_pit_events': mock_get_pit_events,
            'get_results': mock_get_results,
            'get_schedule': mock_get_schedule
        }


@pytest.fixture
def mock_api_with_data(mock_api_calls, sample_lap_data, sample_pit_data):
    """Mock API calls to return realistic test data."""
    mock_api_calls['get_laps'].return_value = sample_lap_data
    mock_api_calls['get_pit_events'].return_value = sample_pit_data
    return mock_api_calls
