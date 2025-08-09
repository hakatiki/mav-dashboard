# 🚆 MÁV Monitor CORS Solution

## Problem
The MÁV Monitor dashboard was experiencing CORS (Cross-Origin Resource Sharing) policy errors when trying to fetch data directly from Google Cloud Storage. This is a common issue when web browsers try to access resources from different domains.

## Solution
We've implemented a multi-layered approach to solve the CORS issue:

### 1. Local Proxy Server (Recommended)
The most reliable solution is to use the local Node.js proxy server:

```bash
# Install dependencies
npm install

# Start the proxy server
npm start
```

The server will run on `http://localhost:3000` and provide:
- CORS-enabled API endpoints for GCS data
- Static file serving for the dashboard
- Health check endpoint

### 2. CORS Proxy Services (Fallback)
If the local server is not available, the dashboard will automatically try these CORS proxy services:
- `https://api.allorigins.win/raw?url=`
- `https://cors-anywhere.herokuapp.com/`
- `https://corsproxy.io/?`

### 3. Generated Data (Final Fallback)
If all external data sources fail, the dashboard falls back to generated sample data.

## Usage

### Option 1: Local Development (Recommended)
1. Navigate to the `website` directory
2. Install dependencies: `npm install`
3. Start the server: `npm start`
4. Open `http://localhost:3000` in your browser

### Option 2: Direct File Access
1. Open `index.html` directly in your browser
2. The dashboard will automatically try CORS proxy services
3. If proxies fail, it will use generated data

## API Endpoints

### Local Proxy Server
- `GET /api/mav-data/:date/:file` - Fetch GCS data
- `GET /health` - Health check
- `GET /` - Serve static files

### Example Usage
```javascript
// Fetch quick stats for a specific date
fetch('/api/mav-data/2025-07-30/quick_stats.json')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
1. Make sure the local proxy server is running
2. Check that you're accessing the dashboard through the proxy server URL
3. Verify the GCS bucket and file paths are correct

### Data Not Loading
If data doesn't load:
1. Check the browser console for error messages
2. Verify the date format (YYYY-MM-DD)
3. Ensure the GCS bucket contains the expected JSON files

### Proxy Server Issues
If the proxy server fails to start:
1. Check that Node.js is installed
2. Verify all dependencies are installed: `npm install`
3. Check if port 3000 is available (change in `proxy_server.js` if needed)

## File Structure
```
website/
├── index.html              # Main dashboard
├── script.js               # Dashboard logic with CORS handling
├── proxy_server.js         # Local CORS proxy server
├── package.json            # Node.js dependencies
├── max_delay_train_map.html # Map visualization
├── delay_aware_train_map.html # Map visualization
└── CORS_SOLUTION.md       # This file
```

## Security Notes
- The local proxy server is for development use only
- CORS proxy services are third-party and may have rate limits
- Always validate data from external sources in production

## Performance
- Local proxy server provides the best performance
- CORS proxy services may have latency
- Generated data loads instantly but is not real

## Support
For issues with the CORS solution:
1. Check the browser console for detailed error messages
2. Verify the GCS bucket permissions and file availability
3. Test with the local proxy server first 