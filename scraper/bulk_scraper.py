#!/usr/bin/env python3
"""
Bulk MÁV Route Scraper
Processes all station pairs from MAV unique pairs CSV and saves data in organized date-based directories.
"""

import csv
import os
import sys
import time
import random
from datetime import datetime
from typing import Dict, Optional, Tuple
from mav_scraper import MAVScraper
from json_saver import JSONSaver

class BulkMAVScraper:
    """Bulk scraper for processing multiple station pairs."""
    
    def __init__(self, csv_path: str, output_dir: str = "json_output"):
        self.csv_path = csv_path
        self.output_dir = output_dir
        self.scraper = MAVScraper(enable_logging=True)
        self.json_saver = JSONSaver(output_dir)
        
        # Statistics
        self.stats = {
            'total_pairs': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    

    
    def _apply_variable_delay(self, base_delay: float):
        """
        Apply a variable delay with randomization to mimic human behavior.
        
        Args:
            base_delay: Base delay in seconds (e.g., 3.0)
        """
        if base_delay <= 0:
            return
        
        # Random delay: base_delay ± 50% (e.g., 3.0 ± 1.5 = 1.5-4.5 seconds)
        min_delay = base_delay * 0.5
        max_delay = base_delay * 1.5
        delay = random.uniform(min_delay, max_delay)
        
        # Occasionally add longer pauses (5% chance) to simulate human breaks
        if random.random() < 0.05:
            extra_delay = random.uniform(2.0, 8.0)
            delay += extra_delay
            print(f"😴 Taking a longer break: {delay:.1f}s")
        else:
            print(f"⏳ Waiting {delay:.1f}s before next request...")
        
        time.sleep(delay)
    
    def load_station_pairs(self) -> list:
        """Load station pairs from CSV file (expects station IDs)."""
        pairs = []
        
        if not os.path.exists(self.csv_path):
            print(f"❌ CSV file not found: {self.csv_path}")
            return pairs
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    source = row.get('source', '').strip()
                    destination = row.get('destination', '').strip()
                    if source and destination:
                        pairs.append((source, destination))
            
            print(f"📂 Loaded {len(pairs)} station pairs from {self.csv_path}")
            
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
        
        return pairs
    
    def process_pair(self, source_station_id: str, dest_station_id: str, base_delay_seconds: float = 2.0) -> bool:
        """
        Process a single station pair using station IDs directly.
        
        Args:
            source_station_id: Source station ID
            dest_station_id: Destination station ID
            base_delay_seconds: Base delay between requests (will be randomized)
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n🚂 Processing: {source_station_id} → {dest_station_id}")
        
        try:
            # Fetch routes using station IDs directly
            success, data = self.scraper.fetch_routes(
                start_station=source_station_id,
                end_station=dest_station_id,
                travel_date=None,  # Use today
                start_time="00:30",  
                start_station_name=f"Station_{source_station_id}",  # Placeholder name
                end_station_name=f"Station_{dest_station_id}"       # Placeholder name
            )
            
            if success:
                routes = data.get('route', [])
                print(f"✅ Found {len(routes)} routes")
                
                # Save with JSONSaver (automatically goes to date-based directory)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"bulk_{source_station_id}_{dest_station_id}_{timestamp}"
                
                result = self.json_saver.scrape_and_save(
                    start_station=source_station_id,
                    end_station=dest_station_id,
                    travel_date=None,
                    start_time="00:30",
                    filename=filename
                )
                
                return True
            else:
                print(f"❌ Failed to fetch routes")
                return False
                
        except Exception as e:
            print(f"❌ Error processing pair: {e}")
            return False
        
        finally:
            # Be nice to the API with variable delay
            self._apply_variable_delay(base_delay_seconds)
    
    def run_bulk_scraping(self, max_pairs: Optional[int] = None, base_delay_seconds: float = 2.0, progress_callback=None, progress_interval: int = 100):
        """
        Run bulk scraping for all station pairs.
        
        Args:
            max_pairs: Maximum number of pairs to process (None for all)
            base_delay_seconds: Base delay between requests in seconds (will be randomized)
            progress_callback: Function to call every progress_interval processed pairs
            progress_interval: How often to call the progress callback (default: 100)
        """
        print("🚀 Starting Bulk MÁV Route Scraping")
        print("=" * 60)
        
        # Load station pairs
        pairs = self.load_station_pairs()
        if not pairs:
            print("❌ No station pairs to process")
            return
        
        # Limit pairs if specified
        if max_pairs and max_pairs < len(pairs):
            pairs = pairs[:max_pairs]
            print(f"🔢 Processing first {max_pairs} pairs (out of {len(pairs)} total)")
        
        self.stats['total_pairs'] = len(pairs)
        self.stats['start_time'] = datetime.now()
        
        print(f"📊 Processing {len(pairs)} station pairs with ~{base_delay_seconds:.1f}s variable delay between requests")
        print(f"⏱️ Estimated duration: {len(pairs) * base_delay_seconds / 60:.1f} minutes (may vary due to random delays)")
        if progress_callback and progress_interval:
            print(f"📤 Incremental uploads enabled every {progress_interval} processed pairs")
        
        # Process each pair
        for i, (source, dest) in enumerate(pairs, 1):
            print(f"\n{'='*60}")
            print(f"Progress: {i}/{len(pairs)} ({i/len(pairs)*100:.1f}%)")
            
            if self.process_pair(source, dest, base_delay_seconds):
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
            
            self.stats['processed'] += 1
            
            # Call progress callback every N items
            if progress_callback and i % progress_interval == 0:
                try:
                    print(f"📤 Running incremental upload at {i}/{len(pairs)} processed pairs...")
                    progress_callback(i, len(pairs), self.stats)
                except Exception as e:
                    print(f"⚠️ Warning: Progress callback failed: {e}")
            
            # Show progress every 10 items
            if i % 10 == 0:
                self._print_progress_stats()
        
        self.stats['end_time'] = datetime.now()
        self._print_final_stats()
    
    def _print_progress_stats(self):
        """Print progress statistics."""
        processed = self.stats['processed']
        successful = self.stats['successful']
        failed = self.stats['failed']
        success_rate = (successful / processed * 100) if processed > 0 else 0
        
        print(f"\n📈 Progress Update:")
        print(f"   Processed: {processed}/{self.stats['total_pairs']}")
        print(f"   Successful: {successful} ({success_rate:.1f}%)")
        print(f"   Failed: {failed}")
    
    def _print_final_stats(self):
        """Print final statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("🎉 BULK SCRAPING COMPLETE")
        print("=" * 60)
        print(f"📊 Final Statistics:")
        print(f"   Total pairs: {self.stats['total_pairs']}")
        print(f"   Processed: {self.stats['processed']}")
        print(f"   Successful: {self.stats['successful']}")
        print(f"   Failed: {self.stats['failed']}")
        print(f"   Success rate: {self.stats['successful']/self.stats['processed']*100:.1f}%")
        print(f"   Duration: {duration}")
        print(f"   Average time per pair: {duration.total_seconds()/self.stats['processed']:.1f}s")
        
        # Show logging info
        if self.scraper.logger:
            print(f"\n📝 Detailed logs saved to: {self.scraper.logger.log_file}")
            print(f"📁 JSON files organized in: {self.output_dir}/")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk MÁV route scraper")
    parser.add_argument("csv_file", help="Path to CSV file with station pairs")
    parser.add_argument("--output-dir", default="json_output", help="Output directory (default: json_output)")
    parser.add_argument("--max-pairs", type=int, help="Maximum number of pairs to process")
    parser.add_argument("--delay", type=float, default=2.0, help="Base delay between requests in seconds (randomized, default: 2.0)")
    parser.add_argument("--test", action="store_true", help="Test mode: process only first 3 pairs")
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        args.max_pairs = 3
        args.delay = 1.0
        print("🧪 TEST MODE: Processing only first 3 pairs with ~1s variable delay")
    
    # Create and run bulk scraper
    scraper = BulkMAVScraper(args.csv_file, args.output_dir)
    scraper.run_bulk_scraping(args.max_pairs, args.delay)

if __name__ == "__main__":
    main() 