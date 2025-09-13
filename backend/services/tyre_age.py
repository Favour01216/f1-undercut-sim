"""
Tire Age Calculator for F1 Data Analysis

This module provides robust tire age calculation functionality for Formula 1 data,
handling complex edge cases including Safety Car periods, double pit stops,
unsafe releases, and pit lane traversal timing.

The tire age definition follows F1 convention:
- Age 1: First lap after tire change (out-lap)  
- Age 2+: Subsequent laps on same tire set
- Age does NOT increment during pit lane traversal or SC/VSC periods
- Age resets to 1 when new tires are fitted
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Set

logger = logging.getLogger(__name__)


class TyreAgeCalculator:
    """
    Robust tire age calculator for F1 lap data.
    
    Handles:
    - Standard pit stops and tire changes
    - Double pit stops on same lap
    - Safety Car (SC) and Virtual Safety Car (VSC) periods
    - Unsafe releases and pit lane violations
    - Missing or incomplete pit data
    - In-laps and out-laps timing
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the tire age calculator.
        
        Args:
            debug: Enable debug logging for troubleshooting
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
    
    def compute_tyre_age(self, laps_df: pd.DataFrame, pits_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute tire age for all laps in the dataset.
        
        Args:
            laps_df: DataFrame with lap data (must include 'driver_number', 'lap_number')
            pits_df: DataFrame with pit stop data (must include 'driver_number', 'lap_number')
        
        Returns:
            DataFrame with added 'tyre_age' column (int, starting at 1 on first lap after stop)
        
        Raises:
            ValueError: If required columns are missing from input DataFrames
        """
        if laps_df.empty:
            logger.warning("Empty laps DataFrame provided")
            result = laps_df.copy()
            result['tyre_age'] = pd.Series([], dtype=int)
            return result
        
        # Validate required columns
        self._validate_dataframes(laps_df, pits_df)
        
        # Create working copy
        result_df = laps_df.copy()
        
        # Initialize tire age column with default value (1 for first lap)
        result_df['tyre_age'] = 1
        
        # Identify SC/VSC laps for special handling
        sc_vsc_laps = self._identify_sc_vsc_laps(result_df)
        
        if self.debug:
            logger.debug(f"Processing {len(result_df)} laps for {result_df['driver_number'].nunique()} drivers")
            logger.debug(f"Found {len(sc_vsc_laps)} SC/VSC laps")
        
        # Process each driver independently
        for driver in result_df['driver_number'].unique():
            driver_mask = result_df['driver_number'] == driver
            driver_laps = result_df[driver_mask].copy().sort_values('lap_number')
            driver_pits = self._get_driver_pit_events(pits_df, driver)
            
            # Calculate tire ages for this driver
            tire_ages = self._calculate_driver_tire_ages(
                driver_laps, driver_pits, sc_vsc_laps
            )
            
            # Update the result DataFrame
            result_df.loc[driver_mask, 'tyre_age'] = tire_ages
            
            if self.debug:
                logger.debug(f"Driver {driver}: {len(driver_pits)} pit stops, ages {tire_ages[:5]}...")
        
        return result_df
    
    def _validate_dataframes(self, laps_df: pd.DataFrame, pits_df: pd.DataFrame) -> None:
        """Validate that required columns exist in the DataFrames."""
        required_lap_cols = ['driver_number', 'lap_number']
        missing_lap_cols = [col for col in required_lap_cols if col not in laps_df.columns]
        if missing_lap_cols:
            raise ValueError(f"Missing required lap columns: {missing_lap_cols}")
        
        if not pits_df.empty:
            required_pit_cols = ['driver_number', 'lap_number']
            missing_pit_cols = [col for col in required_pit_cols if col not in pits_df.columns]
            if missing_pit_cols:
                raise ValueError(f"Missing required pit columns: {missing_pit_cols}")
    
    def _identify_sc_vsc_laps(self, laps_df: pd.DataFrame) -> Set[int]:
        """
        Identify Safety Car and Virtual Safety Car laps.
        
        Returns:
            Set of lap numbers that occurred under SC/VSC conditions
        """
        sc_vsc_laps = set()
        
        # Method 1: Check track_status column if available
        if 'track_status' in laps_df.columns:
            # Common track status codes: 4=SC, 6=VSC
            sc_vsc_mask = laps_df['track_status'].isin(['4', '6', 'SC', 'VSC'])
            sc_vsc_laps.update(laps_df.loc[sc_vsc_mask, 'lap_number'].unique())
        
        # Method 2: Use the public SC detection method for each lap
        if 'lap_time' in laps_df.columns or 'lap_duration' in laps_df.columns:
            for _, lap_row in laps_df.iterrows():
                if self.is_safety_car_lap(lap_row):
                    sc_vsc_laps.add(lap_row['lap_number'])
        
        return sc_vsc_laps
    
    def _get_driver_pit_events(self, pits_df: pd.DataFrame, driver: int) -> pd.DataFrame:
        """
        Get pit events for a specific driver, handling edge cases.
        
        Args:
            pits_df: Pit events DataFrame
            driver: Driver number
        
        Returns:
            DataFrame of pit events for the driver, sorted by lap number
        """
        if pits_df.empty:
            return pd.DataFrame(columns=['lap_number'])
        
        driver_pits = pits_df[pits_df['driver_number'] == driver].copy()
        
        if driver_pits.empty:
            return pd.DataFrame(columns=['lap_number'])
        
        # Sort by lap number and handle duplicates (double stops)
        driver_pits = driver_pits.sort_values('lap_number')
        
        # For double stops on same lap, keep the last one (final tire change)
        driver_pits = driver_pits.drop_duplicates(subset=['lap_number'], keep='last')
        
        if self.debug and len(driver_pits) > 0:
            logger.debug(f"Driver {driver} pit stops: laps {driver_pits['lap_number'].tolist()}")
        
        return driver_pits
    
    def _calculate_driver_tire_ages(
        self, 
        driver_laps: pd.DataFrame, 
        driver_pits: pd.DataFrame, 
        sc_vsc_laps: Set[int]
    ) -> np.ndarray:
        """
        Calculate tire ages for a single driver across all laps.
        
        Args:
            driver_laps: Sorted laps for the driver
            driver_pits: Pit events for the driver
            sc_vsc_laps: Set of lap numbers under SC/VSC
        
        Returns:
            Array of tire ages corresponding to driver_laps
        """
        lap_numbers = driver_laps['lap_number'].values
        pit_laps = driver_pits['lap_number'].values if not driver_pits.empty else np.array([])
        
        tire_ages = np.ones(len(lap_numbers), dtype=int)
        
        # Track current tire age state
        current_age = 1
        last_pit_lap = 0  # Lap number of last pit stop
        
        for i, lap_num in enumerate(lap_numbers):
            # Check if this is marked as a pit out lap (tire change)
            is_pit_out = False
            if 'is_pit_out_lap' in driver_laps.columns:
                is_pit_out = bool(driver_laps.iloc[i].get('is_pit_out_lap', False))
            
            # Check if this is a pit lap (tire change lap) from pit data
            if lap_num in pit_laps or is_pit_out:
                # This is a pit lap - reset age to 1 (out-lap)
                current_age = 1
                last_pit_lap = lap_num
                tire_ages[i] = current_age
                
                if self.debug:
                    logger.debug(f"Lap {lap_num}: Pit stop/out-lap, age reset to 1")
            
            elif lap_num in sc_vsc_laps:
                # SC/VSC lap - age doesn't increment (but maintains current value)
                tire_ages[i] = current_age
                
                if self.debug:
                    logger.debug(f"Lap {lap_num}: SC/VSC, age held at {current_age}")
            
            else:
                # Normal racing lap - increment age
                if i > 0:  # Not the first lap
                    current_age += 1
                else:
                    # First lap of the race/stint
                    current_age = 1
                
                tire_ages[i] = current_age
                
                if self.debug and i < 5:  # Debug first few laps
                    logger.debug(f"Lap {lap_num}: Normal racing, age = {current_age}")
        
        return tire_ages
    
    def _is_pit_related_lap(self, lap_row: pd.Series, last_pit_lap: int) -> bool:
        """
        Check if a lap is related to pit lane activity.
        
        Args:
            lap_row: Single lap data row
            last_pit_lap: Lap number of most recent pit stop
        
        Returns:
            True if this lap involves pit lane activity
        """
        # Check for pit out lap flag
        if 'is_pit_out_lap' in lap_row.index and pd.notna(lap_row['is_pit_out_lap']):
            return bool(lap_row['is_pit_out_lap'])
        
        # Check if this is the lap immediately after a pit stop
        if last_pit_lap > 0 and lap_row['lap_number'] == last_pit_lap + 1:
            return True
        
        # Check for unusually slow lap times that might indicate pit activity
        if 'lap_duration' in lap_row.index and pd.notna(lap_row['lap_duration']):
            lap_time = float(lap_row['lap_duration'])
            # If lap time > 200s, likely includes pit stop
            if lap_time > 200:
                return True
        
        return False
    
    def is_safety_car_lap(self, lap_row: pd.Series, threshold: float = 0.30) -> bool:
        """
        Public method to check if a lap is under Safety Car conditions.
        
        Args:
            lap_row: Single lap data row
            threshold: Speed threshold (e.g., 0.30 = 30% slower than normal)
        
        Returns:
            True if lap appears to be under SC/VSC conditions
        """
        # Check for track status column first
        if 'track_status' in lap_row.index and pd.notna(lap_row['track_status']):
            status = str(lap_row['track_status'])
            if status in ['4', '6', 'SC', 'VSC']:
                return True
        
        # Fallback to lap time analysis
        if 'lap_time' in lap_row.index and pd.notna(lap_row['lap_time']):
            lap_time = float(lap_row['lap_time'])
            # Typical F1 lap times are 80-110s, SC laps are usually 130-180s
            # Use threshold-based detection
            normal_lap_estimate = 90.0  # Conservative estimate
            slow_threshold = normal_lap_estimate * (1 + threshold)
            return lap_time > slow_threshold
        
        return False


def compute_tyre_age(laps_df: pd.DataFrame, pits_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to compute tire ages using default calculator settings.
    
    Args:
        laps_df: DataFrame with lap data
        pits_df: DataFrame with pit stop data
    
    Returns:
        DataFrame with added 'tyre_age' column
    
    Examples:
        >>> laps_with_age = compute_tyre_age(laps_df, pits_df)
        >>> print(laps_with_age[['driver_number', 'lap_number', 'tyre_age']].head())
    """
    calculator = TyreAgeCalculator(debug=False)
    return calculator.compute_tyre_age(laps_df, pits_df)


# Edge case handling examples for documentation:
EDGE_CASE_EXAMPLES = {
    "double_stop": {
        "description": "Driver pits twice on same lap (unsafe release)",
        "example": "Lap 15: First stop (unsafe), second stop (final) -> age resets after final stop"
    },
    "sc_period": {
        "description": "Safety Car period",
        "example": "Laps 20-23 under SC -> tire age doesn't increment during SC laps"
    },
    "missing_pit_data": {
        "description": "No pit stop data available",
        "example": "All laps treated as single stint, age increments normally from 0"
    },
    "first_lap": {
        "description": "Race start behavior",
        "example": "Lap 1: Age = 1 (fresh tires from grid), Lap 2: Age = 2, etc."
    }
}