# 🚆 MÁV Monitor Data Documentation

## 📊 Data Sources

### Google Cloud Storage Bucket
All MÁV train data is stored in Google Cloud Storage at:
```
gs://mpt-all-sources/blog/mav/json_output/
```

### Data Structure by Date
Each date has its own folder containing multiple JSON files:
```
gs://mpt-all-sources/blog/mav/json_output/2025-07-30/
├── quick_stats.json
├── delay_histogram.json
├── price_histogram.json
├── expensive_routes.json
├── delayed_routes.json
└── bulk_*.json (raw route data)
```

## 📈 Available Data Files

### 1. Quick Statistics (`quick_stats.json`)
**URL Pattern**: `gs://mpt-all-sources/blog/mav/json_output/{DATE}/quick_stats.json`

**Structure**:
```json
{
  "actual_data_date": "2025-07-30",
  "total_routes_analyzed": 626,
  "unique_station_pairs": 69,
  "delay_performance": {
    "on_time_pct": 52.08,
    "delayed_pct": 47.92,
    "significantly_delayed_pct": 6.39,
    "average_delay_min": 2.17,
    "maximum_delay_min": 40.0
  },
  "pricing_insights": {
    "average_ticket_price_huf": 2356.80,
    "most_expensive_route_huf": 6650.0,
    "price_efficiency_huf_per_minute": 24.22
  },
  "travel_patterns": {
    "average_travel_time_min": 105.12,
    "shortest_route_min": 12.0,
    "longest_route_min": 367.0,
    "longest_route_hours": 6.12,
    "average_transfers": 0.45
  }
}
```

### 2. Delay Histogram (`delay_histogram.json`)
**URL Pattern**: `gs://mpt-all-sources/blog/mav/json_output/{DATE}/delay_histogram.json`

**Structure**:
```json
[
  {"Delay Bucket (min)": "0-5", "Count": 541},
  {"Delay Bucket (min)": "5-10", "Count": 40},
  {"Delay Bucket (min)": "10-15", "Count": 26},
  {"Delay Bucket (min)": "15-20", "Count": 12},
  {"Delay Bucket (min)": "20-25", "Count": 2},
  {"Delay Bucket (min)": "25-30", "Count": 4},
  {"Delay Bucket (min)": "30-35", "Count": 0},
  {"Delay Bucket (min)": "35-40", "Count": 0},
  {"Delay Bucket (min)": "40-45", "Count": 1},
  {"Delay Bucket (min)": "45-50", "Count": 0},
  {"Delay Bucket (min)": "50+", "Count": 0}
]
```

### 3. Price Histogram (`price_histogram.json`)
**URL Pattern**: `gs://mpt-all-sources/blog/mav/json_output/{DATE}/price_histogram.json`

**Structure**:
```json
[
  {"Price Bucket (HUF)": "0 (Free)", "Count": 1},
  {"Price Bucket (HUF)": "1-500", "Count": 5},
  {"Price Bucket (HUF)": "501-1000", "Count": 134},
  {"Price Bucket (HUF)": "1001-1500", "Count": 87},
  {"Price Bucket (HUF)": "1501-2000", "Count": 57},
  {"Price Bucket (HUF)": "2001-2500", "Count": 83},
  {"Price Bucket (HUF)": "2501-3000", "Count": 73},
  {"Price Bucket (HUF)": "3001-3500", "Count": 32},
  {"Price Bucket (HUF)": "3501-4000", "Count": 57},
  {"Price Bucket (HUF)": "4001-4500", "Count": 29},
  {"Price Bucket (HUF)": "4501-5000", "Count": 45},
  {"Price Bucket (HUF)": "5001-5500", "Count": 12},
  {"Price Bucket (HUF)": "5501-6000", "Count": 8},
  {"Price Bucket (HUF)": "6001+", "Count": 3}
]
```

### 4. Expensive Routes (`expensive_routes.json`)
**URL Pattern**: `gs://mpt-all-sources/blog/mav/json_output/{DATE}/expensive_routes.json`

**Structure**:
```json
[
  {
    "price_huf": 6650.0,
    "start_station": "004302329",
    "start_station_name": "Szentgotthárd",
    "end_station": "005501024",
    "end_station_name": "Budapest-Kelenföld",
    "train_name": "9177, 937 (SAVARIA)",
    "departure_time": "08:06",
    "arrival_time": "11:32",
    "date": "2025-07-30"
  }
]
```

### 5. Delayed Routes (`delayed_routes.json`)
**URL Pattern**: `gs://mpt-all-sources/blog/mav/json_output/{DATE}/delayed_routes.json`

