"""
Jolpica F1 API Service

This module provides integration with the Jolpica F1 API for historical F1 data.
Jolpica provides historical race results, driver standings, and circuit information.
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
import os
from datetime import datetime


class JolpicaService:
    """
    Service for interacting with the Jolpica F1 API.
    
    Jolpica provides historical Formula 1 data including:
    - Race results
    - Qualifying results
    - Driver standings
    - Constructor standings
    - Circuit information
    - Historical race data
    """
    
    def __init__(self):
        """Initialize the Jolpica service."""
        self.base_url = os.getenv("JOLPICA_API_URL", "https://jolpica-f1-api.com/v1")
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
    
    async def get_seasons(self) -> List[Dict[str, Any]]:
        """
        Get available F1 seasons.
        
        Returns:
            List of season information
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/seasons")
            response.raise_for_status()
            
            seasons_data = response.json()
            
            # Format season data
            seasons = []
            for season in seasons_data.get("seasons", []):
                seasons.append({
                    "year": season.get("year"),
                    "url": season.get("url"),
                    "total_races": len(season.get("races", []))
                })
            
            return seasons
            
        except httpx.HTTPError as e:
            # Return default recent seasons if API fails
            current_year = datetime.now().year
            return [
                {"year": year, "url": f"/seasons/{year}", "total_races": 23}
                for year in range(current_year - 5, current_year + 1)
            ]
        except Exception as e:
            raise Exception(f"Failed to fetch seasons: {str(e)}")
    
    async def get_races(self, year: int) -> List[Dict[str, Any]]:
        """
        Get races for a specific year.
        
        Args:
            year: Year to get races for
            
        Returns:
            List of race information
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/seasons/{year}/races")
            response.raise_for_status()
            
            races_data = response.json()
            
            races = []
            for race in races_data.get("races", []):
                races.append({
                    "round": race.get("round"),
                    "race_name": race.get("raceName"),
                    "circuit": {
                        "circuit_id": race.get("Circuit", {}).get("circuitId"),
                        "circuit_name": race.get("Circuit", {}).get("circuitName"),
                        "location": race.get("Circuit", {}).get("Location", {})
                    },
                    "date": race.get("date"),
                    "time": race.get("time"),
                    "url": race.get("url")
                })
            
            return races
            
        except httpx.HTTPError as e:
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch races: {str(e)}")
    
    async def get_race_results(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        Get race results for a specific race.
        
        Args:
            year: Year of the race
            round_number: Round number of the race
            
        Returns:
            Dictionary containing race results
        """
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/seasons/{year}/races/{round_number}/results"
            )
            response.raise_for_status()
            
            results_data = response.json()
            race_data = results_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            
            if not race_data:
                return {"error": "No race data found"}
            
            race = race_data[0]
            results = []
            
            for result in race.get("Results", []):
                driver = result.get("Driver", {})
                constructor = result.get("Constructor", {})
                
                results.append({
                    "position": result.get("position"),
                    "driver": {
                        "driver_id": driver.get("driverId"),
                        "permanent_number": driver.get("permanentNumber"),
                        "code": driver.get("code"),
                        "given_name": driver.get("givenName"),
                        "family_name": driver.get("familyName"),
                        "nationality": driver.get("nationality")
                    },
                    "constructor": {
                        "constructor_id": constructor.get("constructorId"),
                        "name": constructor.get("name"),
                        "nationality": constructor.get("nationality")
                    },
                    "grid": result.get("grid"),
                    "laps": result.get("laps"),
                    "status": result.get("status"),
                    "time": result.get("Time", {}).get("time"),
                    "fastest_lap": result.get("FastestLap", {})
                })
            
            return {
                "race": {
                    "season": year,
                    "round": round_number,
                    "race_name": race.get("raceName"),
                    "circuit": race.get("Circuit"),
                    "date": race.get("date"),
                    "time": race.get("time")
                },
                "results": results
            }
            
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch race results: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def get_qualifying_results(self, year: int, round_number: int) -> Dict[str, Any]:
        """
        Get qualifying results for a specific race.
        
        Args:
            year: Year of the race
            round_number: Round number of the race
            
        Returns:
            Dictionary containing qualifying results
        """
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.base_url}/seasons/{year}/races/{round_number}/qualifying"
            )
            response.raise_for_status()
            
            qualifying_data = response.json()
            race_data = qualifying_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            
            if not race_data:
                return {"error": "No qualifying data found"}
            
            race = race_data[0]
            results = []
            
            for result in race.get("QualifyingResults", []):
                driver = result.get("Driver", {})
                constructor = result.get("Constructor", {})
                
                results.append({
                    "position": result.get("position"),
                    "driver": {
                        "driver_id": driver.get("driverId"),
                        "code": driver.get("code"),
                        "given_name": driver.get("givenName"),
                        "family_name": driver.get("familyName")
                    },
                    "constructor": constructor.get("name"),
                    "q1": result.get("Q1"),
                    "q2": result.get("Q2"),
                    "q3": result.get("Q3")
                })
            
            return {
                "race": {
                    "season": year,
                    "round": round_number,
                    "race_name": race.get("raceName"),
                    "circuit": race.get("Circuit")
                },
                "qualifying_results": results
            }
            
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch qualifying results: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def get_driver_standings(self, year: int) -> List[Dict[str, Any]]:
        """
        Get driver championship standings for a year.
        
        Args:
            year: Year to get standings for
            
        Returns:
            List of driver standings
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/seasons/{year}/driverStandings")
            response.raise_for_status()
            
            standings_data = response.json()
            standings_list = standings_data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
            
            if not standings_list:
                return []
            
            driver_standings = []
            for standing in standings_list[0].get("DriverStandings", []):
                driver = standing.get("Driver", {})
                constructors = standing.get("Constructors", [])
                
                driver_standings.append({
                    "position": standing.get("position"),
                    "position_text": standing.get("positionText"),
                    "points": standing.get("points"),
                    "wins": standing.get("wins"),
                    "driver": {
                        "driver_id": driver.get("driverId"),
                        "permanent_number": driver.get("permanentNumber"),
                        "code": driver.get("code"),
                        "given_name": driver.get("givenName"),
                        "family_name": driver.get("familyName"),
                        "nationality": driver.get("nationality")
                    },
                    "constructors": [c.get("name") for c in constructors]
                })
            
            return driver_standings
            
        except httpx.HTTPError as e:
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch driver standings: {str(e)}")
    
    async def get_constructor_standings(self, year: int) -> List[Dict[str, Any]]:
        """
        Get constructor championship standings for a year.
        
        Args:
            year: Year to get standings for
            
        Returns:
            List of constructor standings
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/seasons/{year}/constructorStandings")
            response.raise_for_status()
            
            standings_data = response.json()
            standings_list = standings_data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
            
            if not standings_list:
                return []
            
            constructor_standings = []
            for standing in standings_list[0].get("ConstructorStandings", []):
                constructor = standing.get("Constructor", {})
                
                constructor_standings.append({
                    "position": standing.get("position"),
                    "position_text": standing.get("positionText"),
                    "points": standing.get("points"),
                    "wins": standing.get("wins"),
                    "constructor": {
                        "constructor_id": constructor.get("constructorId"),
                        "name": constructor.get("name"),
                        "nationality": constructor.get("nationality"),
                        "url": constructor.get("url")
                    }
                })
            
            return constructor_standings
            
        except httpx.HTTPError as e:
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch constructor standings: {str(e)}")
    
    async def get_circuit_info(self, circuit_id: str) -> Dict[str, Any]:
        """
        Get information about a specific circuit.
        
        Args:
            circuit_id: Circuit identifier
            
        Returns:
            Dictionary containing circuit information
        """
        try:
            session = await self._get_session()
            response = await session.get(f"{self.base_url}/circuits/{circuit_id}")
            response.raise_for_status()
            
            circuit_data = response.json()
            circuits = circuit_data.get("MRData", {}).get("CircuitTable", {}).get("Circuits", [])
            
            if not circuits:
                return {"error": "Circuit not found"}
            
            circuit = circuits[0]
            location = circuit.get("Location", {})
            
            return {
                "circuit_id": circuit.get("circuitId"),
                "url": circuit.get("url"),
                "circuit_name": circuit.get("circuitName"),
                "location": {
                    "lat": location.get("lat"),
                    "long": location.get("long"),
                    "locality": location.get("locality"),
                    "country": location.get("country")
                }
            }
            
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch circuit info: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def get_historical_data(
        self, 
        year: int, 
        circuit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive historical data for analysis.
        
        Args:
            year: Year to get data for
            circuit_id: Specific circuit (optional)
            
        Returns:
            Dictionary containing historical race data
        """
        try:
            # Get multiple data types concurrently
            tasks = [
                self.get_races(year),
                self.get_driver_standings(year),
                self.get_constructor_standings(year)
            ]
            
            races, driver_standings, constructor_standings = await asyncio.gather(*tasks)
            
            # If specific circuit requested, filter races
            if circuit_id:
                races = [r for r in races if r.get("circuit", {}).get("circuit_id") == circuit_id]
            
            # Get detailed results for each race
            race_results = []
            for race in races[:5]:  # Limit to prevent too many API calls
                if race.get("round"):
                    result = await self.get_race_results(year, int(race["round"]))
                    if "error" not in result:
                        race_results.append(result)
            
            return {
                "year": year,
                "circuit_filter": circuit_id,
                "races": races,
                "race_results": race_results,
                "driver_standings": driver_standings,
                "constructor_standings": constructor_standings,
                "summary": {
                    "total_races": len(races),
                    "detailed_results": len(race_results)
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get historical data: {str(e)}"}