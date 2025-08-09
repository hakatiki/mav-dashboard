#!/usr/bin/env python3
"""
MAV Rail Data Fetcher
Fetches detailed train data from MAV GraphQL API for all RAIL routes
"""

import json
import requests
import time
import os
from datetime import datetime
from typing import List, Dict, Any

class MAVRailFetcher:
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
    
    def fetch_route_data(self, route_id: str) -> Dict[str, Any]:
        """Fetch data for a specific route from the API"""
        query_data = self.create_graphql_query(route_id)
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=query_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data for route {route_id}: {e}")
            return {"error": str(e), "route_id": route_id}
    
    def save_response(self, route_id: str, data: Dict[str, Any], output_dir: str = "rail_data"):
        """Save API response to a JSON file"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean route_id for filename (remove special characters)
        clean_route_id = route_id.replace(":", "_").replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/route_{clean_route_id}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved data for route {route_id} to {filename}")
        except Exception as e:
            print(f"Error saving data for route {route_id}: {e}")
    
    def process_routes(self, limit: int = None):
        """Process RAIL routes and fetch their data"""
        print("Loading routes...")
        routes = self.load_routes()
        
        if not routes:
            print("No routes loaded. Exiting.")
            return
        
        print(f"Total routes loaded: {len(routes)}")
        
        rail_routes = self.filter_rail_routes(routes)
        print(f"RAIL routes found: {len(rail_routes)}")
        
        if limit:
            rail_routes = rail_routes[:limit]
            print(f"Processing first {limit} RAIL routes...")
        
        successful = 0
        failed = 0
        
        for i, route in enumerate(rail_routes, 1):
            route_id = route.get('id')
            if not route_id:
                print(f"Route {i}: No ID found, skipping")
                failed += 1
                continue
                
            print(f"Processing route {i}/{len(rail_routes)}: {route_id} - {route.get('longName', 'Unknown')}")
            
            # Fetch data
            data = self.fetch_route_data(route_id)
            
            # Save response
            self.save_response(route_id, data)
            
            if "error" in data:
                failed += 1
            else:
                successful += 1
            
            # Add delay to be respectful to the API
            time.sleep(1)
        
        print(f"\nProcessing complete:")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total processed: {successful + failed}")

def main():
    """Main function"""
    fetcher = MAVRailFetcher()
    
    # Start with 1 route for testing
    print("Testing with 1 RAIL route...")
    fetcher.process_routes(limit=1)
    
    input("\nPress Enter to continue with 10 routes, or Ctrl+C to exit...")
    
    # Then try 10 routes
    print("Testing with 10 RAIL routes...")
    fetcher.process_routes(limit=10)
    
    input("\nPress Enter to process ALL RAIL routes, or Ctrl+C to exit...")
    
    # Process all routes
    print("Processing ALL RAIL routes...")
    fetcher.process_routes()

if __name__ == "__main__":
    main() 