# Hungarian Train Route Dashboard

A comprehensive dashboard for visualizing Hungarian train routes with real-time delay information and beautiful interactive maps.

## 🎯 **NEW: Delay-Aware Visualization**

We've successfully integrated **real delay data** with route coordinates! 

### 📊 **Data Joining Results**
- **125 bulk delay files** analyzed
- **77 successful joins (61.6%)** - routes with both coordinate and delay data
- **48 partial joins (38.4%)** - one station found but not both
- **0 failed joins (0.0%)** - all station pairs had at least one station match

### 🎨 **Three Powerful Visualizers**

1. **Route Map Visualizer** (`visualizers/route_map_visualizer.py`)
   - Clean route network visualization
   - Smooth organic curves
   - Hungarian border outline
   - Professional styling

 2. **🆕 Delay-Aware Map Visualizer** (`visualizers/delay_map_visualizer.py`)
    - Routes colored by **average delay** information
    - Clean interface without legends or controls
    - Color-coded delay levels (green to red)
    - Shows delay statistics in popups

3. **🔥 Maximum Delay Map Visualizer** (`visualizers/max_delay_map_visualizer.py`)
   - Routes colored by **MAXIMUM delay** information (worst-case scenarios)
   - Shows peak delays rather than averages
   - Identifies problematic routes that occasionally have severe delays
   - Critical for operational risk assessment

## 📁 **Organized Structure**

```
dashboard/
├── data/                    # Data files (hu.json border data)
├── maps/                    # Generated HTML map files
├── loaders/                 # Data loading modules
│   ├── route_loader.py      # Route coordinate data loader
│   ├── bulk_loader.py       # Delay data loader
│   └── data_joiner.py       # Joins route + delay data
├── visualizers/             # Map visualization modules
│   ├── route_map_visualizer.py          # Basic route map
│   ├── delay_map_visualizer.py          # 🆕 Average delay map
│   ├── max_delay_map_visualizer.py      # 🔥 Maximum delay map
│   └── map_dashboard.py                 # Dashboard components
├── test_data_joining.py     # Test script for data joining
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 **Quick Start**

### Generate Basic Route Map
```bash
cd visualizers
python route_map_visualizer.py
```
**Output:** `../maps/magyar_vonalhalo_terkep.html`

### Generate Average Delay Map
```bash
cd visualizers  
python delay_map_visualizer.py
```
**Output:** `../maps/delay_aware_train_map.html`

### Generate Maximum Delay Map (NEW!)
```bash
cd visualizers  
python max_delay_map_visualizer.py
```
**Output:** `../maps/max_delay_train_map.html`

### Test Data Joining
```bash
python test_data_joining.py
```

## 🎨 **Delay Color Coding**

### Average Delay Map:
- 🟢 **Green** - On time (< 2 minutes)
- 🟡 **Yellow** - Minor delay (2-10 minutes)  
- 🟠 **Orange** - Moderate delay (10-20 minutes)
- 🔴 **Red** - Severe delay (20+ minutes)
- ⚫ **Gray** - No delay data available

### Maximum Delay Map:
- 🟢 **Green** - Low maximum (< 5 minutes)
- 🟡 **Yellow** - Moderate maximum (5-15 minutes)  
- 🟠 **Orange** - High maximum (15-30 minutes)
- 🔴 **Red** - Critical maximum (30+ minutes)
- ⚫ **Gray** - No delay data available

## 📊 **Current Statistics**

### Average Delay Results (1,460 route patterns):
- **Kis késés (2-10p):** 450 routes (30.8%) 
- **Időben (<2p):** 104 routes (7.1%)
- **Közepes (10-20p):** 86 routes (5.9%)
- **Súlyos (20p+):** 0 routes (0.0%)
- **Nincs adat:** 820 routes (56.2%)

### Maximum Delay Results (1,460 route patterns):
- **Közepes max (5-15p):** 265 routes (18.2%)
- **Magas max (15-30p):** 235 routes (16.1%)
- **Alacsony max (<5p):** 89 routes (6.1%)
- **Kritikus max (30p+):** 51 routes (3.5%) ⚠️
- **Nincs adat:** 820 routes (56.2%)

## 🛠 **Requirements**

```txt
folium>=0.14.0
numpy
```

## 🗺️ **Map Features**

All three visualizers include:

✅ **Hungarian border outline** (from accurate GeoJSON data)  
✅ **Smooth, organic route curves** (custom interpolation)  
✅ **Interactive popups** with route details  
✅ **Fullscreen mode**  
✅ **Measurement tools**  
✅ **Clean interface** without cluttered controls  
✅ **Professional styling**  
✅ **Website-ready** (100% width/height)  
✅ **Hungarian language** interface  

### 🆕 **Delay-Aware Features**

✅ **Color-coded routes** by delay severity  
✅ **Clean map interface** without legends or layer controls  
✅ **Delay statistics** in route popups  
✅ **Real-time delay data** integration  
✅ **Intuitive color coding** for instant delay recognition  

### 🔥 **Maximum Delay Features**

✅ **Worst-case scenario visualization**  
✅ **Peak delay identification**  
✅ **Risk assessment capability**  
✅ **Both average and maximum** delays shown in popups  
✅ **Critical route highlighting**  

## 🔧 **Technical Details**

### Data Sources
- **Route coordinates:** `../map_v2/all_rail_data/` (552 route files)
- **Delay data:** `../analytics/data/2025-07-23/` (125 bulk files)
- **Hungarian border:** `data/hu.json` (accurate GeoJSON)

### Key Components
- **RouteLoader:** Parses route JSON files with coordinates
- **BulkLoader:** Parses delay data from bulk JSON files  
- **DataJoiner:** Matches routes with delay information
- **BeautifulRouteMap:** Basic route visualization
- **DelayAwareRouteMap:** Average delay visualization
- **MaxDelayRouteMap:** Maximum delay visualization (worst-case)

### Delay Calculation Methodology

**For Average Delays:**
1. Collect all delay instances for each station pair (if route runs 10x/day, get all 10 delays)
2. Calculate average delay per station pair
3. Average across all segments in a route pattern

**For Maximum Delays:**
1. Collect all delay instances for each station pair
2. Take the **maximum** delay observed for each station pair
3. Take the **maximum** across all segments in a route pattern (worst segment defines the route)

### Map Specifications
- **Tiles:** CartoDB Positron (clean, light theme)
- **Center:** Calculated from route data (Hungary focus)
- **Zoom:** Auto-calculated for optimal view
- **Coordinates:** WGS84 (lat/lon)
- **Smoothing:** Custom interpolation algorithm
- **Border:** 2.5px black outline
- **Routes:** 1.3-1.8px lines (color-coded by delay)

## 🎉 **Success!**

We successfully:

1. ✅ **Reorganized** the dashboard into a clean structure
2. ✅ **Tested data joining** - 61.6% success rate with real delay data
3. ✅ **Created average delay visualizer** with color-coded routes
4. ✅ **Created maximum delay visualizer** for worst-case analysis
5. ✅ **Generated beautiful maps** ready for website embedding

The maps now provide both **typical performance** (average delays) and **risk assessment** (maximum delays) for comprehensive operational insights into Hungarian train punctuality! 🚂

### 🔍 **Key Insights**
- **51 routes (3.5%) have critical maximum delays over 30 minutes** - these need operational attention
- **Most routes have acceptable average performance** but significant variance in peak delays
- **Maximum delay analysis reveals hidden reliability issues** not visible in average-only analysis 