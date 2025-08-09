# all_routes_breakdown

JSON files listing MÁV railway routes and stops, with station names, coordinates, and IDs.

- **Mode**: The type of transport, e.g., "RAIL".
- **Stops**: An array of stops along the route. Each stop entry includes:
  - Unique stop ID and code
  - Name of the station
  - Geographic coordinates (latitude and longitude)
  - Location type (e.g., "STOP")
  - Geometries in GeoJSON format for mapping


## Daily Route Data Exports

In addition to the full route and stop data, there are daily JSON exports containing all trains for a given day between a specific pair of stations or along a line. These files are located at:

mpt-all-sources/blog/mav/json_output/YYYY-MM-DD

This data only conatins legs so no stop level attribution or latitude and longitude.

