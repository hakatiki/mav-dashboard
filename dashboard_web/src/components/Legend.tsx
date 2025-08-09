import React from 'react';
import { LegendProps } from '../types';

const Legend: React.FC<LegendProps> = () => {
  const legendItems = [
    { color: '#00FF00', label: 'On Time (0 min)' },
    { color: '#FFFF00', label: 'Slight (≤2 min)' },
    { color: '#FFA500', label: 'Moderate (3-5 min)' },
    { color: '#FF6600', label: 'Significant (6-10 min)' },
    { color: '#FF0000', label: 'Major (>10 min)' }
  ];

  return (
    <div className="legend-panel">
      <h3 className="legend-title">Delay Legend</h3>
      
      {legendItems.map((item, index) => (
        <div key={index} className="legend-item">
          <div 
            className="legend-color" 
            style={{ backgroundColor: item.color }}
          />
          <span className="legend-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
};

export default Legend; 