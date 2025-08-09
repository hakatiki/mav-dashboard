# Map Generator Refactored

A clean, refactored version of the Hungarian train map generator that loads data from Google Cloud Storage and generates both delay-aware and maximum delay maps.

## Structure

```
map_generator_refactored/
├── loaders/                 # Data loading modules
│   ├── bulk_loader.py      # Loads bulk delay data from GCS/local
│   ├── route_loader.py     # Loads route data from JSON files
│   └── data_joiner.py      # Joins route and delay data
├── visualizers/            # Map visualization modules
│   ├── max_delay_map_visualizer.py  # Maximum delay map generator
│   └── delay_map_visualizer.py      # Average delay map generator
├── data/                   # Static data files
│   └── hu.json            # Hungarian border coordinates
├── maps/                   # Generated map outputs
├── generate_maps.py        # Main script to generate both maps
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features

- **GCS Integration**: Loads data directly from Google Cloud Storage
- **Dual Map Types**: Generates both average delay and maximum delay maps
- **Clean Architecture**: Well-organized, modular code structure
- **Error Handling**: Robust error handling with fallbacks
- **Modern UI**: Clean, website-ready map visualizations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud Storage credentials (if using GCS):
```bash
# Set your GCS credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
```

## Usage

### One-command run (maps + analytics)

Run everything for a specific date:

```bash
python -m map_generator_refactored --date 2025-07-30
```

Options:
- `--only maps` to generate only the maps
- `--only analysis` to generate only the analytics
- `--bucket` to set a GCS bucket (default: `mpt-all-sources`)
- `--gcs-prefix` to set GCS prefix (default: `blog/mav/json_output/`)
- `--route-data-dir` to set local route data path (default: `data/all_rail_data`)

This preserves existing behavior and uploads to the same GCS locations.

### Generate Both Maps

```bash
python generate_maps.py
```

This will:
- Load today's data from GCS
- Generate a maximum delay map (worst-case scenarios)
- Generate a delay-aware map (average delays)
- Save both maps to GCS and local storage

### Individual Map Generation

You can also generate maps individually by importing the functions:

```python
from visualizers.max_delay_map_visualizer import generate_max_delay_map_html
from visualizers.delay_map_visualizer import generate_delay_map_html
from loaders.bulk_loader import BulkLoader

# Initialize loader
bulk_loader = BulkLoader(
    bucket_name='mpt-all-sources',
    gcs_prefix="blog/mav/json_output/"
)

# Generate maximum delay map
max_delay_html = generate_max_delay_map_html(bulk_loader)

# Generate delay-aware map
delay_html = generate_delay_map_html(bulk_loader)
```

## Configuration

### GCS Settings

The default GCS configuration is:
- Bucket: `mpt-all-sources`
- Prefix: `blog/mav/json_output/`

You can modify these in `generate_maps.py` or when initializing `BulkLoader`.

### Route Data Directory

The default route data directory is `../../map_v2/all_rail_data`. You can modify this in the visualizer functions.

## Output

Maps are saved to:
- **GCS**: `gs://mpt-all-sources/blog/mav/maps/`
- **Local**: `maps/` directory

Generated files:
- `max_delay_train_map.html` - Maximum delay visualization
- `delay_aware_train_map.html` - Average delay visualization

## Deploy to Google Cloud Run Jobs

1) Build and push the image (replace `PROJECT_ID` and `REGION`):

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/mav-maps:latest map_generator_refactored
gcloud run deploy placeholder --image gcr.io/PROJECT_ID/mav-maps:latest --region REGION --no-traffic --platform managed
```

2) Create the job (uses today's date by default):

```bash
gcloud run jobs create mav-maps-job \
  --image gcr.io/PROJECT_ID/mav-maps:latest \
  --region REGION \
  --service-account SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com \
  --args "--only=all"
```

To set a fixed date, pass `--args "--date=2025-07-30 --only=all"`.

3) Run the job on demand:

```bash
gcloud run jobs run mav-maps-job --region REGION
```

4) Schedule daily via Cloud Scheduler (example):

```bash
gcloud scheduler jobs create http mav-maps-daily \
  --schedule "0 2 * * *" \
  --uri "https://REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/PROJECT_ID/jobs/mav-maps-job:run" \
  --oauth-service-account-email SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com \
  --http-method POST
```

Permissions: grant the service account Storage Object Admin on the target bucket and Cloud Run Invoker for Scheduler if used. No JSON key is needed on Cloud Run.

## Dependencies

- `folium` - Map visualization
- `numpy` - Numerical operations
- `google-cloud-storage` - GCS integration

## License

This project is part of the Hungarian train delay analysis system. 