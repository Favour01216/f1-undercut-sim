"""
FastF1 Integration Service

This module provides integration with FastF1 for compound data enrichment
when OpenF1 data lacks per-lap compound information.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

# FastF1 imports with error handling for offline mode
try:
    import fastf1
    import fastf1.core
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    fastf1 = None

logger = logging.getLogger(__name__)


class FastF1Client:
    """
    Client for enriching F1 data with compound information from FastF1.
    
    Features:
    - Compound data extraction for sessions missing this info
    - Graceful fallback when FastF1 is unavailable
    - Efficient caching of FastF1 session data
    - Left join strategy for compound enrichment
    """
    
    def __init__(self, cache_dir: Optional[str] = None, offline_mode: Optional[bool] = None):
        """
        Initialize the FastF1 client.
        
        Args:
            cache_dir: Directory for caching FastF1 data
            offline_mode: If True, skip FastF1 integration (default: env OFFLINE)
        """
        self.cache_dir = Path(cache_dir or "features/fastf1_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Check offline mode from environment or parameter
        self.offline_mode = offline_mode
        if self.offline_mode is None:
            self.offline_mode = os.getenv("OFFLINE", "0").lower() in ("1", "true", "yes")
        
        self.available = FASTF1_AVAILABLE and not self.offline_mode
        
        if not self.available:
            if not FASTF1_AVAILABLE:
                logger.warning("FastF1 not available - compound enrichment disabled")
            else:
                logger.info("Offline mode enabled - FastF1 integration disabled")
        else:
            # Configure FastF1 caching
            fastf1.Cache.enable_cache(str(self.cache_dir))
            logger.info(f"FastF1 initialized with cache: {self.cache_dir}")
    
    def get_compound_data(self, gp: str, year: int) -> Optional[pd.DataFrame]:
        """
        Get compound data for a specific Grand Prix using FastF1.
        
        Args:
            gp: Grand Prix identifier
            year: Race year
            
        Returns:
            DataFrame with driver_number, lap_number, compound columns or None
        """
        if not self.available:
            return None
        
        try:
            logger.info(f"Fetching compound data from FastF1 for {gp} {year}")
            
            # Load the race session
            session = fastf1.get_session(year, gp, 'R')  # 'R' for Race
            session.load()
            
            # Get laps data with compound information
            laps = session.laps
            
            if laps.empty:
                logger.warning(f"No lap data available from FastF1 for {gp} {year}")
                return None
            
            # Extract relevant columns and rename to match OpenF1 format
            compound_data = laps[['Driver', 'LapNumber', 'Compound']].copy()
            
            # Convert driver names to numbers (requires driver info)
            driver_mapping = self._get_driver_mapping(session)
            compound_data['driver_number'] = compound_data['Driver'].map(driver_mapping)
            
            # Rename columns to match OpenF1 format
            compound_data = compound_data.rename(columns={
                'LapNumber': 'lap_number',
                'Compound': 'compound'
            })
            
            # Filter out rows where driver mapping failed
            compound_data = compound_data.dropna(subset=['driver_number'])
            compound_data['driver_number'] = compound_data['driver_number'].astype(int)
            
            # Standardize compound names to match OpenF1 format
            compound_data['compound'] = compound_data['compound'].str.upper()
            
            logger.info(f"Successfully extracted {len(compound_data)} compound records from FastF1")
            return compound_data[['driver_number', 'lap_number', 'compound']]
            
        except Exception as e:
            logger.error(f"Failed to get compound data from FastF1 for {gp} {year}: {e}")
            return None
    
    def _get_driver_mapping(self, session) -> Dict[str, int]:
        """
        Create mapping from driver abbreviations to driver numbers.
        
        Args:
            session: FastF1 session object
            
        Returns:
            Dictionary mapping driver abbreviations to numbers
        """
        try:
            # Get driver info from session
            drivers = {}
            
            # Try to get driver numbers from session results
            if hasattr(session, 'results') and session.results is not None:
                for _, driver in session.results.iterrows():
                    if pd.notna(driver.get('Abbreviation')) and pd.notna(driver.get('DriverNumber')):
                        drivers[driver['Abbreviation']] = int(driver['DriverNumber'])
            
            # Fallback to common driver mappings for recent years
            if not drivers:
                drivers = self._get_fallback_driver_mapping()
            
            logger.debug(f"Driver mapping: {drivers}")
            return drivers
            
        except Exception as e:
            logger.warning(f"Failed to get driver mapping: {e}")
            return self._get_fallback_driver_mapping()
    
    def _get_fallback_driver_mapping(self) -> Dict[str, int]:
        """Get fallback driver number mapping for common abbreviations."""
        return {
            'VER': 1, 'PER': 11, 'LEC': 16, 'SAI': 55, 'HAM': 44, 'RUS': 63,
            'ALO': 14, 'STR': 18, 'NOR': 4, 'PIA': 81, 'OCO': 31, 'GAS': 10,
            'ALB': 23, 'SAR': 2, 'MAG': 20, 'HUL': 27, 'TSU': 22, 'RIC': 3,
            'BOT': 77, 'ZHO': 24, 'MSC': 47, 'DEV': 21, 'LAW': 40, 'NYC': 50
        }


class HybridDataEnricher:
    """
    Service for enriching OpenF1 data with compound information from FastF1.
    
    Implements a hybrid data layer that:
    1. Uses OpenF1 as primary source for timing data
    2. Enriches with FastF1 compound data when missing
    3. Caches enriched results for performance
    4. Falls back gracefully when FastF1 is unavailable
    """
    
    def __init__(self, cache_dir: Optional[str] = None, offline_mode: Optional[bool] = None):
        """
        Initialize the hybrid data enricher.
        
        Args:
            cache_dir: Directory for caching enriched data
            offline_mode: If True, skip FastF1 integration
        """
        self.cache_dir = Path(cache_dir or "features/enriched")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.fastf1_client = FastF1Client(offline_mode=offline_mode)
        
    def enrich_laps_with_compounds(self, laps_df: pd.DataFrame, gp: str, year: int) -> pd.DataFrame:
        """
        Enrich OpenF1 lap data with compound information from FastF1.
        
        Args:
            laps_df: OpenF1 lap data
            gp: Grand Prix identifier
            year: Race year
            
        Returns:
            Enhanced DataFrame with compound information
        """
        if laps_df.empty:
            return laps_df
        
        # Check cache first
        cache_file = self._get_cache_filename(gp, year)
        cached_data = self._load_from_cache(cache_file)
        if cached_data is not None:
            logger.info(f"Using cached enriched data for {gp} {year}")
            return self._filter_cached_data(cached_data, laps_df)
        
        # Start with OpenF1 data
        enriched_df = laps_df.copy()
        
        # Check if compound data is already present and complete
        has_compound = 'compound' in enriched_df.columns
        compound_coverage = 0.0
        
        if has_compound:
            compound_coverage = enriched_df['compound'].notna().mean()
            logger.info(f"OpenF1 compound coverage: {compound_coverage:.1%}")
        
        # If compound coverage is low, try to enrich with FastF1
        if not has_compound or compound_coverage < 0.8:
            compound_data = self.fastf1_client.get_compound_data(gp, year)
            
            if compound_data is not None:
                # Perform left join to enrich OpenF1 data with FastF1 compounds
                enriched_df = self._merge_compound_data(enriched_df, compound_data)
                logger.info(f"Enhanced lap data with FastF1 compounds")
            else:
                # FastF1 failed, add fallback compound estimation
                enriched_df = self._add_fallback_compounds(enriched_df)
                logger.info("Added fallback compound estimates")
        
        # Cache the enriched data
        self._save_to_cache(enriched_df, cache_file)
        
        return enriched_df
    
    def _merge_compound_data(self, laps_df: pd.DataFrame, compound_data: pd.DataFrame) -> pd.DataFrame:
        """
        Merge FastF1 compound data with OpenF1 lap data using left join strategy.
        
        Args:
            laps_df: OpenF1 lap data
            compound_data: FastF1 compound data
            
        Returns:
            Merged DataFrame with compound information
        """
        # Ensure join columns exist and are correct type
        if 'driver_number' not in laps_df.columns or 'lap_number' not in laps_df.columns:
            logger.warning("Missing join columns in OpenF1 data - cannot merge compounds")
            return self._add_fallback_compounds(laps_df)
        
        # Convert to consistent types for joining
        laps_df = laps_df.copy()
        laps_df['driver_number'] = pd.to_numeric(laps_df['driver_number'], errors='coerce')
        laps_df['lap_number'] = pd.to_numeric(laps_df['lap_number'], errors='coerce')
        
        compound_data = compound_data.copy()
        compound_data['driver_number'] = pd.to_numeric(compound_data['driver_number'], errors='coerce')
        compound_data['lap_number'] = pd.to_numeric(compound_data['lap_number'], errors='coerce')
        
        # Remove any rows with invalid join keys
        laps_df = laps_df.dropna(subset=['driver_number', 'lap_number'])
        compound_data = compound_data.dropna(subset=['driver_number', 'lap_number'])
        
        # Perform left join - prefer OpenF1 timing, add FastF1 compounds
        join_cols = ['driver_number', 'lap_number']
        
        # If compound already exists in laps_df, suffix the FastF1 version
        if 'compound' in laps_df.columns:
            merged = pd.merge(
                laps_df, 
                compound_data, 
                on=join_cols, 
                how='left', 
                suffixes=('', '_fastf1')
            )
            
            # Fill missing compounds with FastF1 data
            merged['compound'] = merged['compound'].fillna(merged['compound_fastf1'])
            merged = merged.drop(columns=['compound_fastf1'], errors='ignore')
        else:
            # Direct merge when no compound exists in OpenF1
            merged = pd.merge(laps_df, compound_data, on=join_cols, how='left')
        
        # Log merge statistics
        original_count = len(laps_df)
        compound_count = merged['compound'].notna().sum()
        coverage = compound_count / original_count if original_count > 0 else 0
        
        logger.info(f"Compound merge: {compound_count}/{original_count} laps ({coverage:.1%} coverage)")
        
        return merged
    
    def _add_fallback_compounds(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add fallback compound estimates when FastF1 data is unavailable.
        
        Uses heuristics based on stint patterns and lap times.
        
        Args:
            laps_df: Lap data without compound information
            
        Returns:
            DataFrame with estimated compound information
        """
        df = laps_df.copy()
        
        if 'compound' not in df.columns:
            df['compound'] = None
        
        # Simple heuristic: estimate compounds based on stint length and tire age
        if 'tyre_age_at_start' in df.columns:
            # Short stints (1-15 laps) -> likely SOFT
            # Medium stints (16-30 laps) -> likely MEDIUM  
            # Long stints (30+ laps) -> likely HARD
            
            # Group by driver and stint (consecutive laps with same tire age pattern)
            for driver in df['driver_number'].unique():
                if pd.isna(driver):
                    continue
                    
                driver_data = df[df['driver_number'] == driver].sort_values('lap_number')
                
                # Simple stint detection: tire age resets indicate new stint
                if 'tyre_age_at_start' in driver_data.columns:
                    tire_ages = driver_data['tyre_age_at_start'].ffill()
                    
                    # Estimate compound based on stint characteristics
                    # This is a rough heuristic - real compound allocation is more complex
                    stint_lengths = []
                    current_stint_start = 0
                    
                    for i, age in enumerate(tire_ages):
                        if i > 0 and age < tire_ages.iloc[i-1]:  # New stint detected
                            stint_length = i - current_stint_start
                            stint_lengths.append(stint_length)
                            
                            # Estimate compound for previous stint
                            if stint_length <= 15:
                                estimated_compound = 'SOFT'
                            elif stint_length <= 30:
                                estimated_compound = 'MEDIUM'
                            else:
                                estimated_compound = 'HARD'
                            
                            # Apply to stint laps
                            stint_mask = (
                                (df['driver_number'] == driver) & 
                                (df['lap_number'] >= driver_data.iloc[current_stint_start]['lap_number']) &
                                (df['lap_number'] < driver_data.iloc[i]['lap_number'])
                            )
                            df.loc[stint_mask, 'compound'] = estimated_compound
                            
                            current_stint_start = i
        
        # Fill remaining NaN values with most common compounds
        if df['compound'].isna().any():
            # Use MEDIUM as default fallback (most balanced compound)
            df['compound'] = df['compound'].fillna('MEDIUM')
        
        logger.info("Applied fallback compound estimates")
        return df
    
    def _get_cache_filename(self, gp: str, year: int) -> Path:
        """Generate cache filename for enriched data."""
        safe_gp = "".join(c if c.isalnum() else "_" for c in str(gp).lower())
        filename = f"{safe_gp}_{year}_laps.parquet"
        return self.cache_dir / filename
    
    def _load_from_cache(self, cache_file: Path) -> Optional[pd.DataFrame]:
        """Load enriched data from cache if available and recent."""
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is recent (within 24 hours)
            import time
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age > 24 * 3600:  # 24 hours
                logger.debug(f"Cache expired: {cache_file}")
                return None
            
            df = pd.read_parquet(cache_file)
            logger.debug(f"Loaded from cache: {cache_file}")
            return df
            
        except Exception as e:
            logger.warning(f"Failed to load from cache {cache_file}: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, cache_file: Path) -> None:
        """Save enriched data to cache."""
        try:
            df.to_parquet(cache_file, index=False)
            logger.debug(f"Saved to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save to cache {cache_file}: {e}")
    
    def _filter_cached_data(self, cached_df: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter cached data to match the structure of the original OpenF1 data.
        
        This ensures cached data is compatible even if the original request
        has different filtering or structure.
        """
        if cached_df.empty or original_df.empty:
            return cached_df
        
        # Try to match on key columns that should exist in both
        key_columns = ['driver_number', 'lap_number']
        available_keys = [col for col in key_columns if col in cached_df.columns and col in original_df.columns]
        
        if not available_keys:
            # No matching keys, return original structure with compound if available
            result_df = original_df.copy()
            if 'compound' in cached_df.columns and 'compound' not in result_df.columns:
                result_df['compound'] = 'MEDIUM'  # Fallback
            return result_df
        
        # Merge cached compound data with original structure
        try:
            compound_cols = [col for col in cached_df.columns if col.startswith('compound') or col in available_keys]
            compound_data = cached_df[compound_cols].drop_duplicates()
            
            merged = pd.merge(original_df, compound_data, on=available_keys, how='left')
            return merged
            
        except Exception as e:
            logger.warning(f"Failed to filter cached data: {e}")
            return original_df