// API Configuration
// In development, the "proxy" field in package.json forwards /api requests
// to the Flask server (http://localhost:4000), so we always use relative paths.
// In production builds, the same relative path works when served behind a
// reverse proxy or from the same origin.

function getDesktopApiBase(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    const params = new URLSearchParams(window.location.search);
    const portRaw = params.get('apiPort');
    if (!portRaw) return null;

    const port = Number(portRaw);
    if (!Number.isInteger(port) || port <= 0) return null;

    return `http://127.0.0.1:${port}/api`;
  } catch {
    return null;
  }
}

export const API_BASE = getDesktopApiBase() || '/api';
