# MÁV Train Route Scraper

python scraper/bulk_scraper.py ends/mav_unique_pairs_20250715_221609.csv --delay 3.0

A clean, modular Python scraper for fetching train route data from the Hungarian State Railways (MÁV) API and analyzing delay patterns.

## Features

- 🚆 Fetch real-time train schedules and delays
- 📊 Calculate comprehensive delay statistics
- 💾 Save raw and processed data to JSON files
- 🎯 Clean, modular code structure
- ⚙️ Configurable station codes and settings

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python mav_scraper.py
```

### Custom Route

```python
from mav_scraper import MAVScraper

scraper = MAVScraper()

# Scrape specific route
results = scraper.scrape_route(
    start_station="005504747",  # Budapest-Keleti
    end_station="005501024",    # Szeged
    save_results=True,
    display_limit=10
)
```

### Using Station Names

```python
from config import STATION_CODES

start = STATION_CODES['budapest_keleti']
end = STATION_CODES['szeged']

results = scraper.scrape_route(start, end)
```

## Configuration

Edit `config.py` to:
- Add new station codes
- Modify API settings
- Change output preferences

## Output

The scraper generates:
- **Console output**: Formatted train schedules and delay statistics
- **Raw data**: Complete API response (`mav_raw_data_TIMESTAMP.json`)
- **Processed data**: Clean format with statistics (`mav_processed_data_TIMESTAMP.json`)

## Example Output

```
🚆 TRAIN SCHEDULE & DELAY ANALYSIS
==================================================

📊 DELAY STATISTICS
Total trains: 12
Average delay: 3.2 minutes
Maximum delay: 15 minutes
On time: 8/12 (66.7%)
Delayed: 4/12 (33.3%)
Significantly delayed (>5min): 2/12

🚂 TRAIN SCHEDULES (showing first 5)
--------------------------------------------------
1. IC 311 Budapest-Keleti - Szeged
   Departure: 08:15
   Arrival: 10:45
   Travel time: 150 min
   🟢 Delay: 0 min

2. R 3112 Budapest-Keleti - Szeged
   Departure: 10:20
   Arrival: 13:15
   Travel time: 175 min
   🟡 Delay: 3 min
```

## API Structure

The scraper is built around a clean `MAVScraper` class with methods:

- `fetch_routes()`: Get data from MÁV API
- `parse_route_info()`: Clean route data
- `calculate_delay_statistics()`: Analyze delays
- `display_results()`: Format console output
- `save_data()`: Export to JSON files
- `scrape_route()`: Complete workflow

## Error Handling

The scraper includes robust error handling for:
- Network connectivity issues
- API response errors  
- JSON parsing problems
- Invalid station codes

## Data Format

### Processed Route Data
```json
{
  "train_name": "IC 311 Budapest-Keleti - Szeged",
  "departure_time": "08:15",
  "arrival_time": "10:45", 
  "travel_time_min": 150,
  "delay_min": 0,
  "is_delayed": false,
  "is_significantly_delayed": false
}
```

### Statistics Data
```json
{
  "total_trains": 12,
  "average_delay": 3.2,
  "max_delay": 15,
  "trains_on_time": 8,
  "on_time_percentage": 66.7,
  "delayed_percentage": 33.3
}
``` 