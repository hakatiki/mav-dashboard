import csv
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

class MAVCallLogger:
    """
    CSV logger for tracking MÁV API calls with detailed information.
    Logs every API call with start/end times, stations, duration, and results.
    """
    
    def __init__(self, log_file: str = None):
        """
        Initialize the logger with a CSV file.
        
        Args:
            log_file: Path to the CSV log file. If None, uses default in logging directory.
        """
        if log_file is None:
            # Create default log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = f"logging/mav_api_calls_{timestamp}.csv"
        
        self.log_file = log_file
        self.ensure_log_file_exists()
    
    def ensure_log_file_exists(self):
        """Create the CSV file with headers if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'start_time',
                    'end_time',
                    'duration_seconds',
                    'start_station_code',
                    'start_station_name', 
                    'end_station_code',
                    'end_station_name',
                    'travel_date',
                    'start_time_requested',
                    'success',
                    'routes_found',
                    'status_code',
                    'error_message',
                    'response_size_bytes',
                    'api_endpoint'
                ])
    
    def log_api_call(self, 
                     start_time: datetime,
                     end_time: datetime,
                     start_station_code: str,
                     start_station_name: str,
                     end_station_code: str, 
                     end_station_name: str,
                     travel_date: str,
                     start_time_requested: str = "01:00",
                     success: bool = True,
                     routes_found: int = 0,
                     status_code: Optional[int] = None,
                     error_message: str = "",
                     response_data: Optional[Dict[Any, Any]] = None):
        """
        Log a single API call to the CSV file.
        
        Args:
            start_time: When the API call started
            end_time: When the API call completed
            start_station_code: Starting station API code
            start_station_name: Starting station human-readable name
            end_station_code: Destination station API code  
            end_station_name: Destination station human-readable name
            travel_date: Date of travel requested
            start_time_requested: Departure time requested (default "01:00")
            success: Whether the call was successful
            routes_found: Number of routes returned
            status_code: HTTP status code
            error_message: Any error message
            response_data: Raw API response for size calculation
        """
        
        # Calculate duration
        duration = (end_time - start_time).total_seconds()
        
        # Calculate response size
        response_size = 0
        if response_data:
            try:
                response_size = len(json.dumps(response_data).encode('utf-8'))
            except:
                response_size = 0
        
        # API endpoint
        api_endpoint = "https://jegy-a.mav.hu/IK_API_PROD/api/OfferRequestApi/GetOfferRequest"
        
        # Write to CSV
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # log timestamp
                start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # start time with milliseconds
                end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],    # end time with milliseconds  
                f"{duration:.3f}",  # duration in seconds with 3 decimal places
                start_station_code,
                start_station_name,
                end_station_code, 
                end_station_name,
                travel_date,
                start_time_requested,
                success,
                routes_found,
                status_code or "",
                error_message,
                response_size,
                api_endpoint
            ])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Read the log file and return statistics about API calls.
        
        Returns:
            Dictionary with call statistics
        """
        if not os.path.exists(self.log_file):
            return {"error": "Log file does not exist"}
        
        stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_duration": 0.0,
            "total_routes_found": 0,
            "unique_routes": set(),
            "fastest_call": float('inf'),
            "slowest_call": 0.0,
            "most_recent_call": None,
            "error_summary": {}
        }
        
        durations = []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total_calls"] += 1
                
                # Success/failure
                if row["success"].lower() == "true":
                    stats["successful_calls"] += 1
                else:
                    stats["failed_calls"] += 1
                    
                    # Track errors
                    error = row["error_message"]
                    if error:
                        stats["error_summary"][error] = stats["error_summary"].get(error, 0) + 1
                
                # Duration stats
                try:
                    duration = float(row["duration_seconds"])
                    durations.append(duration)
                    stats["fastest_call"] = min(stats["fastest_call"], duration)
                    stats["slowest_call"] = max(stats["slowest_call"], duration)
                except:
                    pass
                
                # Routes
                try:
                    routes = int(row["routes_found"])
                    stats["total_routes_found"] += routes
                except:
                    pass
                
                # Track unique route combinations
                route_key = f"{row['start_station_name']} → {row['end_station_name']}"
                stats["unique_routes"].add(route_key)
                
                # Most recent
                stats["most_recent_call"] = row["timestamp"]
        
        # Calculate averages
        if durations:
            stats["average_duration"] = sum(durations) / len(durations)
        
        if stats["fastest_call"] == float('inf'):
            stats["fastest_call"] = 0.0
            
        # Convert set to list for JSON serialization
        stats["unique_routes"] = list(stats["unique_routes"])
        
        return stats
    
    def print_statistics(self):
        """Print a human-readable summary of API call statistics."""
        stats = self.get_statistics()
        
        if "error" in stats:
            print(f"❌ {stats['error']}")
            return
        
        print("=== MÁV API Call Statistics ===")
        print(f"📊 Total API calls: {stats['total_calls']}")
        print(f"✅ Successful: {stats['successful_calls']}")
        print(f"❌ Failed: {stats['failed_calls']}")
        
        if stats['total_calls'] > 0:
            success_rate = (stats['successful_calls'] / stats['total_calls']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        print(f"\n⏱️ Performance:")
        print(f"   Average duration: {stats['average_duration']:.3f} seconds")
        print(f"   Fastest call: {stats['fastest_call']:.3f} seconds") 
        print(f"   Slowest call: {stats['slowest_call']:.3f} seconds")
        
        print(f"\n🚂 Routes:")
        print(f"   Total routes found: {stats['total_routes_found']}")
        print(f"   Unique route combinations: {len(stats['unique_routes'])}")
        
        if stats['unique_routes']:
            print("   Routes searched:")
            for route in sorted(stats['unique_routes']):
                print(f"     • {route}")
        
        if stats['error_summary']:
            print(f"\n⚠️ Errors encountered:")
            for error, count in stats['error_summary'].items():
                print(f"   • {error}: {count} times")
        
        if stats['most_recent_call']:
            print(f"\n🕐 Most recent call: {stats['most_recent_call']}")

if __name__ == "__main__":
    # Demo usage
    logger = MAVCallLogger()
    print(f"📝 Logger initialized with file: {logger.log_file}")
    logger.print_statistics() 