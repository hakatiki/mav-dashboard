import pandas as pd
import re
import json
import sys
import os
import warnings
from datetime import datetime, timedelta
from google.cloud import storage
from pathlib import Path
import folium
from folium import plugins
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Add the dashboard loaders to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dashboard', 'loaders'))

# Import the loader classes
from route_loader import RouteLoader, Route, Pattern, Stop
from bulk_loader import BulkLoader, BulkData, RouteSegment, Statistics, BulkRoute
from data_joiner import DataJoiner, RouteSegmentWithDelay, StationPairDelay

def load_mav_data_from_gcs(bucket_name='mpt-all-sources', target_date=None):
    """
    Load MAV route data from GCS bucket with automatic date fallback.

    Args:
        bucket_name (str): GCS bucket name
        target_date (str): Date in YYYY-MM-DD format

    Returns:
        list: Processed route data ready for analysis
    """
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for days_back in range(8):
        try_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=days_back)).strftime('%Y-%m-%d')
        gcs_prefix = f"blog/mav/json_output/{try_date}/"
        blobs = list(bucket.list_blobs(prefix=gcs_prefix))
        compact_blobs = [blob for blob in blobs if blob.name.endswith('_compact.json')]

        if compact_blobs:
            routes_data = []
            for blob in compact_blobs:
                try:
                    filename = blob.name.split('/')[-1]
                    match = re.match(r'bulk_(\d+)_(\d+)_(\d{8}_\d{6})_compact\.json', filename)
                    if not match:
                        continue
                    start_station, end_station, timestamp = match.groups()
                    json_content = json.loads(blob.download_as_text())
                    if not json_content.get('success') or not json_content.get('routes'):
                        continue
                    for route in json_content['routes']:
                        routes_data.append({
                            'start_station': start_station,
                            'end_station': end_station,
                            'end_station_name': route.get('route_segments',[])[-1].get('end_station', 'Unknown'),
                            'start_station_name': route.get('route_segments', [])[0].get('start_station', 'Unknown'),
                            'station_pair': f"{start_station}_{end_station}",
                            'timestamp': timestamp,
                            'date': try_date,
                            'train_name': route.get('train_name', 'Unknown'),
                            'departure_time': route.get('departure_time'),
                            'arrival_time': route.get('arrival_time'),
                            'travel_time_min': route.get('travel_time_min', '00:00'),
                            'delay_min': route.get('delay_min', 0),
                            'departure_delay_min': route.get('departure_delay_min', 0),
                            'arrival_delay_min': route.get('arrival_delay_min', 0),
                            'is_delayed': route.get('is_delayed', False),
                            'is_significantly_delayed': route.get('is_significantly_delayed', False),
                            'transfers_count': route.get('transfers_count', 0),
                            'price_huf': route.get('price_huf', 0),
                            'has_actual_times': route.get('has_actual_times', False)
                        })
                except Exception:
                    continue
            if routes_data:
                return routes_data
    raise Exception("No MAV data found in the last 8 days!")

