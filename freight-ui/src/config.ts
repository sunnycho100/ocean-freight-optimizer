// API Configuration
// In development, the "proxy" field in package.json forwards /api requests
// to the Flask server (http://localhost:4000), so we always use relative paths.
// In production builds, the same relative path works when served behind a
// reverse proxy or from the same origin.

export const API_BASE = '/api';
