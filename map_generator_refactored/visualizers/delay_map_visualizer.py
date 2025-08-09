"""
Delay-Aware Route Map Visualizer

Creates a stunning, website-ready map visualization of Hungarian train routes
colored by their delay information. Combines route coordinate data with
real delay statistics from bulk data.
"""

import folium
from folium import plugins
import sys
import os
from pathlib import Path
import numpy as np
from collections import defaultdict
import json

# Add the loaders directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loaders'))

from route_loader import RouteLoader
from data_joiner import DataJoiner


class DelayAwareRouteMap:
    """Creates delay-aware map visualizations with color-coded delay information"""
    
    def __init__(self, route_data_dir: str, bulk_data: str):
        """Initialize the delay-aware visualizer"""
        self.route_loader = RouteLoader(route_data_dir)
        self.bulk_loader = bulk_data
        self.joiner = DataJoiner(self.route_loader, self.bulk_loader)
        
        # Color palette for delays (updated categories)
        self.colors = {
            'no_delay': '#00C851',       # Green for on-time (< 2 min)
            'minor_delay': '#FFD700',    # Yellow for minor delays (2-10 min)
            'moderate_delay': '#FF8800', # Orange for moderate delays (10-20 min)
            'severe_delay': '#AA0000',   # Dark red for severe delays (20+ min)
            'no_data': '#999999',        # Gray for routes without delay data
            'border': '#000000',         # Black border
            'station': '#6A1B9A',        # Purple for stations
            'background': '#F8F9FA'      # Light neutral
        }
        
        # Load Hungarian border from hu.json
        self.hungary_border = self.load_hungary_border()
        
    def load_hungary_border(self):
        """Load Hungarian border coordinates from hu.json"""
        try:
            border_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'hu.json')
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
    
    def get_delay_color(self, avg_delay_minutes: float) -> str:
        """Get color for delay visualization based on average delay"""
        if avg_delay_minutes < 2:
            return self.colors['no_delay']
        elif avg_delay_minutes < 10:
            return self.colors['minor_delay']
        elif avg_delay_minutes < 20:
            return self.colors['moderate_delay']
        else:
            return self.colors['severe_delay']
    
    def get_delay_category(self, avg_delay_minutes: float) -> str:
        """Get delay category name for display"""
        if avg_delay_minutes < 2:
            return "Időben"
        elif avg_delay_minutes < 10:
            return "Kis késés"
        elif avg_delay_minutes < 20:
            return "Közepes késés"
        else:
            return "Súlyos késés"
    
    def interpolate_route(self, coordinates, smoothing_factor=3):
        """Apply simple smoothing to make route lines more organic"""
        if len(coordinates) < 4:
            return coordinates
            
        try:
            # Simple smoothing using moving average
            smooth_coordinates = []
            for i in range(len(coordinates)):
                if i == 0 or i == len(coordinates) - 1:
                    # Keep start and end points unchanged
                    smooth_coordinates.append(coordinates[i])
                else:
                    # Smooth intermediate points
                    start_idx = max(0, i - 1)
                    end_idx = min(len(coordinates), i + 2)
                    window = coordinates[start_idx:end_idx]
                    
                    avg_lat = sum(point[0] for point in window) / len(window)
                    avg_lon = sum(point[1] for point in window) / len(window)
                    smooth_coordinates.append([avg_lat, avg_lon])
            
            return smooth_coordinates
        except Exception as e:
            print(f"⚠️  Smoothing failed: {e}, using original coordinates")
            return coordinates
    
    def get_hungary_bounds(self, routes):
        """Calculate optimal bounds for Hungary based on route data"""
        lats, lons = [], []
        
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if 45.5 <= stop.lat <= 48.6 and 16.0 <= stop.lon <= 23.0:
                        lats.append(stop.lat)
                        lons.append(stop.lon)
        
        if not lats:
            return [47.1625, 19.5033], 9
            
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        if max_range > 4:
            zoom = 8
        elif max_range > 2:
            zoom = 9
        else:
            zoom = 10
            
        return [center_lat, center_lon], zoom
    
    def create_delay_map(self, routes, enriched_segments):
        """Create a delay-aware map with routes colored by delay information"""
        center, zoom = self.get_hungary_bounds(routes)
        
        # Create map
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="CartoDB positron",
            width="100%",
            height="100%",
            control_scale=True,
            prefer_canvas=True,
            max_bounds=True,
            zoom_control=False      # ← hides + /   – buttons
        )
        
        # Add Hungarian border
        self.add_hungary_border(m)
        
        return m
    
    def add_hungary_border(self, map_obj):
        """Add Hungarian border outline to the map"""
        if self.hungary_border:
            folium.PolyLine(
                locations=self.hungary_border,
                color=self.colors['border'],
                weight=2.5,
                opacity=0.9,
                smoothFactor=1.5,
                popup="🇭🇺 Magyarország",
                tooltip="Magyar határ"
            ).add_to(map_obj)
            print("✅ Added Hungarian border from hu.json")
        else:
            # Fallback border
            simple_border = [
                [48.585, 22.906], [48.585, 16.106], [45.748, 16.106], 
                [45.748, 22.906], [48.585, 22.906]
            ]
            folium.PolyLine(
                locations=simple_border,
                color=self.colors['border'],
                weight=2.5,
                opacity=0.9,
                smoothFactor=1.5,
                popup="🇭🇺 Magyarország",
                tooltip="Magyar határ (egyszerűsített)"
            ).add_to(map_obj)
            print("⚠️  Using simplified Hungarian border")
    
    def filter_hungary_routes(self, routes):
        """Filter routes to only include those within Hungary"""
        hungary_routes = []
        
        for route in routes:
            for pattern in route.patterns:
                # Check if any stop is in Hungary (rough bounds)
                hungary_stops = 0
                total_stops = len(pattern.stops)
                
                for stop in pattern.stops:
                    if (45.5 <= stop.lat <= 48.5 and 16.0 <= stop.lon <= 22.9):
                        hungary_stops += 1
                
                # If more than 50% of stops are in Hungary, include this route
                if hungary_stops / total_stops > 0.5:
                    hungary_routes.append(route)
                    break  # Only add each route once
        
        return hungary_routes
    
    def create_delay_legend(self, map_obj):
        """Create legend for delay categories"""
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Delay Categories</b></p>
        <p><i class="fa fa-circle" style="color:#00C851"></i> Időben (&lt;2 min)</p>
        <p><i class="fa fa-circle" style="color:#FFD700"></i> Kis késés (2-10 min)</p>
        <p><i class="fa fa-circle" style="color:#FF8800"></i> Közepes késés (10-20 min)</p>
        <p><i class="fa fa-circle" style="color:#AA0000"></i> Súlyos késés (&gt;20 min)</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def add_delay_routes(self, map_obj, routes, enriched_segments):
        """Add routes colored by delay information"""
        print("🎨 Adding delay-colored routes...")
        
        # Filter to Hungary routes
        hungary_routes = self.filter_hungary_routes(routes)
        print(f"🇭🇺 Found {len(hungary_routes)} routes in Hungary")
        
        # Create a mapping of route segments to delay information
        segment_delays = {}
        for segment in enriched_segments:
            key = (segment.start_stop.pure_id, segment.end_stop.pure_id)
            segment_delays[key] = segment
        
        route_count = 0
        for route in hungary_routes:
            for pattern in route.patterns:
                if len(pattern.stops) < 2:
                    continue
                
                # Get route coordinates
                coordinates = [[stop.lat, stop.lon] for stop in pattern.stops if stop.lat != 0 and stop.lon != 0]
                
                if len(coordinates) < 2:
                    continue
                
                # Find average delay for this route
                total_delay = 0
                delay_samples = 0
                
                # Check each segment of this route for delay data
                for i in range(len(pattern.stops) - 1):
                    start_stop = pattern.stops[i]
                    end_stop = pattern.stops[i + 1]
                    
                    # Look for delay data for this station pair
                    pair = (start_stop.pure_id, end_stop.pure_id)
                    reverse_pair = (end_stop.pure_id, start_stop.pure_id)
                    
                    if pair in segment_delays:
                        segment = segment_delays[pair]
                        total_delay += segment.average_delay
                        delay_samples += segment.delay_samples
                    elif reverse_pair in segment_delays:
                        segment = segment_delays[reverse_pair]
                        total_delay += segment.average_delay
                        delay_samples += segment.delay_samples
                
                # Calculate average delay for this route
                avg_delay = total_delay / delay_samples if delay_samples > 0 else 0
                
                # Determine color based on average delay
                if avg_delay > 0:
                    color = self.get_delay_color(avg_delay)
                    weight = 3
                    opacity = 0.8
                else:
                    color = self.colors['no_data']
                    weight = 1
                    opacity = 0.3
                
                # Interpolate coordinates for smoother lines
                interpolated_coords = self.interpolate_route(coordinates)
                
                # Create route line
                folium.PolyLine(
                    locations=interpolated_coords,
                    color=color,
                    weight=weight,
                    opacity=opacity,
                    popup=f"Route: {route.desc}<br>Avg Delay: {avg_delay:.1f} min<br>Samples: {delay_samples}",
                    tooltip=f"{route.desc} - Avg: {avg_delay:.1f} min"
                ).add_to(map_obj)
                
                route_count += 1
        
        print(f"✅ Added {route_count} delay-colored routes")
    
    def add_delay_stations(self, map_obj, routes):
        """Add station markers to the map"""
        print("🚉 Adding stations...")
        
        stations_added = set()
        station_count = 0
        
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if stop.lat == 0 or stop.lon == 0:
                        continue
                    
                    # Avoid duplicate stations
                    station_key = (stop.lat, stop.lon)
                    if station_key in stations_added:
                        continue
                    
                    stations_added.add(station_key)
                    
                    # Create station marker
                    folium.CircleMarker(
                        location=[stop.lat, stop.lon],
                        radius=3,
                        color=self.colors['station'],
                        fill=True,
                        fillColor=self.colors['station'],
                        fillOpacity=0.7,
                        popup=f"Station: {stop.name}<br>ID: {stop.pure_id}",
                        tooltip=stop.name
                    ).add_to(map_obj)
                    
                    station_count += 1
        
        print(f"✅ Added {station_count} stations")
    
    def create_delay_aware_map(self, output_file="maps/delay_aware_train_map.html"):
        """Create a complete delay-aware Hungarian train map"""
        print("🎨 Creating delay-aware Hungarian train network map...")
        print("=" * 60)
        
        # Ensure maps directory exists
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps'), exist_ok=True)
        
        # Load and join data
        print("📡 Loading and joining data...")
        
        # Load route data
        routes = self.route_loader.load_all_routes()
        if not routes:
            print("❌ No routes found!")
            return None
        print(f"✅ Loaded {len(routes)} routes")
        
        # Load bulk delay data - use stored bulk_data_list if available
        if hasattr(self, 'bulk_data_list') and self.bulk_data_list:
            bulk_data_list = self.bulk_data_list
        else:
            if hasattr(self.bulk_loader, 'load_all_bulk_files_from_gcs'):
                # Try GCS first
                try:
                    bulk_data_list = self.bulk_loader.load_all_bulk_files_from_gcs()
                except:
                    bulk_data_list = self.bulk_loader.load_all_bulk_files()
            else:
                bulk_data_list = self.bulk_loader.load_all_bulk_files()
        
        if not bulk_data_list:
            print("❌ No bulk delay data found!")
            return None
        print(f"✅ Loaded {len(bulk_data_list)} bulk delay files")
        
        # Create station delay map
        station_delays = self.joiner.create_station_delay_map(bulk_data_list)
        print(f"✅ Created delay map with {len(station_delays)} station pairs")
        
        # Create enriched segments
        enriched_segments = self.joiner.create_route_segments_with_delay(routes, station_delays)
        print(f"✅ Created {len(enriched_segments)} enriched route segments")
        
        # Create map
        print("\n🗺️  Creating delay-aware map...")
        map_obj = self.create_delay_map(routes, enriched_segments)
        
        # Add delay-colored routes
        self.add_delay_routes(map_obj, routes, enriched_segments)
        
       
        
        # Save map - try GCS first, then local
        try:
            # Try to save to GCS if bulk_loader has GCS capabilities
            if hasattr(self.bulk_loader, 'bucket') and self.bulk_loader.bucket:
                # Save to GCS
                html_content = map_obj.get_root().render()
                
                # Determine the GCS path based on date
                if hasattr(self, 'date') and self.date:
                    # Save to the same date folder as the JSON files
                    blob_name = f"blog/mav/json_output/{self.date}/maps/{output_file.split('/')[-1]}"
                else:
                    # Fallback to the old path
                    blob_name = f"blog/mav/maps/{output_file.split('/')[-1]}"
                
                blob = self.bulk_loader.bucket.blob(blob_name)
                blob.upload_from_string(html_content, content_type='text/html')
                print(f"💾 Saved delay-aware map to GCS: gs://{self.bulk_loader.bucket_name}/{blob_name}")
            else:
                # Save locally
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', output_file.split('/')[-1])
                print(f"💾 Saving delay-aware map to {output_path}...")
                map_obj.save(output_path)
        except Exception as e:
            print(f"⚠️ Failed to save to GCS, saving locally: {e}")
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', output_file.split('/')[-1])
            print(f"💾 Saving delay-aware map to {output_path}...")
            map_obj.save(output_path)
        
        print("=" * 60)
        print("✨ Delay-aware Hungarian train network map created!")
        print("🎨 Routes colored by real delay information")
        print("🎯 Clean map without legend or layer controls")
        print("🇭🇺 Focused on Hungarian railways")
        print("🌐 Ready for website embedding")
        
        return map_obj


