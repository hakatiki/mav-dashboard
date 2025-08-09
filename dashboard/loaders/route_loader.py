"""
Route Loader Library

Loads and parses route data from JSON files containing detailed route information
with coordinates, stations, and route patterns.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Stop:
    """Represents a train stop/station with coordinates"""
    raw_id: str
    pure_id: str  # Extracted station ID
    lat: float
    lon: float
    name: str
    location_type: str


@dataclass
class Pattern:
    """Represents a route pattern (direction/variant)"""
    id: str
    headsign: str
    from_stop_name: str
    name: str
    stops: List[Stop]


@dataclass
class Route:
    """Represents a complete route with metadata and patterns"""
    id: str
    desc: str
    agency_name: str
    long_name: str
    short_name: str
    mode: str
    route_type: int
    color: str
    text_color: str
    patterns: List[Pattern]


class RouteLoader:
    """Loader for route data from JSON files"""
    
    def __init__(self, data_dir: str):
        """
        Initialize the route loader
        
        Args:
            data_dir: Directory containing route JSON files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"Data directory {data_dir} does not exist")
    
    def extract_pure_station_id(self, raw_id: str) -> str:
        """
        Extract pure station ID from raw ID
        
        Args:
            raw_id: Raw station ID like "1:005514449_0"
            
        Returns:
            Pure station ID like "005514449"
        """
        try:
            return raw_id.split(":")[1].split("_")[0]
        except (IndexError, AttributeError):
            return raw_id
    
    def parse_stop(self, stop_data: dict) -> Stop:
        """Parse a single stop from JSON data"""
        raw_id = stop_data.get("id", "")
        pure_id = self.extract_pure_station_id(raw_id)
        
        return Stop(
            raw_id=raw_id,
            pure_id=pure_id,
            lat=stop_data.get("lat", 0.0),
            lon=stop_data.get("lon", 0.0),
            name=stop_data.get("name", ""),
            location_type=stop_data.get("locationType", "")
        )
    
    def parse_pattern(self, pattern_data: dict) -> Pattern:
        """Parse a route pattern from JSON data"""
        stops = []
        for stop_data in pattern_data.get("stops", []):
            stops.append(self.parse_stop(stop_data))
        
        return Pattern(
            id=pattern_data.get("id", ""),
            headsign=pattern_data.get("headsign", ""),
            from_stop_name=pattern_data.get("fromStopName", ""),
            name=pattern_data.get("name", ""),
            stops=stops
        )
    
    def parse_route_file(self, file_path: Path) -> Optional[Route]:
        """
        Parse a single route JSON file
        
        Args:
            file_path: Path to the route JSON file
            
        Returns:
            Route object or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            route_data = data.get("data", {}).get("route", {})
            if not route_data:
                return None
            
            agency = route_data.get("agency", {})
            patterns = []
            
            for pattern_data in route_data.get("patterns", []):
                patterns.append(self.parse_pattern(pattern_data))
            
            return Route(
                id=route_data.get("id", ""),
                desc=route_data.get("desc", ""),
                agency_name=agency.get("name", ""),
                long_name=route_data.get("longName", ""),
                short_name=route_data.get("shortName", ""),
                mode=route_data.get("mode", ""),
                route_type=route_data.get("type", 0),
                color=route_data.get("color", ""),
                text_color=route_data.get("textColor", ""),
                patterns=patterns
            )
            
        except Exception as e:
            print(f"Error parsing route file {file_path}: {e}")
            return None
    
    def load_single_route(self, filename: str) -> Optional[Route]:
        """
        Load a single route by filename
        
        Args:
            filename: Name of the route file
            
        Returns:
            Route object or None if not found/parsing fails
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            print(f"Route file {filename} not found")
            return None
        
        return self.parse_route_file(file_path)
    
    def load_all_routes(self) -> List[Route]:
        """
        Load all route files from the data directory
        
        Returns:
            List of Route objects
        """
        routes = []
        json_files = list(self.data_dir.glob("*.json"))
        
        print(f"Found {len(json_files)} route files to process")
        
        for file_path in json_files:
            route = self.parse_route_file(file_path)
            if route:
                routes.append(route)
            else:
                print(f"Failed to parse {file_path.name}")
        
        print(f"Successfully loaded {len(routes)} routes")
        return routes
    
    def get_all_stations(self, routes: List[Route]) -> Dict[str, Stop]:
        """
        Extract all unique stations from routes
        
        Args:
            routes: List of Route objects
            
        Returns:
            Dictionary mapping pure station IDs to Stop objects
        """
        stations = {}
        
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if stop.pure_id and stop.pure_id not in stations:
                        stations[stop.pure_id] = stop
        
        return stations
    
    def get_route_by_stations(self, routes: List[Route], 
                            start_station_id: str, end_station_id: str) -> List[Route]:
        """
        Find routes that connect two stations
        
        Args:
            routes: List of Route objects
            start_station_id: Pure station ID of start station
            end_station_id: Pure station ID of end station
            
        Returns:
            List of routes that connect the stations
        """
        matching_routes = []
        
        for route in routes:
            for pattern in route.patterns:
                station_ids = [stop.pure_id for stop in pattern.stops]
                if start_station_id in station_ids and end_station_id in station_ids:
                    matching_routes.append(route)
                    break  # Found match in this route, no need to check other patterns
        
        return matching_routes


if __name__ == "__main__":
    # Test the loader
    loader = RouteLoader("../map_v2/all_rail_data")
    
    # Test loading a single route
    print("Testing single route loading...")
    route = loader.load_single_route("route_1_1660__20250725_223055.json")
    if route:
        print(f"Loaded route: {route.desc}")
        print(f"Patterns: {len(route.patterns)}")
        for i, pattern in enumerate(route.patterns):
            print(f"  Pattern {i+1}: {pattern.headsign} ({len(pattern.stops)} stops)")
            if pattern.stops:
                print(f"    First stop: {pattern.stops[0].name} (ID: {pattern.stops[0].pure_id})")
                print(f"    Last stop: {pattern.stops[-1].name} (ID: {pattern.stops[-1].pure_id})")
    
    print("\nTesting station extraction...")
    if route:
        stations = loader.get_all_stations([route])
        print(f"Found {len(stations)} unique stations")
        for station_id, station in list(stations.items())[:3]:
            print(f"  {station_id}: {station.name} at ({station.lat}, {station.lon})") 