#!/usr/bin/env python3
"""
Simple MÁV Route Output Generator
Creates simplified JSON output with only essential information:
- Departure time (actual)
- Scheduled/actual arrival times
- Travel time
- Transfers
- Price
- Availability status
"""

import json
import os
from datetime import datetime
from mav_scraper import MAVScraper
from date_utils import get_date_based_output_path, get_timestamped_filename


def save_simplified_json(data: dict, from_station: str, to_station: str) -> str:
    """Save simplified JSON data to date-based output folder with timestamp."""
    # Get date-based output directory
    current_time = datetime.now()
    output_dir, date_folder = get_date_based_output_path('output', current_time)
    
    # Create filename with timestamp
    base_name = f"simplified_{from_station.lower()}_{to_station.lower()}"
    filename = get_timestamped_filename(base_name, "json", current_time)
    filepath = os.path.join(output_dir, filename)
    
    # Save with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Simplified JSON saved to {date_folder}/: {filename}")
    return filepath


def display_simplified_routes(routes: list):
    """Display simplified routes in a clean format."""
    for route in routes:
        print(f"\n{route['option_number']}st option" if route['option_number'] == 1 
              else f"{route['option_number']}nd option" if route['option_number'] == 2
              else f"{route['option_number']}rd option" if route['option_number'] == 3
              else f"{route['option_number']}th option")
        
        print(f"Actual departure time: {route['departure_time']}")
        if route['scheduled_arrival_time'] != route['actual_arrival_time']:
            print(f"Scheduled arrival time: {route['scheduled_arrival_time']}")
        print(f"Actual arrival time: {route['actual_arrival_time']}")
        print(f"Travel time: {route['travel_time']}")
        print(f"Transfers: {route['transfers']}")
        print(f"\n{route['price']}")
        print(route['availability'])


def main():
    """Main function to demonstrate simplified output."""
    scraper = MAVScraper()
    
    # Test with Budapest-Déli to Keszthely (using station codes directly)
    from_station = "005510009"  # Budapest-Déli
    to_station = "005504747"    # Keszthely
    start_time = "01:00"
    
    print(f"🚆 Fetching simplified route data: {from_station} → {to_station}")
    print(f"⏰ Start time: {start_time}")
    print("-" * 50)
    
    # Get simplified JSON data
    result = scraper.scrape_to_simplified_json(
        start_station=from_station,
        end_station=to_station,
        start_time=start_time
    )
    
    if not result['success']:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    # Display summary
    print(f"📍 Route: {result['route_info']['from_station']} → {result['route_info']['to_station']}")
    print(f"📅 Date: {result['route_info']['travel_date']}")
    print(f"📊 Found {result['summary']['total_options']} options")
    print(f"💰 Cheapest: {result['summary']['cheapest_price']}")
    print(f"⚡ Fastest: {result['summary']['fastest_time']}")
    
    # Display routes
    display_simplified_routes(result['simplified_routes'])
    
    # Save to file
    filepath = save_simplified_json(result, from_station, to_station)
    print(f"\n💾 Simplified JSON saved to: {filepath}")
    
    # Also create a minimal version with just the routes array
    minimal_data = {
        "routes": result['simplified_routes'],
        "timestamp": result['timestamp']
    }
    
    minimal_filepath = filepath.replace('simplified_', 'minimal_')
    with open(minimal_filepath, 'w', encoding='utf-8') as f:
        json.dump(minimal_data, f, ensure_ascii=False, indent=2)
    
    print(f"📋 Minimal JSON saved to: {minimal_filepath}")


if __name__ == "__main__":
    main() 