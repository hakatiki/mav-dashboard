import { Route, BulkData } from '../types';

/**
 * Service to load train route and delay data
 */
export class DataLoader {
  private static instance: DataLoader;
  private routeCache: Route[] | null = null;
  private bulkDataCache: BulkData[] | null = null;

  static getInstance(): DataLoader {
    if (!DataLoader.instance) {
      DataLoader.instance = new DataLoader();
    }
    return DataLoader.instance;
  }

  /**
   * Load route data from JSON files
   */
  async loadRouteData(): Promise<Route[]> {
    if (this.routeCache) {
      return this.routeCache;
    }

    try {
      // For demo purposes, we'll create some sample data
      // In a real app, you'd fetch from your data directory
      const sampleRoutes: Route[] = await this.loadSampleRouteData();
      
      this.routeCache = sampleRoutes;
      return sampleRoutes;
    } catch (error) {
      console.error('Error loading route data:', error);
      throw new Error('Failed to load route data');
    }
  }

  /**
   * Load bulk delay data from JSON files
   */
  async loadBulkData(): Promise<BulkData[]> {
    if (this.bulkDataCache) {
      return this.bulkDataCache;
    }

    try {
      // For demo purposes, we'll create some sample data
      // In a real app, you'd fetch from your analytics data directory
      const sampleBulkData: BulkData[] = await this.loadSampleBulkData();
      
      this.bulkDataCache = sampleBulkData;
      return sampleBulkData;
    } catch (error) {
      console.error('Error loading bulk data:', error);
      throw new Error('Failed to load bulk delay data');
    }
  }

