const functions = require('firebase-functions');
const fetch = require('node-fetch');

exports.mavProxy = functions.https.onRequest(async (req, res) => {
  try {
    res.set('Access-Control-Allow-Origin', '*');
    res.set('Cache-Control', 'no-store');
    if (req.method === 'OPTIONS') {
      res.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
      res.set('Access-Control-Allow-Headers', 'Content-Type');
      return res.status(204).send('');
    }

    const path = req.path.replace(/^\/api\/mav-data\//, '');
    const [date, ...rest] = path.split('/');
    const file = rest.join('/');
    if (!date || !file) {
      return res.status(400).json({ error: 'Bad request' });
    }
    const gcsUrl = `https://storage.googleapis.com/mpt-all-sources/blog/mav/json_output/${date}/${file}`;
    const r = await fetch(gcsUrl);
    if (!r.ok) {
      return res.status(404).json({ error: 'Not found' });
    }
    const data = await r.json();
    return res.json(data);
  } catch (e) {
    console.error('mavProxy error', e);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