**Structure**:
```json
[
  {
    "delay_min": 40.0,
    "start_station": "005510017",
    "start_station_name": "Zugló",
    "end_station": "005518036",
    "end_station_name": "Békéscsaba",
    "train_name": "6140, 7410",
    "departure_time": "04:01",
    "arrival_time": "07:17",
    "date": "2025-07-30"
  }
]
```

## 🗺️ Map Files

### Delay-Aware Train Map
**URL**: `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/2025-07-30/delay_aware_train_map.html`

### Max Delay Train Map
**URL**: `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/2025-07-30/max_delay_train_map.html`

## 🔧 Integration with Website

### JavaScript Data Loading
The website loads data using the following pattern:

```javascript
// Load quick stats
const quickStatsUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/quick_stats.json`;

// Load histograms
const delayHistogramUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/delay_histogram.json`;
const priceHistogramUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/price_histogram.json`;

// Load detailed routes
const expensiveRoutesUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/expensive_routes.json`;
const delayedRoutesUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/delayed_routes.json`;
```

### Available Dates
Currently available dates in the bucket:
- 2025-07-15
- 2025-07-17
- 2025-07-18
- 2025-07-19
- 2025-07-21
- 2025-07-22
- 2025-07-23
- 2025-07-24
- 2025-07-25
- 2025-07-26
- 2025-07-28
- 2025-07-30

## 📊 Data Analysis Insights

### Delay Categories
- **On-time**: 0 minutes delay
- **Minor delay**: 1-10 minutes
- **Moderate delay**: 11-20 minutes
- **Significant delay**: 21-30 minutes
- **Major delay**: 31+ minutes

### Price Categories
- **Free**: 0 HUF
- **Budget**: 1-1,000 HUF
- **Mid-range**: 1,001-2,500 HUF
- **Premium**: 2,501-5,000 HUF
- **Luxury**: 5,001+ HUF

### Performance Metrics
- **On-time percentage**: Routes with 0 delay
- **Average delay**: Mean delay across all routes
- **Maximum delay**: Highest recorded delay
- **Price efficiency**: HUF per minute of travel time

## 🚀 Usage Examples

### Loading Data for a Specific Date
```javascript
async function loadMAVData(date) {
    const baseUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}`;
    
    try {
        const [quickStats, delayHistogram, priceHistogram] = await Promise.all([
            fetch(`${baseUrl}/quick_stats.json`).then(r => r.json()),
            fetch(`${baseUrl}/delay_histogram.json`).then(r => r.json()),
            fetch(`${baseUrl}/price_histogram.json`).then(r => r.json())
        ]);
        
        return { quickStats, delayHistogram, priceHistogram };
    } catch (error) {
        console.error('Error loading MAV data:', error);
        return null;
    }
}
```

### Updating Dashboard with Real Data
```javascript
function updateDashboard(data) {
    // Update summary cards
    document.getElementById('total-routes').textContent = data.quickStats.total_routes_analyzed;
    document.getElementById('avg-delay').textContent = data.quickStats.delay_performance.average_delay_min.toFixed(1);
    document.getElementById('ontime-percentage').textContent = `${data.quickStats.delay_performance.on_time_pct.toFixed(1)}%`;
    document.getElementById('max-delay').textContent = data.quickStats.delay_performance.maximum_delay_min;
    
    // Update charts with histogram data
    updateDelayChart(data.delayHistogram);
    updatePriceChart(data.priceHistogram);
}
```

## 📝 Data Processing Notes

### Data Cleaning
- Outliers are removed for price efficiency calculations
- Travel time is converted to minutes
- Station names are standardized
- Duplicate routes are filtered (latest timestamp kept)

### Histogram Generation
- Delay bins: 5-minute intervals (0-5, 5-10, etc.)
- Price bins: 500 HUF intervals for paid routes
- Free routes are counted separately

### Map Integration
- Maps are generated separately and stored as HTML files
- Color coding based on delay severity
- Interactive features for route exploration

## 🔄 Data Update Frequency

- **Raw data**: Collected multiple times per day
- **Processed statistics**: Updated daily
- **Maps**: Regenerated when new data is available
- **Histograms**: Recalculated with each data update

## 📞 Support

For questions about the data structure or integration:
- Check the analytics notebook for detailed processing logic
- Review the JavaScript code in `script.js` for implementation examples
- Contact the development team for technical support

---

*Last updated: 2025-01-27*
*Data source: MÁV (Magyar Államvasutak Zrt.)*
*Processing: Google Cloud Storage + Python Analytics* 