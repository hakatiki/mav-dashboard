#!/usr/bin/env python3
"""
Extract Route Pairs from Comprehensive Route Dataset

This script loads all route data and extracts start/end station pairs
for use with the bulk scraper.
"""

import sys
import csv
import os
from pathlib import Path
from typing import Set, Tuple, List
from route_loader import RouteLoader


def extract_pure_station_id(raw_id: str) -> str:
    """
    Extract pure station ID from raw ID
    
    Args:
        raw_id: Raw station ID like "1:005514449_0"
        
    Returns:
        Pure station ID like "005514449"
    """
    try:
        return raw_id.split(":")[1].split("_")[0]
    except (IndexError, AttributeError):
        return raw_id


def extract_route_pairs(data_dir: str) -> Set[Tuple[str, str]]:
    """
    Extract all unique start/end station pairs from route data
    
    Args:
        data_dir: Directory containing route JSON files
        
    Returns:
        Set of (start_station_id, end_station_id) tuples
    """
    print(f"🔍 Loading routes from {data_dir}...")
    
    loader = RouteLoader(data_dir)
    routes = loader.load_all_routes()
    
    if not routes:
        print("❌ No routes found!")
        return set()
    
    print(f"📊 Processing {len(routes)} routes...")
    
    pairs = set()
    
    for route in routes:
        print(f"Processing route: {route.desc} ({route.id})")
        
        for pattern in route.patterns:
            if len(pattern.stops) < 2:
                continue  # Skip patterns with less than 2 stops
            
            # Extract pure station IDs
            station_ids = []
            for stop in pattern.stops:
                pure_id = extract_pure_station_id(stop.raw_id)
                if pure_id:
                    station_ids.append(pure_id)
            
            if len(station_ids) < 2:
                continue
            
            # Add start-end pair (first and last stations)
            start_station = station_ids[0]
            end_station = station_ids[-1]
            
            if start_station != end_station:
                pairs.add((start_station, end_station))
                # Also add reverse direction
                pairs.add((end_station, start_station))
            
            print(f"  Pattern: {pattern.headsign} - {len(station_ids)} stops")
            print(f"    {start_station} → {end_station}")
    
    print(f"✅ Found {len(pairs)} unique station pairs")
    return pairs


def save_pairs_to_csv(pairs: Set[Tuple[str, str]], output_file: str):
    """
    Save station pairs to CSV file
    
    Args:
        pairs: Set of (start_station_id, end_station_id) tuples
        output_file: Output CSV file path
    """
    print(f"💾 Saving {len(pairs)} pairs to {output_file}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'destination'])  # Header
        
        for start_id, end_id in sorted(pairs):
            writer.writerow([start_id, end_id])
    
    print(f"✅ Saved to {output_file}")


def main():
    """Main function"""
    # Paths
    data_dir = "all_rail_data"
    output_file = "../scraper/data/route_station_pairs.csv"
    
    print("🚆 Route Pair Extraction Tool")
    print("=" * 50)
    
    # Extract pairs
    pairs = extract_route_pairs(data_dir)
    
    if not pairs:
        print("❌ No pairs extracted!")
        return
    
    # Save to CSV
    save_pairs_to_csv(pairs, output_file)
    
    print("\n📈 Summary:")
    print(f"  Total unique pairs: {len(pairs)}")
    print(f"  Output file: {output_file}")
    print("  Ready for bulk scraper!")


if __name__ == "__main__":
    main() 