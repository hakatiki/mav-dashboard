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

# Add the loaders directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loaders'))

from route_loader import RouteLoader
from bulk_loader import BulkLoader
from data_joiner import DataJoiner


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
                    all_delays.append(segment.departure_delay)
                    all_delays.append(segment.arrival_delay)
            
            # Calculate max and average delay statistics
            delays = [d for d in all_delays if d > 0]  # Only count actual delays
            max_delay = max(delays) if delays else 0
            avg_delay = np.mean(delays) if delays else 0.0
            
            station_max_delays[pair] = {
                'start_station_id': bulk_data.start_station,
                'end_station_id': bulk_data.end_station,
                'max_delay': max_delay,
                'average_delay': avg_delay,
                'sample_count': len(delays)
            }
        
        return station_max_delays
    
    def interpolate_route(self, coordinates, smoothing_factor=3):
        """Apply simple smoothing to make route lines more organic"""
        if len(coordinates) < 4:
            return coordinates
            
        try:
            # Simple smoothing using moving average
            smooth_coordinates = []
            smooth_coordinates.append(coordinates[0])
            
            for i in range(1, len(coordinates) - 1):
                if i == 1 or i == len(coordinates) - 2:
                    smooth_coordinates.append(coordinates[i])
                else:
                    prev_lat, prev_lon = coordinates[i-1]
                    curr_lat, curr_lon = coordinates[i]
                    next_lat, next_lon = coordinates[i+1]
                    
                    smooth_lat = (prev_lat + 2*curr_lat + next_lat) / 4
                    smooth_lon = (prev_lon + 2*curr_lon + next_lon) / 4
                    smooth_coordinates.append([smooth_lat, smooth_lon])
            
            smooth_coordinates.append(coordinates[-1])
            
            # Add intermediate points for smoother curves
            final_coordinates = []
            for i in range(len(smooth_coordinates) - 1):
                curr = smooth_coordinates[i]
                next_coord = smooth_coordinates[i + 1]
                final_coordinates.append(curr)
                
                mid_lat = (curr[0] + next_coord[0]) / 2
                mid_lon = (curr[1] + next_coord[1]) / 2
                final_coordinates.append([mid_lat, mid_lon])
            
            final_coordinates.append(smooth_coordinates[-1])
            return final_coordinates
            
        except Exception as e:
            print(f"⚠️  Route smoothing failed: {e}, using original coordinates")
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
    
    def create_max_delay_map(self, routes):
        """Create a max delay map with routes colored by maximum delay information"""
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
            max_bounds=True
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
        """Filter routes to show only those within Hungary"""
        hungary_routes = []
        
        for route in routes:
            has_hungary_stops = False
            filtered_patterns = []
            
            for pattern in route.patterns:
                hungary_stops = []
                for stop in pattern.stops:
                    if 45.5 <= stop.lat <= 48.6 and 16.0 <= stop.lon <= 23.0:
                        hungary_stops.append(stop)
                        has_hungary_stops = True
                
                if len(hungary_stops) >= 2:
                    filtered_pattern = pattern
                    filtered_pattern.stops = hungary_stops
                    filtered_patterns.append(filtered_pattern)
            
            if has_hungary_stops and filtered_patterns:
                route.patterns = filtered_patterns
                hungary_routes.append(route)
        
        return hungary_routes
    
    def add_max_delay_routes(self, map_obj, routes, station_max_delays):
        """Add routes colored by maximum delay information"""
        print("🔥 Creating maximum delay route visualization...")
        
        # Create segment lookup for maximum delay information
        segment_max_delays = {}
        segment_avg_delays = {}
        
        for pair, delay_info in station_max_delays.items():
            # Find route segments that connect these stations
            route_segments = self.joiner.find_route_segments_for_stations(routes, pair[0], pair[1])
            
            for route, pattern, start_idx, end_idx in route_segments:
                for i in range(start_idx, end_idx):
                    start_stop = pattern.stops[i]
                    end_stop = pattern.stops[i + 1]
                    segment_key = (start_stop.pure_id, end_stop.pure_id)
                    
                    if segment_key not in segment_max_delays:
                        segment_max_delays[segment_key] = []
                        segment_avg_delays[segment_key] = []
                    
                    segment_max_delays[segment_key].append(delay_info['max_delay'])
                    segment_avg_delays[segment_key].append(delay_info['average_delay'])
        
        # Calculate maximum of maximum delays for segments
        for key in segment_max_delays:
            segment_max_delays[key] = max(segment_max_delays[key])
            segment_avg_delays[key] = np.mean(segment_avg_delays[key])
        
        # Group routes by max delay level for layering
        delay_groups = {
            'no_delay': folium.FeatureGroup(name="🟢 Alacsony max (<5p)", show=True),
            'minor_delay': folium.FeatureGroup(name="🟡 Közepes max (5-15p)", show=True),
            'moderate_delay': folium.FeatureGroup(name="🟠 Magas max (15-30p)", show=True),
            'severe_delay': folium.FeatureGroup(name="🔴 Kritikus max (30p+)", show=True),
            'no_data': folium.FeatureGroup(name="⚫ Nincs késési adat", show=True)
        }
        
        hungary_routes = self.filter_hungary_routes(routes)
        total_patterns = 0
        delay_stats = defaultdict(int)
        
        for route in hungary_routes:
            for pattern in route.patterns:
                if len(pattern.stops) < 3:
                    continue
                
                # Extract coordinates
                coordinates = []
                for stop in pattern.stops:
                    if stop.lat != 0.0 and stop.lon != 0.0:
                        coordinates.append([stop.lat, stop.lon])
                
                if len(coordinates) < 3:
                    continue
                
                # Apply smoothing
                smooth_coordinates = self.interpolate_route(coordinates)
                
                # Calculate maximum delay for this route pattern
                pattern_max_delays = []
                pattern_avg_delays = []
                
                for i in range(len(pattern.stops) - 1):
                    start_id = pattern.stops[i].pure_id
                    end_id = pattern.stops[i + 1].pure_id
                    segment_key = (start_id, end_id)
                    
                    if segment_key in segment_max_delays:
                        pattern_max_delays.append(segment_max_delays[segment_key])
                        pattern_avg_delays.append(segment_avg_delays[segment_key])
                
                # Determine delay category and color based on MAXIMUM delay
                if pattern_max_delays:
                    max_delay = max(pattern_max_delays)  # Take the worst segment
                    avg_delay = np.mean(pattern_avg_delays)  # Average for reference
                    delay_color = self.get_max_delay_color(max_delay)
                    delay_category = self.get_max_delay_category(max_delay)
                    
                    # Determine which group to add to
                    if max_delay < 5:
                        target_group = delay_groups['no_delay']
                        delay_stats['no_delay'] += 1
                    elif max_delay < 15:
                        target_group = delay_groups['minor_delay']
                        delay_stats['minor_delay'] += 1
                    elif max_delay < 30:
                        target_group = delay_groups['moderate_delay']
                        delay_stats['moderate_delay'] += 1
                    else:
                        target_group = delay_groups['severe_delay']
                        delay_stats['severe_delay'] += 1
                else:
                    max_delay = 0
                    avg_delay = 0
                    delay_color = self.colors['no_data']
                    delay_category = "Nincs adat"
                    target_group = delay_groups['no_data']
                    delay_stats['no_data'] += 1
                
                # Create route line
                folium.PolyLine(
                    locations=smooth_coordinates,
                    color=delay_color,
                    weight=1.8,
                    opacity=0.8,
                    smoothFactor=3.0,
                    popup=folium.Popup(
                        f"""
                        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 320px; background: white; padding: 20px; border-radius: 6px; border-left: 4px solid {delay_color};">
                            <h3 style="color: {delay_color}; margin: 0 0 12px 0; font-weight: 600;">🚂 {route.short_name}</h3>
                            <p style="margin: 8px 0; font-size: 15px; font-weight: 500; color: #333;">{route.desc or 'Vasútvonal'}</p>
                            <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                <p style="margin: 4px 0; color: #666; font-size: 13px;">
                                    📍 <strong>{pattern.from_stop_name}</strong> → <strong>{pattern.headsign}</strong>
                                </p>
                                <p style="margin: 4px 0; color: #666; font-size: 13px;">
                                    🚉 <strong>{len(coordinates)} állomás</strong>
                                </p>
                                <p style="margin: 4px 0; color: {delay_color}; font-size: 14px; font-weight: 600;">
                                    🔥 <strong>MAX késés: {max_delay:.1f} perc</strong>
                                </p>
                                <p style="margin: 4px 0; color: #666; font-size: 13px;">
                                    📊 Átlag: <strong>{avg_delay:.1f} perc</strong>
                                </p>
                                <p style="margin: 4px 0; color: #666; font-size: 13px;">
                                    📊 <strong>{len(pattern_max_delays)} szegmens</strong> késési adattal
                                </p>
                                <p style="margin: 4px 0; color: {delay_color}; font-size: 13px; font-weight: 500;">
                                    ⚠️ <strong>{delay_category}</strong>
                                </p>
                            </div>
                            <p style="margin: 4px 0; font-size: 11px; color: #999;">Vonal ID: {route.id}</p>
                        </div>
                        """,
                        max_width=420
                    ),
                    tooltip=f"🚂 {route.short_name} - MAX: {max_delay:.1f}p ({delay_category})"
                ).add_to(target_group)
                
                total_patterns += 1
        
        # Add groups to map in order (worst delays on top)
        delay_groups['no_data'].add_to(map_obj)
        delay_groups['no_delay'].add_to(map_obj)
        delay_groups['minor_delay'].add_to(map_obj)
        delay_groups['moderate_delay'].add_to(map_obj)
        delay_groups['severe_delay'].add_to(map_obj)
        
        print(f"✅ Added {total_patterns} maximum delay route patterns")
        print(f"📊 Maximum delay distribution:")
        for category, count in delay_stats.items():
            percentage = count / total_patterns * 100 if total_patterns > 0 else 0
            print(f"   {category}: {count} ({percentage:.1f}%)")
    
    def add_stations(self, map_obj, routes):
        """Add stations with uniform styling"""
        print("🚉 Adding Hungarian stations...")
        all_stations = self.route_loader.get_all_stations(routes)
        
        # Filter to Hungary
        hungary_stations = {
            station_id: station for station_id, station in all_stations.items()
            if 45.5 <= station.lat <= 48.6 and 16.0 <= station.lon <= 23.0
        }
        
        stations_group = folium.FeatureGroup(name="🚉 Állomások", show=False)
        
        station_count = 0
        for station in hungary_stations.values():
            if station.lat == 0.0 or station.lon == 0.0:
                continue
                
            folium.CircleMarker(
                location=[station.lat, station.lon],
                radius=3,
                popup=folium.Popup(
                    f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 200px; background: white; padding: 15px; border-radius: 6px; border-left: 4px solid {self.colors['station']};">
                        <h3 style="color: {self.colors['station']}; margin: 0 0 10px 0; font-weight: 600; text-align: center;">
                            🚉 {station.name}
                        </h3>
                        <p style="margin: 5px 0; font-size: 11px; color: #999; text-align: center;">
                            Állomás ID: {station.pure_id}
                        </p>
                    </div>
                    """,
                    max_width=250
                ),
                tooltip=f"🚉 {station.name}",
                color='white',
                fillColor=self.colors['station'],
                fillOpacity=0.8,
                weight=1
            ).add_to(stations_group)
            station_count += 1
        
        stations_group.add_to(map_obj)
        print(f"🚉 Added {station_count} Hungarian railway stations")
    
    def create_max_delay_aware_map(self, output_file="maps/max_delay_train_map.html"):
        """Create a complete maximum delay aware Hungarian train map"""
        print("🔥 Creating MAXIMUM delay Hungarian train network map...")
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
                blob_name = f"blog/mav/maps/{output_file.split('/')[-1]}"
                blob = self.bulk_loader.bucket.blob(blob_name)
                blob.upload_from_string(html_content, content_type='text/html')
                print(f"💾 Saved maximum delay map to GCS: gs://{self.bulk_loader.bucket_name}/{blob_name}")
            else:
                # Save locally
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', output_file.split('/')[-1])
                print(f"💾 Saving maximum delay map to {output_path}...")
                map_obj.save(output_path)
        except Exception as e:
            print(f"⚠️ Failed to save to GCS, saving locally: {e}")
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', output_file.split('/')[-1])
            print(f"💾 Saving maximum delay map to {output_path}...")
            map_obj.save(output_path)
        
        print("=" * 60)
        print("🔥 Maximum delay Hungarian train network map created!")
        print("🎨 Routes colored by MAXIMUM delay information (worst-case)")
        print("🎯 Clean map without legend or layer controls")
        print("🇭🇺 Focused on Hungarian railways")
        print("🌐 Ready for website embedding")
        
        return map_obj


def generate_max_delay_map_html(bulk_loader, route_data_dir="../../map_v2/all_rail_data", bulk_data_list=None):
    """
    Generate the maximum delay Hungarian train map as HTML string (for embedding).
    Args:
        bulk_loader: BulkLoader instance
        route_data_dir (str): Path to route data directory.
        bulk_data_list: List of BulkData objects (optional, will load from bulk_loader if not provided)
    Returns:
        str: HTML string of the generated map.
    """
    visualizer = MaxDelayRouteMap(route_data_dir, bulk_loader)
    
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
    
    # Store the bulk data in the visualizer for use in create_max_delay_aware_map
    visualizer.bulk_data_list = bulk_data_list
    
    map_obj = visualizer.create_max_delay_aware_map("max_delay_train_map.html")
    return map_obj.get_root().render()


