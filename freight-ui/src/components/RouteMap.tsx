import React from 'react';
import {
  generateGoogleMapsDirectionsUrl,
  generateGoogleMapsEmbedUrl,
  cleanLocationString,
} from '../utils/googleMapsHelper';

interface RouteMapProps {
  pod: string;
  destination: string;
  rankLabel?: string;
  variant?: 'single' | 'grid';
}

const RouteMap: React.FC<RouteMapProps> = ({ pod, destination, rankLabel, variant = 'single' }) => {
  if (!pod || !destination) return null;
  
  const mapsUrl = generateGoogleMapsDirectionsUrl(pod, destination);
  const embedUrl = generateGoogleMapsEmbedUrl(pod, destination);
  const cleanPod = cleanLocationString(pod);
  const cleanDest = cleanLocationString(destination);
  const isGrid = variant === 'grid';
  
  const handleViewRoute = () => {
    window.open(mapsUrl, '_blank', 'noopener,noreferrer');
  };
  
  return (
    <div className={`route-map-container ${isGrid ? 'route-map--grid' : ''}`}>
      <div className="route-info">
        <h3 className="route-info-title">{rankLabel || 'Route Information'}</h3>
        <div className={`route-path ${isGrid ? 'route-path--compact' : ''}`}>
          <div className="route-location">
            <span className="route-value">{cleanPod}</span>
          </div>
          <div className="route-arrow">↓</div>
          <div className="route-location">
            <span className="route-value">{cleanDest}</span>
          </div>
        </div>
      </div>

      <div className="map-embed-wrapper">
        <iframe
          title={`Route from ${cleanPod} to ${cleanDest}`}
          src={embedUrl}
          className="map-embed"
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>

      <button 
        className="btn-view-route btn-view-route--small"
        onClick={handleViewRoute}
        type="button"
      >
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
          style={{ marginRight: 6 }}
        >
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        View in Google Maps
      </button>

      {!isGrid && (
        <p className="route-note">
          Opens Google Maps in a new tab with directions from {cleanPod} to {cleanDest}
        </p>
      )}

      <p className="map-caption">
        Inline preview. Use the button for full directions.
      </p>
    </div>
  );
};

export default RouteMap;