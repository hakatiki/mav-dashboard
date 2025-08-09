#!/usr/bin/env python3
"""
Fetch ALL RAIL routes from MAV GraphQL API
"""

import json
import requests
import time
import os
from datetime import datetime
from typing import List, Dict, Any

class MAVAllRailFetcher:
    def __init__(self):
        self.api_url = "https://emma.mav.hu//otp2-backend/otp/routers/default/index/graphql"
        self.headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-GB,en;q=0.9,hu-HU;q=0.8,hu;q=0.7,en-US;q=0.6,nl;q=0.5',
            'connection': 'keep-alive',
            'content-type': 'application/json',
            'host': 'emma.mav.hu',
            'origin': 'https://emma.mav.hu',
            'referer': 'https://emma.mav.hu/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        self.service_day = datetime.now().strftime("%Y%m%d")
        self.output_dir = "all_rail_data"
        
    def load_routes(self) -> List[Dict[str, Any]]:
        """Load routes from routes.json file"""
        try:
            with open('routes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Extract routes from the nested structure
            if isinstance(data, dict) and 'data' in data and 'routes' in data['data']:
                return data['data']['routes']
            else:
                print("Unexpected JSON structure in routes.json")
                return []
        except Exception as e:
            print(f"Error loading routes.json: {e}")
            return []
    
    def filter_rail_routes(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter routes to only include RAIL mode"""
        rail_routes = []
        for route in routes:
            if route.get('mode') == 'RAIL':
                rail_routes.append(route)
        return rail_routes
    
    def create_graphql_query(self, route_id: str) -> Dict[str, Any]:
        """Create GraphQL query for a specific route"""
        query = f"""
        {{
            route(id: "{route_id}") {{
                alerts (types: [STOPS_ON_ROUTE], serviceDay: "{self.service_day}") {{
                    alertHash
                    alertUrl
                    alertCause
                    alertEffect
                    alertHeaderText
                    alertSeverityLevel
                    alertDescriptionText
                    alertUrlTranslations {{
                        language
                        text
                    }}
                    alertHeaderTextTranslations {{
                        language
                        text
                    }}
                    alertDescriptionTextTranslations {{
                        text
                        language
                    }}
                    id
                    effectiveStartDate
                    effectiveEndDate
                    feed
                }}
                id: gtfsId
                desc
                agency {{
                    id: gtfsId
                    name
                    url
                    timezone
                    lang
                    phone
                }}
                longName
                shortName
                mode
                type
                color
                textColor
                bikesAllowed
                routeBikesAllowed: bikesAllowed
                url
                patterns {{
                    id
                    headsign
                    fromStopName
                    name
                    patternGeometry {{
                        points
                        length
                    }}
                    trips {{
                        activeDates
                    }},
                    stops {{
                        code
                        id: gtfsId
                        lat
                        lon
                        name
                        locationType
                        geometries {{
                            geoJson
                        }}
                        routes {{
                            textColor
                            color
                        }}
                        alerts (types: [STOP_ON_ROUTES, STOP_ON_TRIPS, STOP], serviceDay: "{self.service_day}") {{
                            alertHash
                            alertUrl
                            alertCause
                            alertEffect
                            alertHeaderText
                            alertSeverityLevel
                            alertDescriptionText
                            alertUrlTranslations {{
                                language
                                text
                            }}
                            alertHeaderTextTranslations {{
                                language
                                text
                            }}
                            alertDescriptionTextTranslations {{
                                text
                                language
                            }}
                            id
                            effectiveStartDate
                            effectiveEndDate
                            feed
                        }}
                    }}
                    tripsForDate(serviceDate: "{self.service_day}") {{
                        departureStoptime(serviceDate: "{self.service_day}") {{
                            scheduledDeparture
                        }}
                        gtfsId
                    }}
                    alerts (types: [ROUTE], serviceDay: "{self.service_day}") {{
                        alertHash
                        alertUrl
                        alertCause
                        alertEffect
                        alertHeaderText
                        alertSeverityLevel
                        alertDescriptionText
                        alertUrlTranslations {{
                            language
                            text
                        }}
                        alertHeaderTextTranslations {{
                            language
                            text
                        }}
                        alertDescriptionTextTranslations {{
                            text
                            language
                        }}
                        id
                        effectiveStartDate
                        effectiveEndDate
                        feed
                    }}
                    vehiclePositions {{
                        vehicleId
                        label
                        lat
                        lon
                        stopRelationship {{
                            status
                            stop {{
                                name
                                gtfsId
                            }}
                            arrivalTime
                            departureTime
                        }}
                        speed
                        heading
                        lastUpdated
                        trip {{
                            tripHeadsign
                            tripShortName
                            id
                            gtfsId
                            tripShortName
                            routeShortName
                            activeDates
                            serviceId
                            pattern {{
                                id
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        return {"query": query}
    
    def fetch_route_data(self, route_id: str, max_retries: int = 3) -> Dict[str, Any]:
        """Fetch data for a specific route from the API with retry logic"""
        query_data = self.create_graphql_query(route_id)
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=query_data,
                    timeout=60  # Increased timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{max_retries} for route {route_id}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
                    continue
                return {"error": "Timeout after all retries", "route_id": route_id}
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}/{max_retries} for route {route_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
                    continue
                return {"error": str(e), "route_id": route_id}
            except Exception as e:
                print(f"Unexpected error for route {route_id}: {e}")
                return {"error": str(e), "route_id": route_id}
    
    def save_response(self, route_id: str, data: Dict[str, Any]) -> bool:
        """Save API response to a JSON file"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Clean route_id for filename (remove special characters)
        clean_route_id = route_id.replace(":", "_").replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/route_{clean_route_id}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved data for route {route_id} to {filename}")
            return True
        except Exception as e:
            print(f"✗ Error saving data for route {route_id}: {e}")
            return False
    
    def save_progress(self, processed_routes: List[str], successful: int, failed: int):
        """Save progress to a JSON file"""
        progress_file = f"{self.output_dir}/progress.json"
        progress_data = {
            "processed_routes": processed_routes,
            "successful": successful,
            "failed": failed,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def load_progress(self) -> tuple:
        """Load previous progress if it exists"""
        progress_file = f"{self.output_dir}/progress.json"
        
        if not os.path.exists(progress_file):
            return [], 0, 0
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            return (
                progress_data.get("processed_routes", []),
                progress_data.get("successful", 0),
                progress_data.get("failed", 0)
            )
        except Exception as e:
            print(f"Error loading progress: {e}")
            return [], 0, 0
    
    def process_all_rail_routes(self):
        """Process ALL RAIL routes and fetch their data"""
        print("🚂 Starting MAV Rail Data Fetcher for ALL routes...")
        print("=" * 60)
        
        # Load routes
        print("Loading routes...")
        routes = self.load_routes()
        
        if not routes:
            print("No routes loaded. Exiting.")
            return
        
        print(f"Total routes loaded: {len(routes)}")
        
        rail_routes = self.filter_rail_routes(routes)
        print(f"RAIL routes found: {len(rail_routes)}")
        
        # Load previous progress
        processed_routes, successful, failed = self.load_progress()
        
        if processed_routes:
            print(f"Resuming from previous session:")
            print(f"  - Already processed: {len(processed_routes)} routes")
            print(f"  - Previous successful: {successful}")
            print(f"  - Previous failed: {failed}")
        
        print(f"Processing ALL {len(rail_routes)} RAIL routes...")
        print("=" * 60)
        
        start_time = datetime.now()
        
        for i, route in enumerate(rail_routes, 1):
            route_id = route.get('id')
            if not route_id:
                print(f"Route {i}: No ID found, skipping")
                failed += 1
                continue
            
            # Skip if already processed
            if route_id in processed_routes:
                print(f"Route {i}/{len(rail_routes)}: {route_id} - Already processed, skipping")
                continue
                
            print(f"Route {i}/{len(rail_routes)}: {route_id} - {route.get('longName', 'Unknown')}")
            
            # Fetch data
            data = self.fetch_route_data(route_id)
            
            # Save response
            if self.save_response(route_id, data):
                if "error" not in data:
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
            
            # Update progress
            processed_routes.append(route_id)
            
            # Save progress every 10 routes
            if i % 10 == 0:
                self.save_progress(processed_routes, successful, failed)
                elapsed = datetime.now() - start_time
                avg_time = elapsed.total_seconds() / len(processed_routes)
                remaining = (len(rail_routes) - len(processed_routes)) * avg_time
                print(f"📊 Progress: {len(processed_routes)}/{len(rail_routes)} | Success: {successful} | Failed: {failed}")
                print(f"⏱️  Estimated time remaining: {remaining/60:.1f} minutes")
                print("-" * 40)
            
            # Add delay to be respectful to the API
            time.sleep(2)  # Increased delay
        
        # Final save
        self.save_progress(processed_routes, successful, failed)
        
        elapsed = datetime.now() - start_time
        print("=" * 60)
        print("🎉 Processing complete!")
        print(f"Total time: {elapsed}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total processed: {successful + failed}")
        print(f"Success rate: {successful/(successful+failed)*100:.1f}%")
        print(f"Data saved in: {self.output_dir}/")

def main():
    """Main function"""
    fetcher = MAVAllRailFetcher()
    fetcher.process_all_rail_routes()

if __name__ == "__main__":
    main() 