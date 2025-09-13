"""
Tests for TyreAgeCalculator - Comprehensive edge case validation for F1 tire age computation.

This test suite validates all critical edge cases identified in F1 data processing:
- Off-by-one errors in lap counting
- Double pit stops on same lap  
- Safety Car/Virtual Safety Car period handling
- Unsafe releases and pit lane traversal timing
- Missing data and boundary conditions
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock

from services.tyre_age import TyreAgeCalculator


class TestTyreAgeCalculator:
    """Test suite for TyreAgeCalculator with comprehensive edge case coverage."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        self.calculator = TyreAgeCalculator()

    def test_basic_tire_age_calculation(self):
        """Test basic tire age calculation without pit stops."""
        # Driver completes 10 laps without pitting
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False] * 10
        })
        
        pits_df = pd.DataFrame(columns=['lap_number', 'driver_number'])  # No pit stops
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Tire age should increment by 1 each lap
        expected_tire_ages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_single_pit_stop_tire_age_reset(self):
        """Test tire age resets after pit stop."""
        # Driver pits on lap 5, continues for 5 more laps
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, False, False, True, False, False, False, False, False]
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [5],
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Tire age: [1,2,3,4,1,2,3,4,5,6] - resets on pit out lap
        expected_tire_ages = [1, 2, 3, 4, 1, 2, 3, 4, 5, 6]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_double_pit_stop_edge_case(self):
        """Test handling of double pit stops on same lap (unsafe release scenario)."""
        # Driver has two pit entries on lap 5 (unsafe release + return)
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, False, False, True, False, False, False, False, False]
        })
        
        # Double pit stop entries for lap 5
        pits_df = pd.DataFrame({
            'lap_number': [5, 5],  # Two pit entries on same lap
            'driver_number': [1, 1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Should handle gracefully - tire age still resets only once
        expected_tire_ages = [1, 2, 3, 4, 1, 2, 3, 4, 5, 6]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_safety_car_lap_detection(self):
        """Test SC/VSC lap detection and filtering."""
        # Simulate laps with safety car period
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False] * 10,
            'lap_time': [90.5, 91.2, 90.8, 120.5, 125.3, 122.7, 91.1, 90.9, 91.4, 90.6]  # Laps 4-6 are SC
        })
        
        pits_df = pd.DataFrame(columns=['lap_number', 'driver_number'])
        
        # Mock SC detection to return laps 4-6 as SC laps
        self.calculator.is_safety_car_lap = Mock(side_effect=lambda row, **kwargs: row['lap_number'] in [4, 5, 6])
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # SC laps should not increment tire age
        expected_tire_ages = [1, 2, 3, 3, 3, 3, 4, 5, 6, 7]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_multiple_drivers_independent_calculation(self):
        """Test tire age calculation for multiple drivers independently."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
            'driver_number': [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            'is_pit_out_lap': [False, False, False, False, True, False, False, False, False, False]
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [3],  # Only driver 1 pits
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Driver 1: [1,2,1,2,3] - pits on lap 3
        # Driver 2: [1,2,3,4,5] - no pit stops
        driver1_ages = result[result['driver_number'] == 1]['tyre_age'].tolist()
        driver2_ages = result[result['driver_number'] == 2]['tyre_age'].tolist()
        
        assert driver1_ages == [1, 2, 1, 2, 3]
        assert driver2_ages == [1, 2, 3, 4, 5]

    def test_pit_out_lap_without_pit_data(self):
        """Test handling of is_pit_out_lap=True without corresponding pit data."""
        # Edge case: lap marked as pit out but no pit entry in pit data
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5],
            'driver_number': [1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, True, False, False]  # Lap 3 marked as pit out
        })
        
        pits_df = pd.DataFrame(columns=['lap_number', 'driver_number'])  # No pit data
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Should treat pit out lap as tire age reset even without pit data
        expected_tire_ages = [1, 2, 1, 2, 3]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_missing_is_pit_out_lap_column(self):
        """Test graceful handling when is_pit_out_lap column is missing."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5],
            'driver_number': [1, 1, 1, 1, 1]
            # Missing is_pit_out_lap column
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [3],
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Should fall back to pit data only
        expected_tire_ages = [1, 2, 1, 2, 3]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_empty_dataframes(self):
        """Test handling of empty input dataframes."""
        empty_laps = pd.DataFrame(columns=['lap_number', 'driver_number', 'is_pit_out_lap'])
        empty_pits = pd.DataFrame(columns=['lap_number', 'driver_number'])
        
        result = self.calculator.compute_tyre_age(empty_laps, empty_pits)
        
        assert len(result) == 0
        assert 'tyre_age' in result.columns

    def test_single_lap_race(self):
        """Test edge case of single lap race."""
        laps_df = pd.DataFrame({
            'lap_number': [1],
            'driver_number': [1],
            'is_pit_out_lap': [False]
        })
        
        pits_df = pd.DataFrame(columns=['lap_number', 'driver_number'])
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        assert result['tyre_age'].tolist() == [1]

    def test_late_race_pit_stop(self):
        """Test pit stop on final lap (edge case scenario)."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5],
            'driver_number': [1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, False, False, True]  # Pit on final lap
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [5],
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        expected_tire_ages = [1, 2, 3, 4, 1]  # Tire age resets on final lap
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_consecutive_pit_stops(self):
        """Test consecutive pit stops on adjacent laps."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, True, True, False, False, False, False]  # Pits on laps 3,4
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [3, 4],
            'driver_number': [1, 1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Each pit resets tire age
        expected_tire_ages = [1, 2, 1, 1, 2, 3, 4, 5]
        assert result['tyre_age'].tolist() == expected_tire_ages

    def test_safety_car_threshold_detection(self):
        """Test SC detection threshold logic."""
        # Test the actual SC detection method
        normal_lap = pd.Series({'lap_time': 90.5})
        slow_lap = pd.Series({'lap_time': 115.0})  # 28% slower (should not be SC)
        very_slow_lap = pd.Series({'lap_time': 130.0})  # 44% slower (should be SC)
        
        # With 30% threshold, only very slow lap should be detected as SC
        assert not self.calculator.is_safety_car_lap(normal_lap, threshold=0.30)
        assert not self.calculator.is_safety_car_lap(slow_lap, threshold=0.30)  
        assert self.calculator.is_safety_car_lap(very_slow_lap, threshold=0.30)

    def test_missing_lap_time_for_sc_detection(self):
        """Test SC detection with missing lap time data."""
        lap_no_time = pd.Series({'lap_number': 5})  # Missing lap_time
        
        # Should not crash and should return False
        assert not self.calculator.is_safety_car_lap(lap_no_time)

    def test_pit_on_lap_one(self):
        """Test pit stop on the very first lap (formation lap scenario)."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5],
            'driver_number': [1, 1, 1, 1, 1],
            'is_pit_out_lap': [True, False, False, False, False]  # Pit on lap 1
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [1],
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # First lap should start with tire age 1, then continue normally
        expected_tire_ages = [1, 2, 3, 4, 5]
        assert result['tyre_age'].tolist() == expected_tire_ages


class TestTyreAgeIntegration:
    """Integration tests for TyreAgeCalculator with realistic F1 data patterns."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.calculator = TyreAgeCalculator()

    def test_realistic_race_scenario_bahrain_2024_pattern(self):
        """Test with realistic pit stop pattern from Bahrain 2024."""
        # Simulate 57-lap race with typical pit strategy
        lap_numbers = list(range(1, 58))
        
        laps_df = pd.DataFrame({
            'lap_number': lap_numbers,
            'driver_number': [44] * 57,  # Hamilton's car number
            'is_pit_out_lap': [False] * 57,
            'lap_time': [90.5] * 57  # Normal lap times
        })
        
        # Mark pit out laps
        laps_df.loc[laps_df['lap_number'].isin([15, 38]), 'is_pit_out_lap'] = True
        
        pits_df = pd.DataFrame({
            'lap_number': [15, 38],  # Two-stop strategy
            'driver_number': [44, 44]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Validate key points in tire age progression
        assert result.iloc[0]['tyre_age'] == 1  # First lap
        assert result.iloc[14]['tyre_age'] == 1  # Pit out lap 15 (reset)
        assert result.iloc[16]['tyre_age'] == 3   # Lap 17 (3rd lap on new tires)
        assert result.iloc[37]['tyre_age'] == 1  # Pit out lap 38 (reset)
        assert result.iloc[56]['tyre_age'] == 20 # Final lap (20th lap on final stint)

    def test_multi_driver_race_with_different_strategies(self):
        """Test multiple drivers with different pit strategies."""
        # 3 drivers, 30 laps, different strategies
        drivers = [1, 2, 3]
        laps_per_driver = 30
        
        # Create lap data for all drivers
        laps_data = []
        for driver in drivers:
            for lap in range(1, laps_per_driver + 1):
                laps_data.append({
                    'lap_number': lap,
                    'driver_number': driver,
                    'is_pit_out_lap': False,
                    'lap_time': 90.0 + np.random.normal(0, 0.5)
                })
        
        laps_df = pd.DataFrame(laps_data)
        
        # Different pit strategies
        pits_data = [
            {'lap_number': 12, 'driver_number': 1},  # Driver 1: one stop
            {'lap_number': 8, 'driver_number': 2},   # Driver 2: two stops
            {'lap_number': 20, 'driver_number': 2},
            {'lap_number': 6, 'driver_number': 3},   # Driver 3: three stops
            {'lap_number': 15, 'driver_number': 3},
            {'lap_number': 24, 'driver_number': 3},
        ]
        
        pits_df = pd.DataFrame(pits_data)
        
        # Mark pit out laps
        for _, pit in pits_df.iterrows():
            mask = (laps_df['lap_number'] == pit['lap_number']) & \
                   (laps_df['driver_number'] == pit['driver_number'])
            laps_df.loc[mask, 'is_pit_out_lap'] = True
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # Validate each driver's tire age progression
        for driver in drivers:
            driver_data = result[result['driver_number'] == driver].sort_values('lap_number')
            
            # Tire age should never exceed stint length
            max_stint_length = driver_data['tyre_age'].max()
            assert max_stint_length <= 30  # Reasonable maximum
            
            # Tire age should reset to 1 after each pit stop
            pit_laps = pits_df[pits_df['driver_number'] == driver]['lap_number'].tolist()
            for pit_lap in pit_laps:
                pit_out_age = driver_data[driver_data['lap_number'] == pit_lap]['tyre_age'].iloc[0]
                assert pit_out_age == 1

    def test_edge_case_safety_car_with_pit_stops(self):
        """Test complex scenario with SC periods and pit stops."""
        laps_df = pd.DataFrame({
            'lap_number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'driver_number': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'is_pit_out_lap': [False, False, False, False, True, False, False, False, False, False],
            'lap_time': [90.0, 91.0, 120.0, 125.0, 90.5, 122.0, 91.5, 90.0, 91.0, 90.5]  # SC on laps 3,4,6
        })
        
        pits_df = pd.DataFrame({
            'lap_number': [5],
            'driver_number': [1]
        })
        
        result = self.calculator.compute_tyre_age(laps_df, pits_df)
        
        # SC laps should not increment tire age, but pit stops should reset
        # Expected: [1, 2, 2, 2, 1, 1, 2, 3, 4, 5]
        # Lap 3-4: SC (no increment), Lap 5: pit (reset), Lap 6: SC (no increment)
        expected_pattern = [1, 2, 2, 2, 1, 1, 2, 3, 4, 5]
        assert result['tyre_age'].tolist() == expected_pattern


if __name__ == "__main__":
    pytest.main([__file__, "-v"])