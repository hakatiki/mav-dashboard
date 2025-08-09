import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = 'Loading train delay data...' 
}) => {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <div className="loading-text">{message}</div>
    </div>
  );
};

export default LoadingSpinner; 