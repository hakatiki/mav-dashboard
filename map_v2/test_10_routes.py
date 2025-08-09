#!/usr/bin/env python3
"""
Test script to fetch 10 RAIL routes automatically
"""

from mav_rail_fetcher import MAVRailFetcher

def main():
    """Test with 10 RAIL routes"""
    fetcher = MAVRailFetcher()
    
    print("Testing with 10 RAIL routes...")
    fetcher.process_routes(limit=10)

if __name__ == "__main__":
    main() 