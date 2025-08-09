import React from 'react';
import { MapContainer, TileLayer, Polyline, Popup } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { MapProps } from '../types';
import 'leaflet/dist/leaflet.css';

const TrainMap: React.FC<MapProps> = ({ segments }) => {
  // Hungary center coordinates
  const hungaryCenter: LatLngExpression = [47.1625, 19.5033];
  
  return (
    <MapContainer
      center={hungaryCenter}
      zoom={7}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      
      {segments.map((segment, index) => (
        <Polyline
          key={index}
          positions={segment.coordinates}
          color={segment.color}
          weight={segment.weight}
          opacity={0.8}
        >
          <Popup>
            <div style={{ maxWidth: '300px' }}>
              <div className="popup-title">{segment.route_desc}</div>
              
              <div className="popup-section">
                <div className="popup-label">Pattern:</div>
                <div className="popup-value">{segment.pattern_name}</div>
              </div>
              
              <div className="popup-section">
                <div className="popup-label">From:</div>
                <div className="popup-value">{segment.start_station}</div>
              </div>
              
              <div className="popup-section">
                <div className="popup-label">To:</div>
                <div className="popup-value">{segment.end_station}</div>
              </div>
              
              <div className="popup-section">
                <strong>Delay Information:</strong>
                <br />
                <div className="popup-label">Average Delay:</div>
                <div className="popup-value">{segment.average_delay.toFixed(1)} minutes</div>
                <div className="popup-label">Max Delay:</div>
                <div className="popup-value">{segment.max_delay} minutes</div>
                <div className="popup-label">Samples:</div>
                <div className="popup-value">{segment.sample_count}</div>
              </div>
              
              <div className="popup-section">
                <strong>Stations:</strong>
                <div className="popup-stations">
                  {segment.stations.join(' → ')}
                </div>
              </div>
            </div>
          </Popup>
        </Polyline>
      ))}
    </MapContainer>
  );
};

export default TrainMap; 