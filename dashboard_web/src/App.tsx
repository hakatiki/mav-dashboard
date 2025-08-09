import React from 'react';
import TrainMap from './components/TrainMap';
import StatsPanel from './components/StatsPanel';
import Legend from './components/Legend';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorDisplay from './components/ErrorDisplay';
import { useTrainData } from './hooks/useTrainData';

const App: React.FC = () => {
  const { segments, statistics, loading, error, retry } = useTrainData();

  if (loading) {
    return <LoadingSpinner message="Loading Hungary train delay data..." />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={retry} />;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">🚂 Hungary Train Delays Dashboard</h1>
        <p className="dashboard-subtitle">
          Interactive map showing train routes colored by average delay
        </p>
      </header>
      
      <main className="dashboard-content">
        <div className="map-container">
          <TrainMap segments={segments} statistics={statistics} />
          <StatsPanel statistics={statistics} />
          <Legend />
        </div>
      </main>
    </div>
  );
};

export default App; 