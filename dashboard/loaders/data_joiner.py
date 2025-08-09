"""
Data Joiner Library

Combines route data with bulk delay data by matching station IDs and 
handling intermediate stations and route segments.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from route_loader import RouteLoader, Route, Pattern, Stop
from bulk_loader import BulkLoader, BulkData, RouteSegment
import numpy as np


@dataclass
class RouteSegmentWithDelay:
    """Route segment enriched with delay information"""
    start_stop: Stop
    end_stop: Stop
    route_id: str
    route_desc: str
    pattern_id: str
    average_delay: float
    max_delay: float
    delay_samples: int
    color: str
    text_color: str


@dataclass
class StationPairDelay:
    """Delay information for a station pair"""
    start_station_id: str
    end_station_id: str
    average_delay: float
    max_delay: float
    sample_count: int
    segments: List[RouteSegment]


class DataJoiner:
    """Joins route data with bulk delay data"""
    
    def __init__(self, route_loader: RouteLoader, bulk_loader: BulkLoader):
        """
        Initialize the data joiner
        
        Args:
            route_loader: RouteLoader instance
            bulk_loader: BulkLoader instance
        """
        self.route_loader = route_loader
        self.bulk_loader = bulk_loader
    
    def create_station_delay_map(self, bulk_data_list: List[BulkData]) -> Dict[Tuple[str, str], StationPairDelay]:
        """
        Create a mapping of station pairs to delay information
        
        Args:
            bulk_data_list: List of BulkData objects
            
        Returns:
            Dictionary mapping (start_id, end_id) to StationPairDelay
        """
        station_delays = {}
        
        for bulk_data in bulk_data_list:
            pair = (bulk_data.start_station, bulk_data.end_station)
            
            # Collect all segments for this station pair
            all_segments = []
            delays = []
            
            for route in bulk_data.routes:
                for segment in route.route_segments:
                    all_segments.append(segment)
                    delays.append(segment.departure_delay)
                    delays.append(segment.arrival_delay)
            
            # Calculate aggregated delay statistics
            delays = [d for d in delays if d > 0]  # Only count actual delays
            avg_delay = np.mean(delays) if delays else 0.0
            max_delay = max(delays) if delays else 0
            
            station_delays[pair] = StationPairDelay(
                start_station_id=bulk_data.start_station,
                end_station_id=bulk_data.end_station,
                average_delay=avg_delay,
                max_delay=max_delay,
                sample_count=len(delays),
                segments=all_segments
            )
        
        return station_delays
    
    def find_route_segments_for_stations(self, routes: List[Route], 
                                       start_id: str, end_id: str) -> List[Tuple[Route, Pattern, int, int]]:
        """
        Find route segments that connect two stations
        
        Args:
            routes: List of Route objects
            start_id: Start station ID
            end_id: End station ID
            
        Returns:
            List of (route, pattern, start_index, end_index) tuples
        """
        matching_segments = []
        
        for route in routes:
            for pattern in route.patterns:
                # Get all station IDs in this pattern
                station_ids = [stop.pure_id for stop in pattern.stops]
                
                # Find indices of start and end stations
                start_indices = [i for i, sid in enumerate(station_ids) if sid == start_id]
                end_indices = [i for i, sid in enumerate(station_ids) if sid == end_id]
                
                # Check if both stations exist and end comes after start
                for start_idx in start_indices:
                    for end_idx in end_indices:
                        if end_idx > start_idx:
                            matching_segments.append((route, pattern, start_idx, end_idx))
        
        return matching_segments
    
    def create_route_segments_with_delay(self, routes: List[Route], 
                                       station_delays: Dict[Tuple[str, str], StationPairDelay]) -> List[RouteSegmentWithDelay]:
        """
        Create route segments enriched with delay information
        
        Args:
            routes: List of Route objects
            station_delays: Dictionary of station pair delays
            
        Returns:
            List of RouteSegmentWithDelay objects
        """
        enriched_segments = []
        
        # Process each station pair with delay data
        for (start_id, end_id), delay_info in station_delays.items():
            # Find route segments that connect these stations
            route_segments = self.find_route_segments_for_stations(routes, start_id, end_id)
            
            for route, pattern, start_idx, end_idx in route_segments:
                # Create segments for each consecutive pair of stops in the route
                for i in range(start_idx, end_idx):
                    start_stop = pattern.stops[i]
                    end_stop = pattern.stops[i + 1]
                    
                    enriched_segment = RouteSegmentWithDelay(
                        start_stop=start_stop,
                        end_stop=end_stop,
                        route_id=route.id,
                        route_desc=route.desc,
                        pattern_id=pattern.id,
                        average_delay=delay_info.average_delay,
                        max_delay=delay_info.max_delay,
                        delay_samples=delay_info.sample_count,
                        color=route.color,
                        text_color=route.text_color
                    )
                    enriched_segments.append(enriched_segment)
        
        return enriched_segments
    
    def expand_intermediate_stations(self, bulk_data: BulkData, 
                                   routes: List[Route]) -> List[Tuple[str, str, float]]:
        """
        Expand a bulk route to include all intermediate station pairs with delays
        
        Args:
            bulk_data: BulkData with start/end stations
            routes: List of Route objects to find intermediate stations
            
        Returns:
            List of (start_id, end_id, delay) tuples for all segments
        """
        expanded_pairs = []
        
        # Find matching routes
        route_segments = self.find_route_segments_for_stations(
            routes, bulk_data.start_station, bulk_data.end_station
        )
        
        if not route_segments:
            # No matching route found, just use the original pair
            return [(bulk_data.start_station, bulk_data.end_station, bulk_data.statistics.average_delay)]
        
        # Use the first matching route to get intermediate stations
        route, pattern, start_idx, end_idx = route_segments[0]
        
        # Create pairs for each consecutive segment
        for i in range(start_idx, end_idx):
            start_station_id = pattern.stops[i].pure_id
            end_station_id = pattern.stops[i + 1].pure_id
            
            # For now, use the overall delay for each segment
            # In a more sophisticated version, we could distribute delays based on segment length
            expanded_pairs.append((start_station_id, end_station_id, bulk_data.statistics.average_delay))
        
        return expanded_pairs
    
    def aggregate_delays_by_segment(self, enriched_segments: List[RouteSegmentWithDelay]) -> Dict[Tuple[str, str], float]:
        """
        Aggregate delay information by route segment
        
        Args:
            enriched_segments: List of RouteSegmentWithDelay objects
            
        Returns:
            Dictionary mapping (start_station_id, end_station_id) to average delay
        """
        segment_delays = {}
        segment_counts = {}
        
        for segment in enriched_segments:
            pair = (segment.start_stop.pure_id, segment.end_stop.pure_id)
            
            if pair not in segment_delays:
                segment_delays[pair] = 0.0
                segment_counts[pair] = 0
            
            segment_delays[pair] += segment.average_delay
            segment_counts[pair] += 1
        
        # Calculate averages
        for pair in segment_delays:
            if segment_counts[pair] > 0:
                segment_delays[pair] /= segment_counts[pair]
        
        return segment_delays
    
    def get_delay_color(self, delay_minutes: float) -> str:
        """
        Get color for delay visualization
        
        Args:
            delay_minutes: Average delay in minutes
            
        Returns:
            Hex color string
        """
        if delay_minutes <= 0:
            return "#00FF00"  # Green for on time
        elif delay_minutes <= 2:
            return "#FFFF00"  # Yellow for slight delay
        elif delay_minutes <= 5:
            return "#FFA500"  # Orange for moderate delay
        elif delay_minutes <= 10:
            return "#FF6600"  # Red-orange for significant delay
        else:
            return "#FF0000"  # Red for major delay


def test_data_joining():
    """Test the data joining functionality"""
    print("Testing data joining...")
    
    # Initialize loaders
    route_loader = RouteLoader("../map_v2/all_rail_data")
    bulk_loader = BulkLoader("../analytics/data/2025-07-23")
    joiner = DataJoiner(route_loader, bulk_loader)
    
    # Load a single route for testing
    print("Loading test route...")
    route = route_loader.load_single_route("route_1_1660__20250725_223055.json")
    if not route:
        print("Failed to load test route")
        return
    
    # Load a few bulk files for testing
    print("Loading test bulk data...")
    bulk_data_list = bulk_loader.load_all_bulk_files()[:10]  # Just first 10 for testing
    print(f"Loaded {len(bulk_data_list)} bulk files")
    
    # Create station delay map
    print("Creating station delay map...")
    station_delays = joiner.create_station_delay_map(bulk_data_list)
    print(f"Found {len(station_delays)} station pairs with delay data")
    
    # Show some examples
    for i, (pair, delay_info) in enumerate(list(station_delays.items())[:3]):
        print(f"  {pair[0]} -> {pair[1]}: {delay_info.average_delay:.1f} min avg delay ({delay_info.sample_count} samples)")
    
    # Test finding route segments
    print("\nTesting route segment matching...")
    if station_delays:
        test_pair = list(station_delays.keys())[0]
        start_id, end_id = test_pair
        segments = joiner.find_route_segments_for_stations([route], start_id, end_id)
        print(f"Found {len(segments)} route segments for {start_id} -> {end_id}")
    
    # Test intermediate station expansion
    print("\nTesting intermediate station expansion...")
    if bulk_data_list:
        test_bulk = bulk_data_list[0]
        expanded = joiner.expand_intermediate_stations(test_bulk, [route])
        print(f"Expanded {test_bulk.start_station} -> {test_bulk.end_station} into {len(expanded)} segments:")
        for segment in expanded:
            print(f"  {segment[0]} -> {segment[1]}: {segment[2]:.1f} min")


if __name__ == "__main__":
    test_data_joining() 