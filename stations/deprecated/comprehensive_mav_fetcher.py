#!/usr/bin/env python3
"""
Comprehensive MAV Stations Fetcher
Fetches Hungarian railway stations from multiple sources including:
- OpenStreetMap Overpass API
- Wikidata
- Static known station lists
- MAV website scraping (where possible)
"""

import json
import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import csv
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveMAVFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MAV-Stations-Fetcher/1.0 (https://github.com/user/project)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,hu;q=0.8'
        })
        self.stations = []
        self.seen_ids = set()
        
    def fetch_from_overpass(self) -> List[Dict[str, Any]]:
        """
        Fetch railway stations in Hungary from OpenStreetMap via Overpass API
        """
        logger.info("Fetching stations from OpenStreetMap...")
        
        overpass_query = """
        [out:json][timeout:60];
        (
          node["railway"="station"]["country"="HU"];
          node["railway"="halt"]["country"="HU"];
          node["public_transport"="station"]["railway"="rail"]["country"="HU"];
          way["railway"="station"]["country"="HU"];
          relation["railway"="station"]["country"="HU"];
        );
        out geom;
        """
        
        try:
            url = "https://overpass-api.de/api/interpreter"
            response = self.session.post(url, data=overpass_query, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                stations = []
                
                for element in data.get('elements', []):
                    tags = element.get('tags', {})
                    
                    if 'name' in tags:
                        station = {
                            'id': f"osm_{element.get('id')}",
                            'name': tags.get('name', ''),
                            'name_hu': tags.get('name:hu', tags.get('name', '')),
                            'name_en': tags.get('name:en', ''),
                            'type': 'station',
                            'country': 'Hungary',
                            'countryIso': 'HU',
                            'source': 'OpenStreetMap',
                            'railway_type': tags.get('railway', 'station'),
                            'operator': tags.get('operator', 'MÁV'),
                            'coordinates': self._extract_coordinates(element),
                            'city': tags.get('addr:city', ''),
                            'postcode': tags.get('addr:postcode', ''),
                            'website': tags.get('website', ''),
                            'wikipedia': tags.get('wikipedia', ''),
                            'wikidata': tags.get('wikidata', ''),
                            'ref': tags.get('ref', ''),
                            'uic_ref': tags.get('uic_ref', ''),
                            'raw_tags': tags
                        }
                        stations.append(station)
                
                logger.info(f"Found {len(stations)} stations from OpenStreetMap")
                return stations
                
        except Exception as e:
            logger.error(f"Error fetching from Overpass API: {e}")
        
        return []
    
    def _extract_coordinates(self, element: Dict) -> Optional[Dict[str, float]]:
        """Extract coordinates from OSM element"""
        if 'lat' in element and 'lon' in element:
            return {
                'latitude': float(element['lat']),
                'longitude': float(element['lon'])
            }
        elif 'center' in element:
            return {
                'latitude': float(element['center']['lat']),
                'longitude': float(element['center']['lon'])
            }
        return None
    
    def fetch_from_wikidata(self) -> List[Dict[str, Any]]:
        """
        Fetch Hungarian railway stations from Wikidata
        """
        logger.info("Fetching stations from Wikidata...")
        
        sparql_query = """
        SELECT ?station ?stationLabel ?coord ?cityLabel ?operatorLabel ?uicCode WHERE {
          ?station wdt:P31/wdt:P279* wd:Q55488 .  # railway station
          ?station wdt:P17 wd:Q28 .                # country: Hungary
          OPTIONAL { ?station wdt:P625 ?coord }
          OPTIONAL { ?station wdt:P131 ?city }
          OPTIONAL { ?station wdt:P137 ?operator }
          OPTIONAL { ?station wdt:P954 ?uicCode }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "hu,en" }
        }
        """
        
        try:
            url = "https://query.wikidata.org/sparql"
            response = self.session.get(url, params={
                'query': sparql_query,
                'format': 'json'
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                stations = []
                
                for binding in data.get('results', {}).get('bindings', []):
                    station_uri = binding.get('station', {}).get('value', '')
                    wikidata_id = station_uri.split('/')[-1] if station_uri else ''
                    
                    station = {
                        'id': f"wd_{wikidata_id}",
                        'name': binding.get('stationLabel', {}).get('value', ''),
                        'type': 'station',
                        'country': 'Hungary',
                        'countryIso': 'HU',
                        'source': 'Wikidata',
                        'wikidata': wikidata_id,
                        'city': binding.get('cityLabel', {}).get('value', ''),
                        'operator': binding.get('operatorLabel', {}).get('value', ''),
                        'uic_ref': binding.get('uicCode', {}).get('value', ''),
                        'coordinates': self._parse_wikidata_coords(binding.get('coord', {}).get('value', '')),
                        'wikidata_uri': station_uri
                    }
                    stations.append(station)
                
                logger.info(f"Found {len(stations)} stations from Wikidata")
                return stations
                
        except Exception as e:
            logger.error(f"Error fetching from Wikidata: {e}")
        
        return []
    
    def _parse_wikidata_coords(self, coord_string: str) -> Optional[Dict[str, float]]:
        """Parse Wikidata coordinate string"""
        if coord_string and coord_string.startswith('Point('):
            try:
                coords = coord_string.replace('Point(', '').replace(')', '').split()
                return {
                    'longitude': float(coords[0]),
                    'latitude': float(coords[1])
                }
            except (ValueError, IndexError):
                pass
        return None
    
    def get_known_mav_stations(self) -> List[Dict[str, Any]]:
        """
        Get a list of known major MAV stations
        """
        logger.info("Adding known MAV stations...")
        
        known_stations = [
            {
                'id': '005510009',
                'name': 'BUDAPEST*',
                'aliasNames': ['Bp (BUDAPEST*)', 'Budapest', 'Budapest Central'],
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Budapest',
                'isInternational': True,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005513005',
                'name': 'BUDAPEST-KELETI',
                'aliasNames': ['Budapest Keleti', 'Budapest East', 'Keleti pu.'],
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Budapest',
                'isInternational': True,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005513006',
                'name': 'BUDAPEST-NYUGATI',
                'aliasNames': ['Budapest Nyugati', 'Budapest West', 'Nyugati pu.'],
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Budapest',
                'isInternational': True,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005513007',
                'name': 'BUDAPEST-DÉLI',
                'aliasNames': ['Budapest Déli', 'Budapest South', 'Déli pu.'],
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Budapest',
                'isInternational': False,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005516001',
                'name': 'DEBRECEN',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Debrecen',
                'isInternational': True,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005517001',
                'name': 'SZEGED',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Szeged',
                'isInternational': False,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005518001',
                'name': 'PÉCS',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Pécs',
                'isInternational': False,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005519001',
                'name': 'GYŐR',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Győr',
                'isInternational': True,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005520001',
                'name': 'SZOLNOK',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Szolnok',
                'isInternational': False,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            },
            {
                'id': '005521001',
                'name': 'MISKOLC',
                'type': 'station',
                'country': 'Hungary',
                'countryIso': 'HU',
                'city': 'Miskolc',
                'isInternational': False,
                'operator': 'MÁV',
                'source': 'known_stations',
                'major_hub': True
            }
        ]
        
        # Add transport mode to all stations
        for station in known_stations:
            station['transportMode'] = {
                'code': 100,
                'name': 'Rail',
                'description': 'Rail. Used for intercity or long-distance travel.'
            }
            station['canUseForOfferRequest'] = True
            station['canUseForPassengerInformation'] = True
        
        logger.info(f"Added {len(known_stations)} known MAV stations")
        return known_stations
    
    def merge_stations(self, *station_lists) -> List[Dict[str, Any]]:
        """
        Merge stations from multiple sources, avoiding duplicates
        """
        merged = []
        seen_names = set()
        seen_coords = set()
        
        for station_list in station_lists:
            for station in station_list:
                # Check for duplicates by name and coordinates
                name_key = station.get('name', '').lower().strip()
                coords = station.get('coordinates')
                coord_key = None
                if coords and coords.get('latitude') and coords.get('longitude'):
                    # Round coordinates to avoid floating point precision issues
                    coord_key = (round(coords['latitude'], 4), round(coords['longitude'], 4))
                
                is_duplicate = False
                
                # Check for name duplicates
                if name_key and name_key in seen_names:
                    is_duplicate = True
                
                # Check for coordinate duplicates (if coordinates exist)
                if coord_key and coord_key in seen_coords:
                    is_duplicate = True
                
                if not is_duplicate:
                    merged.append(station)
                    if name_key:
                        seen_names.add(name_key)
                    if coord_key:
                        seen_coords.add(coord_key)
                else:
                    logger.debug(f"Skipping duplicate station: {station.get('name')}")
        
        return merged
    
    def save_stations_data(self, stations: List[Dict[str, Any]], output_file: str = "comprehensive_mav_stations.json"):
        """
        Save comprehensive stations data to files
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save complete JSON data
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stations, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            # Save CSV format
            csv_path = output_path.with_suffix('.csv')
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if stations:
                    fieldnames = ['id', 'name', 'city', 'country', 'operator', 'source', 'latitude', 'longitude']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for station in stations:
                        coords = station.get('coordinates', {}) or {}
                        row = {
                            'id': station.get('id', ''),
                            'name': station.get('name', ''),
                            'city': station.get('city', ''),
                            'country': station.get('country', ''),
                            'operator': station.get('operator', ''),
                            'source': station.get('source', ''),
                            'latitude': coords.get('latitude', ''),
                            'longitude': coords.get('longitude', '')
                        }
                        writer.writerow(row)
            
            # Create summary
            sources = {}
            for station in stations:
                source = station.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            summary = {
                'total_stations': len(stations),
                'sources': sources,
                'major_hubs': len([s for s in stations if s.get('major_hub', False)]),
                'international_stations': len([s for s in stations if s.get('isInternational', False)]),
                'stations_with_coordinates': len([s for s in stations if s.get('coordinates')]),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                'data_sources': [
                    'OpenStreetMap (via Overpass API)',
                    'Wikidata (via SPARQL)',
                    'Known MAV stations database'
                ],
                'sample_stations': stations[:10] if stations else []
            }
            
            summary_path = output_path.parent / f"{output_path.stem}_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved {len(stations)} stations to {output_path}")
            logger.info(f"CSV format saved to {csv_path}")
            logger.info(f"Summary saved to {summary_path}")
            
        except Exception as e:
            logger.error(f"Error saving stations data: {e}")
    
    def fetch_all_stations(self, output_file: str = "comprehensive_mav_stations.json"):
        """
        Fetch stations from all available sources
        """
        logger.info("🚂 Starting comprehensive MAV stations fetch...")
        
        all_station_lists = []
        
        # Fetch from multiple sources
        try:
            osm_stations = self.fetch_from_overpass()
            if osm_stations:
                all_station_lists.append(osm_stations)
        except Exception as e:
            logger.error(f"OSM fetch failed: {e}")
        
        try:
            wikidata_stations = self.fetch_from_wikidata()
            if wikidata_stations:
                all_station_lists.append(wikidata_stations)
        except Exception as e:
            logger.error(f"Wikidata fetch failed: {e}")
        
        # Add known stations
        known_stations = self.get_known_mav_stations()
        all_station_lists.append(known_stations)
        
        # Merge all stations
        if all_station_lists:
            merged_stations = self.merge_stations(*all_station_lists)
            
            # Sort by name
            merged_stations.sort(key=lambda x: x.get('name', ''))
            
            # Save data
            self.save_stations_data(merged_stations, output_file)
            
            logger.info(f"✅ Comprehensive fetch completed! Found {len(merged_stations)} unique stations.")
            return True
        else:
            logger.error("❌ No station data could be fetched from any source")
            return False

def main():
    """
    Main function
    """
    fetcher = ComprehensiveMAVFetcher()
    
    output_file = Path(__file__).parent / "comprehensive_mav_stations.json"
    success = fetcher.fetch_all_stations(str(output_file))
    
    if success:
        print(f"🎉 Successfully created comprehensive MAV stations database!")
        print(f"📁 Data saved to: {output_file}")
        print(f"📊 Check the summary file for detailed statistics")
        print(f"📋 CSV format also available: {output_file.with_suffix('.csv')}")
    else:
        print("❌ Failed to fetch comprehensive station data")

if __name__ == "__main__":
    main() 