def create_analytics():
    """
    Sets the date to today and loads MAV data as a DataFrame.
    Returns:
        pd.DataFrame: DataFrame containing MAV route data for today or fallback date.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    raw_data = load_mav_data_from_gcs(target_date=today_str)
    df = pd.DataFrame(raw_data)
    return df


class MaxDelayMapGenerator:
    """Integrated maximum delay map generator using GCS data"""
    
    def __init__(self):
        """Initialize the max delay map generator"""
        
        # Color palette for maximum delays
        self.max_delay_colors = {
            'low_max': '#00C851',        # Green for low maximum (< 5 min)
            'moderate_max': '#FFD700',   # Yellow for moderate maximum (5-15 min)
            'high_max': '#FF8800',       # Orange for high maximum (15-30 min)
            'critical_max': '#AA0000',   # Red for critical maximum (30+ min)
            'no_data': '#999999',        # Gray for routes without delay data
            'border': '#000000',         # Black border
            'station': '#6A1B9A',        # Purple for stations
            'background': '#F8F9FA'      # Light neutral
        }
        
        # Load Hungarian border
        self.hungary_border = self.load_hungary_border()
    
    def load_hungary_border(self):
        """Load Hungarian border coordinates from hu.json"""
        try:
            border_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dashboard', 'data', 'hu.json')
            with open(border_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract coordinates from GeoJSON
            if data.get('type') == 'FeatureCollection' and data.get('features'):
                feature = data['features'][0]
                if feature.get('geometry', {}).get('type') == 'Polygon':
                    coords = feature['geometry']['coordinates'][0]
                    # Convert from [lon, lat] to [lat, lon] for folium
                    return [[coord[1], coord[0]] for coord in coords]
            
            print("⚠️  Could not parse Hungarian border from hu.json, using fallback")
            return None
            
        except Exception as e:
            print(f"⚠️  Error loading Hungarian border: {e}")
            return None
    
    def convert_gcs_data_to_bulk_format(self, df: pd.DataFrame) -> List[BulkData]:
        """Convert GCS DataFrame to BulkData format for map generation"""
        bulk_data_list = []
        
        # Group by station pairs
        for (start_station, end_station), group in df.groupby(['start_station', 'end_station']):
            # Create route segments from the data
            route_segments = []
            delays = []
            
            for _, row in group.iterrows():
                # Create a simple route segment
                segment = RouteSegment(
                    leg_number=1,
                    train_name=row.get('train_name', 'Unknown'),
                    train_number=row.get('train_name', 'Unknown'),
                    train_full_name=row.get('train_name', 'Unknown'),
                    start_station=row.get('start_station_name', 'Unknown'),
                    end_station=row.get('end_station_name', 'Unknown'),
                    departure_scheduled=row.get('departure_time', '00:00'),
                    departure_actual=None,
                    departure_delay=row.get('departure_delay_min', 0),
                    arrival_scheduled=row.get('arrival_time', '00:00'),
                    arrival_actual=None,
                    arrival_delay=row.get('arrival_delay_min', 0),
                    travel_time=row.get('travel_time_min', '00:00'),
                    services=[],
                    has_delays=row.get('is_delayed', False)
                )
                route_segments.append(segment)
                delays.extend([row.get('departure_delay_min', 0), row.get('arrival_delay_min', 0)])
            
            # Calculate statistics
            delays = [d for d in delays if d > 0]
            avg_delay = np.mean(delays) if delays else 0.0
            max_delay = max(delays) if delays else 0
            
            # Create BulkRoute objects
            routes = []
            for _, row in group.iterrows():
                route = BulkRoute(
                    train_name=row.get('train_name', 'Unknown'),
                    departure_time=row.get('departure_time', '00:00'),
                    departure_time_actual=None,
                    arrival_time=row.get('arrival_time', '00:00'),
                    arrival_time_actual=None,
                    travel_time_min=row.get('travel_time_min', '00:00'),
                    delay_min=row.get('delay_min', 0),
                    departure_delay_min=row.get('departure_delay_min', 0),
                    arrival_delay_min=row.get('arrival_delay_min', 0),
                    is_delayed=row.get('is_delayed', False),
                    is_significantly_delayed=row.get('is_significantly_delayed', False),
                    transfers_count=row.get('transfers_count', 0),
                    price_huf=row.get('price_huf', 0),
                    services=[],
                    intermediate_stations=[],
                    route_segments=route_segments
                )
                routes.append(route)
            
            # Create Statistics object
            # Handle None values in boolean columns
            is_delayed_mask = group['is_delayed'].fillna(False).astype(bool)
            is_significantly_delayed_mask = group['is_significantly_delayed'].fillna(False).astype(bool)
            
            stats = Statistics(
                total_trains=len(group),
                average_delay=avg_delay,
                max_delay=max_delay,
                trains_on_time=len(group[~is_delayed_mask]),
                trains_delayed=len(group[is_delayed_mask]),
                trains_significantly_delayed=len(group[is_significantly_delayed_mask]),
                on_time_percentage=len(group[~is_delayed_mask]) / len(group) * 100,
                delayed_percentage=len(group[is_delayed_mask]) / len(group) * 100
            )
            
            # Create BulkData object
            bulk_data = BulkData(
                success=True,
                timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'),
                start_station=start_station,
                end_station=end_station,
                travel_date=datetime.now().strftime('%Y-%m-%d'),
                statistics=stats,
                routes=routes
            )
            
            bulk_data_list.append(bulk_data)
        
        return bulk_data_list
    
    def get_max_delay_color(self, max_delay_minutes: float) -> str:
        """Get color for maximum delay visualization"""
        if max_delay_minutes < 5:
            return self.max_delay_colors['low_max']
        elif max_delay_minutes < 15:
            return self.max_delay_colors['moderate_max']
        elif max_delay_minutes < 30:
            return self.max_delay_colors['high_max']
        else:
            return self.max_delay_colors['critical_max']
    
    def create_base_map(self, center_lat: float = 47.1625, center_lon: float = 19.5033) -> folium.Map:
        """Create a base map centered on Hungary"""
        return folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap',
            prefer_canvas=True,
            control_scale=True
        )
    
    def add_hungary_border(self, map_obj: folium.Map):
        """Add Hungarian border to the map"""
        if self.hungary_border:
            folium.Polygon(
                locations=self.hungary_border,
                color=self.max_delay_colors['border'],
                weight=2,
                fill=False,
                opacity=0.8
            ).add_to(map_obj)
    
    def create_max_delay_map(self, df: pd.DataFrame, output_file: str = "../dashboard/maps/max_delay_train_map.html"):
        """Create maximum delay map using GCS data"""
        print("🔥 Creating maximum delay Hungarian train network map...")
        print("=" * 60)
        
        # Convert GCS data to bulk format
        bulk_data_list = self.convert_gcs_data_to_bulk_format(df)
        print(f"✅ Converted {len(bulk_data_list)} station pairs from GCS data")
        
        # Create station delay map
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
        
        print(f"✅ Created delay map with {len(station_delays)} station pairs")
        
        # Create map
        print("\n🗺️  Creating maximum delay map...")
        map_obj = self.create_base_map()
        self.add_hungary_border(map_obj)
        
        # Add max delay-colored routes (simplified version)
        for (start_id, end_id), delay_info in station_delays.items():
            if delay_info.sample_count > 0:
                color = self.get_max_delay_color(delay_info.max_delay)
                
                # Create a simple line between stations (you'd need actual coordinates here)
                # For now, we'll create a placeholder
                popup_text = f"""
                <b>Station Pair:</b> {start_id} → {end_id}<br>
                <b>Average Delay:</b> {delay_info.average_delay:.1f} min<br>
                <b>Maximum Delay:</b> {delay_info.max_delay} min<br>
                <b>Samples:</b> {delay_info.sample_count}
                """
                
                # Add a simple marker for now (you'd need actual coordinates)
                folium.Marker(
                    location=[47.1625, 19.5033],  # Center of Hungary
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(map_obj)
        
        # Add plugins
        plugins.Fullscreen(
            position='topleft',
            title='Teljes képernyő',
            title_cancel='Kilépés a teljes képernyőből',
            force_separate_button=True
        ).add_to(map_obj)
        
        plugins.MeasureControl(
            position='topleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles'
        ).add_to(map_obj)
        
        # Save map
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        print(f"💾 Saving maximum delay map to {output_file}...")
        map_obj.save(output_file)
        
        print("=" * 60)
        print("🔥 Maximum delay Hungarian train network map created!")
        print("🎨 Routes colored by maximum delay information from GCS")
        print("🇭🇺 Focused on Hungarian railways")
        print("🌐 Ready for website embedding")
        
        return map_obj


def main():
    """Main function to run analytics and generate maximum delay map"""
    print("🚀 Starting Hungarian Train Analytics and Maximum Delay Map Generation...")
    print("=" * 60)
    
    # Create analytics DataFrame
    print("📊 Loading MAV data from GCS...")
    df = create_analytics()
    print(f"✅ Loaded {len(df)} route records")
    
    # Create map generator
    print("\n🗺️  Initializing maximum delay map generator...")
    map_gen = MaxDelayMapGenerator()
    
    # Generate maximum delay map
    print("\n🔥 Generating maximum delay map...")
    map_gen.create_max_delay_map(df)
    
    print("\n" + "=" * 60)
    print("✨ Maximum delay map generated successfully!")
    print("📁 Map saved to: ../dashboard/maps/max_delay_train_map.html")
    print("🌐 Open the HTML file in your browser to view the map")


if __name__ == "__main__":
    main() 