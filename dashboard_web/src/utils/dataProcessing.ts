import { Route, BulkData, RouteSegmentWithDelay, DelayStatistics, Stop } from '../types';

/**
 * Extract pure station ID from complex route ID format
 */
export function extractPureStationId(rawId: string): string {
  try {
    return rawId.split(':')[1].split('_')[0];
  } catch {
    return rawId;
  }
}

/**
 * Get color based on delay minutes
 */
export function getDelayColor(delayMinutes: number): string {
  if (delayMinutes <= 0) return '#00FF00';  // Green for on time
  if (delayMinutes <= 2) return '#FFFF00';  // Yellow for slight delay
  if (delayMinutes <= 5) return '#FFA500';  // Orange for moderate delay
  if (delayMinutes <= 10) return '#FF6600'; // Red-orange for significant delay
  return '#FF0000';  // Red for major delay
}

/**
 * Get line weight based on delay
 */
export function getDelayWeight(delayMinutes: number): number {
  if (delayMinutes <= 0) return 2;
  if (delayMinutes <= 2) return 3;
  if (delayMinutes <= 5) return 4;
  if (delayMinutes <= 10) return 5;
  return 6;
}

/**
 * Create a mapping of station pairs to delay information
 */
export function createStationDelayMap(bulkDataList: BulkData[]) {
  const stationDelays = new Map<string, {
    start_station: string;
    end_station: string;
    average_delay: number;
    max_delay: number;
    sample_count: number;
  }>();

  for (const bulkData of bulkDataList) {
    const pairKey = `${bulkData.start_station}-${bulkData.end_station}`;
    
    // Collect all delays from route segments
    const delays: number[] = [];
    
    for (const route of bulkData.routes) {
      for (const segment of route.route_segments) {
        if (segment.departure_delay > 0) delays.push(segment.departure_delay);
        if (segment.arrival_delay > 0) delays.push(segment.arrival_delay);
      }
    }

    const avgDelay = delays.length > 0 ? delays.reduce((a, b) => a + b, 0) / delays.length : 0;
    const maxDelay = delays.length > 0 ? Math.max(...delays) : 0;

    stationDelays.set(pairKey, {
      start_station: bulkData.start_station,
      end_station: bulkData.end_station,
      average_delay: avgDelay,
      max_delay: maxDelay,
      sample_count: delays.length
    });
  }

  return stationDelays;
}

/**
 * Find route segments that connect two stations
 */
export function findRouteSegmentsForStations(
  routes: Route[], 
  startId: string, 
  endId: string
): Array<{ route: Route; pattern: any; startIdx: number; endIdx: number }> {
  const matchingSegments: Array<{ route: Route; pattern: any; startIdx: number; endIdx: number }> = [];

  for (const route of routes) {
    for (const pattern of route.patterns) {
      const stationIds = pattern.stops.map((stop: Stop) => extractPureStationId(stop.raw_id));
      
      const startIndices = stationIds.map((id, idx) => id === startId ? idx : -1).filter(idx => idx !== -1);
      const endIndices = stationIds.map((id, idx) => id === endId ? idx : -1).filter(idx => idx !== -1);

      for (const startIdx of startIndices) {
        for (const endIdx of endIndices) {
          if (endIdx > startIdx) {
            matchingSegments.push({ route, pattern, startIdx, endIdx });
          }
        }
      }
    }
  }

  return matchingSegments;
}

/**
 * Create route segments enriched with delay information
 */
export function createRouteSegmentsWithDelays(
  routes: Route[],
  stationDelays: Map<string, any>
): RouteSegmentWithDelay[] {
  const segments: RouteSegmentWithDelay[] = [];
  const processedPairs = new Set<string>();

  for (const [pairKey, delayInfo] of stationDelays) {
    if (processedPairs.has(pairKey)) continue;
    processedPairs.add(pairKey);

    const routeSegments = findRouteSegmentsForStations(
      routes,
      delayInfo.start_station,
      delayInfo.end_station
    );

    for (const { route, pattern, startIdx, endIdx } of routeSegments) {
      const coordinates: [number, number][] = [];
      const stationNames: string[] = [];

      for (let i = startIdx; i <= endIdx; i++) {
        const stop = pattern.stops[i];
        coordinates.push([stop.lat, stop.lon]);
        stationNames.push(stop.name);
      }

      if (coordinates.length >= 2) {
        const segment: RouteSegmentWithDelay = {
          coordinates,
          route_desc: route.desc || 'Unknown Route',
          pattern_name: pattern.headsign || 'Unknown Pattern',
          start_station: stationNames[0],
          end_station: stationNames[stationNames.length - 1],
          average_delay: delayInfo.average_delay,
          max_delay: delayInfo.max_delay,
          sample_count: delayInfo.sample_count,
          color: getDelayColor(delayInfo.average_delay),
          weight: getDelayWeight(delayInfo.average_delay),
          stations: stationNames
        };
        segments.push(segment);
      }
    }
  }

  return segments;
}

/**
 * Calculate summary statistics from delay data
 */
export function createStatisticsSummary(stationDelays: Map<string, any>): DelayStatistics {
  const delays = Array.from(stationDelays.values()).map(info => info.average_delay);
  
  if (delays.length === 0) {
    return {
      total_routes: 0,
      average_delay: 0,
      median_delay: 0,
      max_delay: 0,
      routes_on_time: 0,
      routes_delayed: 0,
      routes_significantly_delayed: 0,
      on_time_percentage: 0
    };
  }

  const sortedDelays = [...delays].sort((a, b) => a - b);
  const median = sortedDelays[Math.floor(sortedDelays.length / 2)];
  const average = delays.reduce((a, b) => a + b, 0) / delays.length;
  const max = Math.max(...delays);
  
  const onTime = delays.filter(d => d <= 0).length;
  const delayed = delays.filter(d => d > 0).length;
  const significantlyDelayed = delays.filter(d => d > 5).length;

  return {
    total_routes: delays.length,
    average_delay: average,
    median_delay: median,
    max_delay: max,
    routes_on_time: onTime,
    routes_delayed: delayed,
    routes_significantly_delayed: significantlyDelayed,
    on_time_percentage: (onTime / delays.length) * 100
  };
} 