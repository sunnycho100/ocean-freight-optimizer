import React from 'react';
import './styles/app.css';
import RouteDashboard from './components/RouteDashboard';
import { testGoogleMapsUrl } from './utils/googleMapsHelper';

// Make test function available in browser console
if (typeof window !== 'undefined') {
  (window as any).testGoogleMapsUrl = testGoogleMapsUrl;
}

function App() {
  return (
    <div className="app">
      <div className="app-container">
        <RouteDashboard />
      </div>
    </div>
  );
}

export default App;
