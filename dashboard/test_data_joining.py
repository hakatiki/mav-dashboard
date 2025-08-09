"""
Test Data Joining

Test script to analyze how many bulk delay files can be successfully
joined with route coordinate data.
"""

import sys
import os
from pathlib import Path

# Add loaders to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loaders'))

from route_loader import RouteLoader
from bulk_loader import BulkLoader
from data_joiner import DataJoiner


def test_data_joining():
    """Test joining bulk delay data with route coordinate data"""
    print("🔍 Testing Data Joining...")
    print("=" * 50)
    
    # Paths
    route_data_dir = "../map_v2/all_rail_data"
    bulk_data_dir = "../analytics/data/2025-07-23"
    
    # Check if directories exist
    if not Path(route_data_dir).exists():
        print(f"❌ Route data directory not found: {route_data_dir}")
        return
    
    if not Path(bulk_data_dir).exists():
        print(f"❌ Bulk data directory not found: {bulk_data_dir}")
        return
    
    print(f"✅ Found route data directory: {route_data_dir}")
    print(f"✅ Found bulk data directory: {bulk_data_dir}")
    
    # Initialize loaders
    print("\n📡 Initializing loaders...")
    try:
        route_loader = RouteLoader(route_data_dir)
        bulk_loader = BulkLoader(bulk_data_dir)
        joiner = DataJoiner(route_loader, bulk_loader)
        print("✅ Loaders initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize loaders: {e}")
        return
    
    # Load route data
    print("\n🚂 Loading route data...")
    try:
        routes = route_loader.load_all_routes()
        print(f"✅ Loaded {len(routes)} routes")
        
        # Get all stations from routes
        all_stations = route_loader.get_all_stations(routes)
        print(f"✅ Found {len(all_stations)} unique stations in route data")
        
        # Show some station examples
        station_ids = list(all_stations.keys())[:5]
        print(f"📍 Example station IDs: {station_ids}")
        
    except Exception as e:
        print(f"❌ Failed to load route data: {e}")
        return
    
    # Load bulk delay data
    print("\n📊 Loading bulk delay data...")
    try:
        bulk_data_list = bulk_loader.load_all_bulk_files()
        print(f"✅ Loaded {len(bulk_data_list)} bulk files")
        
        # Analyze station pairs in bulk data
        station_pairs = bulk_loader.get_all_station_pairs(bulk_data_list)
        print(f"✅ Found {len(station_pairs)} unique station pairs in bulk data")
        
        # Show some examples
        print(f"📍 Example station pairs:")
        for i, (start, end) in enumerate(station_pairs[:5]):
            print(f"   {i+1}. {start} → {end}")
            
    except Exception as e:
        print(f"❌ Failed to load bulk data: {e}")
        return
    
    # Test joining process
    print("\n🔗 Testing data joining...")
    
    successful_joins = 0
    failed_joins = 0
    partial_joins = 0
    
    join_results = {
        'successful': [],
        'failed': [],
        'partial': []
    }
    
    for i, bulk_data in enumerate(bulk_data_list):
        try:
            start_id = bulk_data.start_station
            end_id = bulk_data.end_station
            
            # Try to find matching routes
            matching_routes = joiner.find_route_segments_for_stations(routes, start_id, end_id)
            
            if matching_routes:
                successful_joins += 1
                join_results['successful'].append({
                    'start': start_id,
                    'end': end_id,
                    'routes_found': len(matching_routes),
                    'avg_delay': bulk_data.statistics.average_delay
                })
                print(f"✅ {i+1:3d}/{len(bulk_data_list)}: {start_id} → {end_id} ({len(matching_routes)} routes found)")
            else:
                # Check if we can find either station individually
                start_found = start_id in all_stations
                end_found = end_id in all_stations
                
                if start_found or end_found:
                    partial_joins += 1
                    join_results['partial'].append({
                        'start': start_id,
                        'end': end_id,
                        'start_found': start_found,
                        'end_found': end_found,
                        'avg_delay': bulk_data.statistics.average_delay
                    })
                    print(f"🟡 {i+1:3d}/{len(bulk_data_list)}: {start_id} → {end_id} (partial: start={start_found}, end={end_found})")
                else:
                    failed_joins += 1
                    join_results['failed'].append({
                        'start': start_id,
                        'end': end_id,
                        'avg_delay': bulk_data.statistics.average_delay
                    })
                    print(f"❌ {i+1:3d}/{len(bulk_data_list)}: {start_id} → {end_id} (no stations found)")
                    
        except Exception as e:
            failed_joins += 1
            print(f"💥 {i+1:3d}/{len(bulk_data_list)}: Error processing {bulk_data.start_station} → {bulk_data.end_station}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 DATA JOINING SUMMARY")
    print("=" * 50)
    print(f"Total bulk files analyzed: {len(bulk_data_list)}")
    print(f"Successful joins: {successful_joins} ({successful_joins/len(bulk_data_list)*100:.1f}%)")
    print(f"Partial joins: {partial_joins} ({partial_joins/len(bulk_data_list)*100:.1f}%)")
    print(f"Failed joins: {failed_joins} ({failed_joins/len(bulk_data_list)*100:.1f}%)")
    
    # Analyze successful joins
    if join_results['successful']:
        print(f"\n🎉 TOP 5 SUCCESSFUL JOINS:")
        successful_sorted = sorted(join_results['successful'], key=lambda x: x['routes_found'], reverse=True)
        for i, result in enumerate(successful_sorted[:5]):
            print(f"   {i+1}. {result['start']} → {result['end']}: {result['routes_found']} routes, {result['avg_delay']:.1f}min avg delay")
    
    # Analyze failed joins
    if join_results['failed']:
        print(f"\n⚠️  SAMPLE FAILED JOINS:")
        for i, result in enumerate(join_results['failed'][:5]):
            print(f"   {i+1}. {result['start']} → {result['end']}: {result['avg_delay']:.1f}min avg delay")
    
    # Create station delay map for successful joins
    if join_results['successful']:
        print(f"\n🗺️  Creating delay map for successful joins...")
        try:
            successful_bulk_data = [bulk_data for bulk_data in bulk_data_list 
                                  if any(s['start'] == bulk_data.start_station and s['end'] == bulk_data.end_station 
                                        for s in join_results['successful'])]
            
            station_delays = joiner.create_station_delay_map(successful_bulk_data)
            print(f"✅ Created delay map with {len(station_delays)} station pairs")
            
            # Create enriched segments
            enriched_segments = joiner.create_route_segments_with_delay(routes, station_delays)
            print(f"✅ Created {len(enriched_segments)} enriched route segments with delay data")
            
        except Exception as e:
            print(f"❌ Failed to create delay map: {e}")
    
    return join_results


if __name__ == "__main__":
    test_data_joining() 