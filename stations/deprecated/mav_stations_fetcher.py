#!/usr/bin/env python3
"""
MAV Stations Fetcher
Fetches all stations from Magyar Államvasutak (Hungarian State Railways)
Similar to the martinlangbecker/mav-stations Node.js package
"""

import json
import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MAVStationsFetcher:
    def __init__(self):
        self.base_url = "https://jegy.mav.hu"
        self.stations_endpoint = "/api/v1/stations"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,hu;q=0.8',
            'Referer': 'https://jegy.mav.hu'
        })
        
    def fetch_stations_list(self) -> List[Dict[str, Any]]:
        """
        Fetch the complete list of MAV stations
        """
        try:
            logger.info("Fetching MAV stations list...")
            
            # Try different possible endpoints
            endpoints_to_try = [
                f"{self.base_url}/api/v1/stations",
                f"{self.base_url}/api/stations", 
                f"{self.base_url}/stations",
                f"{self.base_url}/api/v1/locations",
                f"{self.base_url}/api/locations"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = self.session.get(endpoint, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Successfully fetched {len(data)} stations from {endpoint}")
                            return data
                        elif isinstance(data, dict) and 'stations' in data:
                            stations = data['stations']
                            logger.info(f"Successfully fetched {len(stations)} stations from {endpoint}")
                            return stations
                        elif isinstance(data, dict) and 'data' in data:
                            stations = data['data']
                            logger.info(f"Successfully fetched {len(stations)} stations from {endpoint}")
                            return stations
                    
                except requests.RequestException as e:
                    logger.debug(f"Failed to fetch from {endpoint}: {e}")
                    continue
                    
                time.sleep(1)  # Rate limiting
            
            # If API endpoints fail, try scraping approach
            logger.warning("API endpoints failed, trying alternative approach...")
            return self._fetch_via_search()
            
        except Exception as e:
            logger.error(f"Error fetching stations: {e}")
            return []
    
    def _fetch_via_search(self) -> List[Dict[str, Any]]:
        """
        Alternative method: fetch stations by searching with common letters
        """
        stations = []
        seen_ids = set()
        
        # Hungarian alphabet and common search terms
        search_terms = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'bu', 'de', 'sz', 'pe', 'ke', 'ba', 'ta', 'va', 'za', 'ny'
        ]
        
        for term in search_terms:
            try:
                logger.info(f"Searching for stations starting with '{term}'...")
                
                search_endpoints = [
                    f"{self.base_url}/api/v1/stations/search?q={term}",
                    f"{self.base_url}/api/stations/search?query={term}",
                    f"{self.base_url}/api/search/stations?term={term}"
                ]
                
                for endpoint in search_endpoints:
                    try:
                        response = self.session.get(endpoint, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            
                            if isinstance(data, list):
                                search_results = data
                            elif isinstance(data, dict):
                                search_results = data.get('stations', data.get('results', data.get('data', [])))
                            else:
                                continue
                            
                            for station in search_results:
                                station_id = station.get('id') or station.get('stationId')
                                if station_id and station_id not in seen_ids:
                                    seen_ids.add(station_id)
                                    stations.append(self._normalize_station_data(station))
                            
                            if search_results:
                                logger.info(f"Found {len(search_results)} stations for '{term}'")
                                break
                                
                    except requests.RequestException:
                        continue
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Error searching for '{term}': {e}")
                continue
        
        logger.info(f"Total unique stations found: {len(stations)}")
        return stations
    
    def _normalize_station_data(self, station: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize station data to match the format from mav-stations package
        """
        return {
            'type': 'station',
            'id': str(station.get('id', station.get('stationId', ''))),
            'name': station.get('name', station.get('stationName', '')),
            'aliasNames': station.get('aliasNames', station.get('aliases', [])),
            'baseCode': station.get('baseCode', station.get('code', '')),
            'isInternational': station.get('isInternational', False),
            'canUseForOfferRequest': station.get('canUseForOfferRequest', True),
            'canUseForPassengerInformation': station.get('canUseForPassengerInformation', False),
            'country': station.get('country', 'Hungary'),
            'countryIso': station.get('countryIso', 'HU'),
            'isIn108_1': station.get('isIn108_1', station.get('internationalCapable', False)),
            'transportMode': station.get('transportMode', {
                'code': 100,
                'name': 'Rail',
                'description': 'Rail. Used for intercity or long-distance travel.'
            }),
            'coordinates': {
                'latitude': station.get('latitude', station.get('lat')),
                'longitude': station.get('longitude', station.get('lon', station.get('lng')))
            } if station.get('latitude') or station.get('lat') else None,
            'address': station.get('address', ''),
            'city': station.get('city', ''),
            'region': station.get('region', ''),
            'postalCode': station.get('postalCode', ''),
            'raw_data': station  # Keep original data for reference
        }
    
    def fetch_station_details(self, station_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific station
        """
        try:
            detail_endpoints = [
                f"{self.base_url}/api/v1/stations/{station_id}",
                f"{self.base_url}/api/stations/{station_id}"
            ]
            
            for endpoint in detail_endpoints:
                try:
                    response = self.session.get(endpoint, timeout=15)
                    if response.status_code == 200:
                        return response.json()
                except requests.RequestException:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error fetching details for station {station_id}: {e}")
            return None
    
    def save_stations_data(self, stations: List[Dict[str, Any]], output_file: str = "mav_stations.json"):
        """
        Save stations data to JSON file
        """
        try:
            output_path = Path(output_file)
            
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stations, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            logger.info(f"Successfully saved {len(stations)} stations to {output_path}")
            
            # Also save a summary file
            summary = {
                'total_stations': len(stations),
                'countries': list(set(s.get('country', 'Unknown') for s in stations)),
                'international_stations': len([s for s in stations if s.get('isInternational', False)]),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                'sample_stations': stations[:5] if stations else []
            }
            
            summary_path = output_path.parent / f"{output_path.stem}_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Summary saved to {summary_path}")
            
        except Exception as e:
            logger.error(f"Error saving stations data: {e}")
    
    def fetch_all_stations(self, output_file: str = "mav_stations.json", include_details: bool = False):
        """
        Main method to fetch all MAV stations and save to file
        """
        logger.info("Starting MAV stations fetch...")
        
        # Fetch basic stations list
        stations = self.fetch_stations_list()
        
        if not stations:
            logger.error("No stations data could be fetched")
            return False
        
        # Optionally fetch detailed information for each station
        if include_details:
            logger.info("Fetching detailed information for each station...")
            for i, station in enumerate(stations):
                station_id = station.get('id')
                if station_id:
                    details = self.fetch_station_details(station_id)
                    if details:
                        station.update(details)
                
                # Progress update and rate limiting
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(stations)} stations...")
                time.sleep(0.2)
        
        # Save data
        self.save_stations_data(stations, output_file)
        
        logger.info(f"MAV stations fetch completed! Found {len(stations)} stations.")
        return True

def main():
    """
    Main function to run the MAV stations fetcher
    """
    fetcher = MAVStationsFetcher()
    
    # Fetch and save all stations
    output_file = Path(__file__).parent / "mav_stations.json"
    success = fetcher.fetch_all_stations(str(output_file), include_details=False)
    
    if success:
        print(f"✅ Successfully fetched MAV stations data!")
        print(f"📁 Data saved to: {output_file}")
        print(f"📊 Check the summary file for statistics")
    else:
        print("❌ Failed to fetch MAV stations data")
        print("💡 Check the logs for more information")

if __name__ == "__main__":
    main() 