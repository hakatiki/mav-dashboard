#!/usr/bin/env python3
"""
Test script for map generation functionality
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analytics.max_map import MapGenerator, create_analytics

def test_map_generation():
    """Test the map generation functionality"""
    print("🧪 Testing map generation functionality...")
    print("=" * 50)
    
    try:
        # Test 1: Create analytics DataFrame
        print("📊 Testing analytics data loading...")
        df = create_analytics()
        print(f"✅ Successfully loaded {len(df)} route records")
        
        # Test 2: Initialize map generator
        print("\n🗺️  Testing map generator initialization...")
        map_gen = MapGenerator()
        print("✅ Map generator initialized successfully")
        
        # Test 3: Generate delay-aware map
        print("\n🎨 Testing delay-aware map generation...")
        map_obj = map_gen.create_delay_aware_map(df)
        print("✅ Delay-aware map generated successfully")
        
        # Test 4: Generate max delay map
        print("\n🔥 Testing maximum delay map generation...")
        map_obj = map_gen.create_max_delay_map(df)
        print("✅ Maximum delay map generated successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("📁 Check the ../dashboard/maps/ directory for generated HTML files")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_map_generation()
    sys.exit(0 if success else 1) 