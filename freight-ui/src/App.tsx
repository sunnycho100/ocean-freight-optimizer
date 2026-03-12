import React, { useState } from 'react';
import './styles/app.css';
import RouteDashboard from './components/RouteDashboard';
import HapagDashboard from './components/HapagDashboard';
import SummaryDashboard from './components/SummaryDashboard';
import ChatPanel from './components/ChatPanel';
import { testGoogleMapsUrl } from './utils/googleMapsHelper';
import { I18nProvider, useI18n } from './i18n';

type ViewMode = 'ONE' | 'HAPAG' | 'SUMMARY';

// Make test function available in browser console
if (typeof window !== 'undefined') {
  (window as any).testGoogleMapsUrl = testGoogleMapsUrl;
}

function AppContent() {
  const [viewMode, setViewMode] = useState<ViewMode>('ONE');
  const { t, toggleLang } = useI18n();

  return (
    <div className="app">
      <div className="app-header">
        <h1>{t('appTitle')}</h1>
        <div className="header-right">
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
              {t('summary')}
            </button>
          </div>
          <button className="lang-toggle" onClick={toggleLang}>
            {t('langToggle')}
          </button>
        </div>
      </div>
      <div className="app-container">
        {viewMode === 'ONE' && <RouteDashboard />}
        {viewMode === 'HAPAG' && <HapagDashboard />}
        {viewMode === 'SUMMARY' && <SummaryDashboard />}
      </div>
      <ChatPanel />
    </div>
  );
}

function App() {
  return (
    <I18nProvider>
      <AppContent />
    </I18nProvider>
  );
}

export default App;
