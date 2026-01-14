import React from 'react';
import { FilterState } from '../types';

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
  return (
    <div className="card filters-panel">
      <div className="card-body">
        <div className="filters-content">
          {/* Destination Filter */}
          <div className="filter-group">
            <label htmlFor="destination-select" className="filter-label">
              Destination
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
              Container Type
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
              Apply
            </button>
          </div>

          {/* Data Source Indicator */}
          <div className="data-source">
            <span className="data-source-label">Source:</span>
            <span className="data-source-value">Excel (API)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FiltersPanel;
