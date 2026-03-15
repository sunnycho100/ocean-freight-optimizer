import React from 'react';
import { Route } from '../types';
import { useI18n } from '../i18n';

interface RouteTableProps {
  title: string;
  routes: Route[];
  currency: string;
  variant: 'top' | 'worst';
  showRemarks?: boolean;
}

// POD estimation notes for ports with unavailable freight costs
const POD_NOTE_KEYS: Record<string, 'podNoteBremerhaven' | 'podNoteSalerno'> = {
  'BREMERHAVEN, HB, GERMANY': 'podNoteBremerhaven',
  'SALERNO, ITALY': 'podNoteSalerno',
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
  const { t } = useI18n();
  const cardClass = variant === 'worst' ? 'card card--worst' : 'card';
  const badgeClass = variant === 'worst' ? 'rank-badge rank-badge--worst' : 'rank-badge rank-badge--top';

  // Check if any routes have estimation notes
  const routesWithNotes = routes.filter((route) => POD_NOTE_KEYS[route.pod]);

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
                <th className="col-rank">{t('rank')}</th>
                <th>{t('pod')}</th>
                {showRemarks ? (
                  <th>{t('remarks')}</th>
                ) : (
                  <th>{t('transportMode')}</th>
                )}
                <th className="col-rate">{t('inland')}</th>
                <th className="col-rate">{t('ocean')}</th>
                <th className="col-rate">{t('totalRateEUR')}</th>
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
                    {POD_NOTE_KEYS[route.pod] && <span className="pod-note-marker"> *</span>}
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
                {t(POD_NOTE_KEYS[route.pod])}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RouteTable;
