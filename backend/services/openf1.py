"""
OpenF1 API Service

This module provides integration with the OpenF1 API for real-time F1 data.
OpenF1 provides live timing, telemetry, and session data.
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
import os
from datetime import datetime, timezone


class OpenF1Service:
    """
    Service for interacting with the OpenF1 API.
    
    OpenF1 provides real-time Formula 1 data including:
    - Session information
    - Live timing data
    - Telemetry data
    - Position data
    - Lap times
    """
    
    def __init__(self):
        """Initialize the OpenF1 service."""
        self.base_url = os.getenv("OPENF1_API_URL", "https://api.openf1.org/v1")
        self.session = None
        self.timeout = 30.0
        
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self.session is None:
            self.session = httpx.AsyncClient(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def get_sessions(self, year: int = 2024) -> List[Dict[str, Any]]:
        """
        Get F1 sessions for a given year.
        
        Args:
            year: Year to get sessions for
            
        Returns:
            List of session dictionaries
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/sessions", params={"year": year})
            response.raise_for_status()
            
            sessions = response.json()
            
            # Filter and format sessions
            formatted_sessions = []
            for session_data in sessions:
                formatted_sessions.append({
                    "session_key": session_data.get("session_key"),
                    "session_name": session_data.get("session_name"),
                    "date_start": session_data.get("date_start"),
                    "date_end": session_data.get("date_end"),
                    "gmt_offset": session_data.get("gmt_offset"),
                    "session_type": session_data.get("session_type"),
                    "location": session_data.get("location"),
                    "country_name": session_data.get("country_name"),
                    "circuit_short_name": session_data.get("circuit_short_name"),
                    "year": session_data.get("year")
                })
            
            return formatted_sessions
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch sessions: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    async def get_session_data(self, session_key: str) -> Dict[str, Any]:
        """
        Get comprehensive data for a specific session.
        
        Args:
            session_key: Unique session identifier
            
        Returns:
            Dictionary containing session data
        """
        try:
            # Get multiple data types concurrently
            tasks = [
                self.get_lap_times(session_key),
                self.get_position_data(session_key),
                self.get_stint_data(session_key),
                self.get_weather_data(session_key)
            ]
            
            lap_times, positions, stints, weather = await asyncio.gather(*tasks)
            
            return {
                "session_key": session_key,
                "lap_times": lap_times,
                "positions": positions,
                "stints": stints,
                "weather": weather,
                "tire_compounds": self._extract_tire_compounds(stints),
                "track_temperature": self._extract_track_temperature(weather)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get session data: {str(e)}")
    
    async def get_lap_times(self, session_key: str) -> List[Dict[str, Any]]:
        """Get lap times for a session."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/laps", 
                params={"session_key": session_key}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            # Return empty list if no data available
            return []
    
    async def get_position_data(self, session_key: str) -> List[Dict[str, Any]]:
        """Get position data for a session."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/position", 
                params={"session_key": session_key}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return []
    
    async def get_stint_data(self, session_key: str) -> List[Dict[str, Any]]:
        """Get stint/tire data for a session."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/stints", 
                params={"session_key": session_key}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return []
    
    async def get_weather_data(self, session_key: str) -> List[Dict[str, Any]]:
        """Get weather data for a session."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/weather", 
                params={"session_key": session_key}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return []
    
    async def get_telemetry_data(
        self, 
        session_key: str, 
        driver_number: int,
        lap_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get telemetry data for a specific driver.
        
        Args:
            session_key: Session identifier
            driver_number: Driver number
            lap_number: Specific lap number (optional)
            
        Returns:
            List of telemetry data points
        """
        try:
            session = await self._get_session()
            params = {
                "session_key": session_key,
                "driver_number": driver_number
            }
            
            if lap_number:
                params["lap_number"] = lap_number
            
            response = await session.get(f"{self.base_url}/car_data", params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return []
    
    async def get_drivers(self, session_key: str) -> List[Dict[str, Any]]:
        """Get driver information for a session."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/drivers", 
                params={"session_key": session_key}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return []
    
    def _extract_tire_compounds(self, stints: List[Dict[str, Any]]) -> List[str]:
        """Extract unique tire compounds from stint data."""
        compounds = set()
        for stint in stints:
            compound = stint.get("compound")
            if compound:
                compounds.add(compound)
        return list(compounds)
    
    def _extract_track_temperature(self, weather: List[Dict[str, Any]]) -> float:
        """Extract average track temperature from weather data."""
        if not weather:
            return 30.0  # Default temperature
        
        temps = []
        for weather_point in weather:
            track_temp = weather_point.get("track_temperature")
            if track_temp is not None:
                temps.append(track_temp)
        
        if temps:
            return sum(temps) / len(temps)
        return 30.0
    
    async def get_live_timing(self, session_key: str) -> Dict[str, Any]:
        """
        Get live timing data for a session.
        
        Args:
            session_key: Session identifier
            
        Returns:
            Dictionary containing live timing information
        """
        try:
            # Get latest data for all drivers
            tasks = [
                self.get_lap_times(session_key),
                self.get_position_data(session_key),
                self.get_drivers(session_key)
            ]
            
            lap_times, positions, drivers = await asyncio.gather(*tasks)
            
            # Process and combine data
            timing_data = self._process_live_timing(lap_times, positions, drivers)
            
            return {
                "session_key": session_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "timing_data": timing_data
            }
            
        except Exception as e:
            raise Exception(f"Failed to get live timing: {str(e)}")
    
    def _process_live_timing(
        self, 
        lap_times: List[Dict[str, Any]], 
        positions: List[Dict[str, Any]], 
        drivers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process raw timing data into structured format."""
        # This is a simplified processing function
        # In a real implementation, you'd merge and process the data more thoroughly
        
        driver_data = {}
        
        # Create driver lookup
        for driver in drivers:
            driver_number = driver.get("driver_number")
            if driver_number:
                driver_data[driver_number] = {
                    "driver_number": driver_number,
                    "name": f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip(),
                    "team": driver.get("team_name", ""),
                    "abbreviation": driver.get("name_acronym", "")
                }
        
        # Add position data
        for position in positions[-20:]:  # Get recent positions
            driver_number = position.get("driver_number")
            if driver_number in driver_data:
                driver_data[driver_number].update({
                    "position": position.get("position"),
                    "date": position.get("date")
                })
        
        # Add lap time data
        for lap in lap_times[-50:]:  # Get recent lap times
            driver_number = lap.get("driver_number")
            if driver_number in driver_data:
                if "lap_times" not in driver_data[driver_number]:
                    driver_data[driver_number]["lap_times"] = []
                
                driver_data[driver_number]["lap_times"].append({
                    "lap_number": lap.get("lap_number"),
                    "lap_time": lap.get("lap_duration"),
                    "is_personal_best": lap.get("is_personal_best", False)
                })
        
        return list(driver_data.values())