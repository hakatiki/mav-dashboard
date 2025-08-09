import { useState, useEffect } from 'react';
import { Route, BulkData, RouteSegmentWithDelay, DelayStatistics } from '../types';
import { DataLoader } from '../services/dataLoader';
import { 
  createStationDelayMap, 
  createRouteSegmentsWithDelays, 
  createStatisticsSummary 
} from '../utils/dataProcessing';

interface UseTrainDataResult {
  segments: RouteSegmentWithDelay[];
  statistics: DelayStatistics;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export const useTrainData = (): UseTrainDataResult => {
  const [segments, setSegments] = useState<RouteSegmentWithDelay[]>([]);
  const [statistics, setStatistics] = useState<DelayStatistics>({
    total_routes: 0,
    average_delay: 0,
    median_delay: 0,
    max_delay: 0,
    routes_on_time: 0,
    routes_delayed: 0,
    routes_significantly_delayed: 0,
    on_time_percentage: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const dataLoader = DataLoader.getInstance();
      
      // Load data in parallel
      const [routes, bulkData] = await Promise.all([
        dataLoader.loadRouteData(),
        dataLoader.loadBulkData()
      ]);

      console.log('Loaded data:', { routesCount: routes.length, bulkDataCount: bulkData.length });

      // Process the data
      const stationDelays = createStationDelayMap(bulkData);
      console.log('Station delays map:', stationDelays);

      const processedSegments = createRouteSegmentsWithDelays(routes, stationDelays);
      console.log('Processed segments:', processedSegments.length);

      const calculatedStatistics = createStatisticsSummary(stationDelays);
      console.log('Statistics:', calculatedStatistics);

      setSegments(processedSegments);
      setStatistics(calculatedStatistics);
    } catch (err) {
      console.error('Error loading train data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const retry = () => {
    loadData();
  };

  useEffect(() => {
    loadData();
  }, []);

  return {
    segments,
    statistics,
    loading,
    error,
    retry
  };
}; 