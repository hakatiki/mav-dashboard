#!/usr/bin/env python3
"""
MÁV Train Scraper - Command Line Interface
One command to scrape train data with custom settings
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from json_saver import JSONSaver
from mav_scraper import MAVScraper
from config import STATION_CODES, STATION_NAMES
from date_utils import get_date_based_output_path, get_timestamped_filename

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🚆 MÁV Train Route Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with station codes
  python mav_cli.py 005510009 005504747
  
  # Using station names
  python mav_cli.py budapest_deli keszthely
  
  # Custom start time (2:30 AM)
  python mav_cli.py budapest_deli keszthely --time 02:30
  
  # Custom date and time
  python mav_cli.py 005510009 005504747 --date 2025-07-16 --time 06:00
  
  # Save with custom filename
  python mav_cli.py budapest_deli keszthely --filename my_route
  
  # Just display, don't save
  python mav_cli.py budapest_deli keszthely --no-save
  
  # Compact JSON output
  python mav_cli.py budapest_deli keszthely --format compact
        """
    )
    
    parser.add_argument('start', nargs='?', help='Start station (code or name from config)')
    parser.add_argument('end', nargs='?', help='End station (code or name from config)')
    
    parser.add_argument('--time', '-t', default='01:00',
                       help='Start time in HH:MM format (default: 01:00)')
    
    parser.add_argument('--date', '-d', 
                       help='Travel date in YYYY-MM-DD format (default: today)')
    
    parser.add_argument('--filename', '-f',
                       help='Custom filename for JSON output (without extension)')
    
    parser.add_argument('--format', choices=['pretty', 'compact', 'both'], default='both',
                       help='JSON output format (default: both)')
    
    parser.add_argument('--simplified', action='store_true',
                       help='Use simplified JSON output with only essential information')
    
    parser.add_argument('--no-save', action='store_true',
                       help='Display only, do not save JSON files')
    
    parser.add_argument('--output-dir', default='json_output',
                       help='Output directory for JSON files (default: json_output)')
    
    parser.add_argument('--list-stations', action='store_true',
                       help='List available station names and codes')
    
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode - minimal output')
    
    return parser.parse_args()

def resolve_station_code(station_input: str) -> str:
    """
    Resolve station input to station code.
    
    Args:
        station_input: Either a station code or name from config
        
    Returns:
        Station code
    """
    # If it's already a code (starts with numbers)
    if station_input.isdigit() or (station_input.startswith('005') and len(station_input) == 9):
        return station_input
    
    # Try to find in station codes
    if station_input.lower() in STATION_CODES:
        return STATION_CODES[station_input.lower()]
    
    # Try exact match
    if station_input in STATION_CODES:
        return STATION_CODES[station_input]
    
    # Not found
    raise ValueError(f"Unknown station: {station_input}")

def list_stations():
    """List all available stations."""
    print("🚉 Available Stations:")
    print("=" * 50)
    for name, code in STATION_CODES.items():
        print(f"  {name:<20} → {code}")
    print()
    print("Usage: python mav_cli.py <start> <end>")
    print("Example: python mav_cli.py budapest_deli keszthely")

def format_route_summary(data: dict) -> str:
    """Format a quick summary of the route data."""
    if not data.get('success'):
        return "❌ Failed to fetch route data"
    
    routes = data.get('routes', [])
    stats = data.get('statistics', {})
    
    summary = []
    summary.append(f"🚂 Found {len(routes)} routes")
    
    if routes:
        prices = [r['price_huf'] for r in routes if r.get('price_huf')]
        if prices:
            summary.append(f"💰 Prices: {min(prices):,} - {max(prices):,} HUF")
        
        fastest = min(routes, key=lambda x: x['travel_time_min'])
        summary.append(f"⚡ Fastest: {fastest['travel_time_min']} ({fastest['train_name']})")
        
        summary.append(f"📊 On time: {stats.get('on_time_percentage', 0)}%")
    
    return " | ".join(summary)

