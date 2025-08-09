// Route data types
export interface Stop {
  raw_id: string;
  pure_id: string;
  lat: number;
  lon: number;
  name: string;
  location_type: string;
}

export interface Pattern {
  id: string;
  headsign: string;
  from_stop_name: string;
  name: string;
  stops: Stop[];
}

export interface Route {
  id: string;
  desc: string;
  agency_name: string;
  long_name: string;
  short_name: string;
  mode: string;
  route_type: number;
  color: string;
  text_color: string;
  patterns: Pattern[];
}

// Delay data types
export interface RouteSegment {
  leg_number: number;
  train_name?: string;
  train_number: string;
  train_full_name: string;
  start_station: string;
  end_station: string;
  departure_scheduled: string;
  departure_actual?: string;
  departure_delay: number;
  arrival_scheduled: string;
  arrival_actual?: string;
  arrival_delay: number;
  travel_time: string;
  services: string[];
  has_delays: boolean;
}

export interface Statistics {
  total_trains: number;
  average_delay: number;
  max_delay: number;
  trains_on_time: number;
  trains_delayed: number;
  trains_significantly_delayed: number;
  on_time_percentage: number;
  delayed_percentage: number;
}

export interface BulkData {
  success: boolean;
  timestamp: string;
  start_station: string;
  end_station: string;
  travel_date?: string;
  statistics: Statistics;
  routes: Array<{
    train_name: string;
    departure_time: string;
    arrival_time: string;
    delay_min: number;
    transfers_count: number;
    route_segments: RouteSegment[];
  }>;
}

// Processed data types for visualization
export interface RouteSegmentWithDelay {
  coordinates: [number, number][];
  route_desc: string;
  pattern_name: string;
  start_station: string;
  end_station: string;
  average_delay: number;
  max_delay: number;
  sample_count: number;
  color: string;
  weight: number;
  stations: string[];
}

export interface DelayStatistics {
  total_routes: number;
  average_delay: number;
  median_delay: number;
  max_delay: number;
  routes_on_time: number;
  routes_delayed: number;
  routes_significantly_delayed: number;
  on_time_percentage: number;
}

// UI component props
export interface MapProps {
  segments: RouteSegmentWithDelay[];
  statistics: DelayStatistics;
  loading?: boolean;
}

export interface StatsProps {
  statistics: DelayStatistics;
}

export interface LegendProps {
  // No additional props needed
}

// Color scale type
export type DelayColor = '#00FF00' | '#FFFF00' | '#FFA500' | '#FF6600' | '#FF0000'; 