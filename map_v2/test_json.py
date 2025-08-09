import json

with open('routes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Type: {type(data)}")
if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
    # Check what's in the data key
    if 'data' in data:
        inner_data = data['data']
        print(f"Data type: {type(inner_data)}")
        if isinstance(inner_data, dict):
            print(f"Inner data keys: {list(inner_data.keys())}")
            # Check if there's a routes key
            if 'routes' in inner_data:
                routes = inner_data['routes']
                print(f"Routes type: {type(routes)}")
                print(f"Number of routes: {len(routes)}")
                if len(routes) > 0:
                    first_route = routes[0]
                    print(f"First route keys: {list(first_route.keys())}")
                    print(f"First route mode: {first_route.get('mode')}")
elif isinstance(data, list):
    print(f"Number of items: {len(data)}")
    if len(data) > 0:
        first_item = data[0]
        print(f"First item type: {type(first_item)}")
        if isinstance(first_item, dict):
            print(f"First item keys: {list(first_item.keys())}")
            print(f"First item mode: {first_item.get('mode')}") 