  /**
   * Generate sample route data for demo
   */
  private async loadSampleRouteData(): Promise<Route[]> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    return [
      {
        id: '1:1660.',
        desc: 'Orosháza - Békéscsaba',
        agency_name: 'MÁV Személyszállítási Zrt.',
        long_name: 'Sz 7720/7741/7751',
        short_name: '♦',
        mode: 'RAIL',
        route_type: 106,
        color: 'FEFEFE',
        text_color: '00A0E3',
        patterns: [
          {
            id: 'UGF0dGVybjoxOjE2NjAuOjowMQ',
            headsign: 'Békéscsaba',
            from_stop_name: 'Orosháza',
            name: '♦ Békéscsaba',
            stops: [
              {
                raw_id: '1:005518614_0',
                pure_id: '005518614',
                lat: 46.566111,
                lon: 20.664722,
                name: 'Orosháza',
                location_type: 'STOP'
              },
              {
                raw_id: '1:005518622_0',
                pure_id: '005518622',
                lat: 46.596944,
                lon: 20.760556,
                name: 'Orosházi tanyák',
                location_type: 'STOP'
              },
              {
                raw_id: '1:005518630_0',
                pure_id: '005518630',
                lat: 46.623611,
                lon: 20.840833,
                name: 'Csorvás',
                location_type: 'STOP'
              },
              {
                raw_id: '1:005518036_0',
                pure_id: '005518036',
                lat: 46.675556,
                lon: 21.030833,
                name: 'Békéscsaba',
                location_type: 'STOP'
              }
            ]
          }
        ]
      },
      {
        id: '1:1672.',
        desc: 'Szombathely - Szentgotthárd',
        agency_name: 'MÁV Személyszállítási Zrt.',
        long_name: 'Graz Hbf',
        short_name: '♦',
        mode: 'RAIL',
        route_type: 106,
        color: 'FEFEFE',
        text_color: '00A0E3',
        patterns: [
          {
            id: 'UGF0dGVybjoxOjE2NzIuOjowMQ',
            headsign: 'Graz Hbf',
            from_stop_name: 'Szombathely',
            name: '♦ Graz Hbf',
            stops: [
              {
                raw_id: '1:004302246_0',
                pure_id: '004302246',
                lat: 47.237778,
                lon: 16.6325,
                name: 'Szombathely',
                location_type: 'STOP'
              },
              {
                raw_id: '1:004302253_0',
                pure_id: '004302253',
                lat: 47.206389,
                lon: 16.641667,
                name: 'Szombathely-Szőlős',
                location_type: 'STOP'
              },
              {
                raw_id: '1:004302261_0',
                pure_id: '004302261',
                lat: 47.161389,
                lon: 16.630556,
                name: 'Ják-Balogunyom',
                location_type: 'STOP'
              },
              {
                raw_id: '1:004302329_0',
                pure_id: '004302329',
                lat: 46.9572,
                lon: 16.2631,
                name: 'Szentgotthárd',
                location_type: 'STOP'
              }
            ]
          }
        ]
      },
      {
        id: '1:1680.',
        desc: 'Budapest - Debrecen',
        agency_name: 'MÁV Személyszállítási Zrt.',
        long_name: 'InterCity',
        short_name: 'IC',
        mode: 'RAIL',
        route_type: 106,
        color: 'FF0000',
        text_color: 'FFFFFF',
        patterns: [
          {
            id: 'UGF0dGVybjoxOjE2ODAuOjowMQ',
            headsign: 'Debrecen',
            from_stop_name: 'Budapest-Keleti',
            name: 'IC Debrecen',
            stops: [
              {
                raw_id: '1:005502455_0',
                pure_id: '005502455',
                lat: 47.500000,
                lon: 19.083333,
                name: 'Budapest-Keleti',
                location_type: 'STOP'
              },
              {
                raw_id: '1:005503491_0',
                pure_id: '005503491',
                lat: 47.683056,
                lon: 20.266111,
                name: 'Szolnok',
                location_type: 'STOP'
              },
              {
                raw_id: '1:005503947_0',
                pure_id: '005503947',
                lat: 47.531944,
                lon: 21.638889,
                name: 'Debrecen',
                location_type: 'STOP'
              }
            ]
          }
        ]
      }
    ];
  }

  /**
   * Generate sample bulk delay data for demo
   */
  private async loadSampleBulkData(): Promise<BulkData[]> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    return [
      {
        success: true,
        timestamp: '2025-07-23T20:48:09.489224',
        start_station: '004302246',
        end_station: '004302329',
        statistics: {
          total_trains: 8,
          average_delay: 3.5,
          max_delay: 12,
          trains_on_time: 3,
          trains_delayed: 5,
          trains_significantly_delayed: 2,
          on_time_percentage: 37.5,
          delayed_percentage: 62.5
        },
        routes: [
          {
            train_name: 'IC 123',
            departure_time: '08:15',
            arrival_time: '10:45',
            delay_min: 5,
            transfers_count: 0,
            route_segments: [
              {
                leg_number: 1,
                train_number: 'IC 123',
                train_full_name: 'InterCity 123',
                start_station: 'Szombathely',
                end_station: 'Szentgotthárd',
                departure_scheduled: '08:15',
                departure_actual: '08:20',
                departure_delay: 5,
                arrival_scheduled: '10:45',
                arrival_actual: '10:45',
                arrival_delay: 0,
                travel_time: '2:30',
                services: ['Air conditioning', 'WiFi'],
                has_delays: true
              }
            ]
          }
        ]
      },
      {
        success: true,
        timestamp: '2025-07-23T21:15:30.123456',
        start_station: '005518614',
        end_station: '005518036',
        statistics: {
          total_trains: 12,
          average_delay: 2.1,
          max_delay: 8,
          trains_on_time: 8,
          trains_delayed: 4,
          trains_significantly_delayed: 1,
          on_time_percentage: 66.7,
          delayed_percentage: 33.3
        },
        routes: [
          {
            train_name: 'Regional 456',
            departure_time: '14:30',
            arrival_time: '15:45',
            delay_min: 3,
            transfers_count: 0,
            route_segments: [
              {
                leg_number: 1,
                train_number: 'R 456',
                train_full_name: 'Regional 456',
                start_station: 'Orosháza',
                end_station: 'Békéscsaba',
                departure_scheduled: '14:30',
                departure_actual: '14:33',
                departure_delay: 3,
                arrival_scheduled: '15:45',
                arrival_actual: '15:45',
                arrival_delay: 0,
                travel_time: '1:15',
                services: ['Standard seating'],
                has_delays: true
              }
            ]
          }
        ]
      },
      {
        success: true,
        timestamp: '2025-07-23T19:30:15.789012',
        start_station: '005502455',
        end_station: '005503947',
        statistics: {
          total_trains: 15,
          average_delay: 8.7,
          max_delay: 25,
          trains_on_time: 2,
          trains_delayed: 13,
          trains_significantly_delayed: 8,
          on_time_percentage: 13.3,
          delayed_percentage: 86.7
        },
        routes: [
          {
            train_name: 'IC 789',
            departure_time: '16:20',
            arrival_time: '19:35',
            delay_min: 12,
            transfers_count: 0,
            route_segments: [
              {
                leg_number: 1,
                train_number: 'IC 789',
                train_full_name: 'InterCity 789 Budapest-Debrecen',
                start_station: 'Budapest-Keleti',
                end_station: 'Debrecen',
                departure_scheduled: '16:20',
                departure_actual: '16:32',
                departure_delay: 12,
                arrival_scheduled: '19:35',
                arrival_actual: '19:47',
                arrival_delay: 12,
                travel_time: '3:15',
                services: ['Air conditioning', 'Restaurant car', 'WiFi'],
                has_delays: true
              }
            ]
          }
        ]
      }
    ];
  }

  /**
   * Clear cache (useful for development/testing)
   */
  clearCache(): void {
    this.routeCache = null;
    this.bulkDataCache = null;
  }
} 