// API Configuration
// Determines API base URL based on environment
// Windows uses port 5000 (hardcoded in start.bat)
// Mac/Linux uses dynamic port detection starting from 4000

const getApiBase = (): string => {
  // Check if running in development mode
  if (process.env.NODE_ENV === 'development') {
    // First try to use REACT_APP_API_PORT if set by start script
    const apiPort = process.env.REACT_APP_API_PORT;
    if (apiPort) {
      return `http://localhost:${apiPort}/api`;
    }
    
    // Default: try common ports in order
    // This allows the app to work even if the env var isn't set
    // React will handle the actual connection, we just need a base URL
    return 'http://localhost:4000/api';
  }
  
  // Production build would use relative URLs or production API endpoint
  return '/api';
};

export const API_BASE = getApiBase();
