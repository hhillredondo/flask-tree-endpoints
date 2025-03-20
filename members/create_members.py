from flask import jsonify, request
import json

def normalize_data(gremlin_data):
    # Convert to JSON string and back to ensure it's a plain dictionary
    map_stripped_data = json.loads(json.dumps(gremlin_data, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x)))
    
    return map_stripped_data


def create_member_query(g):
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        name = data.get('name')
        description = data.get('description')
        born = data.get('born')

        # Input validation
        required_fields = ['name', 'description', 'born']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        new_member = g.addV('_Member').property('name', name).property('description', description).property('born', born).next()


        return normalize_data(new_member), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
