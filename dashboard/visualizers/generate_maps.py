from max_delay_map_visualizer import generate_max_delay_map_html
from delay_map_visualizer import generate_delay_map_html
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loaders'))

from bulk_loader import BulkLoader


if __name__ == "__main__":
    # Set today's date
    today = "2025-08-05"
    print(f"📅 Loading data for today: {today}")
    
    # Initialize BulkLoader with GCS configuration
    # Using the same bucket and prefix as in mav_analytics_library.py
    bulk_loader = BulkLoader(
        bucket_name='mpt-all-sources',
        gcs_prefix="blog/mav/json_output/"
    )
    
    try:
        # Load bulk data from GCS for today
        print("🔍 Loading bulk data from Google Cloud Storage...")
        bulk_data = bulk_loader.load_all_bulk_files_from_gcs(target_date=today)
        
        if bulk_data:
            print(f"✅ Successfully loaded {len(bulk_data)} bulk files from GCS")
            
            # Generate maps using the loaded bulk data
            print("🗺️ Generating maximum delay map...")
            generate_max_delay_map_html(bulk_loader, route_data_dir="../../map_v2/all_rail_data", bulk_data_list=bulk_data)
            
            print("🗺️ Generating delay-aware map...")
            generate_delay_map_html(bulk_loader, route_data_dir="../../map_v2/all_rail_data", bulk_data_list=bulk_data)
            
            print("✅ Map generation completed successfully!")
        else:
            print("❌ No bulk data found for today")
            
    except Exception as e:
        print(f"❌ Error loading data from GCS: {e}")
        print("🔄 Falling back to local data...")
        
        # Fallback to local data if GCS fails
        try:
            local_loader = BulkLoader("../analytics/data/2025-07-23")
            bulk_data = local_loader.load_all_bulk_files()
            
            if bulk_data:
                print(f"✅ Successfully loaded {len(bulk_data)} bulk files from local storage")
                
                # Generate maps using the loaded bulk data
                print("🗺️ Generating maximum delay map...")
                generate_max_delay_map_html(local_loader, route_data_dir="../../map_v2/all_rail_data", bulk_data_list=bulk_data)
                
                print("🗺️ Generating delay-aware map...")
                generate_delay_map_html(local_loader, route_data_dir="../../map_v2/all_rail_data", bulk_data_list=bulk_data)
                
                print("✅ Map generation completed successfully!")
            else:
                print("❌ No local bulk data found either")
                
        except Exception as local_error:
            print(f"❌ Error loading local data: {local_error}")
