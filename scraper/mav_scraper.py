"""
MÁV Train Route Scraper
A clean, modular scraper for fetching MÁV train data and analyzing delays.
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
import sys

# Add logging directory to path for import
if 'logging' not in sys.path:
    sys.path.append('logging')

try:
    from mav_call_logger import MAVCallLogger
except ImportError:
    # Fallback if import fails
    MAVCallLogger = None


class MAVScraper:
    """
    A clean interface to the MÁV API for fetching train route data and delay information.
    """
    
    def __init__(self, enable_logging: bool = True, log_file: str = None):
        self.base_url = "https://jegy-a.mav.hu/IK_API_PROD/api/OfferRequestApi/GetOfferRequest"
        
        # Create a session for cookie persistence and connection reuse
        self.session = requests.Session()
        
        # Set realistic browser headers to mask the request
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        
        # Set realistic headers that rotate
        self._update_headers()
        
        self.timeout = 15
        
        # Initialize logging
        self.enable_logging = enable_logging and MAVCallLogger is not None
        if self.enable_logging:
            self.logger = MAVCallLogger(log_file)
        else:
            self.logger = None
    
    def _update_headers(self):
        """Update session headers with realistic browser headers."""
        user_agent = random.choice(self.user_agents)
        
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,hu;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://jegy.mav.hu",
            "Referer": "https://jegy.mav.hu/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "UserSessionId": "''"
        })
    
    def _add_random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add a small random delay to mimic human behavior."""
        import time
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def create_payload(self, 
                      start_station: str, 
                      end_station: str, 
                      travel_date: Optional[str] = None,
                      start_time: Optional[str] = "01:00",
                      passenger_count: int = 1) -> Dict:
        """
        Create the API payload for route request.
        
        Args:
            start_station: Starting station code (e.g., "005504747")
            end_station: Ending station code (e.g., "005501024")
            travel_date: Travel date in ISO format, defaults to today
            start_time: Start time in HH:MM format, defaults to "01:00"
            passenger_count: Number of passengers, defaults to 1
            
        Returns:
            Dictionary payload for the API request
        """
        if travel_date is None:
            # Use today's date with the specified start time
            today = datetime.now().date()
            if start_time:
                try:
                    hour, minute = map(int, start_time.split(':'))
                    travel_datetime = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                except ValueError:
                    # Fall back to 1 AM if time format is invalid
                    travel_datetime = datetime.combine(today, datetime.min.time().replace(hour=1, minute=0))
            else:
                travel_datetime = datetime.combine(today, datetime.min.time().replace(hour=1, minute=0))
            
            travel_date = travel_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00")
            
        return {
            "offerkind": "1",
            "startStationCode": start_station,
            "innerStationsCodes": [],
            "endStationCode": end_station,
            "modalities": [100, 200, 109],  # From your working example
            "passangers": [{
                "passengerCount": passenger_count,
                "passengerId": 0,
                "customerTypeKey": "HU_44_025-065",
                "customerDiscountsKeys": []
            }],
            "isOneWayTicket": True,
            "isTravelEndTime": False,
            "isSupplementaryTicketsOnly": False,
            "hasHungaryPass": False,
            "travelStartDate": travel_date,
            "travelReturnDate": travel_date,  # Adding this from your example
            "selectedServices": [52],  # From your working example
            "selectedSearchServices": ["BUDAPESTI_HELYI_KOZLEKEDESSEL"],  # From your example
            "eszkozSzamok": [],
            "isOfDetailedSearch": False,
            "isFromTimeTable": False
        }
    
    def fetch_routes(self, start_station: str, end_station: str, 
                    travel_date: Optional[str] = None,
                    start_time: Optional[str] = "01:00",
                    start_station_name: str = "",
                    end_station_name: str = "") -> Tuple[bool, Dict]:
        """
        Fetch train routes from the MÁV API.
        
        Args:
            start_station: Starting station code
            end_station: Ending station code 
            travel_date: Optional travel date, defaults to today
            start_time: Start time in HH:MM format, defaults to "01:00"
            start_station_name: Human-readable start station name for logging
            end_station_name: Human-readable end station name for logging
            
        Returns:
            Tuple of (success, data) where success is bool and data is the API response
        """
        payload = self.create_payload(start_station, end_station, travel_date, start_time)
        
        # Record start time for logging
        call_start_time = datetime.now()
        success = False
        routes_found = 0
        status_code = None
        error_message = ""
        response_data = None
        
        try:
            print(f"🚆 Fetching routes from {start_station} to {end_station}...")
            
            # Occasionally update headers to rotate User-Agent
            if random.random() < 0.1:  # 10% chance to update headers
                self._update_headers()
            
            self._add_random_delay()  # Add a small delay before request
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            
            status_code = response.status_code
            call_end_time = datetime.now()
            
            if response.status_code == 200:
                data = response.json()
                response_data = data
                routes_found = len(data.get('route', []))
                success = True
                print(f"✅ Successfully fetched {routes_found} routes")
                
                # Log successful call
                self._log_api_call(
                    call_start_time, call_end_time,
                    start_station, start_station_name,
                    end_station, end_station_name,
                    travel_date or datetime.now().strftime("%Y-%m-%d"),
                    start_time, success, routes_found,
                    status_code, error_message, response_data
                )
                
                return True, data
            else:
                error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ API returned status code {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
                # Log failed call
                self._log_api_call(
                    call_start_time, call_end_time,
                    start_station, start_station_name,
                    end_station, end_station_name,
                    travel_date or datetime.now().strftime("%Y-%m-%d"),
                    start_time, success, routes_found,
                    status_code, error_message, response_data
                )
                
                return False, {}
                
        except requests.exceptions.RequestException as e:
            call_end_time = datetime.now()
            error_message = f"Network error: {str(e)}"
            print(f"❌ Network error: {e}")
            
            self._log_api_call(
                call_start_time, call_end_time,
                start_station, start_station_name,
                end_station, end_station_name,
                travel_date or datetime.now().strftime("%Y-%m-%d"),
                start_time, success, routes_found,
                status_code, error_message, response_data
            )
            
            return False, {}
        except json.JSONDecodeError as e:
            call_end_time = datetime.now()
            error_message = f"JSON decode error: {str(e)}"
            print(f"❌ JSON decode error: {e}")
            
            self._log_api_call(
                call_start_time, call_end_time,
                start_station, start_station_name,
                end_station, end_station_name,
                travel_date or datetime.now().strftime("%Y-%m-%d"),
                start_time, success, routes_found,
                status_code, error_message, response_data
            )
            
            return False, {}
        except Exception as e:
            call_end_time = datetime.now()
            error_message = f"Unexpected error: {str(e)}"
            print(f"❌ Unexpected error: {e}")
            
            self._log_api_call(
                call_start_time, call_end_time,
                start_station, start_station_name,
                end_station, end_station_name,
                travel_date or datetime.now().strftime("%Y-%m-%d"),
                start_time, success, routes_found,
                status_code, error_message, response_data
            )
            
            return False, {}
    
    def _log_api_call(self, start_time: datetime, end_time: datetime,
                      start_station_code: str, start_station_name: str,
                      end_station_code: str, end_station_name: str,
                      travel_date: str, start_time_requested: str,
                      success: bool, routes_found: int,
                      status_code: Optional[int], error_message: str,
                      response_data: Optional[Dict]) -> None:
        """Helper method to log API calls if logging is enabled."""
        if self.enable_logging and self.logger:
            self.logger.log_api_call(
                start_time=start_time,
                end_time=end_time,
                start_station_code=start_station_code,
                start_station_name=start_station_name or start_station_code,
                end_station_code=end_station_code,
                end_station_name=end_station_name or end_station_code,
                travel_date=travel_date,
                start_time_requested=start_time_requested,
                success=success,
                routes_found=routes_found,
                status_code=status_code,
                error_message=error_message,
                response_data=response_data
            )
    
    def parse_route_segments(self, route: Dict) -> List[Dict]:
        """
        Parse detailed route segments (individual train legs) from API response.
        
        Args:
            route: Route dictionary from API response
            
        Returns:
            List of route segments with individual train details and timing
        """
        segments = []
        
        # Look for route details directly in details['routes']
        details = route.get('details', {})
        routes = details.get('routes', [])
        
        if not routes:
            return segments
        
        for i, segment in enumerate(routes):
            try:
                # Get train details
                train_details = segment.get('trainDetails', {})
                train_name = train_details.get('name', 'Unknown')
                train_number = train_details.get('trainNumber', 'Unknown')
                train_full_name = f"{train_number} ({train_name})" if train_name != 'Unknown' else train_number
                
                # Get station details
                start_station = segment.get('startStation', {})
                end_station = segment.get('destionationStation', {})  # Note: API has typo "destionation"
                start_station_name = start_station.get('name', 'Unknown')
                end_station_name = end_station.get('name', 'Unknown')
                
                # Get timing from segment level
                departure = segment.get('departure', {})
                arrival = segment.get('arrival', {})
                
                # Parse scheduled departure time
                dep_time = departure.get('time', '')
                dep_scheduled_str = 'Unknown'
                if dep_time and dep_time != "0001-01-01T00:00:00+01:00":
                    try:
                        dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
                        dep_scheduled_str = dep_dt.strftime('%H:%M')
                    except:
                        pass
                
                # Parse actual departure time
                dep_fact = departure.get('timeFact', '')
                dep_actual_str = 'Unknown'
                dep_delay = 0
                if dep_fact and dep_fact != "0001-01-01T00:00:00+01:00":
                    try:
                        dep_actual_dt = datetime.fromisoformat(dep_fact.replace('Z', '+00:00'))
                        dep_actual_str = dep_actual_dt.strftime('%H:%M')
                        if dep_time and dep_time != "0001-01-01T00:00:00+01:00":
                            dep_delay = int((dep_actual_dt - dep_dt).total_seconds() / 60)
                    except:
                        pass
                
                # Parse scheduled arrival time
                arr_time = arrival.get('time', '')
                arr_scheduled_str = 'Unknown'
                if arr_time and arr_time != "0001-01-01T00:00:00+01:00":
                    try:
                        arr_dt = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
                        arr_scheduled_str = arr_dt.strftime('%H:%M')
                    except:
                        pass
                
                # Parse actual arrival time
                arr_fact = arrival.get('timeFact', '')
                arr_actual_str = 'Unknown'
                arr_delay = 0
                if arr_fact and arr_fact != "0001-01-01T00:00:00+01:00":
                    try:
                        arr_actual_dt = datetime.fromisoformat(arr_fact.replace('Z', '+00:00'))
                        arr_actual_str = arr_actual_dt.strftime('%H:%M')
                        if arr_time and arr_time != "0001-01-01T00:00:00+01:00":
                            arr_delay = int((arr_actual_dt - arr_dt).total_seconds() / 60)
                    except:
                        pass
                
                # Calculate segment travel time
                travel_time_str = 'Unknown'
                if (dep_time and dep_time != "0001-01-01T00:00:00+01:00" and 
                    arr_time and arr_time != "0001-01-01T00:00:00+01:00"):
                    try:
                        dep_dt = datetime.fromisoformat(dep_time.replace('Z', '+00:00'))
                        arr_dt = datetime.fromisoformat(arr_time.replace('Z', '+00:00'))
                        travel_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
                        hours = travel_minutes // 60
                        mins = travel_minutes % 60
                        travel_time_str = f"{hours}:{mins:02d}"
                    except:
                        pass
                
                # Get services/amenities
                services = []
                train_services = segment.get('services', {}).get('train', [])
                for service in train_services:
                    desc = service.get('description', '')
                    if desc:
                        services.append(desc)
                
                segment_info = {
                    'leg_number': i + 1,
                    'train_name': train_name,
                    'train_number': train_number,
                    'train_full_name': train_full_name,
                    'start_station': start_station_name,
                    'end_station': end_station_name,
                    'departure_scheduled': dep_scheduled_str,
                    'departure_actual': dep_actual_str if dep_actual_str != 'Unknown' else dep_scheduled_str,
                    'departure_delay': dep_delay,
                    'arrival_scheduled': arr_scheduled_str,
                    'arrival_actual': arr_actual_str if arr_actual_str != 'Unknown' else arr_scheduled_str,
                    'arrival_delay': arr_delay,
                    'travel_time': travel_time_str,
                    'services': services,
                    'has_delays': dep_delay != 0 or arr_delay != 0
                }
                
                segments.append(segment_info)
                
            except Exception as e:
                print(f"⚠️ Error parsing route segment {i}: {e}")
                continue
        
        return segments
    
    def parse_route_info(self, route: Dict) -> Dict:
        """
        Parse a single route from the API response into a clean format.
        
        Args:
            route: Route dictionary from API response
            
        Returns:
            Clean route information dictionary
        """
        try:
            # Basic train info
            train_name = route.get('details', {}).get('trainFullName', 'Unknown')
            delay_min = route.get('delayMin', 0)
            travel_time = route.get('travelTimeMin', 0)
            
            # Parse departure time (scheduled vs actual)
            departure = route.get('departure', {})
            dep_time_scheduled = departure.get('time', '')
            dep_time_expected = departure.get('timeExpected', '')
            dep_time_fact = departure.get('timeFact', '')
            
            # Parse scheduled times
            if dep_time_scheduled:
                dep_dt = datetime.fromisoformat(dep_time_scheduled.replace('Z', '+00:00'))
                dep_str = dep_dt.strftime('%H:%M')
                dep_iso = dep_dt.isoformat()
            else:
                dep_str = 'Unknown'
                dep_iso = None
                dep_dt = None
                
            # Parse arrival time (scheduled vs actual)
            arrival = route.get('arrival', {})
            arr_time_scheduled = arrival.get('time', '')
            arr_time_expected = arrival.get('timeExpected', '')
            arr_time_fact = arrival.get('timeFact', '')
            
            if arr_time_scheduled:
                arr_dt = datetime.fromisoformat(arr_time_scheduled.replace('Z', '+00:00'))
                arr_str = arr_dt.strftime('%H:%M')
                arr_iso = arr_dt.isoformat()
            else:
                arr_str = 'Unknown'
                arr_iso = None
                arr_dt = None
                
            # Parse ACTUAL departure time from timeFact
            actual_dep_str = None
            dep_delay = 0
            if dep_time_fact and dep_time_fact != "0001-01-01T00:00:00+01:00":
                try:
                    actual_dep_dt = datetime.fromisoformat(dep_time_fact.replace('Z', '+00:00'))
                    actual_dep_str = actual_dep_dt.strftime('%H:%M')
                    if dep_dt:
                        dep_delay = int((actual_dep_dt - dep_dt).total_seconds() / 60)
                except:
                    pass
                    
            # Parse ACTUAL arrival time from timeFact
            actual_arr_str = None
            arr_delay = 0
            if arr_time_fact and arr_time_fact != "0001-01-01T00:00:00+01:00":
                try:
                    actual_arr_dt = datetime.fromisoformat(arr_time_fact.replace('Z', '+00:00'))
                    actual_arr_str = actual_arr_dt.strftime('%H:%M')
                    if arr_dt:
                        arr_delay = int((actual_arr_dt - arr_dt).total_seconds() / 60)
                except:
                    pass
            
            # Extract transfers, prices, and services
            transfers_count = route.get('transfersCount', 0)
            
            # Get price from travel classes (usually 2nd class)
            price_huf = None
            travel_classes = route.get('travelClasses', [])
            if travel_classes:
                # Try to get 2nd class price first, fall back to any available
                second_class = next((tc for tc in travel_classes if tc.get('name') == '2'), None)
                if second_class:
                    price_huf = second_class.get('price', {}).get('amount')
                elif travel_classes:
                    price_huf = travel_classes[0].get('price', {}).get('amount')
            
            # Extract route services (like seat reservation requirements)
            services = []
            route_services = route.get('routeServices', [])
            for service in route_services:
                services.append(service.get('description', ''))
            
            # Extract tracks
            dep_track = route.get('departureTrack', {}).get('changedTrackName', '')
            arr_track = route.get('arrivalTrack', {}).get('changedTrackName', '')
            
            # Get intermediate stations and route segments
            route_segments = self.parse_route_segments(route)
            
            # Extract intermediate stations from segments
            intermediate_stations = []
            for segment in route_segments:
                # Use the station names from the segments as intermediate stations
                station_name = segment.get('end_station', '')
                if station_name and station_name != 'Unknown' and station_name not in intermediate_stations:
                    # Don't include the final destination
                    if segment.get('leg_number', 1) < len(route_segments):
                        intermediate_stations.append(station_name)
            
            # Calculate overall delay (max of departure or arrival delay)
            total_delay = max(dep_delay, arr_delay, delay_min)
            has_actual_delay = (actual_dep_str and actual_dep_str != dep_str) or (actual_arr_str and actual_arr_str != arr_str)
            
            return {
                'train_name': train_name,
                'departure_time': dep_str,
                'departure_time_actual': actual_dep_str,
                'departure_iso': dep_iso,
                'arrival_time': arr_str,
                'arrival_time_actual': actual_arr_str,
                'arrival_iso': arr_iso,
                'travel_time_min': travel_time,
                'delay_min': total_delay,
                'departure_delay_min': dep_delay,
                'arrival_delay_min': arr_delay,
                'is_delayed': total_delay > 0 or has_actual_delay,
                'is_significantly_delayed': total_delay > 5,
                'transfers_count': transfers_count,
                'price_huf': price_huf,
                'services': services,
                'departure_track': dep_track,
                'arrival_track': arr_track,
                'has_actual_times': actual_arr_str is not None or actual_dep_str is not None,
                'intermediate_stations': intermediate_stations,
                'route_segments': route_segments
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing route: {e}")
            return {
                'train_name': 'Parse Error',
                'departure_time': 'Unknown',
                'arrival_time': 'Unknown',
                'travel_time_min': 0,
                'delay_min': 0,
                'is_delayed': False,
                'is_significantly_delayed': False,
                'transfers_count': 0,
                'price_huf': None,
                'services': [],
                'intermediate_stations': [],
                'route_segments': [],
                'departure_delay_min': 0,
                'arrival_delay_min': 0,
                'error': str(e)
            }
    
    def calculate_delay_statistics(self, routes: List[Dict]) -> Dict:
        """
        Calculate delay statistics from a list of routes.
        
        Args:
            routes: List of route dictionaries from API response
            
        Returns:
            Dictionary with delay statistics
        """
        if not routes:
            return {
                'total_trains': 0,
                'average_delay': 0,
                'max_delay': 0,
                'trains_on_time': 0,
                'trains_delayed': 0,
                'trains_significantly_delayed': 0,
                'on_time_percentage': 0,
                'delayed_percentage': 0
            }
        
        delays = [route.get('delayMin', 0) for route in routes]
        trains_on_time = len([d for d in delays if d == 0])
        trains_delayed = len([d for d in delays if d > 0])
        trains_significantly_delayed = len([d for d in delays if d > 5])
        
        return {
            'total_trains': len(delays),
            'average_delay': round(sum(delays) / len(delays), 1),
            'max_delay': max(delays) if delays else 0,
            'trains_on_time': trains_on_time,
            'trains_delayed': trains_delayed,
            'trains_significantly_delayed': trains_significantly_delayed,
            'on_time_percentage': round((trains_on_time / len(delays)) * 100, 1),
            'delayed_percentage': round((trains_delayed / len(delays)) * 100, 1)
        }
    
    def display_results(self, routes: List[Dict], stats: Dict, limit: int = 5):
        """
        Display formatted results to console.
        
        Args:
            routes: List of parsed route dictionaries
            stats: Delay statistics dictionary
            limit: Maximum number of routes to display
        """
        print("\n" + "="*50)
        print("🚆 TRAIN SCHEDULE & DELAY ANALYSIS")
        print("="*50)
        
        print(f"\n📊 DELAY STATISTICS")
        print(f"Total trains: {stats['total_trains']}")
        print(f"Average delay: {stats['average_delay']} minutes")
        print(f"Maximum delay: {stats['max_delay']} minutes")
        print(f"On time: {stats['trains_on_time']}/{stats['total_trains']} ({stats['on_time_percentage']}%)")
        print(f"Delayed: {stats['trains_delayed']}/{stats['total_trains']} ({stats['delayed_percentage']}%)")
        print(f"Significantly delayed (>5min): {stats['trains_significantly_delayed']}/{stats['total_trains']}")
        
        print(f"\n🚂 TRAIN SCHEDULES (showing first {min(limit, len(routes))})")
        print("-" * 50)
        
        for i, route in enumerate(routes[:limit]):
            delay_emoji = "🟢" if route['delay_min'] == 0 else "🟡" if route['delay_min'] <= 5 else "🔴"
            
            print(f"{i+1}. {route['train_name']}")
            
            # Show departure time (actual vs scheduled)
            if route.get('departure_time_actual') and route['departure_time_actual'] != route['departure_time']:
                print(f"   Scheduled departure: {route['departure_time']}")
                print(f"   Actual departure: {route['departure_time_actual']}")
                if route.get('departure_delay_min', 0) > 0:
                    print(f"   Departure delay: {route['departure_delay_min']} min")
            else:
                print(f"   Departure: {route['departure_time']}")
            
            # Show arrival time (actual vs scheduled)
            if route.get('arrival_time_actual') and route['arrival_time_actual'] != route['arrival_time']:
                print(f"   Scheduled arrival: {route['arrival_time']}")
                print(f"   Actual arrival: {route['arrival_time_actual']}")
                if route.get('arrival_delay_min', 0) > 0:
                    print(f"   Arrival delay: {route['arrival_delay_min']} min")
            else:
                print(f"   Arrival: {route['arrival_time']}")
                
            print(f"   Travel time: {route['travel_time_min']}")
            print(f"   Transfers: {route.get('transfers_count', 0)}")
            
            # Show intermediate stations
            if route.get('intermediate_stations'):
                stations_str = ", ".join(route['intermediate_stations'])
                print(f"   Via: {stations_str}")
            
            # Show price
            if route.get('price_huf'):
                print(f"   Price: {route['price_huf']:,} HUF")
            
            # Show track info
            if route.get('departure_track'):
                print(f"   Platform: {route['departure_track']}")
                
            # Show services
            if route.get('services'):
                services_str = ", ".join(route['services'][:2])  # Show first 2 services
                if len(services_str) > 50:
                    services_str = services_str[:50] + "..."
                print(f"   Services: {services_str}")
            
            print(f"   {delay_emoji} Status: {route['delay_min']} min delay")
            
            # Show route segments for transfers
            if route.get('route_segments') and len(route['route_segments']) > 1:
                print(f"   Route details:")
                for j, segment in enumerate(route['route_segments']):
                    if segment['start_station_name']:
                        print(f"     {j+1}. {segment['start_station_name']} → {segment['end_station_name']}")
                        print(f"        {segment['departure_time']} → {segment['arrival_time']} ({segment['travel_time']})")
            
            print()
    
    def save_data(self, raw_data: Dict, parsed_routes: List[Dict], 
                  stats: Dict, output_dir: str = "output"):
        """
        Save scraping results to JSON files.
        
        Args:
            raw_data: Raw API response
            parsed_routes: List of parsed route dictionaries
            stats: Delay statistics
            output_dir: Directory to save files in
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        raw_file = os.path.join(output_dir, f"mav_raw_data_{timestamp}.json")
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        
        # Save processed data
        processed_data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'routes': parsed_routes
        }
        processed_file = os.path.join(output_dir, f"mav_processed_data_{timestamp}.json")
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 Data saved:")
        print(f"   Raw data: {raw_file}")
        print(f"   Processed data: {processed_file}")
    
    def scrape_route(self, start_station: str, end_station: str, 
                    travel_date: Optional[str] = None,
                    start_time: Optional[str] = "01:00",
                    save_results: bool = True,
                    save_json: bool = False,
                    display_limit: int = 5) -> Dict:
        """
        Complete scraping workflow for a route.
        
        Args:
            start_station: Starting station code
            end_station: Ending station code
            travel_date: Optional travel date
            save_results: Whether to save results to files
            display_limit: Number of routes to display
            
        Returns:
            Dictionary with all results
        """
        # Fetch data
        success, raw_data = self.fetch_routes(start_station, end_station, travel_date, start_time, "", "")
        
        if not success:
            return {'success': False, 'error': 'Failed to fetch data'}
        
        # Parse routes
        routes_raw = raw_data.get('route', [])
        parsed_routes = [self.parse_route_info(route) for route in routes_raw]
        
        # Calculate statistics
        stats = self.calculate_delay_statistics(routes_raw)
        
        # Display results
        self.display_results(parsed_routes, stats, display_limit)
        
        # Save data if requested
        if save_results:
            self.save_data(raw_data, parsed_routes, stats)
            
        # Save as clean JSON if requested
        if save_json:
            self.save_json_data(start_station, end_station, parsed_routes, stats)
        
        return {
            'success': True,
            'raw_data': raw_data,
            'parsed_routes': parsed_routes,
            'statistics': stats
        }
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def scrape_to_json(self, start_station: str, end_station: str, 
                      travel_date: Optional[str] = None,
                      start_time: Optional[str] = "01:00",
                      pretty: bool = True) -> str:
        """
        Scrape route and return as JSON string.
        
        Args:
            start_station: Starting station code
            end_station: Ending station code
            travel_date: Optional travel date
            pretty: Whether to format JSON nicely
            
        Returns:
            JSON string with route data
        """
        # Fetch data without console output
        success, raw_data = self.fetch_routes(start_station, end_station, travel_date, start_time, "", "")
        
        if not success:
            return json.dumps({
                "success": False,
                "error": "Failed to fetch data from MÁV API",
                "timestamp": self._get_timestamp()
            }, indent=2 if pretty else None)
        
        # Parse routes
        routes_raw = raw_data.get('route', [])
        parsed_routes = [self.parse_route_info(route) for route in routes_raw]
        
        # Calculate statistics
        stats = self.calculate_delay_statistics(routes_raw)
        
        # Build JSON response
        result = {
            "success": True,
            "timestamp": self._get_timestamp(),
            "route_info": {
                "start_station": start_station,
                "end_station": end_station,
                "travel_date": travel_date
            },
            "statistics": stats,
            "routes": parsed_routes,
            "total_routes": len(parsed_routes)
        }
        
        return json.dumps(result, indent=2 if pretty else None, ensure_ascii=False)
    
    def save_json_data(self, start_station: str, end_station: str, 
                      parsed_routes: List[Dict], stats: Dict, 
                      output_dir: str = "json_output"):
        """
        Save clean JSON data to files.
        
        Args:
            start_station: Starting station code
            end_station: Ending station code
            parsed_routes: List of parsed route dictionaries
            stats: Delay statistics
            output_dir: Directory to save files in
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build clean JSON structure
        json_data = {
            "success": True,
            "timestamp": self._get_timestamp(),
            "route_info": {
                "start_station": start_station,
                "end_station": end_station
            },
            "statistics": stats,
            "routes": parsed_routes,
            "total_routes": len(parsed_routes)
        }
        
        # Save pretty JSON
        pretty_file = os.path.join(output_dir, f"mav_routes_{start_station}_{end_station}_{timestamp}.json")
        with open(pretty_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save compact JSON
        compact_file = os.path.join(output_dir, f"mav_routes_{start_station}_{end_station}_{timestamp}_compact.json")
        with open(compact_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)
        
        print(f"\n📁 JSON files saved:")
        print(f"   📄 Pretty: {pretty_file}")
        print(f"   📦 Compact: {compact_file}")

    def format_travel_time(self, travel_time) -> str:
        """Format travel time from minutes (int) or HH:MM string format."""
        if not travel_time:
            return "Unknown"
        
        # If it's already in HH:MM format, return it
        if isinstance(travel_time, str) and ":" in travel_time:
            return travel_time
        
        # If it's a number (minutes), convert to HH:MM
        try:
            minutes_int = int(travel_time)
            if minutes_int == 0:
                return "Unknown"
            hours = minutes_int // 60
            mins = minutes_int % 60
            return f"{hours:02d}:{mins:02d}"
        except (ValueError, TypeError):
            return "Unknown"

    def create_simplified_output(self, routes: List[Dict]) -> List[Dict]:
        """
        Create simplified JSON output with only essential information.
        
        Args:
            routes: List of parsed route dictionaries
            
        Returns:
            List of simplified route entries
        """
        simplified_routes = []
        
        for i, route in enumerate(routes, 1):
            # Get actual or scheduled departure time
            departure_time = route.get('departure_time_actual') or route.get('departure_time', 'Unknown')
            
            # Get scheduled and actual arrival times
            scheduled_arrival = route.get('arrival_time', 'Unknown')
            actual_arrival = route.get('arrival_time_actual') or scheduled_arrival
            
            # Format travel time
            travel_time = self.format_travel_time(route.get('travel_time_min', 0))
            
            # Get transfers
            transfers = route.get('transfers_count', 0)
            
            # Format price
            price_huf = route.get('price_huf')
            price_str = f"{price_huf:,} HUF".replace(',', ' ') if price_huf else "Price unavailable"
            
            # Determine availability (for now, assume unavailable as per user's examples)
            # This would need to be enhanced based on actual API response structure
            availability = "This offer is not available."
            
            # Get detailed route segments (individual train legs)
            route_segments = route.get('route_segments', [])
            train_legs = []
            
            for segment in route_segments:
                leg_info = {
                    "leg_number": segment.get('leg_number', 1),
                    "train": segment.get('train_full_name', 'Unknown'),
                    "from_station": segment.get('start_station', 'Unknown'),
                    "to_station": segment.get('end_station', 'Unknown'),
                    "scheduled_departure": segment.get('departure_scheduled', 'Unknown'),
                    "actual_departure": segment.get('departure_actual', 'Unknown'),
                    "departure_delay_min": segment.get('departure_delay', 0),
                    "scheduled_arrival": segment.get('arrival_scheduled', 'Unknown'),
                    "actual_arrival": segment.get('arrival_actual', 'Unknown'),
                    "arrival_delay_min": segment.get('arrival_delay', 0),
                    "travel_time": segment.get('travel_time', 'Unknown'),
                    "services": segment.get('services', [])
                }
                train_legs.append(leg_info)
            
            simplified_entry = {
                "option_number": i,
                "departure_time": departure_time,
                "scheduled_arrival_time": scheduled_arrival,
                "actual_arrival_time": actual_arrival,
                "travel_time": travel_time,
                "transfers": transfers,
                "price": price_str,
                "availability": availability,
                "train_legs": train_legs  # Added detailed route segments
            }
            
            simplified_routes.append(simplified_entry)
            
        return simplified_routes

    def scrape_to_simplified_json(self, 
                                start_station: str, 
                                end_station: str, 
                                travel_date: Optional[str] = None,
                                start_time: Optional[str] = "01:00") -> Dict:
        """
        Scrape route data and return simplified JSON format.
        
        Args:
            start_station: Starting station code or name
            end_station: Ending station code or name  
            travel_date: Travel date in ISO format, defaults to today
            start_time: Start time in HH:MM format, defaults to "01:00"
            
        Returns:
            Dictionary with simplified route data and metadata
        """
        # Use existing scrape method to get data (without saving files)
        result = self.scrape_route(start_station, end_station, travel_date, start_time, 
                                 save_results=False, save_json=False, display_limit=0)
        
        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'simplified_routes': []
            }
        
        # Create simplified output
        simplified_routes = self.create_simplified_output(result['parsed_routes'])
        
        # Extract prices for summary
        prices = []
        for route in simplified_routes:
            price_str = route.get('price', '')
            if 'HUF' in price_str:
                try:
                    price_num = int(price_str.replace(' HUF', '').replace(' ', ''))
                    prices.append(price_num)
                except:
                    pass
        
        return {
            'success': True,
            'route_info': {
                'from_station': start_station,
                'to_station': end_station,
                'travel_date': travel_date or datetime.now().strftime('%Y-%m-%d'),
                'start_time': start_time
            },
            'summary': {
                'total_options': len(simplified_routes),
                'cheapest_price': f"{min(prices):,} HUF".replace(',', ' ') if prices else 'N/A',
                'fastest_time': min([r.get('travel_time', '99:99') for r in simplified_routes if r.get('travel_time') != 'Unknown'], default='N/A')
            },
            'simplified_routes': simplified_routes,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """
    Main function with example usage of the MÁV scraper.
    """
    scraper = MAVScraper()
    
    # Default route from your quick_test.py
    start_station = "005504747"  # Your working example
    end_station = "005501024"    # Your working example
    
    print("🚆 MÁV Train Route Scraper")
    print("=" * 40)
    
    # Run the scraper
    results = scraper.scrape_route(
        start_station=start_station,
        end_station=end_station,
        save_results=True,
        save_json=True,
        display_limit=10
    )
    
    if results['success']:
        print("\n✅ Scraping completed successfully!")
    else:
        print(f"\n❌ Scraping failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main() 