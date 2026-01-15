import React, { useState, useEffect } from 'react';
import { LaneData, HapagLaneData } from '../types';

import { API_BASE } from '../config';

interface DestinationOption {
  destination: string;
  displayName: string;
}

interface DestinationMapping {
  displayName: string;
  oneDestination: string | null;
  hapagDestination: string | null;
}

const SummaryDashboard: React.FC = () => {
  const [destinationMappings, setDestinationMappings] = useState<DestinationMapping[]>([]);
  const [selectedMapping, setSelectedMapping] = useState<DestinationMapping | null>(null);
  const [oneContainerType, setOneContainerType] = useState<string>('40 FT High Cube Dry');
  const [hapagContainerType, setHapagContainerType] = useState<'20STD' | '40STD' | '40HC'>('40STD');
  
  const [oneData, setOneData] = useState<LaneData | null>(null);
  const [hapagData, setHapagData] = useState<HapagLaneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const USD_TO_EUR = 0.86;

  // Helper to convert between ONE and HAPAG container types
  const oneToHapag = (oneType: string): '20STD' | '40STD' | '40HC' => {
    const map: Record<string, '20STD' | '40STD' | '40HC'> = {
      '20 FT Dry': '20STD',
      '40 FT Dry': '40STD',
      '40 FT High Cube Dry': '40HC',
    };
    return map[oneType] || '40STD';
  };

  const hapagToOne = (hapagType: '20STD' | '40STD' | '40HC'): string => {
    const map: Record<string, string> = {
      '20STD': '20 FT Dry',
      '40STD': '40 FT Dry',
      '40HC': '40 FT High Cube Dry',
    };
    return map[hapagType] || '40 FT High Cube Dry';
  };

  // Helper to fetch with timeout
  const fetchWithTimeout = async (url: string, timeout = 3000): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  };

  // Helper to get short container type display
  const getContainerShortName = (containerType: string): string => {
    const map: Record<string, string> = {
      '20 FT Dry': '20 FT',
      '40 FT Dry': '40 FT',
      '40 FT High Cube Dry': '40 HC',
    };
    return map[containerType] || containerType;
  };

  // Helper to extract city name from destination string
  const extractCityName = (destination: string): string => {
    // For ONE format: "OEGSTGEEST, NETHERLANDS" -> "OEGSTGEEST"
    // For HAPAG format: "OEGSTGEEST" -> "OEGSTGEEST"
    // Also handles: "VALENCE, DROME, FRANCE" -> "VALENCE"
    return destination.split(',')[0].trim();
  };

  // Helper to normalize city name for matching
  const normalizeCityName = (cityName: string): string => {
    return cityName
      .replace(/\s+/g, ' ')  // Normalize spaces
      .replace(/\/.*$/, '')  // Remove suffix like "/DROME"
      .replace(/\s*B\.|\s*I\.|\s*IM\s+/, ' ')  // Normalize German abbreviations
      .replace(/-/g, ' ')  // Remove hyphens (e.g., "ARQUES-LA-BATAILLE" -> "ARQUES LA BATAILLE")
      .replace(/\s+/g, ' ')  // Normalize spaces again after hyphen removal
      .trim()
      .toUpperCase();
  };

  // Create destination mappings
  const createDestinationMappings = (oneDests: string[], hapagDests: string[]): DestinationMapping[] => {
    const mappings: DestinationMapping[] = [];
    const used = new Set<string>();

    // Match ONE destinations to HAPAG
    oneDests.forEach(oneDest => {
      const oneCity = normalizeCityName(extractCityName(oneDest));
      let matchedHapag: string | null = null;

      for (const hapagDest of hapagDests) {
        const hapagCity = normalizeCityName(extractCityName(hapagDest));
        if (oneCity === hapagCity || oneCity.includes(hapagCity) || hapagCity.includes(oneCity)) {
          matchedHapag = hapagDest;
          used.add(hapagDest);
          break;
        }
      }

      mappings.push({
        displayName: extractCityName(oneDest),
        oneDestination: oneDest,
        hapagDestination: matchedHapag,
      });
    });

    // Add remaining HAPAG destinations that didn't match
    hapagDests.forEach(hapagDest => {
      if (!used.has(hapagDest)) {
        mappings.push({
          displayName: extractCityName(hapagDest),
          oneDestination: null,
          hapagDestination: hapagDest,
        });
      }
    });

    return mappings.sort((a, b) => a.displayName.localeCompare(b.displayName));
  };

  // Fetch destinations
  useEffect(() => {
    const fetchDestinations = async () => {
      try {
        setLoading(true);
        const [oneRes, hapagRes] = await Promise.allSettled([
          fetchWithTimeout(`${API_BASE}/destinations`, 3000),
          fetchWithTimeout(`${API_BASE}/hapag/destinations`, 3000),
        ]);

        let oneDest: string[] = [];
        let hapagDest: string[] = [];

        if (oneRes.status === 'fulfilled' && oneRes.value.ok) {
          oneDest = await oneRes.value.json();
        } else {
          console.warn('Failed to fetch ONE destinations');
        }

        if (hapagRes.status === 'fulfilled' && hapagRes.value.ok) {
          hapagDest = await hapagRes.value.json();
        } else {
          console.warn('Failed to fetch HAPAG destinations');
        }

        // Create mappings between ONE and HAPAG destinations
        const mappings = createDestinationMappings(oneDest, hapagDest);
        setDestinationMappings(mappings);
        if (mappings.length > 0) {
          setSelectedMapping(mappings[0]);
        }

        // If both failed, show error
        if (oneRes.status === 'rejected' && hapagRes.status === 'rejected') {
          setError('Failed to fetch destinations. Please ensure the API server is running.');
        }
      } catch (err) {
        console.error('Error fetching destinations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDestinations();
  }, []);

  // Fetch ONE data
  useEffect(() => {
    if (!selectedMapping?.oneDestination || !oneContainerType) {
      setOneData(null);
      return;
    }

    const fetchOneData = async () => {
      try {
        const res = await fetchWithTimeout(
          `${API_BASE}/routes/${encodeURIComponent(selectedMapping.oneDestination!)}/${encodeURIComponent(oneContainerType)}`,
          3000
        );

        if (res.ok) {
          const data = await res.json();
          setOneData(data);
        } else {
          console.warn('No ONE routes found for selected criteria');
          setOneData(null);
        }
      } catch (err) {
        console.error('Failed to fetch ONE data:', err);
        setOneData(null);
      }
    };

    fetchOneData();
  }, [selectedMapping, oneContainerType]);

  // Fetch HAPAG data
  useEffect(() => {
    if (!selectedMapping?.hapagDestination) {
      setHapagData(null);
      return;
    }

    const fetchHapagData = async () => {
      try {
        const res = await fetchWithTimeout(
          `${API_BASE}/hapag/route/${encodeURIComponent(selectedMapping.hapagDestination!)}`,
          3000
        );

        if (res.ok) {
          const data = await res.json();
          setHapagData(data);
        } else {
          console.warn('No HAPAG routes found for selected destination');
          setHapagData(null);
        }
      } catch (err) {
        console.error('Failed to fetch HAPAG data:', err);
        setHapagData(null);
      }
    };

    fetchHapagData();
  }, [selectedMapping]);

  // Calculate HAPAG total in EUR
  const calculateHapagTotal = (): number => {
    if (!hapagData) return 0;
    
    let totalEUR = 0;
    const route = hapagData.route;
    
    // Ocean Freight
    if (route.oceanFreight) {
      const val = hapagContainerType === '20STD' ? route.oceanFreight.value20STD :
                  hapagContainerType === '40STD' ? route.oceanFreight.value40STD :
                  route.oceanFreight.value40HC;
      if (val && val !== '-') {
        const amount = parseFloat(val.replace(/,/g, '')) || 0;
        if (route.oceanFreight.curr === 'USD') {
          totalEUR += amount * USD_TO_EUR;
        } else {
          totalEUR += amount;
        }
      }
    }
    
    // Destination Landfreight (use first valid option or main value)
    if (route.destinationLandfreight) {
      let landVal = '';
      let curr = route.destinationLandfreight.curr;
      
      if (route.destinationLandfreight.subOptions && route.destinationLandfreight.subOptions.length > 0) {
        // Find first valid sub-option
        const validOption = route.destinationLandfreight.subOptions.find(opt => {
          const v = hapagContainerType === '20STD' ? opt.value20 :
                    hapagContainerType === '40STD' ? opt.value40 :
                    opt.value40HC;
          return v && v !== '-';
        });
        if (validOption) {
          landVal = hapagContainerType === '20STD' ? validOption.value20 :
                    hapagContainerType === '40STD' ? validOption.value40 :
                    validOption.value40HC;
        }
      } else {
        landVal = hapagContainerType === '20STD' ? route.destinationLandfreight.value20STD :
                  hapagContainerType === '40STD' ? route.destinationLandfreight.value40STD :
                  route.destinationLandfreight.value40HC;
      }
      
      if (landVal && landVal !== '-') {
        const amount = parseFloat(landVal.replace(/,/g, '')) || 0;
        if (curr === 'USD') {
          totalEUR += amount * USD_TO_EUR;
        } else {
          totalEUR += amount;
        }
      }
    }
    
    return totalEUR;
  };

  // Get top 3 ONE routes
  const getTopThreeONE = () => {
    if (!oneData || !oneData.routes) return [];
    return oneData.routes.slice(0, 3);
  };

  // Calculate ONE route total in EUR
  const calculateONETotal = (route: any): number => {
    const inland = route.inlandRate || 0;
    const ocean = route.oceanRate || 0;
    return inland + ocean;
  };

  const topThreeONE = getTopThreeONE();
  const hapagTotal = calculateHapagTotal();
  const lowestONETotal = topThreeONE.length > 0 ? calculateONETotal(topThreeONE[0]) : Infinity;
  
  const winner = lowestONETotal < hapagTotal ? 'ONE' : 'HAPAG-Lloyd';
  const winnerRoute = winner === 'ONE' && topThreeONE.length > 0 
    ? `via ${topThreeONE[0].pod}` 
    : hapagData ? `via ${hapagData.route.via}` : '';

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

  return (
    <>
      {/* Header */}
      <header className="header">
        <h1 className="header-title">Rate Comparison Summary</h1>
        <p className="header-subtitle">
          Comparing ONE vs HAPAG-LLOYD Routes
        </p>
      </header>

      {/* Destination Selectors */}
      <div className="card filters-panel">
        <div className="card-body">
          <div className="filters-content">
            <div className="filter-group">
              <label className="filter-label">Destination</label>
              <select
                value={selectedMapping?.displayName || ''}
                onChange={(e) => {
                  const mapping = destinationMappings.find(m => m.displayName === e.target.value);
                  if (mapping) setSelectedMapping(mapping);
                }}
              >
                {destinationMappings.map((mapping) => (
                  <option key={mapping.displayName} value={mapping.displayName}>
                    {mapping.displayName}
                    {!mapping.oneDestination && ' (HAPAG only)'}
                    {!mapping.hapagDestination && ' (ONE only)'}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <label className="filter-label">Container Type</label>
              <select
                value={oneContainerType}
                onChange={(e) => {
                  setOneContainerType(e.target.value);
                  setHapagContainerType(oneToHapag(e.target.value));
                }}
              >
                <option value="20 FT Dry">20 FT</option>
                <option value="40 FT Dry">40 FT</option>
                <option value="40 FT High Cube Dry">40 HC</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Winner Banner */}
      <div className="card" style={{ backgroundColor: 'var(--color-primary-lighter)', borderLeft: '4px solid var(--color-primary)' }}>
        <div className="card-body">
          <div style={{ textAlign: 'left' }}>
            <h2 style={{ color: 'var(--color-primary)', fontSize: '20px', margin: '0 0 4px 0', fontWeight: 600 }}>
              Best Rate: {winner} {winnerRoute && <span style={{ fontWeight: 400, fontSize: '16px' }}>({winnerRoute})</span>}
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '16px', margin: 0, fontWeight: 600 }}>
              EUR {winner === 'ONE' 
                ? lowestONETotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : hapagTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
              }
            </p>
          </div>
        </div>
      </div>

      {/* ONE Routes */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">ONE - Top 3 Routes ({getContainerShortName(oneContainerType)})</h2>
        </div>
        <div className="card-body">
          {topThreeONE.length > 0 ? (
            <div className="route-table-container">
              <table className="route-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>POD (Intermediate Port)</th>
                    <th>Transport Mode</th>
                    <th style={{ textAlign: 'right' }}>Inland (EUR)</th>
                    <th style={{ textAlign: 'right' }}>Ocean (EUR)</th>
                    <th style={{ textAlign: 'right' }}>Total (EUR)</th>
                  </tr>
                </thead>
                <tbody>
                  {topThreeONE.map((route, idx) => (
                    <tr key={idx}>
                      <td className="col-rank">
                        <span className="rank-badge rank-badge--top">{idx + 1}</span>
                      </td>
                      <td>{route.pod}</td>
                      <td>{route.mode}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {(route.inlandRate || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {(route.oceanRate || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-primary)' }}>
                        {route.totalRate.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No ONE routes available</div>
          )}
        </div>
      </div>

      {/* HAPAG Route */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            HAPAG-Lloyd - {selectedMapping?.displayName || 'N/A'} ({hapagContainerType})
            {hapagData && <span style={{ fontWeight: 400, fontSize: '14px' }}> via {hapagData.route.via}</span>}
          </h2>
        </div>
        <div className="card-body">
          {hapagData ? (
            <div className="route-table-container">
              <table className="route-table">
                <thead>
                  <tr>
                    <th>Route</th>
                    <th>Charge Type</th>
                    <th style={{ textAlign: 'right' }}>Rate</th>
                    <th style={{ textAlign: 'right' }}>EUR Equivalent</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Ocean Freight */}
                  {hapagData.route.oceanFreight && (
                    <tr>
                      <td>{hapagData.route.from} → {hapagData.route.via} → {hapagData.route.to}</td>
                      <td>Ocean Freight</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {hapagData.route.oceanFreight.curr}{' '}
                        {hapagContainerType === '20STD' ? hapagData.route.oceanFreight.value20STD :
                         hapagContainerType === '40STD' ? hapagData.route.oceanFreight.value40STD :
                         hapagData.route.oceanFreight.value40HC}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {(() => {
                          const val = hapagContainerType === '20STD' ? hapagData.route.oceanFreight.value20STD :
                                      hapagContainerType === '40STD' ? hapagData.route.oceanFreight.value40STD :
                                      hapagData.route.oceanFreight.value40HC;
                          if (val && val !== '-') {
                            const amount = parseFloat(val.replace(/,/g, '')) || 0;
                            const eurAmount = hapagData.route.oceanFreight.curr === 'USD' ? amount * USD_TO_EUR : amount;
                            return eurAmount.toLocaleString(undefined, { minimumFractionDigits: 2 });
                          }
                          return '-';
                        })()}
                      </td>
                    </tr>
                  )}
                  
                  {/* Destination Landfreight */}
                  {hapagData.route.destinationLandfreight && (
                    <tr>
                      <td></td>
                      <td>Destination Landfreight</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {hapagData.route.destinationLandfreight.curr}{' '}
                        {(() => {
                          if (hapagData.route.destinationLandfreight.subOptions && hapagData.route.destinationLandfreight.subOptions.length > 0) {
                            const validOpt = hapagData.route.destinationLandfreight.subOptions.find(opt => {
                              const v = hapagContainerType === '20STD' ? opt.value20 :
                                        hapagContainerType === '40STD' ? opt.value40 :
                                        opt.value40HC;
                              return v && v !== '-';
                            });
                            if (validOpt) {
                              return hapagContainerType === '20STD' ? validOpt.value20 :
                                     hapagContainerType === '40STD' ? validOpt.value40 :
                                     validOpt.value40HC;
                            }
                            return '-';
                          }
                          return hapagContainerType === '20STD' ? hapagData.route.destinationLandfreight.value20STD :
                                 hapagContainerType === '40STD' ? hapagData.route.destinationLandfreight.value40STD :
                                 hapagData.route.destinationLandfreight.value40HC;
                        })()}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {(() => {
                          let val = '';
                          if (hapagData.route.destinationLandfreight.subOptions && hapagData.route.destinationLandfreight.subOptions.length > 0) {
                            const validOpt = hapagData.route.destinationLandfreight.subOptions.find(opt => {
                              const v = hapagContainerType === '20STD' ? opt.value20 :
                                        hapagContainerType === '40STD' ? opt.value40 :
                                        opt.value40HC;
                              return v && v !== '-';
                            });
                            if (validOpt) {
                              val = hapagContainerType === '20STD' ? validOpt.value20 :
                                    hapagContainerType === '40STD' ? validOpt.value40 :
                                    validOpt.value40HC;
                            }
                          } else {
                            val = hapagContainerType === '20STD' ? hapagData.route.destinationLandfreight.value20STD :
                                  hapagContainerType === '40STD' ? hapagData.route.destinationLandfreight.value40STD :
                                  hapagData.route.destinationLandfreight.value40HC;
                          }
                          
                          if (val && val !== '-') {
                            const amount = parseFloat(val.replace(/,/g, '')) || 0;
                            const eurAmount = hapagData.route.destinationLandfreight.curr === 'USD' ? amount * USD_TO_EUR : amount;
                            return eurAmount.toLocaleString(undefined, { minimumFractionDigits: 2 });
                          }
                          return '-';
                        })()}
                      </td>
                    </tr>
                  )}
                  
                  {/* Total */}
                  <tr style={{ borderTop: '2px solid var(--color-primary)', backgroundColor: 'var(--color-primary-lighter)' }}>
                    <td></td>
                    <td><strong>Total Rate</strong></td>
                    <td></td>
                    <td style={{ textAlign: 'right', fontWeight: 700, fontSize: '18px', color: 'var(--color-primary)' }}>
                      {hapagTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No HAPAG routes available</div>
          )}
        </div>
      </div>
    </>
  );
};

export default SummaryDashboard;
