import React, { useState, useEffect, useMemo } from 'react';
import FiltersPanel from './FiltersPanel';
import RouteTable from './RouteTable';
import RouteTableTabs from './RouteTableTabs';
import RouteMap from './RouteMap';
import { FilterState, LaneData, Route } from '../types';
import { API_BASE } from '../config';

const RouteDashboard: React.FC = () => {
  const [destinations, setDestinations] = useState<string[]>([]);
  const [containerTypes, setContainerTypes] = useState<string[]>([]);
  const [laneData, setLaneData] = useState<LaneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<FilterState>({
    destination: '',
    containerType: '',
  });

  const [appliedFilters, setAppliedFilters] = useState<FilterState>(filters);

  // Fetch destinations and container types on mount
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setLoading(true);
        const [destRes, contRes] = await Promise.all([
          fetch(`${API_BASE}/destinations`),
          fetch(`${API_BASE}/container-types`),
        ]);

        if (!destRes.ok || !contRes.ok) {
          throw new Error('Failed to fetch filter options');
        }

        const destData = await destRes.json();
        const contData = await contRes.json();

        setDestinations(destData);
        setContainerTypes(contData);

        // Set default selections
        if (destData.length > 0 && contData.length > 0) {
          const defaultFilters = {
            destination: destData[0],
            containerType: contData[0],
          };
          setFilters(defaultFilters);
          setAppliedFilters(defaultFilters);
        }
      } catch (err) {
        setError('Failed to connect to API. Make sure the server is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []);

  // Fetch routes when applied filters change
  useEffect(() => {
    if (!appliedFilters.destination || !appliedFilters.containerType) return;

    const fetchRoutes = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/routes/${encodeURIComponent(appliedFilters.destination)}/${encodeURIComponent(appliedFilters.containerType)}`
        );

        if (!res.ok) {
          setLaneData(null);
          return;
        }

        const data = await res.json();
        setLaneData({
          destination: data.destination,
          containerType: data.containerType,
          currency: data.currency,
          routes: data.routes,
        });
      } catch (err) {
        console.error('Failed to fetch routes:', err);
        setLaneData(null);
      }
    };

    fetchRoutes();
  }, [appliedFilters]);

  const handleFilterChange = (field: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleApply = () => {
    setAppliedFilters(filters);
  };

  const topRoutes: Route[] = useMemo(() => {
    if (!laneData) return [];
    return laneData.routes.slice(0, 3);
  }, [laneData]);

  const worstRoute: Route | undefined = useMemo(() => {
    if (!laneData || laneData.routes.length === 0) return undefined;
    return laneData.routes[laneData.routes.length - 1];
  }, [laneData]);

  // Tab state: 'mode' or 'remarks'
  const [activeTab, setActiveTab] = useState<'mode' | 'remarks'>('mode');

  return (
    <>
      {/* Header */}
      <header className="header">
        <h1 className="header-title">ONE Route Optimizer</h1>
        <p className="header-subtitle">
          Busan (KR) → POD → Inland Destination
        </p>
      </header>

      {/* Filters */}
      <FiltersPanel
        destinations={destinations}
        containerTypes={containerTypes}
        filters={filters}
        onFilterChange={handleFilterChange}
        onApply={handleApply}
      />

      {/* Tab Switcher */}
      <RouteTableTabs active={activeTab} onChange={setActiveTab} />

      {/* Results */}
      <section className="results-section" aria-label="Route Results">
        {loading ? (
          <div className="card">
            <div className="empty-state">Loading...</div>
          </div>
        ) : error ? (
          <div className="card">
            <div className="empty-state error-state">{error}</div>
          </div>
        ) : laneData ? (
          <>
            <RouteTable
              title="Top 3 Recommended Routes"
              routes={topRoutes}
              currency={laneData.currency}
              variant="top"
              showRemarks={activeTab === 'remarks'}
            />

            <div className="card">
              <div className="card-header card-header--map-compare">
                <h2 className="card-title">Route Comparison on the Map</h2>
                <span className="map-compare-note">* map routes are for visualization purposes</span>
              </div>
              <div className="card-body">
                <div className="map-grid" aria-label="Top routes map comparison">
                  {topRoutes.map((route) => (
                    <RouteMap
                      key={route.rank}
                      pod={route.pod}
                      destination={laneData.destination}
                      rankLabel={`Rank ${route.rank} Route`}
                      variant="grid"
                    />
                  ))}
                </div>
              </div>
            </div>

            {worstRoute && (
              <RouteTable
                title="Highest Cost Route"
                routes={[worstRoute]}
                currency={laneData.currency}
                variant="worst"
                showRemarks={activeTab === 'remarks'}
              />
            )}
          </>
        ) : (
          <div className="card">
            <div className="empty-state">
              No route data available for the selected criteria.
            </div>
          </div>
        )}
      </section>
    </>
  );
};

export default RouteDashboard;
