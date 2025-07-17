#!/usr/bin/env python3
"""
MÁV Station Lookup Utility
Loads the official MÁV stations.json file and provides search functionality
to find station codes by name.
"""

import json
import os
from typing import List, Dict, Optional
import re

class MAVStationLookup:
    """Utility class for looking up MÁV station codes by name."""
    
    def __init__(self, stations_file_path: str = None):
        """
        Initialize the station lookup.
        
        Args:
            stations_file_path: Path to the stations.json file (auto-detected if None)
        """
        if stations_file_path is None:
            # Try to find stations.json in common locations
            possible_paths = [
                "../stations/stations.json",  # From scraper directory
                "stations/stations.json",     # From project root
                "stations.json"               # Current directory
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    stations_file_path = path
                    break
            
            if stations_file_path is None:
                stations_file_path = "stations/stations.json"  # Default fallback
                
        self.stations_file = stations_file_path
        self.stations = []
        self.load_stations()
    
    def load_stations(self):
        """Load stations from the JSON file."""
        try:
            if os.path.exists(self.stations_file):
                with open(self.stations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stations = data.get('stations', [])
                print(f"✅ Loaded {len(self.stations)} stations from MÁV database")
            else:
                print(f"❌ Stations file not found: {self.stations_file}")
        except Exception as e:
            print(f"❌ Error loading stations: {e}")
    
    def search_stations(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for stations by name.
        
        Args:
            query: Search term (station name)
            limit: Maximum number of results to return
            
        Returns:
            List of matching station dictionaries
        """
        if not self.stations:
            return []
        
        query_lower = query.lower().strip()
        matches = []
        
        for station in self.stations:
            name = station.get('name', '').lower()
            name_without_comma = station.get('nameWithoutComma', '').lower()
            
            # Check if query matches station name
            if (query_lower in name or 
                query_lower in name_without_comma or
                name.startswith(query_lower) or
                name_without_comma.startswith(query_lower)):
                
                # Prioritize exact matches and railway stations
                score = 0
                if query_lower == name or query_lower == name_without_comma:
                    score += 100  # Exact match
                if 'vasútállomás' in name or 'állomás' in name:
                    score += 50   # Railway station
                if name.startswith(query_lower):
                    score += 25   # Starts with query
                if query_lower in name:
                    score += 10   # Contains query
                
                matches.append({
                    'station': station,
                    'score': score
                })
        
        # Sort by score (highest first) and return top results
        matches.sort(key=lambda x: x['score'], reverse=True)
        return [match['station'] for match in matches[:limit]]
    
    def find_station_code(self, name: str) -> Optional[str]:
        """
        Find the station code for a given station name.
        
        Args:
            name: Station name to search for
            
        Returns:
            Station code if found, None otherwise
        """
        results = self.search_stations(name, limit=1)
        if results and results[0].get('canUseForOfferRequest', False):
            return results[0].get('code')
        return None
    
    def get_railway_stations(self, query: str) -> List[Dict]:
        """
        Get only railway stations (vasútállomás) for a query.
        
        Args:
            query: Search term
            
        Returns:
            List of railway station dictionaries
        """
        all_results = self.search_stations(query, limit=20)
        railway_stations = []
        
        for station in all_results:
            name = station.get('name', '').lower()
            # Filter for railway stations only
            if ('vasútállomás' in name or 
                'állomás' in name or
                (station.get('canUseForOfferRequest', False) and 
                 not ('autóbusz' in name or 'megállóhely' in name))):
                railway_stations.append(station)
        
        return railway_stations
    
    def display_search_results(self, query: str):
        """Display formatted search results."""
        results = self.get_railway_stations(query)
        
        if not results:
            print(f"❌ No railway stations found for '{query}'")
            return
        
        print(f"🚉 Railway stations matching '{query}':")
        print("="*60)
        
        for i, station in enumerate(results[:10], 1):
            name = station.get('name', 'Unknown')
            code = station.get('code', 'Unknown')
            can_use = "✅" if station.get('canUseForOfferRequest', False) else "❌"
            
            print(f"{i:2d}. {can_use} {name}")
            print(f"    Code: {code}")
            print()

def main():
    """Demo the station lookup functionality."""
    lookup = MAVStationLookup()
    
    # Test searches
    test_queries = ["Kőszeg", "Szombathely", "Budapest", "Szeged"]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: {query}")
        print("-" * 40)
        lookup.display_search_results(query)
        
        # Show the code for API use
        code = lookup.find_station_code(query)
        if code:
            print(f"🎯 API Code for {query}: {code}")
        print()

if __name__ == "__main__":
    main() 