def main():
    """Main CLI function."""
    args = parse_arguments()
    
    # Handle special commands
    if args.list_stations:
        list_stations()
        return
    
    # Check if required arguments are provided
    if not args.start or not args.end:
        print("❌ Error: start and end stations are required")
        print("Use --list-stations to see available stations")
        sys.exit(1)
    
    try:
        # Resolve station codes
        start_code = resolve_station_code(args.start)
        end_code = resolve_station_code(args.end)
        
        if not args.quiet:
            start_name = STATION_NAMES.get(start_code, start_code)
            end_name = STATION_NAMES.get(end_code, end_code)
            print(f"🚆 Scraping: {start_name} → {end_name}")
            print(f"⏰ Start time: {args.time}")
            if args.date:
                print(f"📅 Date: {args.date}")
        
        # Prepare travel date
        travel_date = None
        if args.date:
            try:
                date_obj = datetime.strptime(args.date, '%Y-%m-%d').date()
                hour, minute = map(int, args.time.split(':'))
                travel_datetime = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
                travel_date = travel_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00")
            except ValueError as e:
                print(f"❌ Invalid date format: {e}")
                sys.exit(1)
        
        if args.no_save:
            # Just fetch and display
            scraper = MAVScraper()
            start_name = STATION_NAMES.get(start_code, start_code)
            end_name = STATION_NAMES.get(end_code, end_code)
            success, raw_data = scraper.fetch_routes(start_code, end_code, travel_date, args.time, start_name, end_name)
            
            if success:
                routes_raw = raw_data.get('route', [])
                parsed_routes = [scraper.parse_route_info(route) for route in routes_raw]
                stats = scraper.calculate_delay_statistics(routes_raw)
                
                data = {
                    'success': True,
                    'routes': parsed_routes,
                    'statistics': stats
                }
                
                if not args.quiet:
                    scraper.display_results(parsed_routes, stats, limit=10)
                else:
                    print(format_route_summary(data))
            else:
                print("❌ Failed to fetch data")
                sys.exit(1)
        else:
            # Check if simplified output is requested
            if args.simplified:
                # Use simplified JSON output
                scraper = MAVScraper()
                simplified_data = scraper.scrape_to_simplified_json(start_code, end_code, travel_date, args.time)
                
                if simplified_data['success']:
                    # Generate filename
                    filename = args.filename
                    if not filename:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"simplified_{start_code}_{end_code}_{timestamp}"
                    
                    # Save simplified JSON to date-based output directory
                    current_time = datetime.now()
                    output_dir, date_folder = get_date_based_output_path(args.output_dir, current_time)
                    
                    # Save full simplified format
                    full_file = os.path.join(output_dir, f"{filename}.json")
                    with open(full_file, 'w', encoding='utf-8') as f:
                        json.dump(simplified_data, f, ensure_ascii=False, indent=2)
                    
                    # Save minimal format (just routes array)
                    minimal_data = {
                        "routes": simplified_data['simplified_routes'],
                        "timestamp": simplified_data['timestamp']
                    }
                    minimal_file = os.path.join(output_dir, f"minimal_{filename.replace('simplified_', '')}.json")
                    with open(minimal_file, 'w', encoding='utf-8') as f:
                        json.dump(minimal_data, f, ensure_ascii=False, indent=2)
                    
                    if not args.quiet:
                        print(f"💾 Simplified JSON saved to {date_folder}/: {os.path.basename(full_file)}")
                        print(f"📋 Minimal JSON saved: {os.path.basename(minimal_file)}")
                        print(f"📊 Found {len(simplified_data['simplified_routes'])} options")
                        print(f"💰 Cheapest: {simplified_data['summary']['cheapest_price']}")
                        print(f"⚡ Fastest: {simplified_data['summary']['fastest_time']}")
                else:
                    print(f"❌ Error: {simplified_data.get('error', 'Failed to fetch simplified data')}")
                    sys.exit(1)
            else:
                # Regular JSON output
                saver = JSONSaver(args.output_dir)
                
                # Generate filename
                filename = args.filename
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"route_{start_code}_{end_code}_{args.time.replace(':', '')}_{timestamp}"
                
                # Save based on format preference
                if args.format == 'compact':
                    # Save only compact
                    current_time = datetime.now()
                    output_dir, date_folder = get_date_based_output_path(args.output_dir, current_time)
                    json_data = saver.scraper.scrape_to_json(start_code, end_code, travel_date, args.time, pretty=False)
                    compact_file = os.path.join(output_dir, f"{filename}.json")
                    with open(compact_file, 'w', encoding='utf-8') as f:
                        f.write(json_data)
                    print(f"💾 Saved to {date_folder}/: {os.path.basename(compact_file)}")
                elif args.format == 'pretty':
                    # Save only pretty
                    current_time = datetime.now()
                    output_dir, date_folder = get_date_based_output_path(args.output_dir, current_time)
                    json_data = saver.scraper.scrape_to_json(start_code, end_code, travel_date, args.time, pretty=True)
                    pretty_file = os.path.join(output_dir, f"{filename}.json")
                    with open(pretty_file, 'w', encoding='utf-8') as f:
                        f.write(json_data)
                    print(f"💾 Saved to {date_folder}/: {os.path.basename(pretty_file)}")
                else:
                    # Save both (default)
                    result = saver.scrape_and_save(start_code, end_code, travel_date, args.time, filename)
                    if not args.quiet and result['success']:
                        print(f"📊 Routes: {result['routes_count']}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nUse --list-stations to see available stations")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 