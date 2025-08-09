import React from 'react';
import { StatsProps } from '../types';

const StatsPanel: React.FC<StatsProps> = ({ statistics }) => {
  return (
    <div className="stats-panel">
      <h3 className="stats-title">Summary Statistics</h3>
      
      <div className="stat-item">
        <span className="stat-label">Total Routes</span>
        <span className="stat-value">{statistics.total_routes}</span>
      </div>
      
      <div className="stat-item">
        <span className="stat-label">Average Delay</span>
        <span className="stat-value">{statistics.average_delay.toFixed(1)} min</span>
      </div>
      
      <div className="stat-item">
        <span className="stat-label">Median Delay</span>
        <span className="stat-value">{statistics.median_delay.toFixed(1)} min</span>
      </div>
      
      <div className="stat-item">
        <span className="stat-label">Max Delay</span>
        <span className="stat-value">{statistics.max_delay.toFixed(1)} min</span>
      </div>
      
      <div className="stat-item">
        <span className="stat-label">On Time</span>
        <span className="stat-value">{statistics.on_time_percentage.toFixed(1)}%</span>
      </div>
      
      <div className="stat-item">
        <span className="stat-label">Significantly Delayed</span>
        <span className="stat-value">{statistics.routes_significantly_delayed}</span>
      </div>
    </div>
  );
};

export default StatsPanel; 