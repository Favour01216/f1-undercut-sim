"""
OpenF1 API Client

This module provides integration with the OpenF1 API for F1 data.
Implements caching, retry logic, and data filtering for analysis.
"""

import logging
import os
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    def __init__(self, base_url: str | None = None, cache_dir: str | None = None):
        """
        Initialize the OpenF1 client.

        Args:
            base_url: OpenF1 API base URL
            cache_dir: Directory for caching Parquet files
        """
        self.base_url = base_url or os.getenv(
            "OPENF1_API_URL", "https://api.openf1.org/v1"
        )
        self.cache_dir = Path(cache_dir or "features")
        self.cache_dir.mkdir(exist_ok=True)

        # Configure session with retry strategy
        self.session = requests.Session()

        # Retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,  # 2, 4, 8 seconds
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set timeout and headers
        self.session.timeout = 30
        self.session.headers.update({"User-Agent": "F1-Undercut-Sim/1.0"})

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

    def _get_from_cache(self, cache_file: Path) -> pd.DataFrame | None:
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

    def _make_request(
        self, endpoint: str, params: dict | None = None
    ) -> dict[str, Any]:
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
            logger.info(
                f"Successfully fetched {len(data) if isinstance(data, list) else 1} records from {endpoint}"
            )

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
        if "track_status" in df.columns:
            filters.append(
                ~df["track_status"].isin(["4", "6"])
            )  # 4=SC, 6=VSC in some APIs

        # Check for lap time anomalies (SC/VSC laps are usually much slower)
        if "lap_duration" in df.columns:
            # Remove laps that are significantly slower than normal
            df_numeric = pd.to_numeric(df["lap_duration"], errors="coerce")
            if not df_numeric.isna().all():
                median_time = df_numeric.median()
                if pd.notna(median_time):
                    # Filter out laps > 150% of median (likely SC/VSC)
                    filters.append(df_numeric <= median_time * 1.5)

        # Check for specific flags in the data
        if "is_deleted" in df.columns:
            filters.append(~df["is_deleted"].fillna(False))

        # Apply all filters
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            df = df[combined_filter].copy()

        filtered_count = len(df)
        if initial_count != filtered_count:
            logger.info(
                f"Filtered out {initial_count - filtered_count} SC/VSC laps ({filtered_count} remaining)"
            )

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
            if (
                session.get("session_type") == "Race"
                and str(year) in str(session.get("year", ""))
                and gp.lower().replace("-", " ")
                in session.get("session_name", "").lower()
            ):
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
            if (
                session.get("session_type") == "Race"
                and str(year) in str(session.get("year", ""))
                and gp.lower().replace("-", " ")
                in session.get("session_name", "").lower()
            ):
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

    def close(self) -> None:
        """Close the HTTP session."""
        if hasattr(self, "session"):
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
