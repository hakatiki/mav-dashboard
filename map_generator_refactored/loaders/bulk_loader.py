"""
Bulk Loader Library

Loads and parses bulk delay data from JSON files containing train schedules
and delay information. Supports both local files and Google Cloud Storage.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Optional GCS imports
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("Warning: Google Cloud Storage not available. Install google-cloud-storage for GCS support.")


@dataclass
class RouteSegment:
    """Represents a single leg of a journey"""
    leg_number: int
    train_name: Optional[str]
    train_number: str
    train_full_name: str
    start_station: str
    end_station: str
    departure_scheduled: str
    departure_actual: Optional[str]
    departure_delay: int
    arrival_scheduled: str
    arrival_actual: Optional[str]
    arrival_delay: int
    travel_time: str
    services: List[str]
    has_delays: bool


@dataclass
class BulkRoute:
    """Represents a complete journey with all segments"""
    train_name: str
    departure_time: str
    departure_time_actual: Optional[str]
    arrival_time: str
    arrival_time_actual: Optional[str]
    travel_time_min: str
    delay_min: int
    departure_delay_min: int
    arrival_delay_min: int
    is_delayed: Optional[bool]
    is_significantly_delayed: bool
    transfers_count: int
    price_huf: int
    services: List[str]
    intermediate_stations: List[str]
    route_segments: List[RouteSegment]


@dataclass
class Statistics:
    """Delay statistics for a route"""
    total_trains: int
    average_delay: float
    max_delay: int
    trains_on_time: int
    trains_delayed: int
    trains_significantly_delayed: int
    on_time_percentage: float
    delayed_percentage: float


@dataclass
class BulkData:
    """Complete bulk data entry"""
    success: bool
    timestamp: str
    start_station: str
    end_station: str
    travel_date: Optional[str]
    statistics: Statistics
    routes: List[BulkRoute]


class BulkLoader:
    """Loader for bulk delay data from JSON files (local and GCS)"""
    
    def __init__(self, data_dir: str = None, bucket_name: str = None, gcs_prefix: str = "blog/mav/json_output/"):
        """
        Initialize the bulk loader
        
        Args:
            data_dir: Directory containing bulk JSON files (for local loading)
            bucket_name: GCS bucket name (for cloud loading)
            gcs_prefix: GCS prefix for bulk files
        """
        self.data_dir = Path(data_dir) if data_dir else None
        self.bucket_name = bucket_name
        self.gcs_prefix = gcs_prefix
        self.client = None
        self.bucket = None
        
        # Initialize GCS if bucket_name is provided
        if bucket_name and GCS_AVAILABLE:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(bucket_name)
                print(f"✅ GCS initialized with bucket: {bucket_name}")
            except Exception as e:
                print(f"⚠️ Failed to initialize GCS: {e}")
                self.bucket = None
        
        # Validate local directory if provided
        if data_dir and not self.data_dir.exists():
            raise ValueError(f"Data directory {data_dir} does not exist")
    
    def parse_route_segment(self, segment_data: dict) -> RouteSegment:
        """Parse a single route segment"""
        return RouteSegment(
            leg_number=segment_data.get("leg_number", 0),
            train_name=segment_data.get("train_name"),
            train_number=segment_data.get("train_number", ""),
            train_full_name=segment_data.get("train_full_name", ""),
            start_station=segment_data.get("start_station", ""),
            end_station=segment_data.get("end_station", ""),
            departure_scheduled=segment_data.get("departure_scheduled", ""),
            departure_actual=segment_data.get("departure_actual"),
            departure_delay=segment_data.get("departure_delay", 0),
            arrival_scheduled=segment_data.get("arrival_scheduled", ""),
            arrival_actual=segment_data.get("arrival_actual"),
            arrival_delay=segment_data.get("arrival_delay", 0),
            travel_time=segment_data.get("travel_time", ""),
            services=segment_data.get("services", []),
            has_delays=segment_data.get("has_delays", False)
        )
    
    def parse_bulk_route(self, route_data: dict) -> BulkRoute:
        """Parse a bulk route with all segments"""
        segments = []
        for segment_data in route_data.get("route_segments", []):
            segments.append(self.parse_route_segment(segment_data))
        
        return BulkRoute(
            train_name=route_data.get("train_name", ""),
            departure_time=route_data.get("departure_time", ""),
            departure_time_actual=route_data.get("departure_time_actual"),
            arrival_time=route_data.get("arrival_time", ""),
            arrival_time_actual=route_data.get("arrival_time_actual"),
            travel_time_min=route_data.get("travel_time_min", ""),
            delay_min=route_data.get("delay_min", 0),
            departure_delay_min=route_data.get("departure_delay_min", 0),
            arrival_delay_min=route_data.get("arrival_delay_min", 0),
            is_delayed=route_data.get("is_delayed"),
            is_significantly_delayed=route_data.get("is_significantly_delayed", False),
            transfers_count=route_data.get("transfers_count", 0),
            price_huf=route_data.get("price_huf", 0),
            services=route_data.get("services", []),
            intermediate_stations=route_data.get("intermediate_stations", []),
            route_segments=segments
        )
    
    def parse_statistics(self, stats_data: dict) -> Statistics:
        """Parse delay statistics"""
        return Statistics(
            total_trains=stats_data.get("total_trains", 0),
            average_delay=stats_data.get("average_delay", 0.0),
            max_delay=stats_data.get("max_delay", 0),
            trains_on_time=stats_data.get("trains_on_time", 0),
            trains_delayed=stats_data.get("trains_delayed", 0),
            trains_significantly_delayed=stats_data.get("trains_significantly_delayed", 0),
            on_time_percentage=stats_data.get("on_time_percentage", 0.0),
            delayed_percentage=stats_data.get("delayed_percentage", 0.0)
        )
    
    def parse_bulk_file(self, file_path: Path) -> Optional[BulkData]:
        """
        Parse a single bulk JSON file
        
        Args:
            file_path: Path to the bulk JSON file
            
        Returns:
            BulkData object or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            route_info = data.get("route_info", {})
            statistics = self.parse_statistics(data.get("statistics", {}))
            
            routes = []
            for route_data in data.get("routes", []):
                routes.append(self.parse_bulk_route(route_data))
            
            return BulkData(
                success=data.get("success", False),
                timestamp=data.get("timestamp", ""),
                start_station=route_info.get("start_station", ""),
                end_station=route_info.get("end_station", ""),
                travel_date=route_info.get("travel_date"),
                statistics=statistics,
                routes=routes
            )
            
        except Exception as e:
            print(f"Error parsing bulk file {file_path}: {e}")
            return None
    
    def parse_bulk_json_content(self, json_content: dict, start_station: str = None, end_station: str = None, timestamp: str = None, travel_date: str = None) -> Optional[BulkData]:
        """
        Parse bulk data from JSON content (for GCS or other sources)
        
        Args:
            json_content: JSON content as dict
            start_station: Start station ID (optional, will be extracted from route_info if not provided)
            end_station: End station ID (optional, will be extracted from route_info if not provided)
            timestamp: Timestamp string (optional, will be extracted from JSON if not provided)
            travel_date: Travel date string (optional, will be extracted from route_info if not provided)
            
        Returns:
            BulkData object or None if parsing fails
        """
        try:
            route_info = json_content.get("route_info", {})
            statistics = self.parse_statistics(json_content.get("statistics", {}))
            
            routes = []
            for route_data in json_content.get("routes", []):
                routes.append(self.parse_bulk_route(route_data))
            
            return BulkData(
                success=json_content.get("success", True),
                timestamp=timestamp or json_content.get("timestamp", ""),
                start_station=start_station or route_info.get("start_station", ""),
                end_station=end_station or route_info.get("end_station", ""),
                travel_date=travel_date or route_info.get("travel_date"),
                statistics=statistics,
                routes=routes
            )
            
        except Exception as e:
            print(f"Error parsing bulk JSON content: {e}")
            return None
    
    def load_single_bulk(self, filename: str) -> Optional[BulkData]:
        """
        Load a single bulk file by filename (local only)
        
        Args:
            filename: Name of the bulk file
            
        Returns:
            BulkData object or None if not found/parsing fails
        """
        if not self.data_dir:
            raise ValueError("Local data directory not configured")
        
        file_path = self.data_dir / filename
        if not file_path.exists():
            print(f"Bulk file {filename} not found")
            return None
        
        return self.parse_bulk_file(file_path)
    
    def load_all_bulk_files(self, exclude_compact: bool = True) -> List[BulkData]:
        """
        Load all bulk files from the local data directory
        
        Args:
            exclude_compact: If True, exclude files with "_compact" in the name
            
        Returns:
            List of BulkData objects
        """
        if not self.data_dir:
            raise ValueError("Local data directory not configured")
        
        bulk_data = []
        json_files = list(self.data_dir.glob("*.json"))
        
        if exclude_compact:
            json_files = [f for f in json_files if "_compact" not in f.name]
        
        print(f"Found {len(json_files)} bulk files to process")
        
        for file_path in json_files:
            data = self.parse_bulk_file(file_path)
            if data:
                bulk_data.append(data)
            else:
                print(f"Failed to parse {file_path.name}")
        
        print(f"Successfully loaded {len(bulk_data)} bulk files")
        return bulk_data
    
    def load_all_bulk_files_from_gcs(self, target_date: str = None, exclude_compact: bool = True, max_days_back: int = 8) -> List[BulkData]:
        """
        Load all bulk files from GCS bucket
        
        Args:
            target_date: Date in YYYY-MM-DD format (defaults to today)
            exclude_compact: If True, exclude files with "_compact" in the name
            max_days_back: Maximum number of days to look back if target_date not found
            
        Returns:
            List of BulkData objects
        """
        if not self.bucket:
            raise ValueError("GCS bucket not configured")
        
        target_date = target_date or datetime.now().strftime('%Y-%m-%d')
        print(f"🔍 Loading MAV data from: gs://{self.bucket_name}/{self.gcs_prefix}")
        print(f"📅 Target date: {target_date}")
        
        # Try target date first, then fallback to previous days
        for days_back in range(max_days_back):
            try_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=days_back)).strftime('%Y-%m-%d')
            gcs_prefix = f"{self.gcs_prefix}{try_date}/"
            
            print(f"🔄 Trying date: {try_date}")
            
            # List JSON files
            blobs = list(self.bucket.list_blobs(prefix=gcs_prefix))
            json_blobs = [blob for blob in blobs if blob.name.endswith('.json')]
            
            if exclude_compact:
                json_blobs = [blob for blob in json_blobs if '_compact' not in blob.name]
            
            if json_blobs:
                print(f"✅ Found {len(json_blobs)} files for {try_date}")
                
                # Group blobs by (start_station, end_station), keep only latest timestamp
                latest_blobs = {}
                
                for blob in json_blobs:
                    filename = blob.name.split('/')[-1]
                    match = re.match(r'bulk_(\d+)_(\d+)_(\d{8}_\d{6})\.json', filename)
                    
                    if not match:
                        print(f"⚠️ Filename pattern not matched: {filename}")
                        continue
                    
                    start_station, end_station, timestamp = match.groups()
                    key = (start_station, end_station)
                    
                    # Compare timestamps lexicographically (YYYYMMDD_HHMMSS format)
                    if key not in latest_blobs or timestamp > latest_blobs[key][0]:
                        latest_blobs[key] = (timestamp, blob)
                
                print(f"🎯 Found {len(latest_blobs)} unique station pairs vs {len(json_blobs)} total files")
                
                # Process latest blobs
                bulk_data = []
                for i, ((start_station, end_station), (timestamp, blob)) in enumerate(latest_blobs.items()):
                    try:
                        if i % 25 == 0:
                            print(f"📊 Processing file {i+1}/{len(latest_blobs)}...")
                        
                        json_content = json.loads(blob.download_as_text())
                        parsed_data = self.parse_bulk_json_content(
                            json_content, 
                            start_station=start_station, 
                            end_station=end_station, 
                            timestamp=timestamp, 
                            travel_date=try_date
                        )
                        
                        if parsed_data:
                            bulk_data.append(parsed_data)
                        else:
                            print(f"⚠️ Failed to parse {blob.name}")
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Skipping {blob.name}: Invalid JSON format - {e}")
                        continue
                    except Exception as e:
                        print(f"⚠️ Skipping {blob.name}: Error processing file - {e}")
                        continue
                
                if bulk_data:
                    print(f"🎯 Successfully loaded {len(bulk_data)} bulk files from GCS!")
                    return bulk_data
            
            print(f"❌ No data found for {try_date}")
        
        raise Exception(f"❌ No bulk data found in the last {max_days_back} days!")
    
    def get_available_dates_from_gcs(self) -> List[str]:
        """
        Get all available dates from GCS bucket
        
        Returns:
            List of available dates in YYYY-MM-DD format
        """
        if not self.bucket:
            raise ValueError("GCS bucket not configured")
        
        print(f"🔍 Fetching available dates from: gs://{self.bucket_name}/{self.gcs_prefix}")
        
        # List all blobs in the prefix
        blobs = list(self.bucket.list_blobs(prefix=self.gcs_prefix))
        
        # Extract unique dates from blob names
        dates = set()
        for blob in blobs:
            # Extract date from path like "blog/mav/json_output/2025-07-17/bulk_..."
            path_parts = blob.name.split('/')
            if len(path_parts) >= 4:  # Should have at least 4 parts: blog/mav/json_output/YYYY-MM-DD/...
                date_part = path_parts[3]  # The date part
                # Validate date format (YYYY-MM-DD)
                if re.match(r'^\d{4}-\d{2}-\d{2}$', date_part):
                    dates.add(date_part)
        
        # Convert to sorted list
        available_dates = sorted(list(dates))
        print(f"✅ Found {len(available_dates)} available dates: {available_dates}")
        
        return available_dates

    def get_all_station_pairs(self, bulk_data_list: List[BulkData]) -> List[tuple]:
        """
        Get all unique station pairs from bulk data
        
        Args:
            bulk_data_list: List of BulkData objects
            
        Returns:
            List of (start_station, end_station) tuples
        """
        pairs = set()
        for bulk_data in bulk_data_list:
            pairs.add((bulk_data.start_station, bulk_data.end_station))
        return list(pairs)
    
    def get_delay_summary_by_station_pair(self, bulk_data_list: List[BulkData]) -> Dict[tuple, float]:
        """
        Get average delay for each station pair
        
        Args:
            bulk_data_list: List of BulkData objects
            
        Returns:
            Dictionary mapping (start_station, end_station) to average delay
        """
        delay_summary = {}
        
        for bulk_data in bulk_data_list:
            pair = (bulk_data.start_station, bulk_data.end_station)
            delay_summary[pair] = bulk_data.statistics.average_delay
        
        return delay_summary
    
    def get_all_segments_with_delays(self, bulk_data_list: List[BulkData]) -> List[RouteSegment]:
        """
        Extract all route segments with their delay information
        
        Args:
            bulk_data_list: List of BulkData objects
            
        Returns:
            List of all RouteSegment objects
        """
        all_segments = []
        
        for bulk_data in bulk_data_list:
            for route in bulk_data.routes:
                for segment in route.route_segments:
                    all_segments.append(segment)
        
        return all_segments