def generate_delay_map_html(bulk_loader, route_data_dir="data/all_rail_data", bulk_data_list=None, date=None):
    """
    Generate the delay-aware Hungarian train map as HTML string (for embedding).
    Args:
        bulk_loader: BulkLoader instance
        route_data_dir (str): Path to route data directory.
        bulk_data_list: List of BulkData objects (optional, will load from bulk_loader if not provided)
        date: Date string in YYYY-MM-DD format for GCS folder organization
    Returns:
        str: HTML string of the generated map.
    """
    visualizer = DelayAwareRouteMap(route_data_dir, bulk_loader)
    
    # If bulk_data_list is provided, use it; otherwise load from bulk_loader
    if bulk_data_list is None:
        if hasattr(bulk_loader, 'load_all_bulk_files_from_gcs'):
            # Try GCS first
            try:
                bulk_data_list = bulk_loader.load_all_bulk_files_from_gcs()
            except:
                bulk_data_list = bulk_loader.load_all_bulk_files()
        else:
            bulk_data_list = bulk_loader.load_all_bulk_files()
    
    # Store the bulk data in the visualizer for use in create_delay_aware_map
    visualizer.bulk_data_list = bulk_data_list
    
    # Store the date for GCS saving
    visualizer.date = date
    
    map_obj = visualizer.create_delay_aware_map("delay_aware_train_map.html")
    return map_obj.get_root().render() 