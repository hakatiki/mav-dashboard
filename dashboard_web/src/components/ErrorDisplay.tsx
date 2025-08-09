import React from 'react';

interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry }) => {
  return (
    <div className="error-container">
      <h2 className="error-title">⚠️ Error Loading Data</h2>
      <p className="error-message">{error}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '500'
          }}
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorDisplay; 