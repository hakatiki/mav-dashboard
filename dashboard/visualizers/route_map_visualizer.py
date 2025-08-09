"""
Beautiful Route Map Visualizer

Creates a stunning, website-ready map visualization of Hungarian train routes.
Uses Morgan Stanley color palette and proper Hungarian borders.
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


class BeautifulRouteMap:
    """Creates stunning, website-ready map visualizations of train routes"""
    
    def __init__(self, data_dir: str):
        """Initialize the visualizer"""
        self.loader = RouteLoader(data_dir)
        
        # Updated Color Palette per user specifications
        self.colors = {
            'main_route': '#187ABA',         # Main lines (less thick than border)
            'regional_route': '#A3CAE3',     # Regional lines
            'border': '#000000',             # Hungarian border (black)
            'station': '#D3086F',            # ALL stations (small points)
            'background': '#F8F9FA'          # Light neutral
        }
        
        # Load Hungarian border from hu.json
        self.hungary_border = self.load_hungary_border()
        
    def interpolate_route(self, coordinates, smoothing_factor=3):
        """Apply simple smoothing to make route lines more organic"""
        if len(coordinates) < 4:  # Need at least 4 points for smoothing
            return coordinates
            
        try:
            # Simple smoothing using moving average
            smooth_coordinates = []
            
            # Keep first point
            smooth_coordinates.append(coordinates[0])
            
            # Apply smoothing to middle points
            for i in range(1, len(coordinates) - 1):
                if i == 1 or i == len(coordinates) - 2:
                    # Less smoothing near endpoints
                    smooth_coordinates.append(coordinates[i])
                else:
                    # Average with neighbors for smoothing
                    prev_lat, prev_lon = coordinates[i-1]
                    curr_lat, curr_lon = coordinates[i]
                    next_lat, next_lon = coordinates[i+1]
                    
                    # Weighted average (current point gets more weight)
                    smooth_lat = (prev_lat + 2*curr_lat + next_lat) / 4
                    smooth_lon = (prev_lon + 2*curr_lon + next_lon) / 4
                    
                    smooth_coordinates.append([smooth_lat, smooth_lon])
            
            # Keep last point
            smooth_coordinates.append(coordinates[-1])
            
            # Add intermediate points for smoother curves
            final_coordinates = []
            for i in range(len(smooth_coordinates) - 1):
                curr = smooth_coordinates[i]
                next_coord = smooth_coordinates[i + 1]
                
                final_coordinates.append(curr)
                
                # Add interpolated point between current and next
                mid_lat = (curr[0] + next_coord[0]) / 2
                mid_lon = (curr[1] + next_coord[1]) / 2
                final_coordinates.append([mid_lat, mid_lon])
            
            final_coordinates.append(smooth_coordinates[-1])
            return final_coordinates
            
        except Exception as e:
            print(f"⚠️  Route smoothing failed: {e}, using original coordinates")
            return coordinates
        
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
        
    def get_hungary_bounds(self, routes):
        """Calculate optimal bounds for Hungary based on route data"""
        lats, lons = [], []
        
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if 45.5 <= stop.lat <= 48.6 and 16.0 <= stop.lon <= 23.0:  # Hungary bounds
                        lats.append(stop.lat)
                        lons.append(stop.lon)
        
        if not lats:
            # Fallback to Hungary center with higher zoom
            return [47.1625, 19.5033], 9
            
        # Calculate center and appropriate zoom
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # Calculate bounds for zoom
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        # Determine zoom level based on data spread - increased for closer view
        if max_range > 4:
            zoom = 8  # Increased from 6
        elif max_range > 2:
            zoom = 9  # Increased from 7
        else:
            zoom = 10  # Increased from 8
            
        return [center_lat, center_lon], zoom

    def create_beautiful_map(self, routes):
        """Create a beautiful, professional map focused on Hungary"""
        center, zoom = self.get_hungary_bounds(routes)
        
        # Create map with only CartoDB Positron
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
        
        # Add Hungarian border outline
        self.add_hungary_border(m)
        
        return m
    
    def add_hungary_border(self, map_obj):
        """Add Hungarian border outline to the map"""
        if self.hungary_border:
            folium.PolyLine(
                locations=self.hungary_border,
                color=self.colors['border'],
                weight=2.5,  # 30% thinner (was 3.5)
                opacity=0.9,
                smoothFactor=1.5,  # Make border more organic too
                popup="🇭🇺 Magyarország",
                tooltip="Magyar határ"
            ).add_to(map_obj)
            print("✅ Added proper Hungarian border from hu.json")
        else:
            # Fallback simplified border
            simple_border = [
                [48.585, 22.906], [48.585, 16.106], [45.748, 16.106], 
                [45.748, 22.906], [48.585, 22.906]
            ]
            folium.PolyLine(
                locations=simple_border,
                color=self.colors['border'],
                weight=2.5,  # 30% thinner (was 3.5)
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
                    # Check if stop is in Hungary bounds
                    if 45.5 <= stop.lat <= 48.6 and 16.0 <= stop.lon <= 23.0:
                        hungary_stops.append(stop)
                        has_hungary_stops = True
                
                if len(hungary_stops) >= 2:  # At least 2 stops in Hungary
                    # Create new pattern with only Hungary stops
                    filtered_pattern = pattern
                    filtered_pattern.stops = hungary_stops
                    filtered_patterns.append(filtered_pattern)
            
            if has_hungary_stops and filtered_patterns:
                route.patterns = filtered_patterns
                hungary_routes.append(route)
        
        return hungary_routes
    
    def add_beautiful_routes(self, map_obj, routes):
        """Add routes with spline interpolation - Regional first, then Main (so Main appears on top)"""
        print("🚂 Processing routes for Hungary...")
        hungary_routes = self.filter_hungary_routes(routes)
        
        # Create route groups
        main_routes = folium.FeatureGroup(name="🚂 Fővonalak", show=True)
        regional_routes = folium.FeatureGroup(name="🚃 Regionális vonalak", show=True)
        
        # Separate routes into categories first
        main_route_data = []
        regional_route_data = []
        
        total_patterns = 0
        route_counts = defaultdict(int)
        total_stations_plotted = 0
        
        for route in hungary_routes:
            for pattern in route.patterns:
                if len(pattern.stops) < 3:  # Minimum 3 stops for cleaner look
                    continue
                
                # Extract coordinates for stations along the route
                coordinates = []
                for stop in pattern.stops:
                    if stop.lat != 0.0 and stop.lon != 0.0:
                        coordinates.append([stop.lat, stop.lon])
                        total_stations_plotted += 1
                
                if len(coordinates) < 3:  # Ensure minimum quality
                    continue
                
                # Apply spline interpolation for smooth curves
                smooth_coordinates = self.interpolate_route(coordinates)
                
                # Categorize routes - only Main vs Regional
                route_length = len(coordinates)
                route_desc_upper = (route.desc or '').upper()
                is_main = route_length > 15 or any(keyword in route_desc_upper for keyword in ['BUDAPEST', 'DEBRECEN', 'SZEGED', 'PÉCS', 'MISKOLC', 'GYŐR'])
                
                route_data = {
                    'coordinates': smooth_coordinates,
                    'original_coords': coordinates,
                    'route': route,
                    'pattern': pattern
                }
                
                if is_main:
                    main_route_data.append(route_data)
                else:
                    regional_route_data.append(route_data)
                
                total_patterns += 1
                route_counts[route.short_name] += 1
        
        # Add REGIONAL routes FIRST (so they appear below main routes)
        print("🚃 Adding regional routes first...")
        for route_data in regional_route_data:
            self._add_route_line(
                route_data, 
                regional_routes, 
                color=self.colors['regional_route'],
                weight=1.3,  # 30% thinner (was 1.8)
                opacity=0.7,
                route_type="Regionális"
            )
        
        # Add MAIN routes SECOND (so they appear on top)
        print("🚂 Adding main routes on top...")
        for route_data in main_route_data:
            self._add_route_line(
                route_data, 
                main_routes, 
                color=self.colors['main_route'],
                weight=1.8,  # 30% thinner (was 2.5)
                opacity=0.8,
                route_type="Fővonal"
            )
        
        # Add groups to map - Regional first, then Main (layer order)
        regional_routes.add_to(map_obj)
        main_routes.add_to(map_obj)
        
        print(f"✅ Added {total_patterns} route patterns with smooth curves")
        print(f"📊 {len(route_counts)} total unique routes")
        print(f"🚉 {total_stations_plotted} station connections plotted")
        print(f"🎨 Applied spline interpolation for organic curves")
        
    def _add_route_line(self, route_data, target_group, color, weight, opacity, route_type):
        """Helper method to add a single route line"""
        coordinates = route_data['coordinates']
        original_coords = route_data['original_coords']
        route = route_data['route']
        pattern = route_data['pattern']
        
        # Create smooth, organic route line
        folium.PolyLine(
            locations=coordinates,
            color=color,
            weight=weight,
            opacity=opacity,
            smoothFactor=3.0,  # Additional smoothing by Folium
            popup=folium.Popup(
                f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 280px; background: white; padding: 20px; border-radius: 6px; border-left: 4px solid {color};">
                    <h3 style="color: {color}; margin: 0 0 12px 0; font-weight: 600;">🚂 {route.short_name}</h3>
                    <p style="margin: 8px 0; font-size: 15px; font-weight: 500; color: #333;">{route.desc or 'Vasútvonal'}</p>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        <p style="margin: 4px 0; color: #666; font-size: 13px;">
                            📍 <strong>{pattern.from_stop_name}</strong> → <strong>{pattern.headsign}</strong>
                        </p>
                        <p style="margin: 4px 0; color: #666; font-size: 13px;">
                            🚉 <strong>{len(original_coords)} állomás</strong> | Típus: <strong>{route_type}</strong>
                        </p>
                        <p style="margin: 4px 0; color: #666; font-size: 13px;">
                            ✨ <strong>Simított görbék</strong> a szebb megjelenésért
                        </p>
                    </div>
                    <p style="margin: 4px 0; font-size: 11px; color: #999;">Vonal ID: {route.id}</p>
                </div>
                """,
                max_width=400
            ),
            tooltip=f"🚂 {route.short_name} ({route_type})"
        ).add_to(target_group)
        
    def get_all_stations(self, routes):
        """Get ALL stations within Hungary for display"""
        all_stations = {}
        
        # Collect all stations
        for route in routes:
            for pattern in route.patterns:
                for stop in pattern.stops:
                    if 45.5 <= stop.lat <= 48.6 and 16.0 <= stop.lon <= 23.0:  # Hungary bounds
                        if stop.pure_id not in all_stations:
                            all_stations[stop.pure_id] = stop
        
        return all_stations
    
    def add_all_stations(self, map_obj, routes):
        """Add ALL stations with uniform styling"""
        print("🚉 Adding all Hungarian stations...")
        all_stations = self.get_all_stations(routes)
        
        # Single station group for all stations
        stations_group = folium.FeatureGroup(name="🚉 Állomások", show=False)
        
        station_count = 0
        for station in all_stations.values():
            if station.lat == 0.0 or station.lon == 0.0:
                continue
                
            # Uniform small station styling
            folium.CircleMarker(
                location=[station.lat, station.lon],
                radius=3,  # Small points as requested
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
        
        # Add group to map
        stations_group.add_to(map_obj)
        
        print(f"🚉 Added {station_count} Hungarian railway stations")
    
    def create_website_ready_map(self, output_file="maps/magyar_vonalhalo_terkep.html"):
        """Create a beautiful, professional Hungarian train map"""
        print("🚂 Creating professional Hungarian train network map...")
        
        # Ensure maps directory exists
        os.makedirs('maps', exist_ok=True)
        
        # Load routes
        print("📡 Loading route data...")
        routes = self.loader.load_all_routes()
        if not routes:
            print("❌ No routes found!")
            return None
        
        # Create beautiful map
        print("🗺️  Creating professional map...")
        map_obj = self.create_beautiful_map(routes)
        
        # Add routes
        print("🛤️  Adding route visualization...")
        self.add_beautiful_routes(map_obj, routes)
        
        # Add ALL stations
        print("🚉 Adding all Hungarian stations...")
        self.add_all_stations(map_obj, routes)
        
        # Add layer control
        folium.LayerControl(position='topright', collapsed=False).add_to(map_obj)
        
        # Add professional plugins
        plugins.Fullscreen(
            position='topleft',
            title='Teljes képernyő',
            title_cancel='Kilépés a teljes képernyőből',
            force_separate_button=True
        ).add_to(map_obj)
        
        # Add measurement tool
        plugins.MeasureControl(
            position='topleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles'
        ).add_to(map_obj)
        
        # Save the professional map
        print(f"💾 Saving Hungarian train map to {output_file}...")
        map_obj.save(output_file)
        print(f"✨ Hungarian train network map created!")
        print(f"🇭🇺 Focused on Hungarian railways")
        print(f"🎨 Clean, professional styling with smooth curves")
        print(f"🌐 Ready for website embedding")
        
        return map_obj


def main():
    """Create the professional Hungarian train map"""
    data_dir = "../../map_v2/all_rail_data"
    
    if not Path(data_dir).exists():
        print(f"❌ Data directory {data_dir} not found!")
        return
    
    # Create professional visualizer
    visualizer = BeautifulRouteMap(data_dir)
    
    # Create the professional map
    visualizer.create_website_ready_map("maps/magyar_vonalhalo_terkep.html")


if __name__ == "__main__":
    main() 