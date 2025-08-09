const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS for all routes
app.use(cors({ origin: true }));

// Serve static files from public directory
const publicDir = path.join(__dirname, 'public');
app.use(express.static(publicDir));

// Root routes
app.get('/', (_req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
});

app.get(['/index.html', '/map.html'], (req, res) => {
    const file = req.path.replace('/', '');
    res.sendFile(path.join(publicDir, file));
});

// Proxy endpoint for GCS data
app.get('/api/mav-data/:date/:file', async (req, res) => {
    try {
        const { date, file } = req.params;
        const gcsUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/${file}`;
        
        console.log(`Fetching: ${gcsUrl}`);
        
        const response = await fetch(gcsUrl);
        
        if (!response.ok) {
            return res.status(404).json({ error: 'File not found' });
        }
        
        // Forward JSON with proper CORS headers
        res.set('Access-Control-Allow-Origin', '*');
        res.set('Cache-Control', 'no-store');
        const data = await response.json();
        res.json(data);
        
    } catch (error) {
        console.error('Proxy error:', error);
        res.set('Access-Control-Allow-Origin', '*');
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
    console.log(`CORS Proxy Server running on http://localhost:${PORT}`);
    console.log(`Access the dashboard at: http://localhost:${PORT}/index.html`);
}); 