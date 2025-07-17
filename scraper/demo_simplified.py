#!/usr/bin/env python3
"""
Demo script to show the enhanced simplified output with detailed train legs
"""

from mav_scraper import MAVScraper
import json

def demo_simplified():
    scraper = MAVScraper()
    
    print("🚆 Enhanced MÁV Scraper - Detailed Route Breakdown")
    print("="*60)
    
    # Get simplified data with train legs
    result = scraper.scrape_to_simplified_json("005510009", "005504747", start_time="01:00")
    
    if result['success']:
        print(f"📍 Route: Budapest-Déli → Keszthely")
        print(f"📅 Date: {result['route_info']['travel_date']}")
        print(f"📊 Found {result['summary']['total_options']} options")
        print(f"💰 Cheapest: {result['summary']['cheapest_price']}")
        print(f"⚡ Fastest: {result['summary']['fastest_time']}")
        print()
        
        # Show option 7 (the 842 TÓPART train) in detail
        for route in result['simplified_routes']:
            if route['option_number'] == 7 and route['train_legs']:
                print(f"🚂 OPTION {route['option_number']} - DETAILED BREAKDOWN")
                print("-" * 50)
                print(f"Overall timing: {route['departure_time']} → {route['actual_arrival_time']}")
                print(f"Total travel time: {route['travel_time']}")
                print(f"Transfers: {route['transfers']}")
                print(f"Price: {route['price']}")
                print()
                
                for leg in route['train_legs']:
                    print(f"🚅 LEG {leg['leg_number']}: {leg['train']}")
                    print(f"   Route: {leg['from_station']} → {leg['to_station']}")
                    print(f"   Departure: {leg['scheduled_departure']} → {leg['actual_departure']} "
                          f"({leg['departure_delay_min']:+d} min)")
                    print(f"   Arrival: {leg['scheduled_arrival']} → {leg['actual_arrival']} "
                          f"({leg['arrival_delay_min']:+d} min)")
                    print(f"   Travel time: {leg['travel_time']}")
                    if leg['services']:
                        print(f"   Services: {len(leg['services'])} amenities")
                    print()
                
                break
        
        # Save to file
        filename = "demo_detailed_routes.json"
        with open(f"output/{filename}", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Full detailed data saved to: output/{filename}")
        print()
        print("✅ SUCCESS: Now extracting individual train legs with:")
        print("   • Scheduled vs actual departure/arrival times")  
        print("   • Individual delays for each train leg")
        print("   • Intermediate stations (Balatonszentgyörgy)")
        print("   • Transfer information")
        print("   • Service amenities for each train")
        print("   • Complete route breakdown matching website data!")
        
    else:
        print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    demo_simplified() 