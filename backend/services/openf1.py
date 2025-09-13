"""
OpenF1 API Client

This module provides integration with the OpenF1 API for F1 data.
Implements caching, retry logic, and data filtering for analysis.
"""

import os
import time
import logging
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .tyre_age import compute_tyre_age
from .fastf1_enrichment import HybridDataEnricher

# Import config with absolute path handling
try:
    from ..config import config
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenF1Client:
    """
    Client for interacting with the OpenF1 API.
    
    Features:
    - Synchronous API calls with requests
    - Parquet caching for all responses
    - HTTP retry with exponential backoff
    - SC/VSC lap filtering
    - Comprehensive logging
    """
    
    def __init__(self, base_url: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the OpenF1 client.
        
        Args:
            base_url: OpenF1 API base URL
            cache_dir: Directory for caching Parquet files
        """
        self.base_url = base_url or config.OPENF1_API_URL
        self.cache_dir = Path(cache_dir or config.CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize hybrid data enricher for compound data with config
        enrichment_config = config.get_data_enrichment_config()
        self.enricher = HybridDataEnricher(
            cache_dir=enrichment_config["cache_dir"],
            offline_mode=enrichment_config["offline_mode"]
        )
        
        # Configure session with retry strategy
        self.session = requests.Session()
        
        # Retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,  # 2, 4, 8 seconds
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set timeout and headers
        self.session.timeout = 30
        self.session.headers.update({
            "User-Agent": "F1-Undercut-Sim/1.0"
        })
    
    def _get_cache_filename(self, gp: str, year: int, endpoint: str) -> Path:
        """
        Generate cache filename for a request.
        
        Args:
            gp: Grand Prix name/identifier
            year: Race year
            endpoint: API endpoint being cached
            
        Returns:
            Path to cache file
        """
        today = date.today().isoformat()
        safe_gp = "".join(c if c.isalnum() else "_" for c in str(gp).lower())
        filename = f"{safe_gp}_{year}_{today}_{endpoint}.parquet"
        return self.cache_dir / filename
    
    def _get_from_cache(self, cache_file: Path) -> Optional[pd.DataFrame]:
        """
        Retrieve data from cache if available and recent.
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            Cached DataFrame or None
        """
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"Cache hit: {cache_file.name}")
                return df
            except Exception as e:
                logger.warning(f"Cache read failed for {cache_file.name}: {e}")
        return None
    
    def _save_to_cache(self, df: pd.DataFrame, cache_file: Path) -> None:
        """
        Save DataFrame to cache.
        
        Args:
            df: DataFrame to cache
            cache_file: Path to cache file
        """
        try:
            df.to_parquet(cache_file, index=False)
            logger.info(f"Cached data to: {cache_file.name}")
        except Exception as e:
            logger.error(f"Cache save failed for {cache_file.name}: {e}")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request with logging and error handling.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        logger.info(f"Fetching: {url} with params: {params}")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched {len(data) if isinstance(data, list) else 1} records from {endpoint}")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    def _filter_sc_vsc_laps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out Safety Car (SC) and Virtual Safety Car (VSC) laps.
        
        Args:
            df: DataFrame with lap data
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
        
        initial_count = len(df)
        
        # Filter conditions for SC/VSC laps
        # These conditions may need adjustment based on actual OpenF1 data structure
        filters = []
        
        # Check for track status indicators
        if 'track_status' in df.columns:
            filters.append(~df['track_status'].isin(['4', '6']))  # 4=SC, 6=VSC in some APIs
        
        # Check for lap time anomalies (SC/VSC laps are usually much slower)
        if 'lap_duration' in df.columns:
            # Remove laps that are significantly slower than normal
            df_numeric = pd.to_numeric(df['lap_duration'], errors='coerce')
            if not df_numeric.isna().all():
                median_time = df_numeric.median()
                if pd.notna(median_time):
                    # Filter out laps > 150% of median (likely SC/VSC)
                    filters.append(df_numeric <= median_time * 1.5)
        
        # Check for specific flags in the data
        if 'is_deleted' in df.columns:
            filters.append(~df['is_deleted'].fillna(False))
        
        # Apply all filters
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            df = df[combined_filter].copy()
        
        filtered_count = len(df)
        if initial_count != filtered_count:
            logger.info(f"Filtered out {initial_count - filtered_count} SC/VSC laps ({filtered_count} remaining)")
        
        return df
    
    def get_laps(self, gp: str, year: int) -> pd.DataFrame:
        """
        Get lap times data for a specific Grand Prix.
        
        Args:
            gp: Grand Prix identifier (e.g., 'bahrain', 'saudi-arabia')
            year: Race year
            
        Returns:
            DataFrame with lap times data, filtered for SC/VSC laps
        """
        cache_file = self._get_cache_filename(gp, year, "laps")
        
        # Try cache first
        cached_data = self._get_from_cache(cache_file)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        logger.info(f"Fetching lap data for {gp} {year}")
        
        # Get sessions for the year to find the race session
        sessions_data = self._make_request("sessions", {"year": year})
        
        # Find the race session for the specific GP
        race_session = None
        for session in sessions_data:
            if session.get("session_type") == "Race" and str(year) in str(session.get("year", "")):
                # Check multiple fields for GP matching
                location = session.get("location", "").lower()
                country_name = session.get("country_name", "").lower()
                circuit_short_name = session.get("circuit_short_name", "").lower()
                
                gp_normalized = gp.lower().replace("-", " ")
                
                # Match against location, country, or circuit name
                if (gp_normalized in location or 
                    gp_normalized in country_name or 
                    gp_normalized in circuit_short_name or
                    location in gp_normalized or
                    country_name in gp_normalized or
                    circuit_short_name in gp_normalized):
                    race_session = session
                    break
        
        if not race_session:
            logger.warning(f"No race session found for {gp} {year}")
            return pd.DataFrame()
        
        session_key = race_session.get("session_key")
        if not session_key:
            logger.error(f"No session_key found for {gp} {year}")
            return pd.DataFrame()
        
        # Get lap data for the session
        laps_data = self._make_request("laps", {"session_key": session_key})
        
        if not laps_data:
            logger.warning(f"No lap data found for {gp} {year}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(laps_data)
        
        # Filter out SC/VSC laps
        df = self._filter_sc_vsc_laps(df)
        
        # Add tire age computation using robust calculator
        df = self._add_tire_age_robust(df, session_key)
        
        # Enrich with compound data using hybrid enrichment
        df = self.enricher.enrich_laps_with_compounds(df, gp, year)
        
        # Cache the results
        self._save_to_cache(df, cache_file)
        
        return df
    
    def get_pit_events(self, gp: str, year: int) -> pd.DataFrame:
        """
        Get pit stop events data for a specific Grand Prix.
        
        Args:
            gp: Grand Prix identifier (e.g., 'bahrain', 'saudi-arabia')
            year: Race year
            
        Returns:
            DataFrame with pit stop events data
        """
        cache_file = self._get_cache_filename(gp, year, "pit_events")
        
        # Try cache first
        cached_data = self._get_from_cache(cache_file)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        logger.info(f"Fetching pit events data for {gp} {year}")
        
        # Get sessions for the year to find the race session
        sessions_data = self._make_request("sessions", {"year": year})
        
        # Find the race session for the specific GP
        race_session = None
        for session in sessions_data:
            if session.get("session_type") == "Race" and str(year) in str(session.get("year", "")):
                # Check multiple fields for GP matching
                location = session.get("location", "").lower()
                country_name = session.get("country_name", "").lower()
                circuit_short_name = session.get("circuit_short_name", "").lower()
                
                gp_normalized = gp.lower().replace("-", " ")
                
                # Match against location, country, or circuit name
                if (gp_normalized in location or 
                    gp_normalized in country_name or 
                    gp_normalized in circuit_short_name or
                    location in gp_normalized or
                    country_name in gp_normalized or
                    circuit_short_name in gp_normalized):
                    race_session = session
                    break
        
        if not race_session:
            logger.warning(f"No race session found for {gp} {year}")
            return pd.DataFrame()
        
        session_key = race_session.get("session_key")
        if not session_key:
            logger.error(f"No session_key found for {gp} {year}")
            return pd.DataFrame()
        
        # Get pit stop data for the session
        pit_data = self._make_request("pit", {"session_key": session_key})
        
        if not pit_data:
            logger.warning(f"No pit stop data found for {gp} {year}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(pit_data)
        
        # Cache the results
        self._save_to_cache(df, cache_file)
        
        return df
    
    def _add_tire_age_robust(self, laps_df: pd.DataFrame, session_key: str) -> pd.DataFrame:
        """
        Add tire age column using the robust TyreAgeCalculator.
        
        Args:
            laps_df: DataFrame with lap data
            session_key: Session key to get pit events for
            
        Returns:
            DataFrame with added 'tyre_age' column
        """
        if laps_df.empty:
            return laps_df
        
        # Get pit stop data directly from API using session_key
        try:
            pit_data = self._make_request("pit", {"session_key": session_key})
            pit_events_df = pd.DataFrame(pit_data) if pit_data else pd.DataFrame()
        except Exception as e:
            logger.warning(f"Failed to get pit data for tire age calculation: {e}")
            pit_events_df = pd.DataFrame()
        
        # Use the robust tire age calculator
        try:
            result_df = compute_tyre_age(laps_df, pit_events_df)
            logger.info(f"Computed tire ages for {len(result_df)} laps using robust calculator")
            return result_df
        except Exception as e:
            logger.error(f"Robust tire age calculation failed: {e}")
            # Fallback to simple calculation
            return self._add_tire_age_fallback(laps_df, pit_events_df)
    
    def _add_tire_age_fallback(self, laps_df: pd.DataFrame, pit_events_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fallback tire age calculation for when the robust calculator fails.
        
        Args:
            laps_df: DataFrame with lap data
            pit_events_df: DataFrame with pit events
            
        Returns:
            DataFrame with added 'tyre_age' column
        """
        df = laps_df.copy()
        df['tyre_age'] = 0  # Use 0-based indexing to match robust calculator
        
        if pit_events_df.empty:
            # No pit data - assume all laps are on original tires
            for driver in df['driver_number'].unique():
                driver_mask = df['driver_number'] == driver
                driver_laps = df[driver_mask].sort_values('lap_number')
                df.loc[driver_mask, 'tyre_age'] = range(len(driver_laps))
            return df
        
        # For each driver, compute tire age based on pit stops
        for driver in df['driver_number'].unique():
            driver_mask = df['driver_number'] == driver
            driver_laps = df[driver_mask].sort_values('lap_number')
            
            # Get pit stops for this driver
            driver_pits = pit_events_df[pit_events_df['driver_number'] == driver]['lap_number'].tolist()
            driver_pits.sort()
            
            # Compute tire age for each lap
            tire_ages = []
            current_stint_start = driver_laps['lap_number'].iloc[0] if len(driver_laps) > 0 else 1
            
            for lap_num in driver_laps['lap_number']:
                # Check if there's a pit stop at or before this lap
                recent_pit = None
                for pit_lap in driver_pits:
                    if pit_lap <= lap_num:
                        recent_pit = pit_lap
                    else:
                        break
                
                if recent_pit is not None and recent_pit >= current_stint_start:
                    # Tire age starts from 0 after pit stop
                    current_stint_start = recent_pit
                    tire_age = lap_num - current_stint_start
                else:
                    tire_age = lap_num - current_stint_start
                
                tire_ages.append(max(0, tire_age))  # Ensure at least 0
            
            # Update the dataframe
            df.loc[driver_mask, 'tyre_age'] = tire_ages
        
        return df
    
    def close(self) -> None:
        """Close the HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# For backward compatibility and convenience
def create_openf1_client() -> OpenF1Client:
    """Create and return an OpenF1Client instance."""
    return OpenF1Client()