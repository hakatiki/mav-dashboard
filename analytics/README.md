# Hungarian Train Analytics with Map Generation

This directory contains an integrated solution that combines MAV train data analytics with interactive map visualization.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Complete Analytics and Map Generation
```bash
python dashboard_analyzer.py
```

This will:
- Load MAV data from Google Cloud Storage
- Process the data for analytics
- Generate two interactive maps:
  - `../dashboard/maps/delay_aware_train_map.html` - Routes colored by average delays
  - `../dashboard/maps/max_delay_train_map.html` - Routes colored by maximum delays

### 3. Test the Functionality
```bash
python test_map_generation.py
```

## 📊 What It Does

### Data Loading
- Connects to Google Cloud Storage bucket `mpt-all-sources`
- Loads MAV train data from the last 8 days
- Processes route information with delay statistics

### Map Generation
- **Delay-Aware Map**: Shows routes colored by average delay times
  - 🟢 Green: On time (< 2 minutes)
  - 🟡 Yellow: Minor delays (2-10 minutes)
  - 🟠 Orange: Moderate delays (10-20 minutes)
  - 🔴 Red: Severe delays (20+ minutes)

- **Maximum Delay Map**: Shows routes colored by worst-case delays
  - 🟢 Green: Low maximum (< 5 minutes)
  - 🟡 Yellow: Moderate maximum (5-15 minutes)
  - 🟠 Orange: High maximum (15-30 minutes)
  - 🔴 Red: Critical maximum (30+ minutes)

## 🗂️ File Structure

```
analytics/
├── dashboard_analyzer.py      # Main integrated script
├── test_map_generation.py    # Test script
├── requirements.txt          # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Google Cloud Storage
The script automatically connects to the `mpt-all-sources` bucket. Make sure you have:
- Google Cloud credentials configured
- Access to the bucket

### Data Paths
- Route data: `../map_v2/all_rail_data` (optional)
- Hungarian border: `../dashboard/data/hu.json`
- Output maps: `../dashboard/maps/`

## 🎨 Map Features

- **Interactive**: Click on routes for detailed delay information
- **Hungarian Border**: Shows the country outline
- **Fullscreen Support**: Toggle fullscreen mode
- **Measurement Tools**: Measure distances between points
- **Responsive**: Works on desktop and mobile devices

## 📈 Analytics Features

- Real-time data from Google Cloud Storage
- Automatic date fallback (last 8 days)
- Delay statistics calculation
- Station pair analysis
- Route segment processing

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Cloud Access**: Ensure you have proper credentials
   ```bash
   gcloud auth application-default login
   ```

3. **Missing Data**: The script will automatically try the last 8 days if today's data isn't available

4. **Map Generation**: If maps aren't generated, check that the `../dashboard/maps/` directory exists

### Debug Mode
Run the test script to check each component:
```bash
python test_map_generation.py
```

## 🔄 Integration with Dashboard

The generated maps are compatible with the existing dashboard structure:
- Maps are saved to `../dashboard/maps/`
- HTML files can be embedded in web applications
- Uses the same styling and plugins as the original dashboard

## 📝 Usage Examples

### Basic Usage
```python
from dashboard_analyzer import create_analytics, MapGenerator

# Load data
df = create_analytics()

# Generate maps
map_gen = MapGenerator()
map_gen.create_delay_aware_map(df)
map_gen.create_max_delay_map(df)
```

### Custom Configuration
```python
# Custom data directories
map_gen = MapGenerator(
    route_data_dir="../custom/route/data",
    bulk_data_dir="../custom/bulk/data"
)

# Custom output paths
map_gen.create_delay_aware_map(df, "custom_delay_map.html")
map_gen.create_max_delay_map(df, "custom_max_map.html")
```

## 🤝 Contributing

The integrated solution maintains compatibility with the existing dashboard structure while adding new analytics capabilities. All map generation features are self-contained and can be used independently. 