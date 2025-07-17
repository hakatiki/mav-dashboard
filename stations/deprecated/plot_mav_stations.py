#!/usr/bin/env python3
"""
Plot MAV Stations on Hungary Map
Loads stations from comprehensive_mav_stations.json and plots them on an interactive Folium map.
"""

import json
from pathlib import Path
import folium
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def plot_mav_stations(json_file: str = "comprehensive_mav_stations.json", output_html: str = "mav_stations_map.html"):
    """
    Plot MAV stations on an interactive map of Hungary
    """
    try:
        # Load stations data
        json_path = Path(json_file)
        if not json_path.exists():
            logger.error(f"File not found: {json_path}")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            stations = json.load(f)
        
        logger.info(f"Loaded {len(stations)} stations from {json_path}")
        
        # Filter stations with valid coordinates
        valid_stations = []
        for station in stations:
            coords = station.get('coordinates')
            if coords and coords.get('latitude') and coords.get('longitude'):
                valid_stations.append({
                    'name': station.get('name', 'Unknown'),
                    'lat': float(coords['latitude']),
                    'lon': float(coords['longitude']),
                    'city': station.get('city', ''),
                    'source': station.get('source', ''),
                    'is_international': station.get('isInternational', False),
                    'operator': station.get('operator', ''),
                    'major_hub': station.get('major_hub', False)
                })
        
        if not valid_stations:
            logger.error("No stations with valid coordinates found")
            return False
        
        logger.info(f"Found {len(valid_stations)} stations with valid coordinates")
        
        # Create interactive map centered on Hungary
        # Hungary center: approx lat 47.1625, lon 19.5033
        m = folium.Map(
            location=[47.1625, 19.5033],
            zoom_start=7,  # Zoom level to show all of Hungary
            tiles='CartoDB positron'  # Clean map style
        )
        
        # Add layer control
        folium.TileLayer('openstreetmap').add_to(m)
        folium.TileLayer('cartodbdark_matter', name="Dark Mode").add_to(m)
        folium.LayerControl().add_to(m)
        
        # Add markers for each station
        international_count = 0
        major_hub_count = 0
        
        for station in valid_stations:
            # Determine marker color and size based on station type
            if station['major_hub']:
                color = 'green'
                icon = 'star'
                major_hub_count += 1
            elif station['is_international']:
                color = 'red'
                icon = 'train'
                international_count += 1
            else:
                color = 'blue'
                icon = 'circle'
            
            marker_icon = folium.Icon(color=color, icon=icon, prefix='fa')
            
            popup_text = f"""
            <div style="width: 250px;">
                <h4>{station['name']}</h4>
                <p><strong>City:</strong> {station['city']}</p>
                <p><strong>Operator:</strong> {station['operator']}</p>
                <p><strong>International:</strong> {'Yes' if station['is_international'] else 'No'}</p>
                <p><strong>Major Hub:</strong> {'Yes' if station['major_hub'] else 'No'}</p>
                <p><strong>Source:</strong> {station['source']}</p>
                <p><strong>Coordinates:</strong> {station['lat']:.4f}, {station['lon']:.4f}</p>
            </div>
            """
            
            folium.Marker(
                location=[station['lat'], station['lon']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=station['name'],
                icon=marker_icon
            ).add_to(m)
        
        # Add legend
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px;">
        <h4>Station Types</h4>
        <p><i class="fa fa-star" style="color:green"></i> Major Hubs ({major_hub_count})</p>
        <p><i class="fa fa-train" style="color:red"></i> International ({international_count})</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Domestic ({len(valid_stations) - international_count - major_hub_count})</p>
        <p><strong>Total: {len(valid_stations)} stations</strong></p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map
        output_path = Path(output_html)
        m.save(str(output_path))
        
        logger.info(f"Map saved to {output_path}")
        logger.info(f"Open {output_path} in a web browser to view the interactive map")
        
        # Print statistics
        print(f"\n📊 MAV Stations Map Statistics:")
        print(f"🚂 Total stations plotted: {len(valid_stations)}")
        print(f"⭐ Major hubs: {major_hub_count}")
        print(f"🌍 International stations: {international_count}")
        print(f"🏠 Domestic stations: {len(valid_stations) - international_count - major_hub_count}")
        print(f"🗺️ Map saved to: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error plotting stations: {e}")
        return False

if __name__ == "__main__":
    success = plot_mav_stations()
    if success:
        print("✅ Map generated successfully!")
        print("🌐 Open the HTML file in your web browser to explore the interactive map!")
    else:
        print("❌ Failed to generate map. Check the logs above.") 