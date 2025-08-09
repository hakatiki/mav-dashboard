import argparse
import os
import sys
from datetime import datetime

# Ensure local package imports work when invoked as module or script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Prefer package-relative imports; fall back to local for direct script runs
try:
    from .loaders.bulk_loader import BulkLoader
    from .visualizers.max_delay_map_visualizer import generate_max_delay_map_html
    from .visualizers.delay_map_visualizer import generate_delay_map_html
    from .analytics.mav_analytics_library import run_mav_analysis_for_date
except ImportError:
    from loaders.bulk_loader import BulkLoader
    from visualizers.max_delay_map_visualizer import generate_max_delay_map_html
    from visualizers.delay_map_visualizer import generate_delay_map_html
    from analytics.mav_analytics_library import run_mav_analysis_for_date


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run MAV maps and analytics for a given date")
    parser.add_argument("--date", dest="date", type=str, default=None, help="Target date in YYYY-MM-DD (defaults to today)")
    parser.add_argument("--bucket", dest="bucket", type=str, default="mpt-all-sources", help="GCS bucket name")
    parser.add_argument("--gcs-prefix", dest="gcs_prefix", type=str, default="blog/mav/json_output/", help="GCS prefix for JSON data")
    parser.add_argument("--route-data-dir", dest="route_data_dir", type=str, default=os.path.join("data", "all_rail_data"), help="Path to route data directory (absolute or relative to package)")
    parser.add_argument("--only", dest="only", choices=["maps", "analysis", "all"], default="all", help="Run only maps, only analysis, or all")
    return parser.parse_args(argv)


def run_for_date(date_str: str, bucket: str, gcs_prefix: str, route_data_dir: str, only: str = "all"):
    # Resolve date
    target_date = date_str or datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Target date: {target_date}")

    # Resolve route data directory relative to package if not absolute
    if not os.path.isabs(route_data_dir):
        route_data_dir = os.path.join(CURRENT_DIR, route_data_dir)

    # Init loader (uses GCS by default; can still fall back to local loader paths inside visualizers)
    bulk_loader = BulkLoader(bucket_name=bucket, gcs_prefix=gcs_prefix)

    # Load bulk data list once if we are generating maps
    bulk_data_list = None
    if only in ("maps", "all"):
        print("🔍 Loading bulk data list for map generation...")
        try:
            bulk_data_list = bulk_loader.load_all_bulk_files_from_gcs(target_date=target_date)
            print(f"✅ Loaded {len(bulk_data_list)} bulk files for maps")
        except Exception as e:
            print(f"⚠️ Could not load from GCS for maps: {e}")
            # Attempt local fallback if available (visualizers also try fallback internally)
            try:
                bulk_loader_local = BulkLoader(data_dir=os.path.join(CURRENT_DIR, "data"))
                bulk_data_list = bulk_loader_local.load_all_bulk_files()
            except Exception as e2:
                print(f"❌ Local fallback for maps failed: {e2}")

    # Run maps
    if only in ("maps", "all"):
        print("\n🔥 Generating maximum delay map...")
        try:
            generate_max_delay_map_html(
                bulk_loader=bulk_loader,
                route_data_dir=route_data_dir,
                bulk_data_list=bulk_data_list,
                date=target_date,
            )
            print("✅ Maximum delay map generated")
        except Exception as e:
            print(f"❌ Failed to generate max delay map: {e}")

        print("\n🎨 Generating delay-aware map...")
        try:
            generate_delay_map_html(
                bulk_loader=bulk_loader,
                route_data_dir=route_data_dir,
                bulk_data_list=bulk_data_list,
                date=target_date,
            )
            print("✅ Delay-aware map generated")
        except Exception as e:
            print(f"❌ Failed to generate delay-aware map: {e}")

    # Run analysis
    if only in ("analysis", "all"):
        print("\n🚆 Running analytics...")
        try:
            results = run_mav_analysis_for_date(target_date)
            print("✅ Analytics finished")
            return results
        except Exception as e:
            print(f"❌ Analytics failed: {e}")
            return None


def main(argv=None):
    args = parse_args(argv)
    return run_for_date(
        date_str=args.date,
        bucket=args.bucket,
        gcs_prefix=args.gcs_prefix,
        route_data_dir=args.route_data_dir,
        only=args.only,
    )


if __name__ == "__main__":
    main()


