#!/usr/bin/env python3
"""
Test script for Kőszeg ↔ Szombathely routes using station lookup
"""

from station_lookup import MAVStationLookup
from mav_scraper import MAVScraper
import json

def test_koszeg_szombathely():
    print("🚆 Testing Kőszeg ↔ Szombathely Route")
    print("="*50)
    
    # Initialize station lookup
    lookup = MAVStationLookup()
    
    # Find station codes
    koszeg_code = lookup.find_station_code("Kőszeg")
    szombathely_code = lookup.find_station_code("Szombathely")
    
    print(f"🔍 Station Codes Found:")
    print(f"   Kőszeg: {koszeg_code}")
    print(f"   Szombathely: {szombathely_code}")
    print()
    
    if not koszeg_code or not szombathely_code:
        print("❌ Could not find station codes")
        return
    
    # Test route from Szombathely to Kőszeg
    print("🚅 Testing Route: Szombathely → Kőszeg")
    print("-" * 40)
    
    scraper = MAVScraper()
    
    try:
        # Get simplified JSON data
        result = scraper.scrape_to_simplified_json(
            start_station=szombathely_code,
            end_station=koszeg_code,
            start_time="08:00"
        )
        
        if result['success']:
            print(f"✅ Found {result['summary']['total_options']} route options")
            print(f"💰 Cheapest: {result['summary']['cheapest_price']}")
            print(f"⚡ Fastest: {result['summary']['fastest_time']}")
            print()
            
            # Show first few options
            for i, route in enumerate(result['simplified_routes'][:3], 1):
                print(f"Option {i}:")
                print(f"  Departure: {route['departure_time']}")
                print(f"  Arrival: {route['actual_arrival_time']}")
                print(f"  Travel time: {route['travel_time']}")
                print(f"  Transfers: {route['transfers']}")
                print(f"  Price: {route['price']}")
                
                # Show train legs if available
                if route.get('train_legs'):
                    print(f"  Train legs:")
                    for leg in route['train_legs']:
                        print(f"    {leg['train']}: {leg['from_station']} → {leg['to_station']}")
                        print(f"    Times: {leg['scheduled_departure']} → {leg['actual_departure']} | {leg['scheduled_arrival']} → {leg['actual_arrival']}")
                print()
            
            # Save results
            filename = f"koszeg_szombathely_routes.json"
            with open(f"output/{filename}", 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Results saved to: output/{filename}")
            
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    print("✅ Test completed! Station lookup works with MÁV API codes.")

if __name__ == "__main__":
    test_koszeg_szombathely() 