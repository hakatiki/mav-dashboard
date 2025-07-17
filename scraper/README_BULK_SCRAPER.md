# MÁV Bulk Route Scraper

🚂 **Automated bulk scraping of MÁV train routes with intelligent organization and logging**

## Features

- ✅ **Bulk Processing**: Automatically processes all station pairs from CSV files
- 📅 **Date-Based Organization**: Saves JSON files in organized `yyyy-mm-dd` directories  
- 📝 **Comprehensive Logging**: Tracks every API call with detailed CSV logs
- 🗺️ **Smart Station Mapping**: Handles city name variations (e.g., "Budapest" → "Bp (BUDAPEST*)")
- 🚀 **Progress Tracking**: Real-time progress updates and statistics
- ⏱️ **Rate Limiting**: Configurable delays to be respectful to the API
- 🛡️ **Error Handling**: Robust error handling with detailed failure reporting

## Quick Start

### Test Mode (First 3 pairs)
```bash
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --test
```

### Process 10 pairs with 3-second delay
```bash
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --max-pairs 10 --delay 3
```

### Process all pairs (131 total, ~7 minutes with 3s delay)
```bash
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --delay 3
```

## Directory Structure

After running the bulk scraper, your files will be organized like this:

```
📁 json_output/
├── 📁 2025-07-15/
│   ├── 📄 bulk_005510009_004301974_20250715_230819.json
│   ├── 📄 bulk_005510009_004301974_20250715_230819_compact.json
│   ├── 📄 bulk_004301974_005510009_20250715_230849.json
│   ├── 📄 bulk_004301974_005510009_20250715_230849_compact.json
│   └── 📄 bulk_005510009_005501511_20250715_230910.json
├── 📁 2025-07-14/
│   └── 📄 [previous day's files]
└── 📁 2025-07-13/
    └── 📄 [older files]

📁 logging/
└── 📄 mav_api_calls_20250715.csv  # Detailed call logs
```

## Command Line Options

```bash
python bulk_scraper.py [CSV_FILE] [OPTIONS]

Arguments:
  CSV_FILE              Path to CSV file with station pairs

Options:
  --output-dir DIR      Output directory (default: json_output)
  --max-pairs N         Maximum number of pairs to process
  --delay SECONDS       Delay between requests in seconds (default: 2)
  --test               Test mode: process only first 3 pairs with 1s delay
  -h, --help           Show help message
```

## CSV Format

The CSV file should have columns: `source,destination,total_stations`

Example:
```csv
source,destination,total_stations
Budapest,Rajka,3
Rajka,Budapest,3
Budapest,Esztergom,2
Esztergom,Budapest,2
```

## Station Name Mapping

The scraper automatically handles common city name variations:

| CSV Name | Maps To | Station Code |
|----------|---------|--------------|
| Budapest | Bp (BUDAPEST*) | 005510009 |
| Szeged | Szeged | 005517228 |
| Debrecen | Debrecen | 005513912 |
| Szombathely | Szombathely | 004302246 |
| Kőszeg | Kőszeg | 004305538 |

New cities are automatically discovered during the first run.

## Output Files

Each station pair generates two JSON files:

1. **Pretty JSON** (`bulk_[START]_[END]_[TIMESTAMP].json`)
   - Human-readable formatted
   - Complete route details with train segments
   - Timing information and delays
   - Pricing and transfer details

2. **Compact JSON** (`bulk_[START]_[END]_[TIMESTAMP]_compact.json`)
   - Minified for APIs
   - Same data, smaller file size

## Logging System

Every API call is logged to `logging/mav_api_calls_[DATE].csv` with:

- ⏱️ Start/end times with millisecond precision
- 🚉 Station codes and names
- ✅ Success/failure status
- 📊 Number of routes found  
- 📏 Response size in bytes
- ❌ Error messages if any

### View Logging Statistics

```bash
cd logging
python view_stats.py                    # Basic stats
python view_stats.py --recent 10        # Last 10 calls
python view_stats.py --performance      # Performance analysis
python view_stats.py --all             # Everything
```

## Performance & Timing

- **API Response Time**: ~1-3 seconds per request
- **Processing Time**: ~21 seconds average per pair (including delays)
- **Recommended Delay**: 2-3 seconds to be respectful to the API
- **Estimated Duration** for 131 pairs with 3s delay: ~11 minutes

## Error Handling

The scraper handles:
- 🔍 **Station Not Found**: Unknown city names are reported but don't stop processing
- 🌐 **Network Errors**: Logged and processing continues with next pair
- 📊 **API Failures**: HTTP errors are logged with details
- 💾 **File Errors**: Disk space or permission issues are reported

## Integration with Existing Tools

The bulk scraper works seamlessly with existing tools:

- 🧪 `test_logging.py` - Test logging functionality
- 📊 `mav_cli.py` - Single route CLI interface
- 🗂️ `organize_json_outputs.py` - Organize existing files
- 📈 `logging/view_stats.py` - Analyze API call logs

## Example Usage Session

```bash
# 1. Test with 3 pairs first
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --test

# 2. If successful, run a larger batch
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --max-pairs 20 --delay 3

# 3. Check the results
ls json_output/2025-07-15/

# 4. View API call statistics  
cd logging && python view_stats.py --all

# 5. Process remaining pairs
python bulk_scraper.py ../ends/mav_unique_pairs_20250715_221609.csv --delay 3
```

## Benefits

✅ **Automated**: Set it and forget it - processes all pairs automatically  
📅 **Organized**: Files automatically sorted by date for easy management  
📝 **Tracked**: Every API call logged for analysis and debugging  
🔄 **Resumable**: Can restart from any point if interrupted  
⚡ **Efficient**: Smart caching and rate limiting  
🛡️ **Robust**: Comprehensive error handling  

This system transforms manual route checking into an automated data collection pipeline! 🚀 