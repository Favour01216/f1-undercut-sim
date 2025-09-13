"""
Jolpica F1 API Client

This module provides integration with the Jolpica F1 API for historical F1 data.
Implements caching, retry logic, and comprehensive logging.
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


class JolpicaClient:
    """
    Client for interacting with the Jolpica F1 API.

    Features:
    - Synchronous API calls with requests
    - Parquet caching for all responses
    - HTTP retry with exponential backoff
    - Comprehensive logging
    """

    def __init__(self, base_url: str | None = None, cache_dir: str | None = None):
        """
        Initialize the Jolpica client.

        Args:
            base_url: Jolpica API base URL
            cache_dir: Directory for caching Parquet files
        """
        self.base_url = base_url or os.getenv(
            "JOLPICA_API_URL", "http://ergast.com/api/f1"
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

    def _get_cache_filename_year_only(self, year: int, endpoint: str) -> Path:
        """
        Generate cache filename for year-only requests.

        Args:
            year: Race year
            endpoint: API endpoint being cached

        Returns:
            Path to cache file
        """
        today = date.today().isoformat()
        filename = f"year_{year}_{today}_{endpoint}.parquet"
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
            logger.info(f"Successfully fetched data from {endpoint}")

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def _find_race_round(self, races: list[dict], gp: str) -> int | None:
        """
        Find the round number for a specific Grand Prix.

        Args:
            races: List of race data
            gp: Grand Prix identifier

        Returns:
            Round number or None if not found
        """
        gp_lower = gp.lower().replace("-", " ").replace("_", " ")

        for race in races:
            race_name = race.get("raceName", "").lower()
            circuit_name = race.get("Circuit", {}).get("circuitName", "").lower()
            circuit_id = race.get("Circuit", {}).get("circuitId", "").lower()

            # Try to match by various identifiers
            if (
                gp_lower in race_name
                or gp_lower in circuit_name
                or gp_lower in circuit_id
                or race_name in gp_lower
                or circuit_name in gp_lower
            ):
                return int(race.get("round", 0))

        return None

    def get_results(self, gp: str, year: int) -> pd.DataFrame:
        """
        Get race results for a specific Grand Prix.

        Args:
            gp: Grand Prix identifier (e.g., 'bahrain', 'saudi-arabia')
            year: Race year

        Returns:
            DataFrame with race results data
        """
        cache_file = self._get_cache_filename(gp, year, "results")

        # Try cache first
        cached_data = self._get_from_cache(cache_file)
        if cached_data is not None:
            return cached_data

        # Fetch from API
        logger.info(f"Fetching race results for {gp} {year}")

        # First, get the race schedule to find the round number
        schedule_data = self._make_request(f"{year}.json")

        races = schedule_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            logger.warning(f"No races found for year {year}")
            return pd.DataFrame()

        # Find the specific race round
        round_number = self._find_race_round(races, gp)
        if round_number is None:
            logger.warning(f"Race '{gp}' not found in {year} schedule")
            return pd.DataFrame()

        # Get race results
        results_data = self._make_request(f"{year}/{round_number}/results.json")

        race_table = results_data.get("MRData", {}).get("RaceTable", {})
        races_with_results = race_table.get("Races", [])

        if not races_with_results:
            logger.warning(f"No results found for {gp} {year}")
            return pd.DataFrame()

        race = races_with_results[0]
        results = race.get("Results", [])

        if not results:
            logger.warning(f"No race results found for {gp} {year}")
            return pd.DataFrame()

        # Process results into a flat structure
        processed_results = []
        for result in results:
            driver = result.get("Driver", {})
            constructor = result.get("Constructor", {})
            time_data = result.get("Time", {})
            fastest_lap = result.get("FastestLap", {})
            fastest_lap_time = fastest_lap.get("Time", {})

            processed_results.append(
                {
                    "position": int(result.get("position", 0)),
                    "driver_id": driver.get("driverId"),
                    "driver_code": driver.get("code"),
                    "driver_number": result.get("number"),
                    "given_name": driver.get("givenName"),
                    "family_name": driver.get("familyName"),
                    "nationality": driver.get("nationality"),
                    "constructor_id": constructor.get("constructorId"),
                    "constructor_name": constructor.get("name"),
                    "constructor_nationality": constructor.get("nationality"),
                    "grid_position": int(result.get("grid", 0)),
                    "laps": int(result.get("laps", 0)),
                    "status": result.get("status"),
                    "time_millis": time_data.get("millis"),
                    "time_text": time_data.get("time"),
                    "fastest_lap_rank": fastest_lap.get("rank"),
                    "fastest_lap_time": fastest_lap_time.get("time"),
                    "fastest_lap_avg_speed": fastest_lap.get("AverageSpeed", {}).get(
                        "speed"
                    ),
                    "points": float(result.get("points", 0)),
                    "race_name": race.get("raceName"),
                    "circuit_id": race.get("Circuit", {}).get("circuitId"),
                    "circuit_name": race.get("Circuit", {}).get("circuitName"),
                    "date": race.get("date"),
                    "year": year,
                    "round": round_number,
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(processed_results)

        # Cache the results
        self._save_to_cache(df, cache_file)

        return df

    def get_schedule(self, year: int) -> pd.DataFrame:
        """
        Get race schedule for a specific year.

        Args:
            year: Race year

        Returns:
            DataFrame with race schedule data
        """
        cache_file = self._get_cache_filename_year_only(year, "schedule")

        # Try cache first
        cached_data = self._get_from_cache(cache_file)
        if cached_data is not None:
            return cached_data

        # Fetch from API
        logger.info(f"Fetching race schedule for {year}")

        # Get race schedule
        schedule_data = self._make_request(f"{year}.json")

        race_table = schedule_data.get("MRData", {}).get("RaceTable", {})
        races = race_table.get("Races", [])

        if not races:
            logger.warning(f"No races found for year {year}")
            return pd.DataFrame()

        # Process schedule into a flat structure
        processed_schedule = []
        for race in races:
            circuit = race.get("Circuit", {})
            location = circuit.get("Location", {})

            processed_schedule.append(
                {
                    "round": int(race.get("round", 0)),
                    "race_name": race.get("raceName"),
                    "circuit_id": circuit.get("circuitId"),
                    "circuit_name": circuit.get("circuitName"),
                    "locality": location.get("locality"),
                    "country": location.get("country"),
                    "latitude": (
                        float(location.get("lat", 0)) if location.get("lat") else None
                    ),
                    "longitude": (
                        float(location.get("long", 0)) if location.get("long") else None
                    ),
                    "date": race.get("date"),
                    "time": race.get("time"),
                    "url": race.get("url"),
                    "year": year,
                    "first_practice": race.get("FirstPractice", {}).get("date"),
                    "first_practice_time": race.get("FirstPractice", {}).get("time"),
                    "second_practice": race.get("SecondPractice", {}).get("date"),
                    "second_practice_time": race.get("SecondPractice", {}).get("time"),
                    "third_practice": race.get("ThirdPractice", {}).get("date"),
                    "third_practice_time": race.get("ThirdPractice", {}).get("time"),
                    "qualifying": race.get("Qualifying", {}).get("date"),
                    "qualifying_time": race.get("Qualifying", {}).get("time"),
                    "sprint": race.get("Sprint", {}).get("date"),
                    "sprint_time": race.get("Sprint", {}).get("time"),
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(processed_schedule)

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
def create_jolpica_client() -> JolpicaClient:
    """Create and return a JolpicaClient instance."""
    return JolpicaClient()
