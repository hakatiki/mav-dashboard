#!/usr/bin/env python3
"""
🚆 MAV Analytics Runner Script

This script demonstrates how to use the MAVAnalytics library to run complete analysis
for different dates and upload results to Google Cloud Storage.

Usage:
    python run_mav_analysis.py [date]
    
Examples:
    python run_mav_analysis.py                    # Run for today
    python run_mav_analysis.py 2025-07-30        # Run for specific date
    python run_mav_analysis.py --recent           # Run for last 3 days
"""

import sys
from datetime import datetime, timedelta
from mav_analytics_library import MAVAnalytics, run_mav_analysis_for_date


def run_single_date_analysis(target_date):
    """Run analysis for a single date."""
    print(f"🚆 Starting MAV analysis for {target_date}")
    print("=" * 60)
    
    try:
        results = run_mav_analysis_for_date(target_date)
        print(f"✅ Analysis completed successfully for {target_date}")
        print(f"📊 Processed {results['data_summary']['total_routes']} routes")
        print(f"🚉 Found {results['data_summary']['unique_station_pairs']} unique station pairs")
        return True
    except Exception as e:
        print(f"❌ Error analyzing {target_date}: {e}")
        return False


def run_recent_analysis(days_back=3):
    """Run analysis for the last N days."""
    print(f"🔄 Running analysis for the last {days_back} days...")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for i in range(days_back):
        target_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        print(f"\n📅 Processing date {i+1}/{days_back}: {target_date}")
        
        if run_single_date_analysis(target_date):
            success_count += 1
        total_count += 1
    
    print(f"\n📊 Summary: {success_count}/{total_count} dates processed successfully")
    return success_count, total_count


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) == 1:
        # No arguments - run for today
        target_date = datetime.now().strftime('%Y-%m-%d')
        run_single_date_analysis(target_date)
        
    elif len(sys.argv) == 2:
        if sys.argv[1] == '--recent':
            # Run for recent days
            run_recent_analysis()
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print(__doc__)
        else:
            # Run for specific date
            target_date = sys.argv[1]
            run_single_date_analysis(target_date)
            
    else:
        print("Usage:")
        print("  python run_mav_analysis.py                    # Run for today")
        print("  python run_mav_analysis.py 2025-07-30        # Run for specific date")
        print("  python run_mav_analysis.py --recent           # Run for last 3 days")
        print("  python run_mav_analysis.py --help             # Show this help")


if __name__ == "__main__":
    main() 