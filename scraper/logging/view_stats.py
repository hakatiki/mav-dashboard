#!/usr/bin/env python3
"""
MÁV API Call Statistics Viewer
Utility script to view and analyze logged API call data.
"""

import argparse
import os
import sys
import glob
from datetime import datetime
from mav_call_logger import MAVCallLogger

def list_log_files():
    """List all available log files."""
    log_files = glob.glob("mav_api_calls_*.csv")
    
    if not log_files:
        print("📁 No log files found in the current directory")
        return []
    
    print("📁 Available log files:")
    for i, file in enumerate(sorted(log_files), 1):
        try:
            # Get file size and modification time
            size = os.path.getsize(file)
            mtime = os.path.getmtime(file)
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            print(f"   {i}. {file} ({size:,} bytes, modified: {mtime_str})")
        except OSError:
            print(f"   {i}. {file} (error reading file info)")
    
    return sorted(log_files)

def view_latest_calls(log_file: str, count: int = 10):
    """View the most recent API calls."""
    import csv
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"\n📋 Latest {count} API calls from {log_file}:")
    print("-" * 120)
    
    calls = []
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        calls = list(reader)
    
    # Get the last N calls
    recent_calls = calls[-count:] if len(calls) > count else calls
    
    for call in recent_calls:
        timestamp = call.get('timestamp', 'Unknown')
        duration = call.get('duration_seconds', 'Unknown')
        start_station = call.get('start_station_name') or call.get('start_station_code', 'Unknown')
        end_station = call.get('end_station_name') or call.get('end_station_code', 'Unknown')
        success = call.get('success', 'Unknown')
        routes = call.get('routes_found', '0')
        error = call.get('error_message', '')
        
        status_icon = "✅" if success.lower() == "true" else "❌"
        
        print(f"{status_icon} {timestamp} | {start_station} → {end_station} | "
              f"{duration}s | {routes} routes")
        if error:
            print(f"   ⚠️ Error: {error}")

def compare_route_performance(log_file: str):
    """Compare performance across different routes."""
    import csv
    from collections import defaultdict
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    route_stats = defaultdict(lambda: {
        'calls': 0,
        'total_duration': 0,
        'total_routes': 0,
        'successes': 0,
        'errors': []
    })
    
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = row.get('start_station_name') or row.get('start_station_code', 'Unknown')
            end = row.get('end_station_name') or row.get('end_station_code', 'Unknown')
            route_key = f"{start} → {end}"
            
            stats = route_stats[route_key]
            stats['calls'] += 1
            
            try:
                duration = float(row.get('duration_seconds', 0))
                stats['total_duration'] += duration
            except ValueError:
                pass
            
            try:
                routes = int(row.get('routes_found', 0))
                stats['total_routes'] += routes
            except ValueError:
                pass
            
            if row.get('success', '').lower() == 'true':
                stats['successes'] += 1
            else:
                error = row.get('error_message', 'Unknown error')
                if error not in stats['errors']:
                    stats['errors'].append(error)
    
    print(f"\n📊 Route Performance Analysis from {log_file}:")
    print("-" * 120)
    print(f"{'Route':<40} {'Calls':<7} {'Avg Time':<10} {'Success':<8} {'Avg Routes':<12} {'Issues'}")
    print("-" * 120)
    
    for route, stats in sorted(route_stats.items()):
        avg_duration = stats['total_duration'] / stats['calls'] if stats['calls'] > 0 else 0
        success_rate = (stats['successes'] / stats['calls'] * 100) if stats['calls'] > 0 else 0
        avg_routes = stats['total_routes'] / stats['successes'] if stats['successes'] > 0 else 0
        issues = len(stats['errors'])
        
        print(f"{route:<40} {stats['calls']:<7} {avg_duration:<10.3f} {success_rate:<7.1f}% "
              f"{avg_routes:<12.1f} {issues}")
        
        if issues > 0:
            for error in stats['errors'][:2]:  # Show first 2 errors
                print(f"   ⚠️ {error}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="View MÁV API call statistics")
    parser.add_argument("--file", "-f", help="Specific log file to analyze")
    parser.add_argument("--list", "-l", action="store_true", help="List available log files")
    parser.add_argument("--recent", "-r", type=int, default=10, help="Number of recent calls to show")
    parser.add_argument("--performance", "-p", action="store_true", help="Show route performance comparison")
    parser.add_argument("--all", "-a", action="store_true", help="Show all statistics")
    
    args = parser.parse_args()
    
    # Change to the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if args.list:
        list_log_files()
        return
    
    # Determine which log file to use
    log_file = args.file
    if not log_file:
        # Use the most recent log file
        log_files = glob.glob("mav_api_calls_*.csv")
        if not log_files:
            print("❌ No log files found. Run some API calls first to generate logs.")
            sys.exit(1)
        log_file = sorted(log_files)[-1]
        print(f"📁 Using most recent log file: {log_file}")
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)
    
    # Create logger instance for statistics
    logger = MAVCallLogger(log_file)
    
    # Show basic statistics
    if args.all or not (args.recent or args.performance):
        logger.print_statistics()
    
    # Show recent calls
    if args.recent or args.all:
        view_latest_calls(log_file, args.recent)
    
    # Show performance comparison
    if args.performance or args.all:
        compare_route_performance(log_file)

if __name__ == "__main__":
    main() 