#!/usr/bin/env python3
"""
🚆 MAV Analytics Batch Processing Script

This script runs the MAV analytics library for multiple dates in batch mode.
It processes all the dates efficiently and provides progress tracking.

Usage:
    python run_batch_analysis.py                    # Run for all specified dates
    python run_batch_analysis.py --dates 2025-07-15,2025-07-17  # Run for specific dates
    python run_batch_analysis.py --parallel        # Run with parallel processing
"""

import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from mav_analytics_library import MAVAnalytics, run_mav_analysis_for_date


# All available dates from the GCS bucket
ALL_DATES = [
    "2025-07-17", 
    "2025-07-18",
    "2025-07-19",
    "2025-07-21",
    "2025-07-22",
    "2025-07-23",
    "2025-07-24",
    "2025-07-25",
    "2025-07-26",
    "2025-07-28",
    "2025-07-29",
    "2025-07-30"
]


def run_single_date_analysis(target_date):
    """Run analysis for a single date with error handling."""
    print(f"🚆 Starting MAV analysis for {target_date}")
    start_time = time.time()
    
    try:
        results = run_mav_analysis_for_date(target_date)
        elapsed_time = time.time() - start_time
        
        print(f"✅ Analysis completed successfully for {target_date}")
        print(f"📊 Processed {results['data_summary']['total_routes']} routes")
        print(f"🚉 Found {results['data_summary']['unique_station_pairs']} unique station pairs")
        print(f"⏱️  Completed in {elapsed_time:.1f} seconds")
        
        return {
            'date': target_date,
            'success': True,
            'routes_processed': results['data_summary']['total_routes'],
            'station_pairs': results['data_summary']['unique_station_pairs'],
            'elapsed_time': elapsed_time,
            'error': None
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Error analyzing {target_date}: {e}")
        
        return {
            'date': target_date,
            'success': False,
            'routes_processed': 0,
            'station_pairs': 0,
            'elapsed_time': elapsed_time,
            'error': str(e)
        }


def run_sequential_analysis(dates):
    """Run analysis sequentially for all dates."""
    print(f"🔄 Running sequential analysis for {len(dates)} dates...")
    print("=" * 80)
    
    results = []
    total_start_time = time.time()
    
    for i, target_date in enumerate(dates, 1):
        print(f"\n📅 Processing date {i}/{len(dates)}: {target_date}")
        print("-" * 60)
        
        result = run_single_date_analysis(target_date)
        results.append(result)
        
        # Add a small delay between requests to be nice to the API
        if i < len(dates):
            time.sleep(1)
    
    total_elapsed = time.time() - total_start_time
    return results, total_elapsed


def run_parallel_analysis(dates, max_workers=3):
    """Run analysis in parallel for all dates."""
    print(f"🔄 Running parallel analysis for {len(dates)} dates with {max_workers} workers...")
    print("=" * 80)
    
    results = []
    total_start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_date = {executor.submit(run_single_date_analysis, date): date for date in dates}
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_date), 1):
            date = future_to_date[future]
            print(f"\n📅 Completed date {i}/{len(dates)}: {date}")
            
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Unexpected error for {date}: {e}")
                results.append({
                    'date': date,
                    'success': False,
                    'routes_processed': 0,
                    'station_pairs': 0,
                    'elapsed_time': 0,
                    'error': str(e)
                })
    
    total_elapsed = time.time() - total_start_time
    return results, total_elapsed


def print_summary(results, total_elapsed):
    """Print a comprehensive summary of the batch analysis."""
    print("\n" + "=" * 80)
    print("📊 BATCH ANALYSIS SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful analyses: {len(successful)}/{len(results)}")
    print(f"❌ Failed analyses: {len(failed)}/{len(results)}")
    print(f"⏱️  Total time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")
    
    if successful:
        total_routes = sum(r['routes_processed'] for r in successful)
        total_station_pairs = sum(r['station_pairs'] for r in successful)
        avg_time = sum(r['elapsed_time'] for r in successful) / len(successful)
        
        print(f"\n📈 SUCCESSFUL ANALYSES:")
        print(f"   • Total routes processed: {total_routes:,}")
        print(f"   • Total station pairs: {total_station_pairs:,}")
        print(f"   • Average time per analysis: {avg_time:.1f} seconds")
        
        # Show top 5 by routes processed
        top_by_routes = sorted(successful, key=lambda x: x['routes_processed'], reverse=True)[:5]
        print(f"\n🏆 TOP 5 DATES BY ROUTES PROCESSED:")
        for i, result in enumerate(top_by_routes, 1):
            print(f"   {i}. {result['date']}: {result['routes_processed']:,} routes ({result['station_pairs']} pairs)")
    
    if failed:
        print(f"\n❌ FAILED ANALYSES:")
        for result in failed:
            print(f"   • {result['date']}: {result['error']}")
    
    print("\n" + "=" * 80)
    print("🎯 Batch analysis complete!")
    print("📁 Check Google Cloud Storage for uploaded files")
    print("=" * 80)


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MAV analytics for multiple dates')
    parser.add_argument('--dates', type=str, help='Comma-separated list of dates (YYYY-MM-DD)')
    parser.add_argument('--parallel', action='store_true', help='Run analyses in parallel')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers (default: 3)')
    parser.add_argument('--list', action='store_true', help='List all available dates')
    
    args = parser.parse_args()
    
    if args.list:
        print("📅 Available dates:")
        for date in ALL_DATES:
            print(f"   • {date}")
        return
    
    # Determine which dates to process
    if args.dates:
        dates_to_process = [d.strip() for d in args.dates.split(',')]
        # Validate dates
        invalid_dates = [d for d in dates_to_process if d not in ALL_DATES]
        if invalid_dates:
            print(f"❌ Invalid dates: {invalid_dates}")
            print(f"Available dates: {ALL_DATES}")
            return
    else:
        dates_to_process = ALL_DATES
    
    print(f"🚆 MAV Analytics Batch Processing")
    print(f"📅 Processing {len(dates_to_process)} dates: {', '.join(dates_to_process)}")
    print(f"🔄 Mode: {'Parallel' if args.parallel else 'Sequential'}")
    if args.parallel:
        print(f"👥 Workers: {args.workers}")
    
    # Run the analysis
    if args.parallel:
        results, total_elapsed = run_parallel_analysis(dates_to_process, args.workers)
    else:
        results, total_elapsed = run_sequential_analysis(dates_to_process)
    
    # Print summary
    print_summary(results, total_elapsed)


if __name__ == "__main__":
    main() 