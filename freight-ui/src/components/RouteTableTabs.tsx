import React from 'react';

interface RouteTableTabsProps {
  active: 'mode' | 'remarks';
  onChange: (tab: 'mode' | 'remarks') => void;
}

const RouteTableTabs: React.FC<RouteTableTabsProps> = ({ active, onChange }) => (
  <div className="route-table-tabs">
    <button
      className={active === 'mode' ? 'tab active' : 'tab'}
      onClick={() => onChange('mode')}
      type="button"
    >
      Transport Mode
    </button>
    <button
      className={active === 'remarks' ? 'tab active' : 'tab'}
      onClick={() => onChange('remarks')}
      type="button"
    >
      Remarks
    </button>
  </div>
);

export default RouteTableTabs;
