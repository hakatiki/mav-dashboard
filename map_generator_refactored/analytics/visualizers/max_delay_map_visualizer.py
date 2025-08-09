"""
Maximum Delay Route Map Visualizer

Creates a map visualization showing Hungarian train routes colored by their
MAXIMUM delay information (worst-case scenarios). Shows peak delays rather 
than averages to highlight problematic routes.
"""

import folium
from folium import plugins
import sys
import os
from pathlib import Path
import numpy as np
from collections import defaultdict
import json

# Add the parent directories to Python path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'loaders'))

from loaders.route_loader import RouteLoader
from loaders.bulk_loader import BulkLoader
from loaders.data_joiner import DataJoiner


class MaxDelayRouteMap:
    """Creates map visualizations with color-coded MAXIMUM delay information"""
    
    def __init__(self, route_data_dir: str, bulk_data):
        """Initialize the max delay visualizer"""
        self.route_loader = RouteLoader(route_data_dir)
        self.bulk_loader = bulk_data
        self.joiner = DataJoiner(self.route_loader, self.bulk_loader)
        
        # Color palette for maximum delays (adjusted thresholds)
        self.colors = {
            'no_delay': '#00C851',       # Green for low max delays (< 5 min)
            'minor_delay': '#FFD700',    # Yellow for minor max delays (5-15 min)
            'moderate_delay': '#FF8800', # Orange for moderate max delays (15-30 min)
            'severe_delay': '#AA0000',   # Dark red for severe max delays (30+ min)
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
            border_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'hu.json')
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
    
    def get_max_delay_color(self, max_delay_minutes: float) -> str:
        """Get color for max delay visualization"""
        if max_delay_minutes < 5:
            return self.colors['no_delay']
        elif max_delay_minutes < 15:
            return self.colors['minor_delay']
        elif max_delay_minutes < 30:
            return self.colors['moderate_delay']
        else:
            return self.colors['severe_delay']
    
    def get_max_delay_category(self, max_delay_minutes: float) -> str:
        """Get max delay category name for display"""
        if max_delay_minutes < 5:
            return "Alacsony max"
        elif max_delay_minutes < 15:
            return "Közepes max"
        elif max_delay_minutes < 30:
            return "Magas max"
        else:
            return "Kritikus max"
    
    def create_station_max_delay_map(self, bulk_data_list):
        """Create a mapping of station pairs to MAXIMUM delay information"""
        station_max_delays = {}
        
        for bulk_data in bulk_data_list:
            pair = (bulk_data.start_station, bulk_data.end_station)
            
            # Collect all delays for this station pair
            all_delays = []
            
            for route in bulk_data.routes:
                for segment in route.route_segments:
                    if segment.departure_delay > 0:
                        all_delays.append(segment.departure_delay)
                    if segment.arrival_delay > 0:
                        all_delays.append(segment.arrival_delay)
            
            # Calculate maximum delay for this station pair
            max_delay = max(all_delays) if all_delays else 0
            
            station_max_delays[pair] = {
                'max_delay': max_delay,
                'sample_count': len(all_delays),
                'average_delay': np.mean(all_delays) if all_delays else 0
            }
        
        return station_max_delays
    
    def interpolate_route(self, coordinates, smoothing_factor=3):
        """Interpolate route coordinates for smoother visualization"""
        if len(coordinates) < 2:
            return coordinates
        
        interpolated = []
        for i in range(len(coordinates) - 1):
            start = coordinates[i]
            end = coordinates[i + 1]
            
            # Add the start point
            interpolated.append(start)
            
            # Add interpolated points
            for j in range(1, smoothing_factor):
                t = j / smoothing_factor
                lat = start[0] + t * (end[0] - start[0])
                lon = start[1] + t * (end[1] - start[1])
                interpolated.append([lat, lon])
        
        # Add the final point
        interpolated.append(coordinates[-1])
        return interpolated
    
    def get_hungary_bounds(self, routes):
        """Get the bounding box for Hungary based on route data"""
        all_lats = []
        all_lons = []
        
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if stop.lat != 0 and stop.lon != 0:
                        all_lats.append(stop.lat)
                        all_lons.append(stop.lon)
        
        if all_lats and all_lons:
            return [
                [min(all_lats), min(all_lons)],
                [max(all_lats), max(all_lons)]
            ]
        else:
            # Default Hungary bounds
            return [[45.5, 16.0], [48.5, 22.9]]
    
    def create_max_delay_map(self, routes):
        """Create the base map for maximum delay visualization"""
        bounds = self.get_hungary_bounds(routes)
        
        # Create map centered on Hungary
        map_obj = folium.Map(
            location=[47.0, 19.5],  # Center of Hungary
            zoom_start=7,
            tiles='CartoDB positron',
            prefer_canvas=True
        )
        
        # Add Hungary border if available
        if self.hungary_border:
            self.add_hungary_border(map_obj)
        
        return map_obj
    
    def add_hungary_border(self, map_obj):
        """Add Hungarian border to the map"""
        if self.hungary_border:
            folium.Polygon(
                locations=self.hungary_border,
                color=self.colors['border'],
                weight=2,
                fill=False,
                opacity=0.8
            ).add_to(map_obj)
    
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
    
    def create_max_delay_legend(self, map_obj):
        """Create legend for maximum delay categories"""
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Maximum Delay Categories</b></p>
        <p><i class="fa fa-circle" style="color:#00C851"></i> Alacsony max (&lt;5 min)</p>
        <p><i class="fa fa-circle" style="color:#FFD700"></i> Közepes max (5-15 min)</p>
        <p><i class="fa fa-circle" style="color:#FF8800"></i> Magas max (15-30 min)</p>
        <p><i class="fa fa-circle" style="color:#AA0000"></i> Kritikus max (&gt;30 min)</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def add_max_delay_routes(self, map_obj, routes, station_max_delays):
        """Add routes colored by maximum delay information"""
        print("🎨 Adding maximum delay colored routes...")
        
        # Filter to Hungary routes
        hungary_routes = self.filter_hungary_routes(routes)
        print(f"🇭🇺 Found {len(hungary_routes)} routes in Hungary")
        
        route_count = 0
        for route in hungary_routes:
            for pattern in route.patterns:
                if len(pattern.stops) < 2:
                    continue
                
                # Get route coordinates
                coordinates = [[stop.lat, stop.lon] for stop in pattern.stops if stop.lat != 0 and stop.lon != 0]
                
                if len(coordinates) < 2:
                    continue
                
                # Find maximum delay for this route
                max_delay = 0
                delay_samples = 0
                
                # Check each segment of this route for delay data
                for i in range(len(pattern.stops) - 1):
                    start_stop = pattern.stops[i]
                    end_stop = pattern.stops[i + 1]
                    
                    # Look for delay data for this station pair
                    pair = (start_stop.pure_id, end_stop.pure_id)
                    reverse_pair = (end_stop.pure_id, start_stop.pure_id)
                    
                    if pair in station_max_delays:
                        delay_info = station_max_delays[pair]
                        max_delay = max(max_delay, delay_info['max_delay'])
                        delay_samples += delay_info['sample_count']
                    elif reverse_pair in station_max_delays:
                        delay_info = station_max_delays[reverse_pair]
                        max_delay = max(max_delay, delay_info['max_delay'])
                        delay_samples += delay_info['sample_count']
                
                # Determine color based on maximum delay
                if max_delay > 0:
                    color = self.get_max_delay_color(max_delay)
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
                    popup=f"Route: {route.desc}<br>Max Delay: {max_delay:.1f} min<br>Samples: {delay_samples}",
                    tooltip=f"{route.desc} - Max: {max_delay:.1f} min"
                ).add_to(map_obj)
                
                route_count += 1
        
        print(f"✅ Added {route_count} maximum delay colored routes")
    
    def add_stations(self, map_obj, routes):
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
    
    def create_max_delay_aware_map(self, output_file="maps/max_delay_train_map.html"):
        """Create a complete maximum delay aware Hungarian train map"""
        print("🔥 Creating MAXIMUM delay Hungarian train network map...")
        print("=" * 60)
        
        # Ensure maps directory exists
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'maps'), exist_ok=True)
        
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
        
        # Create station maximum delay map
        station_max_delays = self.create_station_max_delay_map(bulk_data_list)
        print(f"✅ Created maximum delay map with {len(station_max_delays)} station pairs")
        
        # Create map
        print("\n🗺️  Creating maximum delay map...")
        map_obj = self.create_max_delay_map(routes)
        
        # Add max delay colored routes
        self.add_max_delay_routes(map_obj, routes, station_max_delays)
        
        # Add stations
        self.add_stations(map_obj, routes)
        
        # Legend removed per user request
        # self.create_max_delay_legend(map_obj)
        
        # Layer control removed per user request
        # folium.LayerControl(position='topright', collapsed=False).add_to(map_obj)
        
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
                print(f"💾 Saved maximum delay map to GCS: gs://{self.bulk_loader.bucket_name}/{blob_name}")
            else:
                # Save locally
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'maps', output_file.split('/')[-1])
                print(f"💾 Saving maximum delay map to {output_path}...")
                map_obj.save(output_path)
        except Exception as e:
            print(f"⚠️ Failed to save to GCS, saving locally: {e}")
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'maps', output_file.split('/')[-1])
            print(f"💾 Saving maximum delay map to {output_path}...")
            map_obj.save(output_path)
        
        print("=" * 60)
        print("🔥 Maximum delay Hungarian train network map created!")
        print("🎨 Routes colored by MAXIMUM delay information (worst-case)")
        print("🎯 Clean map without legend or layer controls")
        print("🇭🇺 Focused on Hungarian railways")
        print("🌐 Ready for website embedding")
        
        return map_obj


def generate_max_delay_map_html(all_json_content, route_data_dir="data/all_rail_data"):
    """
    Generate the maximum delay Hungarian train map as HTML string (for embedding).
    Args:
        all_json_content: JSON content for map generation
        route_data_dir (str): Path to route data directory.
    Returns:
        str: HTML string of the generated map.
    """
    visualizer = MaxDelayRouteMap(route_data_dir, all_json_content)
    map_obj = visualizer.create_max_delay_aware_map("max_delay_train_map.html")
    return map_obj.get_root().render() 