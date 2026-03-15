import React from 'react';
import { FilterState } from '../types';
import { useI18n } from '../i18n';

interface FiltersPanelProps {
  destinations: string[];
  containerTypes: string[];
  filters: FilterState;
  onFilterChange: (field: keyof FilterState, value: string) => void;
  onApply: () => void;
}

const FiltersPanel: React.FC<FiltersPanelProps> = ({
  destinations,
  containerTypes,
  filters,
  onFilterChange,
  onApply,
}) => {
  const { t } = useI18n();
  return (
    <div className="card filters-panel">
      <div className="card-body">
        <div className="filters-content">
          {/* Destination Filter */}
          <div className="filter-group">
            <label htmlFor="destination-select" className="filter-label">
              {t('destination')}
            </label>
            <select
              id="destination-select"
              value={filters.destination}
              onChange={(e) => onFilterChange('destination', e.target.value)}
            >
              {destinations.map((dest) => (
                <option key={dest} value={dest}>
                  {dest}
                </option>
              ))}
            </select>
          </div>

          {/* Container Type Filter */}
          <div className="filter-group">
            <label htmlFor="container-select" className="filter-label">
              {t('containerType')}
            </label>
            <select
              id="container-select"
              value={filters.containerType}
              onChange={(e) => onFilterChange('containerType', e.target.value)}
            >
              {containerTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Apply Button */}
          <div className="filter-actions">
            <button
              type="button"
              className="btn-primary"
              onClick={onApply}
              disabled={destinations.length === 0}
            >
              {t('apply')}
            </button>
          </div>

          {/* Data Source Indicator */}
          <div className="data-source">
            <span className="data-source-label">{t('source')}:</span>
            <span className="data-source-value">{t('sourceExcelApi')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FiltersPanel;
