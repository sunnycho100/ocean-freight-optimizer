import React, { useState } from 'react';
import './styles/app.css';
import RouteDashboard from './components/RouteDashboard';
import HapagDashboard from './components/HapagDashboard';
import { testGoogleMapsUrl } from './utils/googleMapsHelper';
import { ShippingProvider } from './types';

// Make test function available in browser console
if (typeof window !== 'undefined') {
  (window as any).testGoogleMapsUrl = testGoogleMapsUrl;
}

function App() {
  const [provider, setProvider] = useState<ShippingProvider>('ONE');

  return (
    <div className="app">
      <div className="app-header">
        <h1>Freight Route Analyzer</h1>
        <div className="provider-selector">
          <label htmlFor="provider-select">Provider:</label>
          <select
            id="provider-select"
            value={provider}
            onChange={(e) => setProvider(e.target.value as ShippingProvider)}
            className="provider-dropdown"
          >
            <option value="ONE">ONE</option>
            <option value="HAPAG">HAPAG-LLOYD</option>
          </select>
        </div>
      </div>
      <div className="app-container">
        {provider === 'ONE' ? <RouteDashboard /> : <HapagDashboard />}
      </div>
    </div>
  );
}

export default App;
