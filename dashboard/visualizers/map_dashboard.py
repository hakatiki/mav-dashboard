"""
Hungary Train Delay Dashboard

Creates an interactive map of Hungary showing train routes colored by average delay.
"""

import folium
from folium import plugins
import json
from typing import List, Dict, Tuple
from route_loader import RouteLoader, Route
from bulk_loader import BulkLoader, BulkData
from data_joiner import DataJoiner
import numpy as np


class HungaryTrainDashboard:
    """Interactive dashboard for Hungary train delays"""
    
    def __init__(self):
        """Initialize the dashboard"""
        self.route_loader = RouteLoader("../map_v2/all_rail_data")
        self.bulk_loader = BulkLoader("../analytics/data/2025-07-23")
        self.joiner = DataJoiner(self.route_loader, self.bulk_loader)
        
        # Hungary center coordinates
        self.hungary_center = [47.1625, 19.5033]
        
        # Load data
        print("Loading route data...")
        self.routes = self.route_loader.load_all_routes()
        print(f"Loaded {len(self.routes)} routes")
        
        print("Loading bulk delay data...")
        self.bulk_data = self.bulk_loader.load_all_bulk_files()
        print(f"Loaded {len(self.bulk_data)} bulk files")
        
        # Create delay mapping
        print("Creating delay mappings...")
        self.station_delays = self.joiner.create_station_delay_map(self.bulk_data)
        print(f"Created delay data for {len(self.station_delays)} station pairs")
    
    def get_delay_color(self, delay_minutes: float) -> str:
        """Get color for delay visualization"""
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
    
    def get_delay_weight(self, delay_minutes: float) -> int:
        """Get line weight based on delay"""
        if delay_minutes <= 0:
            return 2
        elif delay_minutes <= 2:
            return 3
        elif delay_minutes <= 5:
            return 4
        elif delay_minutes <= 10:
            return 5
        else:
            return 6
    
    def create_route_segments_with_delays(self) -> List[Dict]:
        """Create route segments enriched with delay information"""
        segments = []
        processed_pairs = set()
        
        for (start_id, end_id), delay_info in self.station_delays.items():
            # Avoid duplicate processing
            if (start_id, end_id) in processed_pairs:
                continue
            processed_pairs.add((start_id, end_id))
            
            # Find routes that connect these stations
            route_segments = self.joiner.find_route_segments_for_stations(
                self.routes, start_id, end_id
            )
            
            for route, pattern, start_idx, end_idx in route_segments:
                # Create coordinate list for this segment
                coordinates = []
                station_names = []
                
                for i in range(start_idx, end_idx + 1):
                    stop = pattern.stops[i]
                    coordinates.append([stop.lat, stop.lon])
                    station_names.append(stop.name)
                
                if len(coordinates) >= 2:  # Need at least 2 points for a line
                    segment = {
                        'coordinates': coordinates,
                        'route_desc': route.desc or 'Unknown Route',
                        'pattern_name': pattern.headsign or 'Unknown Pattern',
                        'start_station': station_names[0],
                        'end_station': station_names[-1],
                        'average_delay': delay_info.average_delay,
                        'max_delay': delay_info.max_delay,
                        'sample_count': delay_info.sample_count,
                        'color': self.get_delay_color(delay_info.average_delay),
                        'weight': self.get_delay_weight(delay_info.average_delay),
                        'stations': station_names
                    }
                    segments.append(segment)
        
        return segments
    
    def create_map(self) -> folium.Map:
        """Create the main map with train routes"""
        # Create base map
        m = folium.Map(
            location=self.hungary_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # Add title
        title_html = '''
                     <h3 align="center" style="font-size:20px"><b>Hungary Train Delays Dashboard</b></h3>
                     <p align="center" style="font-size:14px">Train routes colored by average delay</p>
                     '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Get route segments with delays
        segments = self.create_route_segments_with_delays()
        print(f"Creating {len(segments)} route segments on map")
        
        # Add route segments to map
        for segment in segments:
            # Create popup text
            popup_text = f"""
            <b>{segment['route_desc']}</b><br>
            Pattern: {segment['pattern_name']}<br>
            From: {segment['start_station']}<br>
            To: {segment['end_station']}<br>
            <br>
            <b>Delay Information:</b><br>
            Average Delay: {segment['average_delay']:.1f} minutes<br>
            Max Delay: {segment['max_delay']} minutes<br>
            Samples: {segment['sample_count']}<br>
            <br>
            <b>Stations:</b><br>
            {' → '.join(segment['stations'])}
            """
            
            # Add polyline to map
            folium.PolyLine(
                locations=segment['coordinates'],
                color=segment['color'],
                weight=segment['weight'],
                opacity=0.8,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px;">
        <p><b>Delay Legend</b></p>
        <p><i class="fa fa-circle" style="color:#00FF00"></i> On Time (0 min)</p>
        <p><i class="fa fa-circle" style="color:#FFFF00"></i> Slight (≤2 min)</p>
        <p><i class="fa fa-circle" style="color:#FFA500"></i> Moderate (3-5 min)</p>
        <p><i class="fa fa-circle" style="color:#FF6600"></i> Significant (6-10 min)</p>
        <p><i class="fa fa-circle" style="color:#FF0000"></i> Major (>10 min)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def create_statistics_summary(self) -> Dict:
        """Create summary statistics"""
        delays = [delay_info.average_delay for delay_info in self.station_delays.values()]
        
        if not delays:
            return {}
        
        return {
            'total_routes': len(self.station_delays),
            'average_delay': np.mean(delays),
            'median_delay': np.median(delays),
            'max_delay': max(delays),
            'routes_on_time': sum(1 for d in delays if d <= 0),
            'routes_delayed': sum(1 for d in delays if d > 0),
            'routes_significantly_delayed': sum(1 for d in delays if d > 5),
            'on_time_percentage': (sum(1 for d in delays if d <= 0) / len(delays)) * 100
        }
    
    def save_dashboard(self, filename: str = "hungary_train_delays.html"):
        """Save the dashboard to HTML file"""
        print("Creating map...")
        map_obj = self.create_map()
        
        print("Creating statistics...")
        stats = self.create_statistics_summary()
        
        # Add statistics to the map
        if stats:
            stats_html = f'''
            <div style="position: fixed; 
                        top: 80px; left: 50px; width: 250px; height: 160px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:12px; padding: 10px;">
            <p><b>Summary Statistics</b></p>
            <p>Total Routes: {stats['total_routes']}</p>
            <p>Average Delay: {stats['average_delay']:.1f} min</p>
            <p>Median Delay: {stats['median_delay']:.1f} min</p>
            <p>Max Delay: {stats['max_delay']:.1f} min</p>
            <p>On Time: {stats['on_time_percentage']:.1f}%</p>
            <p>Significantly Delayed: {stats['routes_significantly_delayed']}</p>
            </div>
            '''
            map_obj.get_root().html.add_child(folium.Element(stats_html))
        
        print(f"Saving map to {filename}...")
        map_obj.save(filename)
        
        print("Dashboard saved successfully!")
        print(f"\nStatistics Summary:")
        if stats:
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        return filename


def main():
    """Main function to create the dashboard"""
    print("=" * 60)
    print("HUNGARY TRAIN DELAYS DASHBOARD")
    print("=" * 60)
    
    try:
        # Create dashboard
        dashboard = HungaryTrainDashboard()
        
        # Save to HTML file
        output_file = dashboard.save_dashboard("hungary_train_delays.html")
        
        print(f"\n✅ Dashboard created successfully!")
        print(f"📁 Open {output_file} in your web browser to view the map")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Dashboard creation failed!")
    else:
        print("\n🎉 Dashboard creation completed!") 