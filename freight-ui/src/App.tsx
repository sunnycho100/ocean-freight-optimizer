import React, { useState } from 'react';
import './styles/app.css';
import RouteDashboard from './components/RouteDashboard';
import HapagDashboard from './components/HapagDashboard';
import SummaryDashboard from './components/SummaryDashboard';
import { testGoogleMapsUrl } from './utils/googleMapsHelper';

type ViewMode = 'ONE' | 'HAPAG' | 'SUMMARY';

// Make test function available in browser console
if (typeof window !== 'undefined') {
  (window as any).testGoogleMapsUrl = testGoogleMapsUrl;
}

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('ONE');

  return (
    <div className="app">
      <div className="app-header">
        <h1>Freight Route Analyzer</h1>
        <div className="view-selector">
          <button
            className={`view-btn ${viewMode === 'ONE' ? 'active' : ''}`}
            onClick={() => setViewMode('ONE')}
          >
            ONE
          </button>
          <button
            className={`view-btn ${viewMode === 'HAPAG' ? 'active' : ''}`}
            onClick={() => setViewMode('HAPAG')}
          >
            HAPAG
          </button>
          <button
            className={`view-btn summary-btn ${viewMode === 'SUMMARY' ? 'active' : ''}`}
            onClick={() => setViewMode('SUMMARY')}
          >
            Summary
          </button>
        </div>
      </div>
      <div className="app-container">
        {viewMode === 'ONE' && <RouteDashboard />}
        {viewMode === 'HAPAG' && <HapagDashboard />}
        {viewMode === 'SUMMARY' && <SummaryDashboard />}
      </div>
    </div>
  );
}

export default App;
