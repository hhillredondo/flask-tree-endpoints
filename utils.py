import json

def normalize_data(gremlin_data):
    # Convert to JSON string and back to ensure it's a plain dictionary
    map_stripped_data = json.loads(json.dumps(gremlin_data, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x)))
    
    return map_stripped_data