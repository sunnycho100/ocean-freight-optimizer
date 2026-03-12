import React from 'react';
import { useI18n } from '../i18n';

interface RouteTableTabsProps {
  active: 'mode' | 'remarks';
  onChange: (tab: 'mode' | 'remarks') => void;
}

const RouteTableTabs: React.FC<RouteTableTabsProps> = ({ active, onChange }) => {
  const { t } = useI18n();
  return (
    <div className="route-table-tabs">
      <button
        className={active === 'mode' ? 'tab active' : 'tab'}
        onClick={() => onChange('mode')}
        type="button"
      >
        {t('transportMode')}
      </button>
      <button
        className={active === 'remarks' ? 'tab active' : 'tab'}
        onClick={() => onChange('remarks')}
        type="button"
      >
        {t('remarks')}
      </button>
    </div>
  );
};

export default RouteTableTabs;
