from visualizers.max_delay_map_visualizer import generate_max_delay_map_html
from visualizers.delay_map_visualizer import generate_delay_map_html
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'loaders'))

from loaders.bulk_loader import BulkLoader


if __name__ == "__main__":
    # Set today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Loading data for today: {today}")
    
    # Initialize BulkLoader with GCS configuration
    # Using the same bucket and prefix as in mav_analytics_library.py
    bulk_loader = BulkLoader(
        bucket_name='mpt-all-sources',
        gcs_prefix="blog/mav/json_output/"
    )
    
    try:
        # Load bulk data from GCS for today
        print("🔍 Loading bulk data from GCS...")
        bulk_data_list = bulk_loader.load_all_bulk_files_from_gcs(target_date=today)
        print(f"✅ Successfully loaded {len(bulk_data_list)} bulk data files")
        
        # Generate maximum delay map
        print("\n🔥 Generating maximum delay map...")
        max_delay_html = generate_max_delay_map_html(
            bulk_loader=bulk_loader,
            route_data_dir="data/all_rail_data",
            bulk_data_list=bulk_data_list,
            date=today
        )
        print("✅ Maximum delay map generated successfully!")
        
        # Generate delay-aware map
        print("\n🎨 Generating delay-aware map...")
        delay_html = generate_delay_map_html(
            bulk_loader=bulk_loader,
            route_data_dir="data/all_rail_data",
            bulk_data_list=bulk_data_list,
            date=today
        )
        print("✅ Delay-aware map generated successfully!")
        
        print("\n🎉 Both maps generated successfully!")
        print("📊 Maps saved to GCS and local storage")
        
    except Exception as e:
        print(f"❌ Error generating maps: {e}")
        import traceback
        traceback.print_exc() 