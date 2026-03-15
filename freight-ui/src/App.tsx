import React, { useState } from 'react';
import './styles/app.css';
import './styles/automation-panel.css';
import RouteDashboard from './components/RouteDashboard';
import HapagDashboard from './components/HapagDashboard';
import SummaryDashboard from './components/SummaryDashboard';
import ChatPanel from './components/ChatPanel';
import AutomationPanel from './components/AutomationPanel';
import { testGoogleMapsUrl } from './utils/googleMapsHelper';
import { I18nProvider, useI18n } from './i18n';

type ViewMode = 'ONE' | 'HAPAG' | 'SUMMARY';

// Make test function available in browser console
if (typeof window !== 'undefined') {
  (window as any).testGoogleMapsUrl = testGoogleMapsUrl;
}

function AppContent() {
  const [viewMode, setViewMode] = useState<ViewMode>('ONE');
  const [showAutomation, setShowAutomation] = useState<boolean>(true);
  const [oneWorkflowReady, setOneWorkflowReady] = useState<boolean>(false);
  const [hapagWorkflowReady, setHapagWorkflowReady] = useState<boolean>(false);
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
        <div style={{ marginBottom: '12px' }}>
          <button
            className="view-btn"
            onClick={() => setShowAutomation((prev) => !prev)}
          >
            {showAutomation ? t('hideAutomationControl') : t('showAutomationControl')}
          </button>
        </div>
        {showAutomation && (
          <AutomationPanel
            onWorkflowComplete={(jobType, success) => {
              if (!success) return;
              if (jobType === 'one_pipeline') setOneWorkflowReady(true);
              if (jobType === 'hapag_pipeline') setHapagWorkflowReady(true);
            }}
          />
        )}
        {viewMode === 'ONE' && (
          oneWorkflowReady ? (
            <RouteDashboard />
          ) : (
            <div className="card">
              <div className="empty-state">
                {t('oneWorkflowReadyHint')}
              </div>
            </div>
          )
        )}
        {viewMode === 'HAPAG' && (
          hapagWorkflowReady ? (
            <HapagDashboard />
          ) : (
            <div className="card">
              <div className="empty-state">
                {t('hapagWorkflowReadyHint')}
              </div>
            </div>
          )
        )}
        {viewMode === 'SUMMARY' && (
          oneWorkflowReady || hapagWorkflowReady ? (
            <SummaryDashboard />
          ) : (
            <div className="card">
              <div className="empty-state">
                {t('summaryWorkflowReadyHint')}
              </div>
            </div>
          )
        )}
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
