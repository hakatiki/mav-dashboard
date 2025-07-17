"""
JSON Saver for MÁV scraper - automatically saves data as JSON files
"""

import json
import os
from datetime import datetime
from mav_scraper import MAVScraper
from date_utils import get_date_based_output_path, get_timestamped_filename

class JSONSaver:
    """Scrapes MÁV data and automatically saves as JSON files."""
    
    def __init__(self, output_dir: str = "json_output"):
        self.scraper = MAVScraper()
        self.base_output_dir = output_dir
        # Create base directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def scrape_and_save(self, start_station: str, end_station: str, 
                       travel_date: str = None, start_time: str = "01:00", 
                       filename: str = None):
        """
        Scrape route data and save as JSON file.
        
        Args:
            start_station: Starting station code
            end_station: Ending station code
            travel_date: Optional travel date
            filename: Optional custom filename (without .json extension)
            
        Returns:
            Dict with file paths and success status
        """
        print(f"🚆 Scraping {start_station} → {end_station}...")
        
        # Get JSON data
        json_data = self.scraper.scrape_to_json(start_station, end_station, travel_date, start_time)
        
        # Get date-based output directory
        current_time = datetime.now()
        output_dir, date_folder = get_date_based_output_path(self.base_output_dir, current_time)
        
        # Generate filename if not provided
        if filename is None:
            base_name = f"mav_routes_{start_station}_{end_station}"
            filename = get_timestamped_filename(base_name, "json", current_time).replace(".json", "")
        
        # Save pretty JSON
        pretty_file = os.path.join(output_dir, f"{filename}.json")
        with open(pretty_file, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        # Save compact JSON for APIs
        compact_data = self.scraper.scrape_to_json(start_station, end_station, travel_date, start_time, pretty=False)
        compact_file = os.path.join(output_dir, f"{filename}_compact.json")
        with open(compact_file, 'w', encoding='utf-8') as f:
            f.write(compact_data)
        
        # Parse data to get summary
        data = json.loads(json_data)
        
        print(f"✅ Saved JSON files to {date_folder}/:")
        print(f"   📄 Pretty: {pretty_file}")
        print(f"   📦 Compact: {compact_file}")
        
        if data['success']:
            print(f"📊 Data summary:")
            print(f"   🚂 Routes found: {data['total_routes']}")
            print(f"   💰 Price range: {self._get_price_range(data['routes'])} HUF")
            print(f"   ⏱️ Fastest: {self._get_fastest_route(data['routes'])}")
        
        return {
            'success': data['success'],
            'pretty_file': pretty_file,
            'compact_file': compact_file,
            'routes_count': data.get('total_routes', 0)
        }
    
    def _get_price_range(self, routes):
        """Get price range from routes."""
        prices = [r['price_huf'] for r in routes if r.get('price_huf')]
        if prices:
            return f"{min(prices):,} - {max(prices):,}"
        return "N/A"
    
    def _get_fastest_route(self, routes):
        """Get fastest route info."""
        if routes:
            fastest = min(routes, key=lambda x: x['travel_time_min'])
            return f"{fastest['travel_time_min']} ({fastest['train_name']})"
        return "N/A"
    
    def batch_save(self, routes_list, base_filename: str = None):
        """
        Save multiple routes to JSON files.
        
        Args:
            routes_list: List of (start_station, end_station, description) tuples
            base_filename: Optional base filename
            
        Returns:
            List of results for each route
        """
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, (start, end, description) in enumerate(routes_list):
            print(f"\n🔄 Processing route {i+1}/{len(routes_list)}: {description}")
            
            if base_filename:
                filename = f"{base_filename}_{i+1}_{timestamp}"
            else:
                safe_desc = description.replace(" ", "_").replace("→", "to").replace("-", "_")
                filename = f"{safe_desc}_{timestamp}"
            
            result = self.scrape_and_save(start, end, start_time="01:00", filename=filename)
            result['description'] = description
            results.append(result)
        
        print(f"\n✅ Batch processing completed! Saved {len(results)} route files.")
        return results

def main():
    """Example usage of JSON saver."""
    saver = JSONSaver()
    
    # Example 1: Single route
    print("📁 Example 1: Save Budapest → Keszthely")
    print("=" * 50)
    saver.scrape_and_save("005510009", "005504747", filename="budapest_keszthely")
    
    print("\n" + "=" * 60)
    
    # Example 2: Batch save multiple routes
    print("📁 Example 2: Batch Save Multiple Routes")
    print("=" * 50)
    
    routes = [
        ("005510009", "005504747", "Budapest-Déli → Keszthely"),
        ("005504747", "005501024", "Budapest-Keleti → Szeged"),
    ]
    
    saver.batch_save(routes, "mav_routes_batch")

if __name__ == "__main__":
    main() 