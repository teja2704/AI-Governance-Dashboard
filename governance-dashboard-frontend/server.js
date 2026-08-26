if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config();
}
const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files (html, css, js) from /public
app.use(express.static(path.join(__dirname, 'public')));

// Expose the backend URL to client-side JS at runtime,
// so it isn't hardcoded into api.js and can change per environment.
app.get('/config.js', (req, res) => {
  res.type('application/javascript');
  res.send(`window.API_BASE_URL = "${process.env.FASTAPI_BASE_URL}";`);
});

// Fallback: any unknown route serves login.html (simple SPA-ish behavior)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

app.listen(PORT, () => {
  console.log(`Frontend server running on http://localhost:${PORT}`);
});
