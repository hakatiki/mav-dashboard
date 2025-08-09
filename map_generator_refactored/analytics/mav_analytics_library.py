# 🚆 MAV Analytics Library
# Comprehensive analysis and GCS upload functions for Hungarian train data

import pandas as pd
import numpy as np
import re
import json
from datetime import datetime, timedelta
from google.cloud import storage
from collections import defaultdict
import warnings


warnings.filterwarnings('ignore')
import sys
import os

from loaders.bulk_loader import BulkData, BulkRoute, RouteSegment, Statistics


class MAVAnalytics:
    """
    Comprehensive MAV (Hungarian Railways) analytics library with GCS integration.
    
    This library provides functions to:
    - Load MAV route data from Google Cloud Storage
    - Clean and preprocess data
    - Generate various analytics and statistics
    - Upload results to GCS for web dashboard consumption
    """
    
    def __init__(self, bucket_name='mpt-all-sources', target_date=None):
        """
        Initialize the MAV Analytics library.
        
        Args:
            bucket_name (str): GCS bucket name
            target_date (str): Date in YYYY-MM-DD format (defaults to today)
        """
        self.bucket_name = bucket_name
        self.target_date = target_date or datetime.now().strftime('%Y-%m-%d')
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    def upload_to_gcs(self, data, filename, target_date=None):
        """
        Uploads data to GCS as a JSON file for the given date.
        
        Args:
            data (dict or list): The data to upload (will be JSON-serialized)
            filename (str): The filename (e.g. 'quick_stats.json')
            target_date (str): Date in YYYY-MM-DD format (defaults to instance target_date)
        """
        target_date = target_date or self.target_date
        gcs_path = f"blog/mav/json_output/{target_date}/{filename}"
        blob = self.bucket.blob(gcs_path)
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        blob.upload_from_string(json_data, content_type='application/json')
        print(f"✅ Uploaded data to gs://{self.bucket_name}/{gcs_path}")
        
    def load_mav_data_from_gcs_using_bulk_loader(self, target_date=None, compact=""):
        """
        Load MAV route data from GCS bucket using BulkLoader approach for non-compact data.
        
        Args:
            target_date (str): Date in YYYY-MM-DD format (defaults to instance target_date)
            
        Returns:
            list: Processed route data ready for analysis
        """
        target_date = target_date or self.target_date
        print(f"🔍 Loading MAV data from: gs://{self.bucket_name}/blog/mav/json_output/")
        print(f"📅 Target date: {target_date}")
        
        # Try target date first, then fallback to previous days
        for days_back in range(8):
            try_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=days_back)).strftime('%Y-%m-%d')
            gcs_prefix = f"blog/mav/json_output/{try_date}/"
            
            print(f"🔄 Trying date: {try_date}")
            
            # List non-compact JSON files (exclude _compact.json files)
            blobs = list(self.bucket.list_blobs(prefix=gcs_prefix))
            non_compact_blobs = [blob for blob in blobs if blob.name.endswith('.json') and '_compact' not in blob.name]
            
            if non_compact_blobs:
                print(f"✅ Found {len(non_compact_blobs)} non-compact files for {try_date}")
                
                # Process the data using BulkLoader approach
                routes_data = []
                latest_blobs = {}
                
                for i, blob in enumerate(non_compact_blobs):
                    if i % 25 == 0:
                        print(f"📊 Processing file {i+1}/{len(non_compact_blobs)}...")
                    
                    # Group blobs by (start_station, end_station), keep only latest timestamp
                    filename = blob.name.split('/')[-1]
                    match = re.match(r'bulk_(\d+)_(\d+)_(\d{8}_\d{6})\.json', filename)
                    
                    if not match:
                        print(f"⚠️ Filename pattern not matched: {filename}")
                        continue
                    
                    start_station, end_station, timestamp = match.groups()
                    key = (start_station, end_station)
            
                    # Compare timestamps lexicographically (YYYYMMDD_HHMMSS format)
                    if key not in latest_blobs or timestamp > latest_blobs[key][0]:
                        latest_blobs[key] = (timestamp, blob)
                        
                print(f"🎯 Found {len(latest_blobs)} unique station pairs vs {len(non_compact_blobs)} total files")
                all_json_content = []
                # Process latest blobs using BulkLoader parsing
                for i, ((start_station, end_station), (timestamp, blob)) in enumerate(latest_blobs.items()):
                    try:
                        json_content = json.loads(blob.download_as_text())
                        all_json_content.append(json_content)
                        # Use BulkLoader approach to parse the data
                        bulk_data = self._parse_bulk_data_from_gcs(json_content, start_station, end_station, timestamp, try_date)
                        
                        if bulk_data and bulk_data.routes:
                            # Extract route information from BulkRoute objects
                            for route in bulk_data.routes:
                                # Get station names from route segments
                                start_station_name = 'Unknown'
                                end_station_name = 'Unknown'
                                
                                if route.route_segments:
                                    start_station_name = route.route_segments[0].start_station
                                    end_station_name = route.route_segments[-1].end_station
                                
                                routes_data.append({
                                    'start_station': start_station,
                                    'end_station': end_station,
                                    'end_station_name': end_station_name,
                                    'start_station_name': start_station_name,
                                    'station_pair': f"{start_station}_{end_station}",
                                    'timestamp': timestamp,
                                    'date': try_date,
                                    'train_name': route.train_name,
                                    'departure_time': route.departure_time,
                                    'arrival_time': route.arrival_time,
                                    'travel_time_min': route.travel_time_min,
                                    'delay_min': route.delay_min,
                                    'departure_delay_min': route.departure_delay_min,
                                    'arrival_delay_min': route.arrival_delay_min,
                                    'is_delayed': route.is_delayed,
                                    'is_significantly_delayed': route.is_significantly_delayed,
                                    'transfers_count': route.transfers_count,
                                    'price_huf': route.price_huf,
                                    'has_actual_times': route.departure_time_actual is not None or route.arrival_time_actual is not None
                                })
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Skipping {blob.name}: Invalid JSON format - {e}")
                        continue
                    except Exception as e:
                        print(f"⚠️ Skipping {blob.name}: Error processing file - {e}")
                        continue
                
                if routes_data:
                    print(f"🎯 Successfully loaded {len(routes_data)} route records using BulkLoader!")
                    return routes_data, all_json_content
            
            print(f"❌ No non-compact data found for {try_date}")
        
        raise Exception("❌ No MAV non-compact data found in the last 8 days!")
    
    def _parse_bulk_data_from_gcs(self, json_content, start_station, end_station, timestamp, try_date):
        """
        Parse bulk data from GCS JSON content using BulkLoader approach.
        
        Args:
            json_content (dict): JSON content from GCS blob
            start_station (str): Start station ID
            end_station (str): End station ID
            timestamp (str): Timestamp string
            try_date (str): Date string
            
        Returns:
            BulkData: Parsed bulk data object
        """
        try:
            # Parse statistics
            stats_data = json_content.get('statistics', {})
            statistics = Statistics(
                total_trains=stats_data.get('total_trains', 0),
                average_delay=stats_data.get('average_delay', 0.0),
                max_delay=stats_data.get('max_delay', 0),
                trains_on_time=stats_data.get('trains_on_time', 0),
                trains_delayed=stats_data.get('trains_delayed', 0),
                trains_significantly_delayed=stats_data.get('trains_significantly_delayed', 0),
                on_time_percentage=stats_data.get('on_time_percentage', 0.0),
                delayed_percentage=stats_data.get('delayed_percentage', 0.0)
            )
            
            # Parse routes
            routes = []
            for route_data in json_content.get('routes', []):
                route_segments = []
                
                # Parse route segments
                for segment_data in route_data.get('route_segments', []):
                    segment = RouteSegment(
                        leg_number=segment_data.get('leg_number', 0),
                        train_name=segment_data.get('train_name'),
                        train_number=segment_data.get('train_number', ''),
                        train_full_name=segment_data.get('train_full_name', ''),
                        start_station=segment_data.get('start_station', ''),
                        end_station=segment_data.get('end_station', ''),
                        departure_scheduled=segment_data.get('departure_scheduled', ''),
                        departure_actual=segment_data.get('departure_actual'),
                        departure_delay=segment_data.get('departure_delay', 0),
                        arrival_scheduled=segment_data.get('arrival_scheduled', ''),
                        arrival_actual=segment_data.get('arrival_actual'),
                        arrival_delay=segment_data.get('arrival_delay', 0),
                        travel_time=segment_data.get('travel_time', ''),
                        services=segment_data.get('services', []),
                        has_delays=segment_data.get('has_delays', False)
                    )
                    route_segments.append(segment)
                
                # Create BulkRoute
                route = BulkRoute(
                    train_name=route_data.get('train_name', ''),
                    departure_time=route_data.get('departure_time', ''),
                    departure_time_actual=route_data.get('departure_time_actual'),
                    arrival_time=route_data.get('arrival_time', ''),
                    arrival_time_actual=route_data.get('arrival_time_actual'),
                    travel_time_min=route_data.get('travel_time_min', ''),
                    delay_min=route_data.get('delay_min', 0),
                    departure_delay_min=route_data.get('departure_delay_min', 0),
                    arrival_delay_min=route_data.get('arrival_delay_min', 0),
                    is_delayed=route_data.get('is_delayed'),
                    is_significantly_delayed=route_data.get('is_significantly_delayed', False),
                    transfers_count=route_data.get('transfers_count', 0),
                    price_huf=route_data.get('price_huf', 0),
                    services=route_data.get('services', []),
                    intermediate_stations=route_data.get('intermediate_stations', []),
                    route_segments=route_segments
                )
                routes.append(route)
            
            # Create BulkData
            bulk_data = BulkData(
                success=json_content.get('success', True),
                timestamp=timestamp,
                start_station=start_station,
                end_station=end_station,
                travel_date=try_date,
                statistics=statistics,
                routes=routes
            )
            
            return bulk_data
            
        except Exception as e:
            print(f"⚠️ Error parsing bulk data: {e}")
            return None
        
    def load_mav_data_from_gcs(self, target_date=None):
        """
        Load MAV route data from GCS bucket with automatic date fallback.
        Now uses BulkLoader approach for non-compact data.
        
        Args:
            target_date (str): Date in YYYY-MM-DD format (defaults to instance target_date)
            
        Returns:
            list: Processed route data ready for analysis
        """
        return self.load_mav_data_from_gcs_using_bulk_loader(target_date)
    
    def clean_and_describe_data(self, df, target_date=None):
        """
        Cleans and preprocesses the input DataFrame, prints cleaning info and quick stats,
        and returns a dict with the quick stats. No side effects on the input DataFrame.
        
        Args:
            df (pd.DataFrame): Raw MAV route data
            target_date (str): Date for GCS upload (defaults to instance target_date)
            
        Returns:
            tuple: (cleaned_dataframe, quick_stats_dict)
        """
        target_date = target_date or self.target_date
        print("🧹 Cleaning and preprocessing data...")

        # Convert travel time to minutes
        def parse_travel_time(time_str):
            """Convert HH:MM format to total minutes"""
            if pd.isna(time_str) or time_str == '00:00':
                return 0
            try:
                if ':' in str(time_str):
                    parts = str(time_str).split(':')
                    return int(parts[0]) * 60 + int(parts[1])
                return 0
            except:
                return 0

        # Work on a copy to avoid side effects
        df_proc = df.copy()

        # Apply preprocessing
        df_proc['travel_time_minutes'] = df_proc['travel_time_min'].apply(parse_travel_time)
        df_proc['delay_min'] = pd.to_numeric(df_proc['delay_min'], errors='coerce').fillna(0)
        df_proc['departure_delay_min'] = pd.to_numeric(df_proc['departure_delay_min'], errors='coerce').fillna(0)
        df_proc['arrival_delay_min'] = pd.to_numeric(df_proc['arrival_delay_min'], errors='coerce').fillna(0)
        df_proc['price_huf'] = pd.to_numeric(df_proc['price_huf'], errors='coerce').fillna(0)
        df_proc['transfers_count'] = pd.to_numeric(df_proc['transfers_count'], errors='coerce').fillna(0)

        # Filter out unrealistic values
        df_clean = df_proc[
            (df_proc['travel_time_minutes'] > 0) &
            (df_proc['travel_time_minutes'] < 1440) &  # Less than 24 hours
            (df_proc['delay_min'].abs() < 300) &       # Less than 5 hours delay
            (df_proc['price_huf'] >= 0) &
            (df_proc['price_huf'] < 50000)             # Less than 50k HUF
        ]

        print(f"✅ Data cleaned: {len(df_clean):,} routes ready for analysis")
        print(f"📊 Removed {len(df_proc) - len(df_clean):,} outlier records")

        # Basic statistics
        avg_travel_time = df_clean['travel_time_minutes'].mean()
        avg_delay = df_clean['delay_min'].mean()
        delayed_count = (df_clean['is_delayed'] == True).sum()
        delayed_pct = (df_clean['is_delayed'] == True).mean() * 100
        avg_price = df_clean['price_huf'].mean()

        print(f"\n📈 Quick Stats:")
        print(f"   • Average travel time: {avg_travel_time:.1f} minutes")
        print(f"   • Average delay: {avg_delay:.1f} minutes")
        print(f"   • Routes with delays: {delayed_count:,} ({delayed_pct:.1f}%)")
        print(f"   • Average price: {avg_price:.0f} HUF")

        # Ensure all values are native Python types for JSON serialization
        quick_stats = {
            "removed_outliers": int(len(df_proc) - len(df_clean)),
            "average_travel_time": float(avg_travel_time),
            "average_delay": float(avg_delay),
            "routes_with_delays": int(delayed_count),
            "routes_with_delays_pct": float(delayed_pct),
            "average_price_huf": float(avg_price)
        }

        # Upload quick stats to GCS
        self.upload_to_gcs(quick_stats, filename="quick_stats.json", target_date=target_date)

        return df_clean, quick_stats

    def calculate_delay_histogram(self, df, target_date=None, bins=None, labels=None):
        """
        Calculate delay distribution in specified bins, upload to GCS, and return JSON-serializable stats.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame with 'delay_min' column
            target_date (str): Date for GCS path (defaults to instance target_date)
            bins (list): Optional custom bins
            labels (list): Optional custom labels
            
        Returns:
            list: List of dicts with delay bucket counts
        """
        target_date = target_date or self.target_date
        
        if bins is None:
            bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, float('inf')]
        if labels is None:
            labels = [
                "0-5", "5-10", "10-15", "15-20", "20-25", "25-30",
                "30-35", "35-40", "40-45", "45-50", "50+"
            ]

        # Only consider non-negative delays (delayed or on-time trains)
        delays = df[df['delay_min'] >= 0]['delay_min']

        # Bin the delays
        delay_buckets = pd.cut(delays, bins=bins, labels=labels, right=False, include_lowest=True)

        # Count how many in each bucket
        bucket_counts = delay_buckets.value_counts().sort_index()

        # Convert to JSON-serializable format
        bucket_counts_json = [
            {"Delay Bucket (min)": str(idx), "Count": int(val)}
            for idx, val in bucket_counts.items()
        ]

        # Upload to GCS
        self.upload_to_gcs(bucket_counts_json, filename="delay_histogram.json", target_date=target_date)

        return bucket_counts_json
    def calculate_price_histogram(self, df, target_date=None, bins=None, labels=None):
        """
        Calculate ticket price distribution in specified bins, upload to GCS.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame with 'price_huf' column
            target_date (str): Date for GCS path (defaults to instance target_date)
            bins (list): Optional custom bins
            labels (list): Optional custom labels
            
        Returns:
            list: List of dicts with price bucket counts
        """
        target_date = target_date or self.target_date
        
        # Default: 0, 1-500, 501-1000, ..., 5501-6000, 6001+
        if bins is None:
            bins = [0, 1] + list(range(500, 6500, 500)) + [float('inf')]
        if labels is None:
            labels = [
                "0 (Free)", "1-500", "501-1000", "1001-1500", "1501-2000", "2001-2500",
                "2501-3000", "3001-3500", "3501-4000", "4001-4500", "4501-5000",
                "5001-5500", "5501-6000", "6001+"
            ]

        prices = df['price_huf']

        # Bin the prices
        price_buckets = pd.cut(prices, bins=bins, labels=labels, right=False, include_lowest=True)
        bucket_counts = price_buckets.value_counts().sort_index()

        # Convert to JSON-serializable format
        bucket_counts_json = [
            {"Price Bucket (HUF)": str(idx), "Count": int(val)}
            for idx, val in bucket_counts.items()
        ]

        # Upload to GCS
        self.upload_to_gcs(bucket_counts_json, filename="price_histogram.json", target_date=target_date)

        return bucket_counts_json
    
    def get_mav_route_analysis_summary(self, df, target_date=None):
        """
        Summarizes MAV route analysis statistics and uploads to GCS.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame
            target_date (str): Date for GCS upload (defaults to instance target_date)
            
        Returns:
            dict: Comprehensive analysis summary
        """
        target_date = target_date or self.target_date
        summary = {}

        # Date and basic counts
        summary["actual_data_date"] = str(df['date'].iloc[0]) if not df.empty else None
        summary["total_routes_analyzed"] = int(len(df))
        summary["unique_station_pairs"] = int(df['station_pair'].nunique())

        # Delay performance
        on_time_pct = float((df['delay_min'] == 0).mean() * 100) if not df.empty else None
        delayed_pct = float((df['delay_min'] > 0).mean() * 100) if not df.empty else None
        sig_delayed_pct = float((df['delay_min'] > 10).mean() * 100) if not df.empty else None
        avg_delay = float(df['delay_min'].mean()) if not df.empty else None
        max_delay = float(df['delay_min'].max()) if not df.empty else None

        summary["delay_performance"] = {
            "on_time_pct": on_time_pct,
            "delayed_pct": delayed_pct,
            "significantly_delayed_pct": sig_delayed_pct,
            "average_delay_min": avg_delay,
            "maximum_delay_min": max_delay
        }

        # Pricing insights
        paid_routes_summary = df[df['price_huf'] > 0]
        avg_ticket_price = float(paid_routes_summary['price_huf'].mean()) if not paid_routes_summary.empty else None
        max_price = float(df['price_huf'].max()) if not df.empty else None
        price_per_min_summary = (
            paid_routes_summary['price_huf'] / paid_routes_summary['travel_time_minutes']
            if not paid_routes_summary.empty else None
        )
        price_efficiency = float(price_per_min_summary.mean()) if price_per_min_summary is not None and not price_per_min_summary.empty else None

        summary["pricing_insights"] = {
            "average_ticket_price_huf": avg_ticket_price,
            "most_expensive_route_huf": max_price,
            "price_efficiency_huf_per_minute": price_efficiency
        }

        # Travel patterns
        avg_travel_time = float(df['travel_time_minutes'].mean()) if not df.empty else None
        min_travel_time = float(df['travel_time_minutes'].min()) if not df.empty else None
        max_travel_time = float(df['travel_time_minutes'].max()) if not df.empty else None
        max_travel_time_hours = float(max_travel_time / 60) if max_travel_time is not None else None
        avg_transfers = float(df['transfers_count'].mean()) if not df.empty else None

        summary["travel_patterns"] = {
            "average_travel_time_min": avg_travel_time,
            "shortest_route_min": min_travel_time,
            "longest_route_min": max_travel_time,
            "longest_route_hours": max_travel_time_hours,
            "average_transfers": avg_transfers
        }

        # Upload summary to GCS
        self.upload_to_gcs(summary, filename="route_analysis_summary.json", target_date=target_date)

        return summary
    
    def get_top_most_delayed_trains(self, df, top_n=10, target_date=None):
        """
        Returns a list of the top N most delayed trains and uploads to GCS.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame
            top_n (int): Number of top delayed trains to return
            target_date (str): Date for GCS upload (defaults to instance target_date)
            
        Returns:
            list: List of dicts with delayed train information
        """
        target_date = target_date or self.target_date
        
        if df.empty:
            result = []
        else:
            top_delays = (
                df.sort_values("delay_min", ascending=False)
                .head(top_n)
                .loc[:, [
                    "delay_min",
                    "start_station",
                    "start_station_name",
                    "end_station",
                    "end_station_name",
                    "train_name",
                    "departure_time",
                    "arrival_time",
                    "date"
                ]]
            )

            result = [
                {
                    "delay_min": float(row["delay_min"]),
                    "start_station": row["start_station"],
                    "start_station_name": row.get("start_station_name", None),
                    "end_station": row["end_station"],
                    "end_station_name": row.get("end_station_name", None),
                    "train_name": row.get("train_name", None),
                    "departure_time": row.get("departure_time", None),
                    "arrival_time": row.get("arrival_time", None),
                    "date": row.get("date", None)
                }
                for _, row in top_delays.iterrows()
            ]

        # Upload to GCS
        self.upload_to_gcs(result, filename="delayed_routes.json", target_date=target_date)

        return result
    
    def get_top_most_expensive_routes(self, df, top_n=10, target_date=None):
        """
        Returns a list of the top N most expensive unique routes and uploads to GCS.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame
            top_n (int): Number of top expensive routes to return
            target_date (str): Date for GCS upload (defaults to instance target_date)
            
        Returns:
            list: List of dicts with expensive route information
        """
        target_date = target_date or self.target_date
        
        if df.empty:
            result = []
        else:
            # Create a key for unordered station pairs
            def unordered_pair(row):
                return tuple(sorted([row["start_station"], row["end_station"]]))

            df_proc = df.copy()
            df_proc["route_pair"] = df_proc.apply(unordered_pair, axis=1)

            # Sort by price descending, then drop duplicates for unique unordered pairs
            unique_routes = (
                df_proc.sort_values("price_huf", ascending=False)
                .drop_duplicates(subset=["route_pair"], keep="first")
                .loc[:, [
                    "price_huf",
                    "start_station",
                    "start_station_name",
                    "end_station",
                    "end_station_name",
                    "train_name",
                    "departure_time",
                    "arrival_time",
                    "date"
                ]]
                .head(top_n)
            )

            result = [
                {
                    "price_huf": float(row["price_huf"]),
                    "start_station": row["start_station"],
                    "start_station_name": row.get("start_station_name", None),
                    "end_station": row["end_station"],
                    "end_station_name": row.get("end_station_name", None),
                    "train_name": row.get("train_name", None),
                    "departure_time": row.get("departure_time", None),
                    "arrival_time": row.get("arrival_time", None),
                    "date": row.get("date", None)
                }
                for _, row in unique_routes.iterrows()
            ]

        # Upload to GCS
        self.upload_to_gcs(result, filename="expensive_routes.json", target_date=target_date)

        return result
    
    def get_late_trains_only_analysis(self, df, late_threshold=20, target_date=None):
        """
        Returns a JSON-compatible dict summarizing only late train statistics.
        
        Args:
            df (pd.DataFrame): Cleaned DataFrame
            late_threshold (int): Minutes threshold for "late" trains
            target_date (str): Date for GCS upload (defaults to instance target_date)
            
        Returns:
            dict: Late trains analysis summary
        """
        target_date = target_date or self.target_date
        result = {}
        total_trains = len(df)

        # 20 min = "late and refundable", 21+ min = "late"
        refundable_trains = df[df['delay_min'] == late_threshold]
        late_trains = df[df['delay_min'] > late_threshold]

        refundable_count = int(len(refundable_trains))
        late_trains_count = int(len(late_trains))
        total_late_or_refundable = refundable_count + late_trains_count

        refundable_pct = float(refundable_count / total_trains * 100) if total_trains > 0 else None
        late_trains_pct = float(late_trains_count / total_trains * 100) if total_trains > 0 else None
        total_late_or_refundable_pct = float(total_late_or_refundable / total_trains * 100) if total_trains > 0 else None

        result["late_train_definition_min"] = late_threshold
        result["late_and_refundable_count"] = refundable_count
        result["late_and_refundable_pct_of_total"] = refundable_pct
        result["late_trains_count"] = late_trains_count
        result["late_trains_pct_of_total"] = late_trains_pct
        result["late_or_refundable_total_count"] = total_late_or_refundable
        result["late_or_refundable_pct_of_total"] = total_late_or_refundable_pct

        # Refundable (exactly 20 min) stats
        if refundable_count > 0:
            refundable_stats = {
                "average_delay_min": float(refundable_trains['delay_min'].mean()),
                "median_delay_min": float(refundable_trains['delay_min'].median()),
                "min_delay_min": float(refundable_trains['delay_min'].min()),
                "max_delay_min": float(refundable_trains['delay_min'].max()),
                "std_delay_min": float(refundable_trains['delay_min'].std()) if refundable_count > 1 else 0.0
            }
            refundable_paid = refundable_trains[refundable_trains['price_huf'] > 0]
            refundable_free = refundable_trains[refundable_trains['price_huf'] == 0]
            refundable_pricing = {
                "paid_refundable_routes_count": int(len(refundable_paid)),
                "free_refundable_routes_count": int(len(refundable_free)),
            }
            if len(refundable_paid) > 0:
                refundable_pricing.update({
                    "average_price_paid_routes_huf": float(refundable_paid['price_huf'].mean()),
                    "median_price_paid_routes_huf": float(refundable_paid['price_huf'].median()),
                    "max_price_paid_route_huf": float(refundable_paid['price_huf'].max()),
                    "min_price_paid_route_huf": float(refundable_paid['price_huf'].min())
                })
            else:
                refundable_pricing.update({
                    "average_price_paid_routes_huf": None,
                    "median_price_paid_routes_huf": None,
                    "max_price_paid_route_huf": None,
                    "min_price_paid_route_huf": None
                })
            refundable_travel_patterns = {
                "average_travel_time_min": float(refundable_trains['travel_time_minutes'].mean()),
                "average_travel_time_hours": float(refundable_trains['travel_time_minutes'].mean() / 60),
                "average_transfers": float(refundable_trains['transfers_count'].mean()),
                "unique_routes_affected": int(refundable_trains['station_pair'].nunique())
            }
        else:
            refundable_stats = None
            refundable_pricing = None
            refundable_travel_patterns = None

        result["refundable_delay_statistics"] = refundable_stats
        result["refundable_pricing"] = refundable_pricing
        result["refundable_travel_patterns"] = refundable_travel_patterns

        # Late (21+ min) stats
        if late_trains_count > 0:
            delay_stats = {
                "average_delay_min": float(late_trains['delay_min'].mean()),
                "median_delay_min": float(late_trains['delay_min'].median()),
                "min_delay_min": float(late_trains['delay_min'].min()),
                "max_delay_min": float(late_trains['delay_min'].max()),
                "std_delay_min": float(late_trains['delay_min'].std())
            }
            late_paid = late_trains[late_trains['price_huf'] > 0]
            late_free = late_trains[late_trains['price_huf'] == 0]
            pricing = {
                "paid_late_routes_count": int(len(late_paid)),
                "free_late_routes_count": int(len(late_free)),
            }
            if len(late_paid) > 0:
                pricing.update({
                    "average_price_paid_routes_huf": float(late_paid['price_huf'].mean()),
                    "median_price_paid_routes_huf": float(late_paid['price_huf'].median()),
                    "max_price_paid_route_huf": float(late_paid['price_huf'].max()),
                    "min_price_paid_route_huf": float(late_paid['price_huf'].min())
                })
            else:
                pricing.update({
                    "average_price_paid_routes_huf": None,
                    "median_price_paid_routes_huf": None,
                    "max_price_paid_route_huf": None,
                    "min_price_paid_route_huf": None
                })
            travel_patterns = {
                "average_travel_time_min": float(late_trains['travel_time_minutes'].mean()),
                "average_travel_time_hours": float(late_trains['travel_time_minutes'].mean() / 60),
                "average_transfers": float(late_trains['transfers_count'].mean()),
                "unique_routes_affected": int(late_trains['station_pair'].nunique())
            }
           
            result["late_train_delay_statistics"] = delay_stats
            result["late_train_pricing"] = pricing
            result["late_train_travel_patterns"] = travel_patterns
        else:
            result["late_train_delay_statistics"] = None
            result["late_train_pricing"] = None
            result["late_train_travel_patterns"] = None

        # Upload to GCS
        self.upload_to_gcs(result, filename="late_trains_only_analysis.json", target_date=target_date)

        return result
    
    def run_complete_analysis(self, target_date=None):
        """
        Run complete MAV analysis pipeline for a given date.
        
        Args:
            target_date (str): Date in YYYY-MM-DD format (defaults to instance target_date)
            
        Returns:
            dict: Summary of all analysis results
        """
        target_date = target_date or self.target_date
        print(f"🚀 Starting complete MAV analysis for {target_date}")
        print("=" * 60)
        
        # Load data
        print("📊 Loading MAV data...")
        raw_data, all_json_content = self.load_mav_data_from_gcs(target_date=target_date)

        df = pd.DataFrame(raw_data)
        
        # Clean data
        print("🧹 Cleaning and preprocessing data...")
        df_clean, quick_stats = self.clean_and_describe_data(df, target_date=target_date)
        
        # Generate all analyses
        print("📈 Generating delay histogram...")
        delay_histogram = self.calculate_delay_histogram(df_clean, target_date=target_date)
        
        print("💰 Generating price histogram...")
        price_histogram = self.calculate_price_histogram(df_clean, target_date=target_date)
        
        print("📊 Generating route analysis summary...")
        route_summary = self.get_mav_route_analysis_summary(df_clean, target_date=target_date)
        
        print("🔴 Finding top delayed trains...")
        delayed_trains = self.get_top_most_delayed_trains(df_clean, target_date=target_date)
        
        print("💎 Finding top expensive routes...")
        expensive_routes = self.get_top_most_expensive_routes(df_clean, target_date=target_date)
        
        print("⏰ Analyzing late trains...")
        late_trains_analysis = self.get_late_trains_only_analysis(df_clean, target_date=target_date)
        
  
        # Compile results
        results = {
            "analysis_date": target_date,
            "data_summary": {
                "total_routes": len(df_clean),
                "unique_station_pairs": df_clean['station_pair'].nunique(),
                "date_range": f"{df_clean['date'].min()} to {df_clean['date'].max()}"
            },
            "quick_stats": quick_stats,
            "delay_histogram": delay_histogram,
            "price_histogram": price_histogram,
            "route_summary": route_summary,
            "delayed_trains": delayed_trains,
            "expensive_routes": expensive_routes,
            "late_trains_analysis": late_trains_analysis
        }
        
        print("✅ Complete analysis finished!")
        print(f"📊 Uploaded {len(results) - 1} analysis files to GCS for {target_date}")
        
        return results


def run_mav_analysis_for_date(target_date):
    """
    Convenience function to run complete MAV analysis for a specific date.
    
    Args:
        target_date (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Complete analysis results
    """
    analyzer = MAVAnalytics(target_date=target_date)
    return analyzer.run_complete_analysis()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🚆 Running MAV analysis for {target_date}")
    results = run_mav_analysis_for_date(target_date)
    print(f"✅ Analysis complete! Check GCS for uploaded files.") 