import React from 'react';
import { Route } from '../types';

interface RouteTableProps {
  title: string;
  routes: Route[];
  currency: string;
  variant: 'top' | 'worst';
  showRemarks?: boolean;
}

// POD estimation notes for ports with unavailable freight costs
const POD_NOTES: Record<string, string> = {
  'BREMERHAVEN, HB, GERMANY': '* estimation based on Hamburg, Germany (freight cost unavailable)',
  'SALERNO, ITALY': '* estimated based on Naples, Italy (freight cost unavailable)',
};

const formatRate = (rate: number): string => {
  return rate.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
};

const RouteTable: React.FC<RouteTableProps> = ({
  title,
  routes,
  currency,
  variant,
  showRemarks = false,
}) => {
  const cardClass = variant === 'worst' ? 'card card--worst' : 'card';
  const badgeClass = variant === 'worst' ? 'rank-badge rank-badge--worst' : 'rank-badge rank-badge--top';

  // Check if any routes have estimation notes
  const routesWithNotes = routes.filter((route) => POD_NOTES[route.pod]);

  return (
    <div className={cardClass}>
      <div className="card-header">
        <h2 className="card-title">{title}</h2>
      </div>
      <div className="card-body">
        <div className="route-table-container">
          <table className="route-table">
            <thead>
              <tr>
                <th className="col-rank">Rank</th>
                <th>POD (Intermediate Port)</th>
                {showRemarks ? (
                  <th>Remarks</th>
                ) : (
                  <th>Transport Mode</th>
                )}
                <th className="col-rate">Inland</th>
                <th className="col-rate">Ocean</th>
                <th className="col-rate">Total Rate (EUR)</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((route) => (
                <tr key={route.rank}>
                  <td className="col-rank">
                    <span className={badgeClass}>{route.rank}</span>
                  </td>
                  <td>
                    {route.pod}
                    {POD_NOTES[route.pod] && <span className="pod-note-marker"> *</span>}
                  </td>
                  {showRemarks ? (
                    <td style={{ maxWidth: 320, whiteSpace: 'pre-line', wordBreak: 'break-word' }}>{route.remarks || '-'}</td>
                  ) : (
                    <td>{route.mode}</td>
                  )}
                  <td className="col-rate">
                    <span className="rate-value">
                      {formatRate(route.inlandRate || 0)}
                    </span>
                  </td>
                  <td className="col-rate">
                    <span className="rate-value">
                      {formatRate(route.oceanRate || 0)}
                    </span>
                  </td>
                  <td className="col-rate">
                    <span className="rate-value">
                      {formatRate(route.totalRate)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Estimation notes footer */}
        {routesWithNotes.length > 0 && (
          <div className="table-notes">
            {routesWithNotes.map((route) => (
              <p key={route.pod} className="note-text">
                {POD_NOTES[route.pod]}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RouteTable;
