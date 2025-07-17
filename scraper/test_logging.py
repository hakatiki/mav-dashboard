#!/usr/bin/env python3
"""
Test script for MÁV API call logging functionality.
Demonstrates the new logging system by making a few test calls.
"""

import sys
import os
from datetime import datetime
from mav_scraper import MAVScraper
from station_lookup import MAVStationLookup

def test_logging_functionality():
    """Test the logging functionality with a few API calls."""
    
    print("🧪 Testing MÁV API Call Logging System")
    print("=" * 50)
    
    # Initialize scraper with logging enabled
    scraper = MAVScraper(enable_logging=True)
    print(f"📝 Logging enabled: {scraper.enable_logging}")
    
    if scraper.logger:
        print(f"📄 Log file: {scraper.logger.log_file}")
    
    # Initialize station lookup
    station_lookup = MAVStationLookup()
    station_lookup.load_stations()
    if not station_lookup.stations:
        print("❌ Failed to load stations data")
        return
    
    # Test routes to try
    test_routes = [
        ("Budapest-Keleti", "Szeged"),
        ("Szombathely", "Kőszeg"),
        ("Budapest-Nyugati", "Debrecen")
    ]
    
    print("\n🚂 Making test API calls...")
    
    for i, (start_city, end_city) in enumerate(test_routes, 1):
        print(f"\n--- Test {i}/3: {start_city} → {end_city} ---")
        
        # Look up station codes
        start_stations = station_lookup.search_stations(start_city)
        end_stations = station_lookup.search_stations(end_city)
        
        if not start_stations:
            print(f"❌ No stations found for '{start_city}'")
            continue
            
        if not end_stations:
            print(f"❌ No stations found for '{end_city}'")
            continue
        
        # Use the first station found
        start_station = start_stations[0]
        end_station = end_stations[0]
        
        start_code = start_station['code']
        end_code = end_station['code']
        start_name = start_station['name']
        end_name = end_station['name']
        
        print(f"🔍 Found: {start_name} ({start_code}) → {end_name} ({end_code})")
        
        # Make the API call
        try:
            success, data = scraper.fetch_routes(
                start_station=start_code,
                end_station=end_code,
                travel_date=None,  # Use today
                start_time="08:00",  # 8 AM departure
                start_station_name=start_name,
                end_station_name=end_name
            )
            
            if success:
                routes = data.get('route', [])
                print(f"✅ Success: Found {len(routes)} routes")
            else:
                print("❌ Failed to fetch routes")
                
        except Exception as e:
            print(f"❌ Error during API call: {e}")
        
        # Small delay between calls to be nice to the API
        import time
        time.sleep(1)
    
    print("\n📊 Logging Test Complete!")
    
    # Show logging statistics
    if scraper.logger:
        print("\n" + "=" * 50)
        print("📈 LOGGING STATISTICS")
        print("=" * 50)
        scraper.logger.print_statistics()
    
    return scraper.logger.log_file if scraper.logger else None

def demonstrate_log_viewing(log_file: str):
    """Demonstrate the log viewing utilities."""
    if not log_file or not os.path.exists(log_file):
        print("❌ No log file available for demonstration")
        return
    
    print("\n" + "=" * 50)
    print("📋 LOG VIEWING DEMONSTRATION")
    print("=" * 50)
    
    # Import the logging utilities
    sys.path.append('logging')
    try:
        from view_stats import view_latest_calls, compare_route_performance
        from mav_call_logger import MAVCallLogger
        
        # Show recent calls
        view_latest_calls(log_file, 5)
        
        # Show performance comparison
        compare_route_performance(log_file)
        
    except ImportError as e:
        print(f"❌ Could not import logging utilities: {e}")

def main():
    """Main function."""
    print("🚀 Starting MÁV API Logging Test")
    print("This will make a few test API calls to demonstrate the logging system.\n")
    
    # Test the logging functionality
    log_file = test_logging_functionality()
    
    # Demonstrate log viewing
    demonstrate_log_viewing(log_file)
    
    print("\n🎉 Test completed!")
    
    if log_file:
        print(f"\n💡 To view detailed statistics, run:")
        print(f"   cd logging")
        print(f"   python view_stats.py")
        print(f"   python view_stats.py --all")
        print(f"   python view_stats.py --performance")

if __name__ == "__main__":
    main() 