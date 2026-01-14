import React, { useState, useEffect } from 'react';
import { HapagLaneData, HapagChargeItem, HapagSubOption } from '../types';
import '../styles/hapag-dashboard.css';

const API_BASE = 'http://localhost:5000/api';

type ContainerType = '20STD' | '40STD' | '40HC';

const HapagDashboard: React.FC = () => {
  const [destinations, setDestinations] = useState<string[]>([]);
  const [selectedDestination, setSelectedDestination] = useState<string>('');
  const [selectedContainer, setSelectedContainer] = useState<ContainerType>('20STD');
  const [laneData, setLaneData] = useState<HapagLaneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // For Destination Landfreight sub-options
  const [selectedLandfreightOption, setSelectedLandfreightOption] = useState<number>(0);
  
  // For More Details expandable section
  const [isDetailsExpanded, setIsDetailsExpanded] = useState(false);

  // Fetch destinations on mount
  useEffect(() => {
    const fetchDestinations = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/hapag/destinations`);
        
        if (!res.ok) {
          throw new Error('Failed to fetch destinations');
        }

        const data = await res.json();
        setDestinations(data);

        if (data.length > 0) {
          setSelectedDestination(data[0]);
        }
      } catch (err) {
        setError('Failed to connect to API. Make sure the server is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDestinations();
  }, []);

  // Fetch route data when destination changes
  useEffect(() => {
    if (!selectedDestination) return;

    const fetchRoute = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/hapag/route/${encodeURIComponent(selectedDestination)}`
        );

        if (!res.ok) {
          setLaneData(null);
          return;
        }

        const data = await res.json();
        setLaneData(data);
        
        // Reset to first available container type
        const available = data.route.availableContainers;
        if (!available[selectedContainer]) {
          if (available['20STD']) setSelectedContainer('20STD');
          else if (available['40STD']) setSelectedContainer('40STD');
          else if (available['40HC']) setSelectedContainer('40HC');
        }
        
        // Reset landfreight option selection to 0
        setSelectedLandfreightOption(0);
      } catch (err) {
        console.error('Failed to fetch route:', err);
        setLaneData(null);
      }
    };

    fetchRoute();
  }, [selectedDestination]);

  // Reset landfreight option when container type changes
  useEffect(() => {
    setSelectedLandfreightOption(0);
  }, [selectedContainer]);

  const getValue = (item: HapagChargeItem | undefined, container: ContainerType): string => {
    if (!item) return '-';
    const val = container === '20STD' ? item.value20STD :
                container === '40STD' ? item.value40STD :
                item.value40HC;
    return val && val !== '-' && val !== '' ? val : '-';
  };

  const getSubOptionValue = (option: HapagSubOption, container: ContainerType): string => {
    const val = container === '20STD' ? option.value20 :
                container === '40STD' ? option.value40 :
                option.value40HC;
    return val && val !== '-' && val !== '' ? val : '-';
  };

  // Filter sub-options to only include those with valid numeric values for selected container
  const getValidSubOptions = (subOptions: HapagSubOption[] | undefined): HapagSubOption[] => {
    if (!subOptions) return [];
    return subOptions.filter(opt => {
      const val = getSubOptionValue(opt, selectedContainer);
      return val !== '-' && val !== '';
    });
  };

  const calculateTotal = (): number => {
    if (!laneData) return 0;
    
    let totalEUR = 0;
    const route = laneData.route;
    const USD_TO_EUR = 0.86;
    
    // Ocean Freight
    const oceanVal = getValue(route.oceanFreight, selectedContainer);
    if (oceanVal !== '-' && route.oceanFreight) {
      const amount = parseFloat(oceanVal.replace(/,/g, '')) || 0;
      // Convert to EUR if currency is USD
      if (route.oceanFreight.curr === 'USD') {
        totalEUR += amount * USD_TO_EUR;
      } else {
        totalEUR += amount;
      }
    }
    
    // Destination Landfreight
    if (route.destinationLandfreight?.subOptions && route.destinationLandfreight.subOptions.length > 0) {
      const validOptions = getValidSubOptions(route.destinationLandfreight.subOptions);
      if (validOptions.length > 0) {
        const safeIndex = selectedLandfreightOption >= validOptions.length ? 0 : selectedLandfreightOption;
        const option = validOptions[safeIndex];
        const landVal = getSubOptionValue(option, selectedContainer);
        if (landVal !== '-') {
          const amount = parseFloat(landVal.replace(/,/g, '')) || 0;
          // Convert to EUR if currency is USD
          if (route.destinationLandfreight.curr === 'USD') {
            totalEUR += amount * USD_TO_EUR;
          } else {
            totalEUR += amount;
          }
        }
      }
    } else if (route.destinationLandfreight) {
      const landVal = getValue(route.destinationLandfreight, selectedContainer);
      if (landVal !== '-') {
        const amount = parseFloat(landVal.replace(/,/g, '')) || 0;
        // Convert to EUR if currency is USD
        if (route.destinationLandfreight.curr === 'USD') {
          totalEUR += amount * USD_TO_EUR;
        } else {
          totalEUR += amount;
        }
      }
    }
    
    return totalEUR;
  };

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="empty-state error-state">{error}</div>
      </div>
    );
  }

  if (!laneData) {
    return (
      <div className="card">
        <div className="empty-state">Select a destination to view routes</div>
      </div>
    );
  }

  const route = laneData.route;
  const available = route.availableContainers;

  return (
    <>
      {/* Header */}
      <header className="header">
        <h1 className="header-title">HAPAG-LLOYD Route Analyzer</h1>
        <p className="header-subtitle">
          {route.from} → {route.via} → {route.to}
        </p>
      </header>

      {/* Filters Panel */}
      <div className="card filters-panel">
        <div className="card-body">
          <div className="filters-content">
            <div className="filter-group">
              <label className="filter-label">Destination</label>
              <select
                value={selectedDestination}
                onChange={(e) => setSelectedDestination(e.target.value)}
              >
                {destinations.map((dest) => (
                  <option key={dest} value={dest}>{dest}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Container Type Tabs */}
      <div className="hapag-container-tabs">
        <button
          className={`hapag-tab ${selectedContainer === '20STD' ? 'active' : ''} ${!available['20STD'] ? 'disabled' : ''}`}
          onClick={() => available['20STD'] && setSelectedContainer('20STD')}
          disabled={!available['20STD']}
        >
          20' STD
        </button>
        <button
          className={`hapag-tab ${selectedContainer === '40STD' ? 'active' : ''} ${!available['40STD'] ? 'disabled' : ''}`}
          onClick={() => available['40STD'] && setSelectedContainer('40STD')}
          disabled={!available['40STD']}
        >
          40' STD
        </button>
        <button
          className={`hapag-tab ${selectedContainer === '40HC' ? 'active' : ''} ${!available['40HC'] ? 'disabled' : ''}`}
          onClick={() => available['40HC'] && setSelectedContainer('40HC')}
          disabled={!available['40HC']}
        >
          40' HC
        </button>
      </div>

      {/* Summary Table */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Rate Summary</h2>
        </div>
        <div className="card-body">
          <div className="route-table-container">
            <table className="route-table">
              <thead>
                <tr>
                  <th>Charge Type</th>
                  <th>Description</th>
                  <th style={{ textAlign: 'right' }}>Rate</th>
                </tr>
              </thead>
              <tbody>
                {/* Ocean Freight */}
                {route.oceanFreight && (
                  <tr>
                    <td>Ocean Freight</td>
                    <td>
                      {route.oceanFreight.description}
                      {route.oceanFreight.curr === 'USD' && (
                        <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic', marginTop: '4px' }}>
                          *conversion rate 0.86
                        </div>
                      )}
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>
                      {route.oceanFreight.curr} {getValue(route.oceanFreight, selectedContainer)}
                    </td>
                  </tr>
                )}
                
                {/* Destination Landfreight */}
                {route.destinationLandfreight && (
                  <>
                    {(() => {
                      const validOptions = getValidSubOptions(route.destinationLandfreight.subOptions);
                      
                      if (validOptions.length > 0) {
                        // Ensure selectedLandfreightOption is within bounds
                        const safeIndex = selectedLandfreightOption >= validOptions.length ? 0 : selectedLandfreightOption;
                        
                        return (
                          <tr>
                            <td>Destination Landfreight</td>
                            <td>
                              <select
                                value={safeIndex}
                                onChange={(e) => setSelectedLandfreightOption(parseInt(e.target.value))}
                                style={{ 
                                  padding: '6px 10px', 
                                  borderRadius: '4px', 
                                  border: '1px solid #D8DEE3',
                                  fontSize: '14px',
                                  background: 'white'
                                }}
                              >
                                {validOptions.map((opt, idx) => (
                                  <option key={idx} value={idx}>{opt.description}</option>
                                ))}
                              </select>
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>
                              {route.destinationLandfreight.curr} {getSubOptionValue(validOptions[safeIndex], selectedContainer)}
                            </td>
                          </tr>
                        );
                      } else {
                        // No sub-options or all filtered out, check main item
                        const mainVal = getValue(route.destinationLandfreight, selectedContainer);
                        if (mainVal !== '-') {
                          return (
                            <tr>
                              <td>Destination Landfreight</td>
                              <td>{route.destinationLandfreight.description}</td>
                              <td style={{ textAlign: 'right', fontWeight: 600 }}>
                                {route.destinationLandfreight.curr} {mainVal}
                              </td>
                            </tr>
                          );
                        }
                        return null;
                      }
                    })()}
                  </>
                )}

                {/* Total Rate */}
                <tr style={{ borderTop: '2px solid var(--color-primary)', backgroundColor: 'var(--color-primary-lighter)' }}>
                  <td><strong>Total Rate</strong></td>
                  <td></td>
                  <td style={{ textAlign: 'right', fontWeight: 700, fontSize: '18px', color: 'var(--color-primary)' }}>
                    EUR {calculateTotal().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* More Details (Collapsible) */}
      <div className="card">
        <div 
          className="card-header hapag-details-header"
          onClick={() => setIsDetailsExpanded(!isDetailsExpanded)}
          style={{ cursor: 'pointer' }}
        >
          <h2 className="card-title">
            More Details {isDetailsExpanded ? '▼' : '▶'}
          </h2>
        </div>
        {isDetailsExpanded && (
          <div className="card-body">
            <div className="route-table-container">
              <table className="route-table">
                <thead>
                  <tr>
                    <th>Charge Category</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Destination Landfreight */}
                  {route.destinationLandfreight && (
                    <>
                      {route.destinationLandfreight.subOptions && route.destinationLandfreight.subOptions.length > 0 ? (
                        <>
                          <tr>
                            <td colSpan={3} style={{ paddingTop: '20px', paddingBottom: '10px' }}>
                              <strong>Destination Landfreight</strong>
                              <div style={{ marginTop: '10px' }}>
                                <select
                                  value={selectedLandfreightOption}
                                  onChange={(e) => setSelectedLandfreightOption(parseInt(e.target.value))}
                                  style={{ padding: '8px', borderRadius: '4px', border: '1px solid #D8DEE3' }}
                                >
                                  {route.destinationLandfreight.subOptions.map((opt, idx) => (
                                    <option key={idx} value={idx}>{opt.description}</option>
                                  ))}
                                </select>
                              </div>
                            </td>
                          </tr>
                          <tr>
                            <td>Destination Landfreight</td>
                            <td>{route.destinationLandfreight.subOptions[selectedLandfreightOption].description}</td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>
                              {route.destinationLandfreight.curr} {getSubOptionValue(route.destinationLandfreight.subOptions[selectedLandfreightOption], selectedContainer)}
                            </td>
                          </tr>
                        </>
                      ) : (
                        <tr>
                          <td>Destination Landfreight</td>
                          <td>{route.destinationLandfreight.description}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600 }}>
                            {route.destinationLandfreight.curr} {getValue(route.destinationLandfreight, selectedContainer)}
                          </td>
                        </tr>
                      )}
                    </>
                  )}

                  {/* Other Charges (excluding Terminal Handling Charge Dest which is already in summary) */}
                  {route.otherCharges
                    .filter(c => !c.description.toLowerCase().includes('terminal handling charge dest'))
                    .map((charge, idx) => (
                      <tr key={idx}>
                        <td>Other Charges</td>
                        <td>{charge.description}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>
                          {charge.curr} {getValue(charge, selectedContainer)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default HapagDashboard;