if __name__ == "__main__":
    # Test the loader
    loader = BulkLoader("../analytics/data/2025-07-23")
    
    # Test loading a single bulk file
    print("Testing single bulk file loading...")
    bulk_data = loader.load_single_bulk("bulk_004252667_005512880_20250723_204806.json")
    if bulk_data:
        print(f"Loaded bulk data: {bulk_data.start_station} -> {bulk_data.end_station}")
        print(f"Average delay: {bulk_data.statistics.average_delay} minutes")
        print(f"Total routes: {len(bulk_data.routes)}")
        print(f"Total segments: {sum(len(route.route_segments) for route in bulk_data.routes)}")
        
        # Show first route details
        if bulk_data.routes:
            route = bulk_data.routes[0]
            print(f"\nFirst route: {route.train_name}")
            print(f"Transfers: {route.transfers_count}")
            print(f"Segments:")
            for segment in route.route_segments:
                print(f"  {segment.train_number}: {segment.start_station} -> {segment.end_station} (delay: {segment.departure_delay}min)")
    
    print("\nTesting small batch loading...")
    all_bulk = loader.load_all_bulk_files()
    if all_bulk:
        pairs = loader.get_all_station_pairs(all_bulk[:5])  # Just first 5
        print(f"Found {len(pairs)} unique station pairs in first 5 files")
        
        delay_summary = loader.get_delay_summary_by_station_pair(all_bulk[:5])
        print(f"Delay summary for first few pairs:")
        for pair, delay in list(delay_summary.items())[:3]:
            print(f"  {pair[0]} -> {pair[1]}: {delay} min avg delay") 